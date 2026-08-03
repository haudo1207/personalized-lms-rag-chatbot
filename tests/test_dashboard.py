def test_dashboard_aggregates_chat_and_quiz_activity(
    client, new_user, new_course, uploaded_document, user_headers, monkeypatch
):
    import json

    monkeypatch.setattr(
        "backend.services.rag_pipeline.generate_answer",
        lambda prompt: "Khoa chinh dung de xac dinh duy nhat moi ban ghi.",
    )
    chat_resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "question": "Khoa chinh la gi?",
            "top_k": 3,
        },
        headers=user_headers,
    )
    assert chat_resp.status_code == 200

    fake_quiz = json.dumps(
        [
            {"question": f"Cau {i}?", "options": {"A": "a", "B": "b", "C": "c", "D": "d"}, "correct_answer": "A"}
            for i in range(4)
        ]
    )
    monkeypatch.setattr("backend.services.quiz_generator.generate_answer", lambda prompt: fake_quiz)
    generate_resp = client.post(
        "/quiz/generate",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "topic": chat_resp.json()["topic"] or "Khoa chinh",
            "num_questions": 4,
        },
        headers=user_headers,
    )
    quiz_session_id = generate_resp.json()["quiz_session_id"]

    submit_resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "quiz_session_id": quiz_session_id,
            "answers": ["A", "A", "A", "B"],  # 3 correct out of 4 -> 75%
        },
        headers=user_headers,
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["score"] == 75.0

    dash_resp = client.get(
        f"/dashboard/student/{new_user['id']}",
        params={"course_id": new_course["id"]},
        headers=user_headers,
    )
    assert dash_resp.status_code == 200
    dashboard = dash_resp.json()
    assert dashboard["total_questions"] == 1
    assert dashboard["average_quiz_score"] == 75.0
    assert len(dashboard["quiz_results"]) == 1
    assert "recommendations" in dashboard


def test_profile_endpoint_reflects_user_and_history(client, new_user, new_course, user_headers):
    resp = client.get(f"/chat/profile/{new_user['id']}/{new_course['id']}", headers=user_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == new_user["full_name"]
    assert body["level"] == new_user["level"]
    assert body["recent_questions"] == []
    assert body["weak_topics"] == []


def test_dashboard_forbidden_for_non_owned_course(client, new_user, unique_suffix, admin_headers, user_headers):
    others_course = client.post(
        "/courses/",
        json={"course_code": f"DASHOTH{unique_suffix}", "course_name": "Not yours"},
        headers=admin_headers,
    ).json()
    resp = client.get(
        f"/dashboard/student/{new_user['id']}",
        params={"course_id": others_course["id"]},
        headers=user_headers,
    )
    assert resp.status_code == 403


def test_dashboard_feedback_rate_reflects_chat_feedback(
    client, new_user, uploaded_document, new_course, user_headers, monkeypatch
):
    monkeypatch.setattr("backend.services.rag_pipeline.generate_answer", lambda prompt: "Cau tra loi.")

    no_feedback = client.get(
        f"/dashboard/student/{new_user['id']}", params={"course_id": new_course["id"]}, headers=user_headers
    )
    assert no_feedback.json()["feedback_rate"] is None

    chat_resp = client.post(
        "/chat/",
        json={"user_id": new_user["id"], "course_id": new_course["id"], "question": "Khoa chinh la gi?"},
        headers=user_headers,
    )
    chat_id = chat_resp.json()["chat_id"]
    client.patch(f"/chat/{chat_id}/feedback", json={"feedback": "like"}, headers=user_headers)

    with_feedback = client.get(
        f"/dashboard/student/{new_user['id']}", params={"course_id": new_course["id"]}, headers=user_headers
    )
    body = with_feedback.json()
    assert body["feedback_rate"] == 1.0
    assert body["feedback_like_count"] == 1


def test_recommendation_is_generated_from_course_content_for_active_weak_topic(
    client, new_user, new_course, uploaded_document, user_headers, monkeypatch
):
    from backend.database import SessionLocal
    from backend.models.weak_topic import WeakTopic

    monkeypatch.setattr(
        "backend.services.recommendation.generate_answer",
        lambda prompt: "On lai phan Khoa chinh trong notes.txt.",
    )

    db = SessionLocal()
    try:
        db.add(
            WeakTopic(
                user_id=new_user["id"],
                course_id=new_course["id"],
                topic="Khoa chinh",
                reason="test",
                question_frequency=5,
                quiz_average=30.0,
                review_interval=10,
                weak_score=0.8,
                status="active",
            )
        )
        db.commit()
    finally:
        db.close()

    resp = client.get(
        f"/dashboard/student/{new_user['id']}", params={"course_id": new_course["id"]}, headers=user_headers
    )
    assert resp.status_code == 200
    recs = resp.json()["recommendations"]
    assert any(r["topic"] == "Khoa chinh" and "notes.txt" in r["recommendation"] for r in recs)


def test_recommendation_falls_back_to_generic_advice_when_no_context_found(
    client, new_user, new_course, user_headers
):
    # new_course has no uploaded_document -- no chunks exist to ground a recommendation in.
    from backend.database import SessionLocal
    from backend.models.weak_topic import WeakTopic

    db = SessionLocal()
    try:
        db.add(
            WeakTopic(
                user_id=new_user["id"],
                course_id=new_course["id"],
                topic="Chu de la",
                reason="test",
                question_frequency=5,
                quiz_average=30.0,
                review_interval=10,
                weak_score=0.8,
                status="active",
            )
        )
        db.commit()
    finally:
        db.close()

    resp = client.get(
        f"/dashboard/student/{new_user['id']}", params={"course_id": new_course["id"]}, headers=user_headers
    )
    assert resp.status_code == 200
    recs = resp.json()["recommendations"]
    assert any(r["topic"] == "Chu de la" and "ôn lại chủ đề" in r["recommendation"] for r in recs)
