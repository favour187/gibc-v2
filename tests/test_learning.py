from __future__ import annotations
from datetime import date, timedelta
from app.core.testing import auth_headers, create_user
from app.features.learning.content import SKILLS, QUESTION_BANK, questions_for
from app.features.learning.core import (
    Grade,
    SkillState,
    apply_grade,
    difficulty_scaled,
    due_skills,
    frontier,
    mastery_from_theta,
    next_best_skill,
    path_progress,
    topological_order,
    update_mastery,
)
from app.features.learning.engine import assemble_session, grade_answer

def test_difficulty_scaling():
    assert difficulty_scaled(1) < difficulty_scaled(3) < difficulty_scaled(5)
    assert 0.0 < difficulty_scaled(1) < 1.0

def test_mastery_monotonic_in_theta():
    assert mastery_from_theta(0) == 50.0
    assert mastery_from_theta(3) > mastery_from_theta(0)
    assert mastery_from_theta(-3) < mastery_from_theta(0)

def test_correct_answer_raises_mastery():
    state = SkillState("variables")
    before = state.mastery
    update_mastery(state, difficulty_scaled(2), correct=True)
    assert state.mastery > before
    assert state.encounters == 1
    assert state.correct == 1

def test_wrong_answer_lowers_mastery():
    state = SkillState("variables")
    before = state.mastery
    update_mastery(state, difficulty_scaled(2), correct=False)
    assert state.mastery < before

def test_hard_correct_answer_is_more_informative():
    state = SkillState("variables")
    update_mastery(state, difficulty_scaled(1), correct=True)
    easy_theta = state.theta
    state2 = SkillState("variables")
    update_mastery(state2, difficulty_scaled(5), correct=True)
    assert state2.theta > easy_theta

def test_sm2_intervals_grow():
    state = SkillState("loops", due_date=date.today())
    apply_grade(state, Grade.RIGHT)
    first = state.interval_days
    apply_grade(state, Grade.RIGHT)
    assert state.interval_days > first
    assert state.due_date > date.today()

def test_wrong_answer_resets_repetition():
    state = SkillState("loops", due_date=date.today())
    apply_grade(state, Grade.RIGHT)
    apply_grade(state, Grade.RIGHT)
    apply_grade(state, Grade.WRONG)
    assert state.repetition == 0
    assert state.interval_days == 0.0
    assert state.due_date == date.today() + timedelta(days=1)

def test_due_skills():
    today = date.today()
    overdue = SkillState("loops", due_date=today - timedelta(days=1))
    future = SkillState("loops2", due_date=today + timedelta(days=5))
    due = due_skills({"loops": overdue, "loops2": future}, today=today)
    assert due == ["loops"]

def test_topological_order_respects_prereqs():
    order = topological_order(SKILLS)
    pos = {sid: i for i, sid in enumerate(order)}
    for sid, skill in SKILLS.items():
        for prereq in skill.prerequisites:
            assert pos[prereq] < pos[sid], f"{prereq } must come before {sid }"
    assert len(order) == len(SKILLS)

def test_frontier_shrinks_as_skills_are_learned():
    master = {sid: SkillState(sid, theta=6.0) for sid in ("variables", "conditionals")}
    for s in master.values():
        s.encounters = 5
    front = frontier(SKILLS, master)
    assert "variables" not in front
    assert "functions" not in front
    assert "loops" in front

def test_next_best_picks_weakest_frontier():
    states = {
        "variables": SkillState("variables", theta=5.0, encounters=5),
        "conditionals": SkillState("conditionals", theta=1.0, encounters=2),
    }
    nxt = next_best_skill(SKILLS, states)
    assert nxt in frontier(SKILLS, states)
    assert nxt != "variables"

def test_next_best_chases_target():
    states = {
        "variables": SkillState("variables", theta=4.0, encounters=5),
        "conditionals": SkillState("conditionals", theta=4.0, encounters=5),
        "loops": SkillState("loops", theta=4.0, encounters=5),
    }
    nxt = next_best_skill(SKILLS, states, target_skill="overfitting")
    assert nxt in {"stats_basics", "functions"}

