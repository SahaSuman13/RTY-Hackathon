"""Therapist-only schema hypotheses.

Method follows STEPS (Ang, Gollapalli & Ng, IJCAI-25): compare the patient's own belief statements
with schema descriptions and pass the closest ones on for checking. Differences, on purpose:
  * we do NOT use Young Schema Questionnaire items (restricted/paid copyright); the 18 descriptions
    below are our own plain-language summaries of the published model (Young, Klosko & Weishaar 2003;
    ISST). Team-written, not yet clinician-reviewed.
  * the output is shown ONLY to the therapist, as a hypothesis with the patient's words as evidence.
    The patient is never told a schema (Sylveon's rule; also the therapist's job).
Similarity: Gemini embeddings when a key is set, otherwise word overlap with cue phrases.
"""
import math
import re

from . import llm

SCHEMAS = [  # (domain, name, plain description, cue words incl. Hinglish)
    ("Disconnection & rejection", "Abandonment / instability", "People I love will leave me or stop being there; I panic when someone pulls away or doesn't reply.",
     ["leave", "left", "chhod", "repl", "ignore", "alone", "akela", "abandon", "pull away", "lose him", "lose her"]),
    ("Disconnection & rejection", "Mistrust / abuse", "Others will hurt, use, cheat or humiliate me if I let my guard down.",
     ["trust", "use me", "cheat", "betray", "dhokha", "hurt me", "lie to me"]),
    ("Disconnection & rejection", "Emotional deprivation", "Nobody will really understand me, care for me or meet my emotional needs.",
     ["nobody understands", "koi nahi samajhta", "no one cares", "koi care nahi", "empty", "khali"]),
    ("Disconnection & rejection", "Defectiveness / shame", "I am flawed, bad or unlovable deep inside, and if people really knew me they would reject me.",
     ["unlovable", "worthless", "not good", "defective", "shame", "bekaar", "kisi kaam ka nahi", "not enough", "enough nahi", "hate myself"]),
    ("Disconnection & rejection", "Social isolation / alienation", "I am different from everyone else and don't belong anywhere.",
     ["don't belong", "different from everyone", "fit in", "outsider", "alag hoon"]),
    ("Impaired autonomy", "Dependence / incompetence", "I can't handle everyday life on my own without a lot of help.",
     ["can't handle", "can't manage", "need help for everything", "akele nahi kar sakta"]),
    ("Impaired autonomy", "Vulnerability to harm", "Something terrible is about to happen and I can't prevent it.",
     ["something bad will happen", "disaster", "catastroph", "kuch bura hoga"]),
    ("Impaired autonomy", "Enmeshment / undeveloped self", "I don't know who I am apart from my parent or partner; I'm too fused with them.",
     ["without my mother", "without my parents", "who am i", "lost myself"]),
    ("Impaired autonomy", "Failure", "I have failed or will fail; I'm less talented or successful than others.",
     ["fail", "failure", "fail hounga", "loser", "percentile", "behind everyone", "sab aage", "mock"]),
    ("Impaired limits", "Entitlement / grandiosity", "I'm special and rules shouldn't apply to me; I should get what I want.",
     ["i deserve more", "rules don't apply", "better than them"]),
    ("Impaired limits", "Insufficient self-control", "I can't tolerate frustration or hold back impulses and emotions.",
     ["can't stop myself", "impulse", "lose control", "binge", "rok nahi pata"]),
    ("Other-directedness", "Subjugation", "I must give in to others' wishes or they will be angry or leave; my needs don't count.",
     ["give in", "my needs don't matter", "can't say no", "mana nahi kar pata"]),
    ("Other-directedness", "Self-sacrifice", "I must meet everyone else's needs at my own cost, or I feel guilty.",
     ["guilty", "everyone else first", "people please", "sabko khush"]),
    ("Other-directedness", "Approval-seeking", "My worth depends on others' approval, status or recognition.",
     ["what will people think", "log kya kahenge", "approval", "impress", "sab bole"]),
    ("Overvigilance & inhibition", "Negativity / pessimism", "Things will go wrong; I focus on the negative and worry constantly.",
     ["everything goes wrong", "always worry", "sab galat", "pessim", "overthink"]),
    ("Overvigilance & inhibition", "Emotional inhibition", "I must hide my feelings and stay in control, or I'll be shamed or hurt others.",
     ["hide my feelings", "can't cry", "keep it inside", "andar rakhta"]),
    ("Overvigilance & inhibition", "Unrelenting standards", "I must meet very high standards, or I'm not good enough; I can never relax.",
     ["perfect", "never good enough", "raat bhar padhta", "work harder", "aur karo", "can't relax", "100 percent"]),
    ("Overvigilance & inhibition", "Punitiveness", "People, including me, deserve harsh punishment for mistakes.",
     ["deserve to be punished", "i deserve this", "harsh on myself", "maaf nahi"]),
]
DISCLAIMER = "Hypothesis for clinician review, not a diagnosis. Never shown to the patient."


def _cue_score(text: str, cues: list[str]) -> float:
    t = text.lower()
    return float(sum(1 for c in cues if c in t))


def _cos(a, b):
    num = sum(x * y for x, y in zip(a, b))
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return num / den if den else 0.0


def hypotheses(statements: list[str], top: int = 3) -> dict:
    """statements: the patient's own words (beliefs, check-in answers)."""
    statements = [s for s in statements if s and len(s.strip()) > 2]
    if not statements:
        return {"method": "none", "items": [], "disclaimer": DISCLAIMER}
    embs = llm.embed([s for s in statements] + [d for _, _, d, _ in SCHEMAS]) if llm.enabled() else None
    items = []
    for i, (domain, name, desc, cues) in enumerate(SCHEMAS):
        best, ev = 0.0, None
        for j, s in enumerate(statements):
            sc = _cos(embs[j], embs[len(statements) + i]) if embs else _cue_score(s, cues)
            if sc > best:
                best, ev = sc, s
        items.append({"schema": name, "domain": domain, "description": desc, "score": round(best, 3), "evidence": ev})
    thr = 0.55 if embs else 1.0  # embeddings: cosine threshold; cues: at least one cue matched
    items = sorted([x for x in items if x["score"] >= thr], key=lambda x: -x["score"])[:top]
    return {"method": "gemini embeddings (cosine)" if embs else "cue-phrase overlap (no AI key)", "items": items, "disclaimer": DISCLAIMER}
