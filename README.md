# 🚀 Buildathon: Make Wednesdays Great Again

**Masters' Union · For AI Developers · Winner gets Rs. 25,000**

> **Every team must build in a fork of this repository.** Projects not built in a fork of this repo won't be judged.

| | |
|---|---|
| **Date** | Wednesday, 18 November 2026 |
| **Hacking** | **3:00 PM – 7:00 PM IST** (code freeze at 7:00 PM sharp) |
| **Venue** | CDS Audi, 8th floor |
| **Prize** | Rs. 25,000 to the winning team |
| **Register your fork** | 👉 **[https://forms.gle/ZJUYKwTYjsMsVB2b9](https://forms.gle/ZJUYKwTYjsMsVB2b9)** (**deadline 3:30 PM IST**) |
| **Final submission** | Your fork as it stands at **7:00 PM IST**. There's nothing else to submit. |

> 🤖 **Using an AI coding agent?** Point it at [`AGENTS.md`](AGENTS.md). It has the full event brief, tracks, judging and rules in a form agents can read directly. Claude Code loads it automatically through `CLAUDE.md`, and Codex reads `AGENTS.md` natively.

---

## 🎯 Pick one build track

| # | Track | Brief |
|---|---|---|
| **01** | **Build for the Physical World** | Make a real-world task easier, faster or more reliable. Show it in a realistic scenario. |
| **02** | **Build for AI Agents** | Find something an agent struggles with. Build the tool that fixes it, then demo the agent using it. |
| **03** | **Build in Your Area of Expertise** | Pick a field you know firsthand. Ship a working product that improves how people handle it today. |

## ⚖️ How you'll be judged (each criterion is ⅓ of your score)

| Criterion | The question judges ask |
|---|---|
| **Working product** | Does it do what you say it does? Show the core workflow in your demo. |
| **Problem insight** | Who faces this problem, and why does it happen? |
| **Depth of execution** | How well did you solve the hardest part of the build? |

---

## Why fork this repo?

Everyone starts from the same commit (the **genesis commit**) at the same time. Organizers can then check that:
- all code was written **during** the Buildathon and not brought in from an earlier project,
- teams commit steadily instead of pasting in one huge AI-generated dump at the end,
- every repo stays public and visible while you build.

The organizers track every fork automatically: commits, timing and activity. Read [RULES.md](RULES.md) before you write any code.

---

## ✅ Setup (about 5 minutes, do it at 3:00 PM)

**In short:** fork → register your fork in the form **by 3:30 PM** → build → push before 7:00 PM.

### 1. Fork this repo
Click **Fork** (top right). On the fork screen:
- **Owner:** one team member's personal account. Only **one fork per team**.
- **Repository name:** `buildathon-<team-name>`, for example `buildathon-byte-bandits`
- Click **Create fork**.

> ⚠️ Don't download a ZIP or copy the files into a new repo. **It has to be a real GitHub fork**, or the tracker can't see you.

### 2. Keep it public
Forks of a public repo are public. **Don't make it private, archive it, or delete it** until judging is over.

### 3. Add your teammates
In your fork: **Settings → Collaborators → Add people**. Add each teammate's GitHub account so their commits count toward the team.

### 4. Enable Actions
Open the **Actions** tab of your fork and click **"I understand my workflows, go ahead and enable them"**. This runs the automatic check on every push.

### 5. Make your registration commit (your first commit)
Fill in [`team.json`](team.json). `track` must be one of `physical-world`, `ai-agents` or `area-of-expertise`. Then:

```bash
git clone https://github.com/<your-username>/buildathon-<team-name>.git
cd buildathon-<team-name>
# edit team.json
git add team.json
git commit -m "register: <team name>"
git push
```

The **Hackathon check** in the Actions tab should go green ✅. If it's red, open the run to see what's wrong in `team.json`.

### 6. Register your fork (deadline: 3:30 PM IST)
👉 **[https://forms.gle/ZJUYKwTYjsMsVB2b9](https://forms.gle/ZJUYKwTYjsMsVB2b9)**

It's a 4-question Google Form: team name, fork link, track, team members. It connects your repo to the organizers' live tracker.

- Fill it in **once per team**, right after forking, and **no later than 3:30 PM IST**. **Teams that don't register can't be tracked.**
- Paste your **fork's** URL (`https://github.com/<you>/buildathon-<team-name>`), not this starter repo's.
- Need to change something? Use the **"Edit your response"** link on the confirmation page. Don't fill it in twice.
- **Final submission is automatic.** Whatever is pushed to your fork at 7:00 PM IST is what gets judged.

---

## 🛠 While you build (3:00 – 7:00 PM)

- Put your code anywhere in the repo (`app/`, `src/`, `frontend/`, `backend/`…). There's no required layout.
- **Commit early, commit often**, at least every 30 minutes of real work, with messages that say what changed.
- **Push regularly.** Commits you never push don't exist to the tracker.
- AI coding tools (Claude Code, Codex, Cursor, Copilot…) are **allowed and encouraged**. Keep `AGENTS.md` and `CLAUDE.md` in the repo; they keep your agent within the rules.
- Before 7:00 PM, replace the "Your project" section below with your project's README.

## 🧊 Code freeze: 7:00 PM IST

At 7:00 PM the tracker takes a snapshot of every fork. **Commits pushed after code freeze are ignored.** Judges look at your last commit before 7:00 PM.

## ❌ Things that get you flagged

- Rewriting history (`git push --force`, rebasing away the genesis commit, squashing everything into one commit)
- Commits dated before 3:00 PM
- One or two giant commits containing most of the project
- A repo that isn't a fork of this one, or that's private or deleted

See [RULES.md](RULES.md) for the full list.

---

## Your project

# RallyIQ: a coach's eye on any phone

- **Team:** Team Gyarados (Suman Saha, Aman Kumar, Lakshya Toshniwal)
- **Track:** Physical world
- **Live demo:** https://sahasuman13.github.io/RTY-Hackathon/ (open on a phone or laptop; camera needs HTTPS)

**Problem.** Most young cricket, table tennis and football players in India train without a coach watching every rep. Private coaching is costly and a coach cannot watch every repetition, so small faults (a collapsing front knee, an arm-only forehand) repeat for months. Players already film themselves on phones, but nobody turns that video into measurements.

**What we built.** A browser app that turns the phone camera into a guided technique session:
1. **Guided set-up:** checks whole body in frame, distance, side-on vs front view and stillness, with a voice coach; then a 3-2-1 countdown.
2. **Drill:** 5 reps. Each rep is detected automatically at peak hand/foot speed (or a held posture for the ready stance).
3. **Measurement:** Google MediaPipe Pose (full) gives 33 keypoints; we compute 3D joint angles (world landmarks), trunk lean, trunk turn, low-to-high swing and weight transfer at the key moment (ball release / contact).
4. **Feedback:** each metric is compared with a labelled target (LAW / RESEARCH / COACH), with a cue, a drill and the source.
5. **Replay studio:** animated skeleton of every rep with the hand/foot path, key-moment marker, angle arcs, a ghost of your best rep, slow-mo and 3D orbit.
6. **Train your own model:** a coach approves good reps; after 3, RallyIQ learns that athlete's own target ranges (mean ± 2 SD) and uses them instead of the defaults.
7. **Report + progress:** % in range, consistency score, best vs worst rep, #1 focus drill, session history (stored on the device only).

Movements: cricket fast bowling, cricket front-foot drive, table tennis forehand drive/topspin, backhand drive, ready stance, football instep kick.

**The hardest part.** Making it trustworthy rather than impressive. Pose models jitter and guess, so we (a) gate everything behind a guided set-up, (b) smooth adaptively, (c) drop any joint under 50% confidence and say "not visible" instead of guessing, (d) use no LLM, so no number on screen can be invented, and (e) label every target by evidence strength. Research gives directions, not one "perfect" angle, so the athlete's own best rep and a coach-trained personal model are the main benchmarks.

**Evidence used.** ICC 15° elbow-extension limit; Worthington, King & Ranson 2013 (J Appl Biomech): straighter front knee at release goes with faster bowling in elite men; Iino & Kojima 2009 (J Sports Sci): trunk rotation drives table tennis forehand racket speed; Mao et al. 2023 (Applied Sciences): elbow and knee flexion in topspin forehands; Lees & Nolan 1998 (J Sports Sci) soccer biomechanics review; Sports2D (JOSS) filming guidance; our team's Table Tennis Technique & AI Movement Evaluation Framework (VICTAS, PingSkills, DTTA, Table Tennis Teacher sources). Full table in the app's "Research & limits" tab.

**Honest limits.** Single phone camera = 2D/3D estimates with a few degrees of error. Does not certify bowling actions (needs ICC 3D lab testing), does not diagnose injury, and cannot yet measure racket angle, spin or exact ball contact (roadmap: racket/ball detection, second camera).

**How to run it.** No install. Open `docs/index.html` through any static server, for example `python -m http.server 8010 -d docs`, then visit http://localhost:8010. Pick a movement, press **Live camera** (or **Upload video**), follow the voice coach.

**Code:** `docs/index.html` (single file: UI, pose pipeline, biomechanics, rules, replay, training). The `sylveon/` folder is an earlier idea from this hackathon that we stopped.
