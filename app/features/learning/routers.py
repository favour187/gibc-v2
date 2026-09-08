from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.auth import User, get_current_user
from app.core.db import get_db
from app.core.errors import NotFoundError, ValidationFailedError
from app.features.learning import service

router = APIRouter(prefix="/learning", tags=["learning"])

class GradeIn(BaseModel):
    question_id: str = Field(min_length=1)
    chosen_index: int = Field(ge=0, le=5)
    self_rating: int | None = Field(default=None, ge=1, le=5)

class SessionFinishIn(BaseModel):
    question_count: int = Field(ge=0)
    correct_count: int = Field(ge=0)

class TutorIn(BaseModel):
    message: str = Field(min_length=1, max_length=800)
    question_id: str | None = None

class TargetIn(BaseModel):
    skill_id: str = Field(min_length=1)

@router.get("/overview")
def overview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.overview(db, str(user.id))

@router.get("/session")
def session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.new_session(db, str(user.id))

@router.post("/grade")
def grade(
    payload: GradeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return service.grade(
            db,
            str(user.id),
            question_id=payload.question_id,
            chosen_index=payload.chosen_index,
            self_rating=payload.self_rating,
        )
    except ValueError as exc:
        raise ValidationFailedError(str(exc)) from exc

@router.post("/session/finish")
def finish(
    payload: SessionFinishIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.finish_session(
        db,
        str(user.id),
        question_count=payload.question_count,
        correct_count=payload.correct_count,
    )

@router.post("/tutor")
def tutor(
    payload: TutorIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return service.tutor(
        db, str(user.id), message=payload.message, question_id=payload.question_id
    )

@router.patch("/target")
def set_target(
    payload: TargetIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return service.set_target(db, str(user.id), payload.skill_id)
    except ValueError as exc:
        raise ValidationFailedError(str(exc)) from exc
