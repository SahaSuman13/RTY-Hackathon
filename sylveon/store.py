"""Tiny JSON-file store (enough for a hackathon demo; a real pilot needs an encrypted DB)."""
import json
import threading
import time
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "sylveon_db.json"
_lock = threading.Lock()

# Fictional demo doctor and patient (names from the team's PRD; all fictional).
DEFAULT_DOCTOR = {
    "id": "dr-kabir",
    "name": "Dr Kabir",
    "role": "Schema therapist",
    "style": "Warm, calm and frank. Short replies, one question at a time. Matches English or Hinglish. Never preachy.",
    "approved_notes": [
        {"id": "N1", "topic": "flashcard", "text": "Your flashcard is for moments when you fear being left. Read it slowly, line by line."},
        {"id": "N2", "topic": "mode diary", "text": "Each evening, write one line: what happened, which part of you showed up, and what that part needed."},
        {"id": "N3", "topic": "healthy adult", "text": "The Healthy Adult part can notice the old fear without obeying it. Pause, name the feeling, then choose one kind action."},
        {"id": "N4", "topic": "between sessions", "text": "If you feel worse than usual for more than two days, tell me through the app so I can see it before our session."},
    ],
    "flashcards": [
        {"id": "F1", "title": "When I fear being left",
         "triggers": ["hasn't replied", "hasnt replied", "not replying", "reply nahi", "ignore", "spiral", "spiralling", "spiraling", "left me", "chhod"],
         "lines": [
             "Right now I feel scared he will leave, because this is the part of me that was left alone as a kid.",
             "The fear is real, but it is an old feeling. It is not proof of what is happening today.",
             "What I need right now is to feel safe. My Healthy Adult can give me that.",
             "Instead of sending ten messages, I will do one kind thing for myself and wait an hour.",
         ]},
    ],
    "homework": [{"id": "H1", "title": "Evening mode diary", "text": "One line each evening: what happened, which part of me showed up, what it needed."}],
    "escalation": {"alert_on": ["medium", "high"], "channel": "dashboard + SMS (demo: dashboard only)"},
    "version": 1,
    "signed_off": True,
    "signed_off_at": None,
}

DEFAULT = {
    "doctors": {"dr-kabir": DEFAULT_DOCTOR},
    "patients": {"riya": {"id": "riya", "name": "Riya", "doctor": "dr-kabir", "consent": True}},
    "messages": [],      # {patient, sender, text, ts, step, safety}
    "events": [],        # safety events, saved questions, homework, flashcards
    "doctor_versions": [],
}


def load() -> dict:
    with _lock:
        if not DB.exists():
            DB.parent.mkdir(parents=True, exist_ok=True)
            d = json.loads(json.dumps(DEFAULT))
            d["doctors"]["dr-kabir"]["signed_off_at"] = time.time()
            DB.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
        return json.loads(DB.read_text(encoding="utf-8"))


def save(d: dict) -> None:
    with _lock:
        DB.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")


def reset() -> dict:
    with _lock:
        if DB.exists():
            DB.unlink()
    return load()
