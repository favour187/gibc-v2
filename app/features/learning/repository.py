from __future__ import annotations
import uuid
from datetime import date, datetime, timedelta
from typing import Any
from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from app.core.db import Base, TimestampsMixin, UUIDMixin, iso_utc, utcnow
from app.features.learning.core import SkillState

class StudyProfile(UUIDMixin, TimestampsMixin, Base):
    __tablename__ = "learning_profiles"
    user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    target_skill: Mapped[str] = mapped_column(String(64), default="")
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    states: Mapped[list["SkillProgress"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "target_skill": self.target_skill,
            "started_at": iso_utc(self.started_at),
            "states": [s.to_dict() for s in self.states],
        }

class SkillProgress(UUIDMixin, Base):
    __tablename__ = "learning_progress"
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("learning_profiles.id"), index=True
    )
    skill_id: Mapped[str] = mapped_column(String(64), index=True)
    theta: Mapped[float] = mapped_column(default=0.0)
    encounters: Mapped[int] = mapped_column(default=0)
    correct: Mapped[int] = mapped_column(default=0)
    repetition: Mapped[int] = mapped_column(default=0)
    interval_days: Mapped[float] = mapped_column(default=0.0)
    due_date: Mapped[date] = mapped_column(default=date.today)
    last_grade: Mapped[int] = mapped_column(default=0)
    profile: Mapped[StudyProfile] = relationship(back_populates="states")

    def to_state(self) -> SkillState:
        return SkillState(
            skill_id=self.skill_id,
            theta=self.theta,
            encounters=self.encounters,
            correct=self.correct,
            repetition=self.repetition,
            interval_days=self.interval_days,
            due_date=self.due_date,
            last_grade=self.last_grade,
        )

    def apply_state(self, state: SkillState) -> None:
        self.theta = state.theta
        self.encounters = state.encounters
        self.correct = state.correct
        self.repetition = state.repetition
        self.interval_days = state.interval_days
        self.due_date = state.due_date
        self.last_grade = state.last_grade

    def to_dict(self) -> dict[str, Any]:
        return self.to_state().to_dict()

class StudySessionEntity(UUIDMixin, Base):
    __tablename__ = "learning_sessions"
    profile_id: Mapped[str] = mapped_column(String(64), index=True)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    finished_at: Mapped[datetime] = mapped_column(default=utcnow)
    question_count: Mapped[int] = mapped_column(default=0)
    correct_count: Mapped[int] = mapped_column(default=0)
    sources_json: Mapped[str] = mapped_column(Text, default="[]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "started_at": iso_utc(self.started_at),
            "finished_at": iso_utc(self.finished_at),
            "question_count": self.question_count,
            "correct_count": self.correct_count,
            "accuracy": (
                round(self.correct_count / self.question_count, 3)
                if self.question_count
                else None
            ),
        }

class AttemptEntity(UUIDMixin, Base):
    __tablename__ = "learning_attempts"
    profile_id: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    question_id: Mapped[str] = mapped_column(String(64), index=True)
    skill_id: Mapped[str] = mapped_column(String(64), index=True)
    chosen_index: Mapped[int] = mapped_column(default=0)
    correct: Mapped[bool] = mapped_column(default=False)
    grade: Mapped[int] = mapped_column(default=1)
    theta_after: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

def get_or_create_profile(db: Session, user_id: str) -> StudyProfile:
    profile = db.scalar(select(StudyProfile).where(StudyProfile.user_id == user_id))
    if profile is None:
        profile = StudyProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def get_progress(
    db: Session, profile_id: uuid.UUID, skill_id: str
) -> SkillProgress | None:
    return db.scalar(
        select(SkillProgress).where(
            SkillProgress.profile_id == profile_id, SkillProgress.skill_id == skill_id
        )
    )

def upsert_progress(
    db: Session, profile_id: uuid.UUID, state: SkillState
) -> SkillProgress:
    row = get_progress(db, profile_id, state.skill_id)
    if row is None:
        row = SkillProgress(profile_id=profile_id, skill_id=state.skill_id)
        db.add(row)
    row.apply_state(state)
    db.commit()
    db.refresh(row)
    return row

def all_states(db: Session, profile_id: uuid.UUID) -> dict[str, SkillState]:
    rows = db.scalars(
        select(SkillProgress).where(SkillProgress.profile_id == profile_id)
    )
    return {r.skill_id: r.to_state() for r in rows}

def record_session(
    db: Session, profile_id: str, data: dict[str, Any]
) -> StudySessionEntity:
    import json

    session = StudySessionEntity(
        profile_id=profile_id,
        question_count=data.get("question_count", 0),
        correct_count=data.get("correct_count", 0),
        sources_json=json.dumps(data.get("sources", [])),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def record_attempt(
    db: Session, profile_id: str, session_id: str, record: dict[str, Any]
) -> AttemptEntity:
    attempt = AttemptEntity(
        profile_id=profile_id,
        session_id=session_id,
        question_id=record["question_id"],
        skill_id=record["skill_id"],
        chosen_index=record["chosen_index"],
        correct=record["correct"],
        grade=record["grade"],
        theta_after=record["theta_after"],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt

def study_streak(db: Session, profile_id: uuid.UUID | str) -> int:
    rows = db.scalars(
        select(AttemptEntity.created_at).where(
            AttemptEntity.profile_id == str(profile_id)
        )
    )
    days = {r.date() for r in rows}
    streak = 0
    cursor = date.today()
    if cursor not in days:
        cursor -= timedelta(days=1)
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak

def review_queue_size(db: Session, profile_id: uuid.UUID) -> int:
    rows = db.scalars(
        select(SkillProgress).where(SkillProgress.profile_id == profile_id)
    )
    today = date.today()
    return sum(1 for r in rows if not r.to_state().mastered and r.due_date <= today)
