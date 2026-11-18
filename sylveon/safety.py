"""Safety gate: runs on every patient message BEFORE anything else, and on every AI reply.

Layer 1 (always on): phrase lists in English, Hindi (Devanagari) and Hinglish.
Layer 2 (when GEMINI_API_KEY is set): an LLM risk classifier (see llm.py).
Rule: when in doubt, escalate. Missing a crisis is far worse than a false alarm.
"""
import re
import unicodedata

# --- crisis signals -----------------------------------------------------------
# HIGH: plan / time / intent stated. MEDIUM: self-harm or suicidal thoughts.
# LOW: hopelessness. Lists are deliberately broad ("when in doubt, escalate").
HIGH = [
    r"\btonight\b.*\b(end|die|kill)", r"\b(end|kill)\b.*\btonight\b", r"\bgoodbye forever\b",
    r"\bplan(ned)? to (die|kill|end)", r"\bwrote (a|my) (suicide )?note\b", r"\blast message\b",
    r"aaj raat.*(khatam|mar)", r"(khatam|mar).*aaj raat", r"\bakhri (baar|message)\b",
    r"kal ke baad koi problem nahi", r"सुसाइड नोट", r"आज रात.*(मर|खत्म)",
]
MEDIUM = [
    r"\bkill (my ?self|me)\b", r"\bend (my|this) life\b", r"\bsuicid", r"\bwant to die\b",
    r"\bwanna die\b", r"\bbetter off without me\b", r"\bno reason to live\b", r"\bhurt(ing)? my ?self\b",
    r"\bself[- ]?harm", r"\bcut(ting)? my ?self\b", r"\bdon'?t want to (live|be alive|exist)\b",
    r"\bkhud ?kushi\b", r"\bmar (jaana|jaun|jaunga|jaungi|jau)\b", r"\bmarna chaht[ai]\b",
    r"\bjeena nahi\b", r"\bjeene ka (mann|man) nahi\b", r"\bsab khatam kar", r"\bkhatam kar (dunga|dungi|lunga|lungi|du)\b",
    r"\bzindagi khatam\b", r"\bmere bina sab\b", r"\bsabko (mujhse )?chutkara\b", r"\bapne aap ko (hurt|nuksan|chot)\b",
    r"\bkoi problem nahi rahegi\b", r"\bnahi rehna (is duniya|yahan)\b",
    r"आत्महत्या", r"मर जा", r"मरना चाह", r"जीना नहीं", r"खुदकुशी", r"खुद को (नुकसान|चोट)",
]
LOW = [
    r"\bwhat'?s the point\b", r"\bhopeless\b", r"\bcan'?t go on\b", r"\bkya fayda\b", r"\bkoi matlab nahi\b",
    r"\bthak gay[ai] hoon (sab|zindagi)", r"\bsab bekaar\b", r"\bkoi nahi hai mera\b", r"कोई फायदा नहीं",
]

# --- topics the Doctor AI must never handle itself ------------------------------
BLOCKED = {
    "medicine": [r"\bdos(e|age)\b", r"\bmg\b", r"\btablet", r"\bmedicine", r"\bmedication", r"\bpills?\b",
                 r"\bdawai\b", r"\bdawa\b", r"\bgoli\b", r"\bstop taking\b", r"\bband kar (du|doon|dun)\b",
                 r"\bside effect", r"\bsertraline|escitalopram|fluoxetine|lithium|quetiapine|clonazepam\b", r"दवा"],
    "diagnosis": [r"\bdo i have\b", r"\bdiagnos", r"\bam i (bipolar|depressed|borderline|crazy|mad)\b",
                  r"\bwhat'?s wrong with me\b", r"\bmujhe kya (bimari|disorder)\b", r"\bkya mujhe .* hai\b",
                  r"\bpagal hoon\b", r"\bwhat is my schema\b", r"\bmy schema\b", r"\bmera schema\b"],
    "impersonation": [r"\bare you (the |a )?(real )?(doctor|human|person)\b", r"\bpretend (to be|you'?re|you are)\b",
                      r"\bact as (the |dr|doctor)", r"\bkya (aap|tum) (doctor|insaan|asli)\b", r"\bignore (your|previous) (rules|instructions)\b"],
}

# --- unsafe AI replies --------------------------------------------------------------
REPLY_BLOCK = [
    r"\bsab theek ho jayega\b", r"\bjust meditate\b", r"\bitna to sahna\b", r"\byou have (an? )?\w+ (schema|disorder)\b",
    r"\b\d+\s?mg\b", r"\b(increase|decrease|stop|start) (your|the) (dose|medicine|medication)\b",
    r"\bi am dr\.? \w+\b(?! ?'s ai)", r"\bi'?m (a |the )?(human|real person|doctor)\b",
]


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text).lower()


def _hits(text: str, patterns) -> list[str]:
    t = _norm(text)
    return [p for p in patterns if re.search(p, t)]


def check_message(text: str) -> dict:
    """Return {'level': none|low|medium|high, 'blocked': topic|None, 'matched': [...]}"""
    level, matched = "none", []
    for name, pats in (("high", HIGH), ("medium", MEDIUM), ("low", LOW)):
        h = _hits(text, pats)
        if h:
            level, matched = name, h
            break
    blocked = None
    for topic, pats in BLOCKED.items():
        if _hits(text, pats):
            blocked = topic
            break
    return {"level": level, "blocked": blocked, "matched": matched, "source": "phrases"}


def check_reply(text: str) -> list[str]:
    """Return the rules an AI reply breaks (empty list = safe to send)."""
    return _hits(text, REPLY_BLOCK)


ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3}


def max_level(a: str, b: str) -> str:
    return a if ORDER[a] >= ORDER[b] else b
