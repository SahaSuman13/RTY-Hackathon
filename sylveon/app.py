"""Sylveon web app.  Run:  .venv\\Scripts\\python -m uvicorn sylveon.app:app --port 8000"""
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import assessment, engine, llm, redteam, store

app = FastAPI(title="Sylveon")
STATIC = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class Msg(BaseModel):
    text: str


class DoctorCfg(BaseModel):
    style: str
    approved_notes: list[dict]
    flashcards: list[dict]
    homework: list[dict]


@app.get("/")
def patient_page():
    return FileResponse(STATIC / "patient.html")


@app.get("/doctor")
def doctor_page():
    return FileResponse(STATIC / "doctor.html")


@app.get("/api/status")
def status():
    return {"llm": llm.enabled(), "model": llm.MODEL if llm.enabled() else None}


@app.post("/api/chat/{pid}")
def chat(pid: str, m: Msg):
    if not m.text.strip():
        raise HTTPException(400, "empty message")
    if pid not in store.load()["patients"]:
        raise HTTPException(404, "unknown patient")
    return engine.handle(pid, m.text.strip())


@app.get("/api/history/{pid}")
def history(pid: str):
    return [m for m in store.load()["messages"] if m["patient"] == pid]


@app.get("/api/doctor/{did}")
def get_doctor(did: str):
    d = store.load()
    return {"doctor": d["doctors"][did], "versions": [v for v in d["doctor_versions"] if v["id"] == did]}


@app.post("/api/doctor/{did}/signoff")
def signoff(did: str, cfg: DoctorCfg):
    """The doctor edits and signs off a new version of their AI. Every version is kept (audit)."""
    d = store.load()
    doc = d["doctors"][did]
    d["doctor_versions"].append({k: doc[k] for k in ("id", "version", "style", "approved_notes", "flashcards", "homework", "signed_off_at")})
    doc.update(cfg.model_dump(), version=doc["version"] + 1, signed_off=True, signed_off_at=time.time())
    store.save(d)
    return {"ok": True, "version": doc["version"]}


@app.get("/evidence")
def evidence_page():
    return FileResponse(STATIC / "evidence.html")


@app.get("/api/phq9")
def phq9_items():
    return {"stem": assessment.STEM, "items": assessment.ITEMS, "options": assessment.OPTIONS, "citation": assessment.CITATION}


class Answers(BaseModel):
    answers: list[int]


@app.post("/api/phq9/{pid}")
def phq9_submit(pid: str, a: Answers):
    try:
        res = assessment.score(a.answers)
    except ValueError as e:
        raise HTTPException(400, str(e))
    d = store.load()
    d["events"].append({"patient": pid, "kind": "phq9", "ts": time.time(), **res})
    if res["safety_flag"]:  # item 9 > 0: never wait for the next session
        d["events"].append({"patient": pid, "kind": "safety", "ts": time.time(), "level": "medium",
                            "text": f"PHQ-9 item 9 answered {res['item9']} (thoughts of being better off dead or self-harm)",
                            "doctor_alerted": True, "helpline": engine.HELPLINE})
    store.save(d)
    # the patient sees no score or label, only thanks (and crisis help if item 9 > 0)
    msg = "Thank you. Your answers are saved for Dr Kabir."
    if res["safety_flag"]:
        msg += f" You mentioned thoughts of being better off dead or hurting yourself. Please talk to someone now: {engine.HELPLINE}. Dr Kabir has been alerted."
    return {"message": msg, "crisis": res["safety_flag"]}


@app.get("/api/summary/{pid}")
def summary(pid: str):
    return engine.summary(pid)


@app.post("/api/reset")
def reset():
    store.reset()
    return {"ok": True}


@app.post("/api/redteam")
def run_redteam():
    snapshot = store.load()
    try:
        return redteam.run(with_baseline=True)
    finally:
        store.save(snapshot)  # the eval must not wipe the demo conversation
