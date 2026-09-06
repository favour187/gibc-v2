"""AI layer for Adaptive Learning Studio.

Deterministic local skills use the curated content (concept definitions,
explanations, misconceptions) so the app is fully functional with no API key.
When a key is configured, the same prompts go to the remote LLM with the
curriculum passed as context; the scores and scheduling still come from the
deterministic engine either way.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.ai import AIMessage, AIProvider, LocalDemoProvider
from app.features.learning.content import SKILLS, question_by_id


class ExplainSkill:
    """Explain a concept using the curated definition + misconception."""

    id = "explain"

    def can_handle(self, user_text: str, system: str) -> bool:
        lowered = user_text.lower()
        return any(k in lowered for k in ("explain", "concept", "what is", "what's", "how does"))

    def respond(self, user_text: str, system: str, context: dict[str, Any] | None) -> str:
        # Try to find the skill or question being asked about.
        topic = user_text.lower()
        skill = None
        for sid, s in SKILLS.items():
            if sid.replace("_", " ") in topic or s.title.lower().split(" ")[0] in topic:
                skill = s
                break
        if skill is None:
            return (
                f"The curriculum currently covers these skills: "
                f"{', '.join(s.title for s in SKILLS.values())}. Ask me about one and I'll "
                f"explain it, or say 'explain <concept>'."
            )
        return (
            f"**{skill.title}** ({skill.track}, difficulty {skill.difficulty}/5)\n\n"
            f"{skill.description}\n\n{skill.concept}\n\n"
            f"Common misconception: {_common_misconception(skill.skill_id) or 'none recorded for this skill.'}"
        )


def _common_misconception(skill_id: str) -> str | None:
    from app.features.learning.content import questions_for

    for q in questions_for(skill_id):
        if q.misconception:
            return q.misconception
    return None


class WrongAnswerSkill:
    """Explain WHY an answer was wrong (uses the question explanation)."""

    id = "wrong-answer"

    def can_handle(self, user_text: str, system: str) -> bool:
        lowered = user_text.lower()
        return any(k in lowered for k in ("wrong", "why is", "why did", "incorrect"))

    def respond(self, user_text: str, system: str, context: dict[str, Any] | None) -> str:
        qid = None
        if context and isinstance(context.get("question_id"), str):
            qid = context["question_id"]
        # fall back: look for a question id pattern in the text
        if not qid:
            import re

            match = re.search(r"q_[a-z0-9_]+", user_text)
            if match:
                qid = match.group(0)
        question = question_by_id(qid) if qid else None
        if question is None:
            return (
                "Tell me which question you got wrong (or paste its id) and I'll explain the "
                "reasoning behind the correct answer."
            )
        return (
            f"**{question.stem}**\n\nCorrect answer: **{question.options[question.answer_index]}**\n\n"
            f"Why: {question.explanation}"
        )


class StudyTipSkill:
    """Personalised coaching from the learner's actual state."""

    id = "study-tip"

    def can_handle(self, user_text: str, system: str) -> bool:
        return "tip" in user_text.lower() or "stuck" in user_text.lower() or "motivat" in user_text.lower()

    def respond(self, user_text: str, system: str, context: dict[str, Any] | None) -> str:
        due = context.get("due_count", 0) if context else 0
        front = context.get("frontier_count", 0) if context else 0
        return (
            f"Quick study tip: you have {due} review(s) due — clear those first, spaced "
            f"repetition beats cramming. Then unlock one of the {front} frontier skills. "
            f"Short daily sessions (5–8 questions) outperform marathon weekends, and the "
            f"engine keeps the tricky items coming back at the right time."
        )


LOCAL_SKILLS: list[Any] = [ExplainSkill(), WrongAnswerSkill(), StudyTipSkill()]


def local_provider() -> AIProvider:
    return LocalDemoProvider(LOCAL_SKILLS)


SYSTEM_PROMPT = (
    "You are the AI tutor for Adaptive Learning Studio, a hackathon demo adaptive learning "
    "engine. You explain concepts clearly (max 150 words), using the curriculum context given. "
    "Never invent mastery scores or schedule data — that comes from the engine. If asked why an "
    "answer was wrong, reason about the specific misconception. Be warm and concise."
)


def concept_context(skill_ids: list[str]) -> str:
    parts = []
    for sid in skill_ids:
        s = SKILLS.get(sid)
        if s:
            parts.append(f"- {s.title}: {s.concept}")
    return "\n".join(parts) if parts else ""


def build_messages(user_text: str, *, question_id: str | None = None, skill_ids: list[str] | None = None) -> list[AIMessage]:
    context: list[str] = []
    if question_id:
        q = question_by_id(question_id)
        if q:
            context.append(
                f"Question in play: {q.stem} | correct answer: {q.options[q.answer_index]} | "
                f"explanation: {q.explanation} | misconception: {q.misconception}"
            )
    curriculum = concept_context(skill_ids or [])
    if curriculum:
        context.append(f"Curriculum context:\n{curriculum}")
    system = SYSTEM_PROMPT + ("\n\n" + "\n\n".join(context) if context else "")
    return [
        AIMessage(role="system", content=system),
        AIMessage(role="user", content=user_text),
    ]
