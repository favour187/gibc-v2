from __future__ import annotations
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import IntEnum
from typing import Any

DIFFICULTY_MIN = 0.10
DIFFICULTY_MAX = 0.90


def difficulty_scaled(level: int) -> float:
    level = max(1, min(5, int(level)))
    return DIFFICULTY_MIN + (level - 1) * (DIFFICULTY_MAX - DIFFICULTY_MIN) / 4.0


def mastery_from_theta(theta: float) -> float:
    return round(100.0 / (1.0 + math.exp(-theta)), 1)


@dataclass(frozen=True, slots=True)
class Skill:
    skill_id: str
    title: str
    track: str
    description: str
    concept: str
    difficulty: int
    prerequisites: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Question:
    question_id: str
    skill_id: str
    stem: str
    options: tuple[str, ...]
    answer_index: int
    difficulty: int
    explanation: str
    misconception: str = ""


class Grade(IntEnum):
    WRONG = 1
    HARD_RIGHT = 3
    RIGHT = 4
    EASY_RIGHT = 5


@dataclass(slots=True)
class SkillState:
    skill_id: str
    theta: float = 0.0
    encounters: int = 0
    correct: int = 0
    repetition: int = 0
    interval_days: float = 0.0
    due_date: date = field(default_factory=date.today)
    last_grade: int = 0

    @property
    def mastery(self) -> float:
        return mastery_from_theta(self.theta)

    @property
    def mastered(self) -> bool:
        return self.mastery >= 75.0 and self.encounters >= 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "theta": round(self.theta, 3),
            "mastery": self.mastery,
            "mastered": self.mastered,
            "encounters": self.encounters,
            "correct": self.correct,
            "accuracy": (
                round(self.correct / self.encounters, 3) if self.encounters else None
            ),
            "repetition": self.repetition,
            "interval_days": round(self.interval_days, 2),
            "due_date": self.due_date.isoformat(),
            "last_grade": self.last_grade,
        }


def expected_correct(theta: float, difficulty: float) -> float:
    return 1.0 / (1.0 + math.exp(-(theta - difficulty)))


def update_mastery(
    state: SkillState, difficulty: float, correct: bool, *, k: float = 0.6
) -> SkillState:
    p = expected_correct(state.theta, difficulty)
    surprise = (1.0 if correct else 0.0) - p
    state.theta += k * surprise
    state.encounters += 1
    if correct:
        state.correct += 1
    return state


INTERVALS = (1, 3, 7, 14, 30, 60)


def apply_grade(
    state: SkillState, grade: Grade, *, today: date | None = None
) -> SkillState:
    today = today or date.today()
    state.last_grade = int(grade)
    if grade == Grade.WRONG:
        state.repetition = 0
        state.interval_days = 0.0
        state.due_date = today + timedelta(days=1)
        return state
    if grade == Grade.HARD_RIGHT:
        state.due_date = today + timedelta(days=1)
        return state
    state.repetition += 1
    idx = min(state.repetition - 1, len(INTERVALS) - 1)
    state.interval_days = float(INTERVALS[idx])
    state.due_date = today + timedelta(days=state.interval_days)
    return state


def grade_for_answer(correct: bool, *, self_rating: int | None = None) -> Grade:
    if self_rating is not None and self_rating >= 1:
        if not correct:
            return Grade.WRONG
        return {
            1: Grade.HARD_RIGHT,
            2: Grade.HARD_RIGHT,
            3: Grade.RIGHT,
            4: Grade.RIGHT,
            5: Grade.EASY_RIGHT,
        }[min(self_rating, 5)]
    return Grade.RIGHT if correct else Grade.WRONG


def topological_order(skills: dict[str, Skill]) -> list[str]:
    indegree: dict[str, int] = {sid: len(s.prerequisites) for sid, s in skills.items()}
    dependents: dict[str, list[str]] = {sid: [] for sid in skills}
    for sid, skill in skills.items():
        for prereq in skill.prerequisites:
            dependents[prereq].append(sid)
    ready = sorted([sid for sid, deg in indegree.items() if deg == 0])
    order: list[str] = []
    while ready:
        sid = ready.pop(0)
        order.append(sid)
        for nxt in dependents[sid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
                ready.sort()
    return order


def frontier(skills: dict[str, Skill], states: dict[str, SkillState]) -> list[str]:
    ok: list[str] = []
    for sid, skill in skills.items():
        state = states.get(sid)
        if state and state.mastered:
            continue
        prereq_ok = all(
            (states.get(p) and (states[p].mastered or states[p].mastery >= 70.0))
            for p in skill.prerequisites
        )
        if not skill.prerequisites or prereq_ok:
            ok.append(sid)
    return sorted(ok)


def next_best_skill(
    skills: dict[str, Skill],
    states: dict[str, SkillState],
    *,
    target_skill: str | None = None,
) -> str | None:
    cand = frontier(skills, states)
    if not cand:
        return None
    if target_skill and target_skill in skills:
        chain: set[str] = set()
        stack = [target_skill]
        while stack:
            sid = stack.pop()
            if sid in chain:
                continue
            chain.add(sid)
            stack.extend(skills[sid].prerequisites)
        in_chain = [c for c in cand if c in chain]
        if in_chain:
            return min(
                in_chain, key=lambda c: states.get(c).mastery if states.get(c) else 0.0
            )
    return min(cand, key=lambda c: states.get(c).mastery if states.get(c) else 0.0)


def path_progress(
    skills: dict[str, Skill], states: dict[str, SkillState]
) -> dict[str, Any]:
    total = len(skills)
    if total == 0:
        return {
            "total": 0,
            "mastered": 0,
            "in_progress": 0,
            "not_started": 0,
            "average_mastery": 0.0,
        }
    mastered = sum(1 for s in states.values() if s.mastered)
    in_progress = sum(1 for s in states.values() if s.encounters > 0 and not s.mastered)
    average = round(sum(s.mastery for s in states.values()) / total, 1)
    return {
        "total": total,
        "mastered": mastered,
        "in_progress": in_progress,
        "not_started": total - mastered - in_progress,
        "average_mastery": average,
    }


def due_skills(
    states: dict[str, SkillState], *, today: date | None = None
) -> list[str]:
    today = today or date.today()
    return sorted(
        sid for sid, s in states.items() if not s.mastered and s.due_date <= today
    )