def test_progress_counts():
    states = {"variables": SkillState("variables", theta=6.0, encounters=5)}
    p = path_progress(SKILLS, states)
    assert p["total"] == len(SKILLS)
    assert p["mastered"] >= 1
    assert p["not_started"] == p["total"] - p["in_progress"] - p["mastered"]

def test_session_assembly_mixes_sources():
    states = {
        "variables": SkillState("variables", theta=5.0, encounters=5),
        "conditionals": SkillState("conditionals", theta=0.5, encounters=2),
    }
    session = assemble_session(SKILLS, states)
    assert 0 < session.question_count <= 8
    sources = {q.source for q in session.questions}
    assert "weak" in sources or "new" in sources

def test_grade_answer_updates_state():
    q = questions_for("loops")[0]
    state = SkillState("loops")
    record = grade_answer(state, q, chosen_index=q.answer_index)
    assert record.correct is True
    assert record.mastery_after > 50.0
    assert state.encounters == 1
    wrong = grade_answer(state, q, chosen_index=(q.answer_index + 1) % 4)
    assert wrong.correct is False
    assert wrong.grade == int(Grade.WRONG)

def test_curriculum_content_is_complete():
    for sid, skill in SKILLS.items():
        bank = questions_for(sid)
        assert len(bank) >= 2, sid
        for q in bank:
            assert q.skill_id == sid
            assert 0 <= q.answer_index < len(q.options)
            assert 1 <= q.difficulty <= 5
    assert all(q.question_id and q.stem and q.explanation for q in QUESTION_BANK)

def test_api_learning_flow(client):
    headers = auth_headers(create_user(client, email="learn@example.com")["token"])
    res = client.get("/api/learning/overview", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["curriculum"]["total_skills"] == len(SKILLS)
    assert "next_skill" in body
    assert body["due_count"] == 0
    res = client.get("/api/learning/session", headers=headers)
    assert res.status_code == 200
    session = res.json()
    assert session["count"] > 0
    first = session["questions"][0]
    assert "answer_index" not in first
    q = next(q for q in QUESTION_BANK if q.question_id == first["question_id"])
    res = client.post(
        "/api/learning/grade",
        headers=headers,
        json={"question_id": first["question_id"], "chosen_index": q.answer_index},
    )
    assert res.status_code == 200, res.text
    graded = res.json()
    assert graded["record"]["correct"] is True
    assert graded["skill"]["encounters"] >= 1
    res = client.post(
        "/api/learning/tutor", headers=headers, json={"message": "Explain loops to me"}
    )
    assert res.status_code == 200
    tutor = res.json()
    assert tutor["reply"]
    assert tutor["used_fallback"] is True
    assert "Loops" in tutor["reply"] or "loops" in tutor["reply"].lower()
    res = client.patch(
        "/api/learning/target", headers=headers, json={"skill_id": "overfitting"}
    )
    assert res.status_code == 200
    assert res.json()["target_skill"] == "overfitting"
    res = client.patch(
        "/api/learning/target", headers=headers, json={"skill_id": "nope"}
    )
    assert res.status_code == 422
    res = client.post(
        "/api/learning/grade",
        headers=headers,
        json={"question_id": "q_does_not_exist", "chosen_index": 0},
    )
    assert res.status_code == 422
    assert client.get("/api/learning/overview").status_code == 401

def test_api_session_finish(client):
    headers = auth_headers(create_user(client, email="finish@example.com")["token"])
    res = client.post(
        "/api/learning/session/finish",
        headers=headers,
        json={"question_count": 5, "correct_count": 4},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["question_count"] == 5
    assert body["accuracy"] == 0.8

def test_attempt_lookups_use_text_profile_id(client):
    import uuid
    from app.core.state import get_app_state
    from app.core.db import session_scope
    from app.features.learning.repository import study_streak

    with session_scope(get_app_state().session_factory) as db:
        assert study_streak(db, uuid.uuid4()) == 0
