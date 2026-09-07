from __future__ import annotations
import random
from dataclasses import dataclass
from datetime import date
from typing import Any
from app.features.learning.core import (
    Grade,
    Question,
    Skill,
    SkillState,
    apply_grade,
    difficulty_scaled,
    due_skills,
    frontier,
    grade_for_answer,
    next_best_skill,
    update_mastery,
)

SESSION_SIZE = 8


@dataclass(slots=True)
class SessionQuestion:
    question: Question
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question.question_id,
            "skill_id": self.question.skill_id,
            "stem": self.question.stem,
            "options": list(self.question.options),
            "difficulty": self.question.difficulty,
            "source": self.source,
        }


@dataclass(slots=True)
class Session:
    questions: list[SessionQuestion]
    skill_title: dict[str, str]

    @property
    def question_count(self) -> int:
        return len(self.questions)


def assemble_session(
    skills: dict[str, Skill],
    states: dict[str, SkillState],
    *,
    target_skill: str | None = None,
    rng: random.Random | None = None,
    size: int = SESSION_SIZE,
    today: date | None = None,
) -> Session:
    rng = rng or random.Random()
    today = today or date.today()
    due = [sid for sid in due_skills(states, today=today) if sid in skills]
    weak = [
        sid
        for sid in frontier(skills, states)
        if sid not in due and (sid not in states or states[sid].mastery < 60)
    ]
    fresh = [
        sid for sid in frontier(skills, states) if sid not in due and sid not in weak
    ]
    upcoming: list[str] = []
    from app.features.learning.core import topological_order

    for sid in topological_order(skills):
        if sid in due or sid in weak or sid in fresh:
            continue
        prereq_started = all(
            (states.get(p) is not None and states[p].encounters > 0)
            for p in skills[sid].prerequisites
        )
        if skills[sid].prerequisites and prereq_started:
            upcoming.append(sid)
        if len(upcoming) >= size:
            break
    ordered = due + weak + fresh + upcoming
    pool_size = len(ordered)
    picked: list[SessionQuestion] = []
    used_skills: list[str] = []
    remaining = size
    for sid in ordered:
        if remaining <= 0:
            break
        bank = [
            q
            for q in skills_knowledge_bank(sid)
            if q.question_id not in picked_ids(picked)
        ]
        if not bank:
            continue
        per_skill = 3 if pool_size <= 2 else (2 if sid in due else 1)
        take = min(len(bank), per_skill, remaining)
        chosen = rng.sample(bank, take)
        for q in chosen:
            source = "review" if sid in due else ("weak" if sid in weak else "new")
            picked.append(SessionQuestion(q, source))
        used_skills.append(sid)
        remaining -= take
    titles = {sid: skills[sid].title for sid in used_skills}
    return Session(questions=picked, skill_title=titles)


def picked_ids(items: list[SessionQuestion]) -> set[str]:
    return {q.question.question_id for q in items}


def skills_knowledge_bank(skill_id: str) -> list[Question]:
    from app.features.learning.content import questions_for

    return questions_for(skill_id)


@dataclass(slots=True)
class AnswerRecord:
    question_id: str
    skill_id: str
    correct: bool
    grade: int
    theta_before: float
    theta_after: float
    mastery_after: float
    interval_days_after: float
    due_date_after: date

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "skill_id": self.skill_id,
            "correct": self.correct,
            "grade": self.grade,
            "theta_before": round(self.theta_before, 3),
            "theta_after": round(self.theta_after, 3),
            "mastery_after": self.mastery_after,
            "interval_days_after": round(self.interval_days_after, 2),
            "due_date_after": self.due_date_after.isoformat(),
        }


def grade_answer(
    state: SkillState,
    question: Question,
    *,
    chosen_index: int,
    self_rating: int | None = None,
    today: date | None = None,
) -> AnswerRecord:
    correct = chosen_index == question.answer_index
    grade = grade_for_answer(correct, self_rating=self_rating)
    theta_before = state.theta
    update_mastery(state, difficulty_scaled(question.difficulty), correct)
    apply_grade(state, grade, today=today)
    return AnswerRecord(
        question_id=question.question_id,
        skill_id=question.skill_id,
        correct=correct,
        grade=int(grade),
        theta_before=theta_before,
        theta_after=state.theta,
        mastery_after=state.mastery,
        interval_days_after=state.interval_days,
        due_date_after=state.due_date,
    )
