"""PHQ-9 (Kroenke, Spitzer & Williams, 2001). The official form states that no permission is
required to reproduce, translate, display or distribute it. Items are shown word for word and
scored the standard way. The score goes to the doctor only. Item 9 > 0 triggers the safety path.
"""
STEM = "Over the last 2 weeks, how often have you been bothered by any of the following problems?"
ITEMS = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
    "Trouble concentrating on things, such as reading the newspaper or watching television",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
    "Thoughts that you would be better off dead or of hurting yourself in some way",
]
OPTIONS = [("Not at all", 0), ("Several days", 1), ("More than half the days", 2), ("Nearly every day", 3)]
BANDS = [(0, 4, "minimal"), (5, 9, "mild"), (10, 14, "moderate"), (15, 19, "moderately severe"), (20, 27, "severe")]
CITATION = "Kroenke K, Spitzer RL, Williams JBW. The PHQ-9. J Gen Intern Med. 2001;16(9):606-613."


def score(answers: list[int]) -> dict:
    if len(answers) != 9 or any(a not in (0, 1, 2, 3) for a in answers):
        raise ValueError("PHQ-9 needs 9 answers, each 0-3")
    total = sum(answers)
    band = next(b for lo, hi, b in BANDS if lo <= total <= hi)
    return {"total": total, "severity": band, "item9": answers[8], "safety_flag": answers[8] > 0, "answers": answers}
