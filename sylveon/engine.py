"""The Doctor AI engine. Code decides every step; the LLM (optional) only rewrites wording.

Order on every patient message:
  1. safety gate (phrases + optional LLM classifier) -> crisis path stops everything
  2. blocked topics (medicine / diagnosis / impersonation) -> decline + save for the doctor
  3. active flashcard walk -> next line, word for word
  4. hard-moment trigger -> offer the doctor's flashcard
  5. homework / question about therapy -> only from the doctor's approved notes
  6. otherwise -> schema route-map check-in (one question per step)
"""
import re
import time

from . import llm, safety, store

HELPLINE = "Tele-MANAS 14416 (free, 24x7, many Indian languages)"

STEPS = ["what_happened", "trigger", "feeling_body", "need", "coping", "next_step"]
Q = {  # one question per route-map step: (english, hinglish)
    "what_happened": ("That sounds heavy. What happened today?", "Ye kaafi heavy lag raha hai. Aaj kya hua?"),
    "trigger": ("What was the moment it got worse?", "Kis moment pe ye sabse zyada badh gaya?"),
    "feeling_body": ("What are you feeling right now, and where do you feel it in your body?",
                     "Abhi andar kya feel ho raha hai, aur body mein kahan feel ho raha hai?"),
    "need": ("When you feel this, what do you need most?", "Jab aisa lagta hai, tab tumhe sabse zyada kis cheez ki zarurat hoti hai?"),
    "coping": ("In moments like this, what do you usually do?", "Aise moments mein tum usually kya karte ho?"),
    "next_step": ("Thank you for walking through this. Want to try one small step your Healthy Adult can take right now?",
                  "Thanks ye sab share karne ke liye. Ek chhota step try karein jo tumhara Healthy Adult abhi le sakta hai?"),
}
HINGLISH = re.compile(r"\b(hai|nahi|kya|mujhe|main|mera|meri|yaar|bahut|kar|raha|rahi|hoon|kyun|aaj|kal|sab|abhi|tha|thi)\b")
YES = re.compile(r"^\s*(ok|okay|yes|ya|haan|han|ha|sure|chalo|theek|thik|next|done|hmm|k)\b", re.I)


def lang_of(text: str) -> str:
    return "hinglish" if HINGLISH.search(text.lower()) or re.search(r"[ऀ-ॿ]", text) else "english"


def _t(key: str, lang: str) -> str:
    e, h = Q[key]
    return h if lang == "hinglish" else e


def _state(db: dict, pid: str) -> dict:
    return db.setdefault("state", {}).setdefault(pid, {"mode": "checkin", "step": 0, "slots": {}, "card": None, "line": 0})


def _event(db, pid, kind, **kw):
    db["events"].append({"patient": pid, "kind": kind, "ts": time.time(), **kw})


def _final(text: str, doctor: dict, user_text: str, lang: str, keep_exact: bool = False) -> tuple[str, dict]:
    """Optionally reword with the LLM, then run the reply filter. Falls back to the safe draft."""
    out, via = text, "template"
    if not keep_exact:
        r = llm.reword(text, doctor, user_text, lang)
        if r:
            broken = safety.check_reply(r)
            if broken:
                via = "template (LLM reply blocked by filter)"
            else:
                out, via = r, "llm"
    return out, {"wording": via}


