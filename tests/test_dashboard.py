def test_dashboard_aggregates_chat_and_quiz_activity(client, new_user, new_course, uploaded_document, monkeypatch):
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
    )
    assert chat_resp.status_code == 200

    submit_resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "topic": chat_resp.json()["topic"] or "Khoa chinh",
            "total_questions": 4,
            "correct_answers": 3,
        },
    )
    assert submit_resp.status_code == 200

    dash_resp = client.get(f"/dashboard/student/{new_user['id']}", params={"course_id": new_course["id"]})
    assert dash_resp.status_code == 200
    dashboard = dash_resp.json()
    assert dashboard["total_questions"] == 1
    assert dashboard["average_quiz_score"] == 75.0
    assert len(dashboard["quiz_results"]) == 1
    assert "recommendations" in dashboard


def test_profile_endpoint_reflects_user_and_history(client, new_user, new_course):
    resp = client.get(f"/chat/profile/{new_user['id']}/{new_course['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["full_name"] == new_user["full_name"]
    assert body["level"] == new_user["level"]
    assert body["recent_questions"] == []
    assert body["weak_topics"] == []
