# Adaptive Learning Studio

An adaptive learning web app for computer science and AI fundamentals.

## Features

- Skill mastery tracking
- Prerequisite-based learning paths
- Spaced-repetition reviews
- Quizzes with explanations
- Progress dashboard and skill map
- Optional AI tutor
- User accounts and persistence

## Stack

- Python, FastAPI, SQLAlchemy
- React, TypeScript, Vite
- SQLite/PostgreSQL
- Docker

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd web
npm install
npm run dev
```

Run tests:

```bash
python -m pytest
```

## Environment

Optional AI configuration:

- `AI_MODE`
- `AI_BASE_URL`
- `AI_API_KEY`
- `AI_MODEL`

The tutor works without an API key using built-in deterministic skills.

## Demo

https://adaptive-learning-studio.onrender.com

## License

MIT — see `LICENSE`.