def handle(pid: str, text: str) -> dict:
    db = store.load()
    pat = db["patients"][pid]
    doc = db["doctors"][pat["doctor"]]
    st = _state(db, pid)
    lang = lang_of(text)
    intro = f"I'm {doc['name']}'s AI." if lang == "english" else f"Main {doc['name']} ka AI hoon."
    db["messages"].append({"patient": pid, "sender": "patient", "text": text, "ts": time.time()})

    # 1. safety gate -----------------------------------------------------------------
    s = safety.check_message(text)
    llm_lvl = llm.classify_risk(text)
    level = safety.max_level(s["level"], llm_lvl) if llm_lvl else s["level"]
    meta = {"risk": level, "phrase_level": s["level"], "llm_level": llm_lvl, "blocked": s["blocked"]}
    if level in ("medium", "high"):
        st.update(mode="crisis")
        alerted = level in doc["escalation"]["alert_on"]
        _event(db, pid, "safety", level=level, text=text, doctor_alerted=alerted, helpline=HELPLINE)
        reply = (f"{intro} Thank you for telling me. I want you to have a real person with you right now. "
                 f"Are you safe at this moment? You can talk to a trained counsellor now, free: {HELPLINE}. "
                 f"{doc['name']} has been alerted. I'll stay here while you reach them.")
        if lang == "hinglish":
            reply = (f"{intro} Mujhe batane ke liye thank you. Main chahta hoon ki abhi tumhare saath ek real insaan ho. "
                     f"Kya tum abhi safe ho? Abhi free mein trained counsellor se baat kar sakte ho: {HELPLINE}. "
                     f"{doc['name']} ko alert kar diya gaya hai. Main yahin hoon jab tak tum unse baat karo.")
        return _reply(db, pid, reply, {**meta, "path": "crisis", "doctor_alerted": alerted, "wording": "fixed (never reworded)"})

    # 2. blocked topics -----------------------------------------------------------------
    if s["blocked"]:
        _event(db, pid, "saved_question", topic=s["blocked"], text=text)
        msgs = {
            "medicine": ("I can't advise on medicines or doses, only {d} can. I've saved your question for {d} so it's answered properly. Is something else bothering you right now?",
                         "Dawai ya dose pe main advice nahi de sakta, ye sirf {d} bata sakte hain. Maine tumhara sawaal {d} ke liye save kar diya hai. Abhi aur kuch pareshan kar raha hai?"),
            "diagnosis": ("I can't diagnose or name what you have, that's for {d} in session. I've saved this question for your next visit. What made you wonder about it today?",
                          "Main diagnose nahi kar sakta, ye {d} session mein discuss karenge. Maine ye sawaal next visit ke liye save kar liya. Aaj ye sawaal kyun aaya?"),
            "impersonation": ("I'm an AI that helps between sessions, not {d} and not a human. I follow only what {d} approved. What would help right now?",
                              "Main ek AI hoon jo sessions ke beech help karta hai, {d} ya insaan nahi. Main sirf wahi follow karta hoon jo {d} ne approve kiya. Abhi kya help karega?"),
        }
        e, h = msgs[s["blocked"]]
        reply = (h if lang == "hinglish" else e).format(d=doc["name"])
        return _reply(db, pid, f"{intro} {reply}", {**meta, "path": f"blocked:{s['blocked']}", "wording": "fixed"})

    # 3. active flashcard walk ----------------------------------------------------------
    if st["mode"] == "flashcard" and st["card"]:
        card = next(c for c in doc["flashcards"] if c["id"] == st["card"])
        if st["line"] < len(card["lines"]):
            i = st["line"]
            st["line"] += 1
            more = st["line"] < len(card["lines"])
            line = f'Line {i + 1}, in {doc["name"]}\'s words: "{card["lines"][i]}"'
            tail = (" Read it slowly. Ready for the next line?" if lang == "english" else " Dheere se padho. Next line ke liye ready?") if more else \
                   (" That's the whole card. How does it feel now, from 0 to 10?" if lang == "english" else " Card poora ho gaya. Ab kaisa lag raha hai, 0 se 10?")
            if not more:
                st.update(mode="checkin", step=0, card=None, line=0)
                _event(db, pid, "flashcard_done", card=card["id"])
            return _reply(db, pid, line + tail, {**meta, "path": "flashcard", "card": card["id"], "wording": "doctor's exact words"})

    # 4. hard moment -> offer the doctor's flashcard ------------------------------------
    low = text.lower()
    for card in doc["flashcards"]:
        if any(tr in low for tr in card["triggers"]):
            st.update(mode="flashcard", card=card["id"], line=0)
            _event(db, pid, "flashcard_offered", card=card["id"], text=text)
            draft = (f"{intro} That sounds really heavy. This is the moment your flashcard is for. Want to open it together?"
                     if lang == "english" else f"{intro} Ye bahut heavy lag raha hai. Isi moment ke liye tumhara flashcard hai. Saath mein kholein?")
            out, w = _final(draft, doc, text, lang)
            return _reply(db, pid, out, {**meta, "path": "flashcard_offer", **w})

    # 5. homework / approved notes -------------------------------------------------------
    if re.search(r"\b(homework|diary|kaam|task)\b", low):
        hw = doc["homework"][0]
        _event(db, pid, "homework", text=text, done=bool(re.search(r"\b(did|done|kiya|kar liya|likh)", low)))
        draft = f'{intro} Your homework from {doc["name"]}: "{hw["text"]}" Want to write tonight\'s line now?'
        return _reply(db, pid, draft, {**meta, "path": "homework", "note": hw["id"], "wording": "doctor's exact words"})
    if "?" in text and re.search(r"\b(why|what|how|kyun|kya|kaise)\b", low):
        words = set(re.findall(r"[a-z]{4,}", low))
        best = max(doc["approved_notes"], key=lambda n: len(words & set(re.findall(r"[a-z]{4,}", (n["text"] + " " + n["topic"]).lower()))))
        overlap = len(words & set(re.findall(r"[a-z]{4,}", (best["text"] + " " + best["topic"]).lower())))
        if overlap >= 2:
            return _reply(db, pid, f'{intro} From {doc["name"]}\'s notes: "{best["text"]}"', {**meta, "path": "approved_note", "note": best["id"], "wording": "doctor's exact words"})
        _event(db, pid, "saved_question", topic="not in approved notes", text=text)
        draft = f"{intro} {doc['name']} hasn't given me notes on that, so I won't guess. I've saved it for your next session."
        return _reply(db, pid, draft, {**meta, "path": "not_in_notes", "wording": "fixed"})

    # 6. route-map check-in ---------------------------------------------------------------
    st["mode"] = "checkin"
    step = st["step"]
    if step > 0:
        st["slots"][STEPS[step - 1]] = text
    if step >= len(STEPS):
        st["slots"]["next_step"] = text
        _event(db, pid, "checkin_done", slots=dict(st["slots"]))
        st.update(step=0, slots={})
        draft = ("Good. I've added tonight to your diary for Dr Kabir. Do one small kind thing for yourself now." if lang == "english"
                 else "Achha. Aaj ki baat diary mein add ho gayi, Dr Kabir dekhenge. Ab apne liye ek chhoti si achhi cheez karo.")
        out, w = _final(draft, doc, text, lang)
        return _reply(db, pid, out, {**meta, "path": "checkin_close", **w})
    q = _t(STEPS[step], lang)
    st["step"] = step + 1
    draft = (f"{intro} {q}" if step == 0 else q)
    if level == "low":
        draft += (" I'm here with you." if lang == "english" else " Main yahin hoon.")
    out, w = _final(draft, doc, text, lang)
    return _reply(db, pid, out, {**meta, "path": f"route_map:{STEPS[step]}", **w})


def _reply(db, pid, text, meta):
    db["messages"].append({"patient": pid, "sender": "ai", "text": text, "ts": time.time(), "meta": meta})
    store.save(db)
    return {"reply": text, "meta": meta}


def summary(pid: str) -> dict:
    """Pre-visit summary for the doctor: the patient's own words, flags, homework, saved questions."""
    db = store.load()
    ev = [e for e in db["events"] if e["patient"] == pid]
    own = [m["text"] for m in db["messages"] if m["patient"] == pid and m["sender"] == "patient"]
    return {
        "patient": db["patients"][pid]["name"],
        "flags": [e for e in ev if e["kind"] == "safety"],
        "checkins": [e["slots"] for e in ev if e["kind"] == "checkin_done"],
        "flashcards_used": sum(1 for e in ev if e["kind"] == "flashcard_done"),
        "homework": [e for e in ev if e["kind"] == "homework"],
        "saved_questions": [e for e in ev if e["kind"] == "saved_question"],
        "own_words": own[-12:],
        "messages": len(own),
    }
