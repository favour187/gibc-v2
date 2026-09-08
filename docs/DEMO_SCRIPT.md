# Adaptive Learning Studio — demo video script (target 3:30–4:30; rules require 2–5 min, English audio or subtitles)

**Setup before recording**

```bash
rm -f data/app.db                               # fresh database
uvicorn app.main:app --reload --port 8000       # terminal 1
cd web && npm run dev                           # terminal 2 → http://localhost:5173
```

Register a fresh account (e.g. "Kemi") so the first session shows the cold-start behaviour. Record at 1280×800 or larger, light mode, 100 % zoom. Keep `python -m pytest` output (22 passed) in a terminal for the last beat. Show the project *running* — the rules say the video must show the working system and explain the approach.

| Time | On screen | Say |
|---|---|---|
| 0:00 | Landing page | "Static courses give everyone the same next lesson. Adaptive Learning Studio gives each learner the question with the biggest learning gain — using a documented, testable learning-science engine. This is our Track 03 entry: a working prototype, not a slide deck." |
| 0:20 | Register → **Your learning** dashboard | "Kemi starts with no history. The engine still has a plan: 17 skills across two tracks — CS and AI fundamentals — arranged as a prerequisite graph. Only the roots are unlocked, so **Next up** points at the weakest unlocked skill." |
| 0:45 | **Skill map** tab → click a deeper skill → **Make this my target** | "She can choose a goal. The path engine runs a topological sort over prerequisites and steers her toward the nearest prerequisite on the way to that target." |
| 1:05 | Dashboard → **Start session (8 questions)** | "Sessions are assembled with a reason for every question: due reviews first, then weak spots, then new material." |
| 1:20 | Answer a question wrongly on purpose → result banner | "Wrong answer. Look at what comes back: the explanation, the *misconception* this distractor tests, the new mastery percentage, and the next review date — tomorrow, because wrong answers reset the interval." |
| 1:50 | Answer the next two correctly → badges show mastery rising and "next review in 3d" | "Every answer updates a per-skill ability estimate — a logistic model where the update is scaled by question difficulty, so a hard question moves you more than an easy one. Intervals then grow 1, 3, 7, 14, 30, 60 days — spaced repetition, SM-2 style." |
| 2:20 | **Session complete** → back to dashboard → **Frontier** card | "After the session the frontier has moved: a skill crossed 70 %, so its dependants unlocked. Mastery is `100 / (1 + e^−θ)`; mastered means ≥ 75 % after at least three encounters. Everything is shown, nothing is a black box." |
| 2:45 | **Tutor** tab → click *"What is overfitting?"* then *"I'm not motivated today"* | "The tutor is grounded in the curriculum and the learner's own mastery numbers. Right now it's running deterministic local skills with no API key; the same prompt drives any OpenAI-compatible LLM when one is configured." |
| 3:15 | Editor: `app/features/learning/core.py` (models) and `content.py` (51 questions with misconceptions) | "Architecture: FastAPI and SQLAlchemy on the back, React and TypeScript on the front. All learning-science logic is pure Python in one module with no I/O — which is why it's fully unit-tested." |
| 3:40 | Terminal: `python -m pytest` → 22 passed; CI badge; `docker compose` file | "Twenty-two tests cover the ability update, mastery thresholds, path ordering, scheduler intervals and the API. CI runs them plus the TypeScript build on every push; Docker Compose serves it as a single origin." |
| 4:00 | End card with repo URL | "Adaptive Learning Studio — the right question, for the right reason, at the right time. Thank you." |

## Screenshots for Devpost (≥ 3 required)

1. Dashboard: Mastery + Next up + Frontier
2. Skill map with a target selected
3. Session result banner (wrong answer with misconception, mastery and next-review badges)
4. Tutor conversation
5. Mobile width (≈ 390 px)

## Devpost copy blocks

**Tagline:** A learning engine that adapts to you — mastery model, prerequisite path, spaced repetition, grounded tutor.

**Built with:** Python 3.11, FastAPI, Pydantic, SQLAlchemy 2, SQLite, pytest, React 18, TypeScript, Vite, Docker, GitHub Actions. AI coding assistance (Claude-based agent tooling on Arena.ai) — **listed in Built With as the rules require**.

**Team:** real full name(s) of every member, each added on Devpost (needed for certificates).
