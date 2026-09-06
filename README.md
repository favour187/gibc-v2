# Adaptive Learning Studio — GIBC V2 (Track 03: Open)

> A learning engine that adapts to you: mastery model, prerequisite path, spaced repetition, AI explanations.

**Event:** Global Innovation Build Challenge V2 (Devpost)
**Track:** 03 — Open (General Technical Invention)
**Build window:** Jul 11 – Sep 21, 2026 · **Deadline:** Sep 21, 2026 @ 11:45pm Taipei (15:45 UTC)
**Event verified:** ✅ Yes (official rules page fetched 2026-09-06)

## What it is

A web app that teaches people computer science and AI fundamentals through an
**adaptive learning engine** instead of a static course:

- Every answer updates a per-skill **mastery estimate** (a logistic "ability"
  model whose update is scaled by question difficulty — think Elo + knowledge
  tracing, kept interpretable).
- A **prerequisite DAG** (17 skills, 2 tracks) drives which skills are unlocked;
  the engine always steers you toward your **weakest unlocked skill** (the
  biggest learning gain), or toward a target you choose.
- A **spaced-repetition scheduler** (SM-2-inspired) replays exactly what you're
  about to forget, with growing intervals.
- A **tutor** layer explains concepts and your wrong answers — grounded in the
  curriculum content and each question's *misconception* field — via the AI
  gateway (deterministic local skills with zero API key, or any
  OpenAI-compatible LLM when configured).
- Sessions are assembled so every question has a reason: **due reviews**,
  **weak spots**, **new material**.

**Why Track 03:** the tech is a real, testable learning-science implementation
(running code, end-to-end flow, documented model) — not a slide deck. It was
built entirely inside the July 11 – September 21, 2026 window.

## The learning model (documented, deterministic, unit-tested)

| Component | What it does | Where |
|---|---|---|
| Ability estimate θ | `P(correct) = sigmoid(θ − d)`; θ += 0.6·(observed − expected) | `app/features/learning/core.py` |
| Mastery | `100 / (1 + e^−θ)`; mastered at ≥75% after ≥3 encounters | same |
| Path | Kahn topological sort over prereqs; frontier = all prereqs ≥70% | same |
| Next skill | weakest frontier skill, or nearest prerequisite on the way to your target | same |
| Spaced repetition | intervals 1→3→7→14→30→60 days; wrong answers reset and re-queue tomorrow | same |
| Question difficulty | 1–5 mapped to [0.1, 0.9] for the mastery update | same |

Estimates are deliberately transparent — every answer shows its theta change,
new mastery, and next review date.

## Architecture

```
web/  React + TypeScript + Vite (typed API client, shared UI kit:
      dashboard, quiz session, skill map, tutor chat)
app/
  core/                   generic foundation (config, logging, errors, HTTP
                          factory, rate limiting, SQLAlchemy, auth, AI gateway)
  features/learning/
    core.py               learning-science models (pure, testable)
    content.py            curriculum: 17 skills, 51-question bank with
                          explanations + misconceptions
    engine.py             session assembly + grading pipeline
    repository.py         persistence (profiles, progress, sessions, attempts)
    service.py            orchestration
    routers.py            REST API
    ai_skills.py          deterministic tutor skills + LLM prompt layer
```

The generic foundation is shared with the author's other hackathon repos;
`app/features/learning/` is unique to this competition and was built during the
GIBC V2 window (first commit in this repo: Sep 6, 2026).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
# → API docs http://localhost:8000/api/docs
# → demo account: demo@example.com / demo-password-123

cd web && npm install && npm run dev   # http://localhost:5173 (proxies /api → :8000)
python -m pytest                        # 22 tests: mastery math, path engine, API flow
```

## AI configuration

| Variable | Default | Notes |
|---|---|---|
| `AI_MODE` | `auto` | remote when a key exists, deterministic local otherwise |
| `AI_BASE_URL` | `https://api.openai.com/v1` | any OpenAI-compatible endpoint |
| `AI_API_KEY` | *(empty)* | empty → built-in curriculum-grounded tutor skills |
| `AI_MODEL` | `gpt-4o-mini` | |

The tutor works fully offline; with a key it answers the same prompts with the
LLM + curriculum context. Mastery/scheduling always come from the deterministic
engine either way.

## Honest notes (for judges)

- The learning models are **simplified but real**: a logistic ability model with
  difficulty-scaled updates, Kahn topological ordering, SM-2-style intervals.
  They're chosen for transparency and testability, and each is documented and
  unit-tested. Replacing them with IRT/BKT or a full SM-2 implementation is a
  drop-in change.
- **AI disclosure:** development used AI coding tools (Claude-based agent
  tooling on the Arena.ai platform), disclosed per the rules (see
  `docs/COMPLIANCE.md`). All AI-assisted code was reviewed by the author, and
  the core learning logic is deterministic, human-reviewed, tested code.

## Deployment

`Dockerfile` + `docker compose up --build` serve the built frontend + API.
CI runs `pytest` (backend) and `tsc + vite build` (frontend) on every push.

## License

MIT — see [LICENSE](LICENSE).
