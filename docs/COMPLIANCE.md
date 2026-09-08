# Compliance & rules notes — Adaptive Learning Studio (GIBC V2)

*Repository created:* 2026-09-06 · All work committed on or after that date.

## Event facts (verified from official Devpost rules page on 2026-09-06)

| Field | Value |
|---|---|
| Event | Global Innovation Build Challenge V2 (Devpost) |
| Track | **03: Open — General Technical Invention** (running code required; no theory-only submissions) |
| Build window | **July 11 – Sep 21, 2026** (12:00pm Taipei start) |
| Submission deadline | Sep 21, 2026 @ 11:45pm Taipei (15:45 UTC) |
| Eligibility | students worldwide, 13+; teams ≤ 6; one project, one track |
| Entry requirements | description, public repo + runnable README, 2–5 min video (English audio/subtitles), Built With, team info (real names), ≥3 screenshots |

## Why Track 03 (and not Track 01 / 02)

- Track 01 (foundational LLM ≤50M params, trained from scratch) is a different,
  resource-heavy build; this project is a learning-science application, and
  Track 03's rubric (Creativity · Execution · Impact · Presentation) fits it.
- Track 02 (med/finance pipelines, de-identified public data) does not apply.
- The submission is a working prototype with a complete end-to-end flow and
  documentation — exactly what Track 03 requires.

## Originality / build-period compliance

- **Nothing pre-exists.** The repository was created 2026-09-06 with no prior
  code; every commit falls inside Jul 11 – Sep 21 (git log).
- **Not substantially the same as a previous hackathon entry.** This is a new
  project; it is not derived from, and was not entered in, any other hackathon.
  A single project is submitted to a single track, per the rules.
- **Third-party code / libraries:** only standard OSS libraries (FastAPI,
  SQLAlchemy, React, Vite) — credited in Built With. Pretrained models are not
  used anywhere (and are irrelevant to Track 03). No hosted inference API is
  used as the submission; the LLM integration is optional app functionality
  with a deterministic fallback, and is disclosed.
- **Shared foundation disclaimer.** `app/core/` is generic infrastructure
  (config, auth, DB, error handling, AI gateway) also present in the author's
  other hackathon repos. It contains no GIBC-specific logic: all submission
  value — the learning models, curriculum, path engine, scheduler, tutor — lives
  in `app/features/learning/`, which is unique to this repo and was built for
  this event.

## AI tool disclosure

Development used AI coding assistance (Claude-based agent tooling on the
Arena.ai platform). Disclosed here and in Built With. The author reviewed every
AI-assisted change, can explain any part of the codebase, and takes full
responsibility. The product's core logic (mastery model, path, scheduler) is
deterministic, unit-tested code written and validated by the author — not model
output.

## Deliverables checklist (for submission day)

- [x] Public repository (https://github.com/favour187/gibc-v2) with a runnable README (setup, prerequisites, usage)
- [x] Running prototype, end-to-end flow verified (register → learn → grade → mastery/schedule updates → tutoring)
- [x] Backend tests green (22) + frontend type-check/build green
- [ ] Demo video 2–5 min, English audio/subtitles (recorder: author)
- [ ] ≥3 screenshots (interfaces, mastery progression, skill map)
- [ ] Devpost page: description, Built With (incl. AI-tool disclosure + libraries), team names
- [ ] Submission only after the above, before Sep 21, 2026 @ 11:45pm Taipei
