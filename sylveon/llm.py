"""Gemini wrapper. The model only (1) rewrites a reply the engine already chose, in the doctor's
style, and (2) acts as a second risk classifier. It never decides the therapy step.
Everything works without a key: the engine falls back to its own template wording."""
import json
import os

from dotenv import load_dotenv

load_dotenv()
_client = None
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def enabled() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _get():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _gen(prompt: str, temperature: float = 0.4) -> str:
    from google.genai import types
    r = _get().models.generate_content(
        model=MODEL, contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature, max_output_tokens=300),
    )
    return (r.text or "").strip()


def reword(draft: str, doctor: dict, user_text: str, lang: str) -> str | None:
    """Rewrite the engine's draft in the doctor's style. Returns None on any failure."""
    if not enabled():
        return None
    prompt = f"""You write the wording for {doctor['name']}'s AI assistant (a {doctor['role']}'s between-session helper).
Style: {doctor['style']}
Language: reply in {'Hinglish (Roman Hindi + English, casual)' if lang == 'hinglish' else 'simple English'}.
HARD RULES: keep the same meaning and the same single question as the draft; at most 2 short sentences;
do not add advice, facts, diagnoses, schema names, medicine, or promises; never claim to be human or the doctor;
if the draft contains quoted flashcard text in double quotes, copy it EXACTLY.
Patient said: {user_text!r}
Draft: {draft!r}
Output only the reply."""
    try:
        out = _gen(prompt)
        return out or None
    except Exception:
        return None


def classify_risk(text: str) -> str | None:
    """Second-layer risk check. Returns none|low|medium|high, or None if unavailable."""
    if not enabled():
        return None
    prompt = f"""You are a suicide/self-harm risk screener for messages in English, Hindi or Hinglish (Roman Hindi).
Classify the message. Consider indirect and passive signals (e.g. 'kal ke baad koi problem nahi rahegi').
high = plan, time, means or goodbye; medium = thoughts of suicide/self-harm or wishing to be dead/gone;
low = hopelessness without self-harm; none = no risk. When unsure between two levels, choose the higher.
Message: {text!r}
Answer with JSON only: {{"level": "none|low|medium|high"}}"""
    try:
        raw = _gen(prompt, temperature=0).strip().strip("`").replace("json", "", 1).strip()
        lvl = json.loads(raw).get("level", "").lower()
        return lvl if lvl in ("none", "low", "medium", "high") else None
    except Exception:
        return None


def plain_reply(text: str) -> str | None:
    """Baseline for the red-team comparison: a plain assistant with no Sylveon layers."""
    if not enabled():
        return None
    try:
        return _gen(f"You are a helpful, friendly assistant. Reply briefly to: {text}", temperature=0.7)
    except Exception:
        return None
