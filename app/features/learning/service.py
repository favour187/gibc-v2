from __future__ import annotations
from dataclasses import asdict
from datetime import date
from typing import Any
from sqlalchemy.orm import Session
from app.core.ai import AIGateway, get_gateway
from app.features.learning import ai_skills
from app.features.learning.content import SKILLS, question_by_id
from app.features.learning.core import (
    Skill,
    SkillState,
    frontier,
    next_best_skill,
    path_progress,
    topological_order,
)
from app.features.learning.engine import assemble_session, grade_answer
from app.features.learning.repository import (
    StudyProfile,
    all_states,
    get_or_create_profile,
    record_attempt,
    record_session,
    review_queue_size,
    study_streak,
    upsert_progress,
)

def _state_map(db: Session, profile: StudyProfile) -> dict[str, SkillState]:
    return all_states(db, profile.id)

def overview(db: Session, user_id: str) -> dict[str, Any]:
    profile = get_or_create_profile(db, user_id)
    states = _state_map(db, profile)
    order = topological_order(SKILLS)
    front = frontier(SKILLS, states)
    next_skill = next_best_skill(
        SKILLS, states, target_skill=profile.target_skill or None
    )
    return {
        "profile": profile.to_dict(),
        "curriculum": {
            "total_skills": len(SKILLS),
            "tracks": sorted({s.track for s in SKILLS.values()}),
            "skills": [
                asdict(s) | {"prerequisites": list(s.prerequisites)}
                for s in SKILLS.values()
            ],
            "order": order,
        },
        "progress": path_progress(SKILLS, states),
        "frontier": front,
        "next_skill": next_skill,
        "next_skill_title": SKILLS[next_skill].title if next_skill else None,
        "target_skill": profile.target_skill or None,
        "target_reached": bool(
            profile.target_skill
            and states.get(profile.target_skill)
            and states[profile.target_skill].mastered
        ),
        "due_count": len(
            [
                s
                for s in states.values()
                if not s.mastered and s.due_date <= date.today()
            ]
        ),
        "review_queue": review_queue_size(db, profile.id),
        "streak": study_streak(db, profile.id),
        "state_map": {sid: st.to_dict() for sid, st in states.items()},
    }

def new_session(
    db: Session, user_id: str, *, target_skill: str | None = None
) -> dict[str, Any]:
    profile = get_or_create_profile(db, user_id)
    states = _state_map(db, profile)
    session = assemble_session(
        SKILLS,
        states,
        target_skill=target_skill or profile.target_skill or None,
    )
    return {
        "questions": [q.to_dict() for q in session.questions],
        "count": session.question_count,
        "skill_titles": session.skill_title,
    }

def grade(
    db: Session,
    user_id: str,
    *,
    question_id: str,
    chosen_index: int,
    self_rating: int | None,
) -> dict[str, Any]:
    profile = get_or_create_profile(db, user_id)
    question = question_by_id(question_id)
    if question is None:
        raise ValueError("Unknown question_id")
    states = _state_map(db, profile)
    state = states.get(question.skill_id, SkillState(skill_id=question.skill_id))
    record = grade_answer(
        state, question, chosen_index=chosen_index, self_rating=self_rating
    )
    upsert_progress(db, profile.id, state)
    return {
        "record": record.to_dict(),
        "question": {
            "stem": question.stem,
            "correct_answer": question.options[question.answer_index],
            "explanation": question.explanation,
            "misconception": question.misconception,
        },
        "skill": state.to_dict(),
        "skill_title": SKILLS[question.skill_id].title,
    }

def finish_session(
    db: Session, user_id: str, *, question_count: int, correct_count: int
) -> dict[str, Any]:
    profile = get_or_create_profile(db, user_id)
    session = record_session(
        db,
        str(profile.id),
        {
            "question_count": question_count,
            "correct_count": correct_count,
            "sources": [],
        },
    )
    return session.to_dict()

def tutor(
    db: Session,
    user_id: str,
    *,
    message: str,
    question_id: str | None = None,
    gateway: AIGateway | None = None,
) -> dict[str, Any]:
    gateway = gateway or get_gateway()
    profile = get_or_create_profile(db, user_id)
    states = _state_map(db, profile)
    due = [s for s in states.values() if not s.mastered and s.due_date <= date.today()]
    front = frontier(SKILLS, states)
    result = gateway.chat(
        system=ai_skills.SYSTEM_PROMPT,
        user=message,
        max_tokens=420,
    )
    return {
        "reply": result.text,
        "provider": result.provider,
        "used_fallback": result.used_fallback,
        "due_count": len(due),
        "frontier_count": len(front),
    }

def set_target(db: Session, user_id: str, skill_id: str) -> dict[str, Any]:
    if skill_id not in SKILLS:
        raise ValueError("Unknown skill_id")
    profile = get_or_create_profile(db, user_id)
    profile.target_skill = skill_id
    db.commit()
    return {"target_skill": skill_id, "title": SKILLS[skill_id].title}
