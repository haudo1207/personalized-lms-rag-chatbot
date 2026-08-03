from backend.services.prompt_template import INSUFFICIENT_INFORMATION_ANSWER

FAKE_ANSWER = "Khoa chinh dung de xac dinh duy nhat moi ban ghi trong bang."


def test_chat_returns_answer_with_sources(
    client, new_user, new_course, uploaded_document, user_headers, monkeypatch
):
    monkeypatch.setattr("backend.services.rag_pipeline.generate_answer", lambda prompt: FAKE_ANSWER)

    resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "question": "Khoa chinh la gi?",
            "top_k": 3,
        },
        headers=user_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == FAKE_ANSWER
    assert body["sources"]
    assert body["topic"]

    history = client.get(f"/chat/history/{new_user['id']}", headers=user_headers)
    assert history.status_code == 200
    assert any(h["question"] == "Khoa chinh la gi?" for h in history.json())


def test_chat_without_matching_documents_returns_insufficient_info(
    client, new_user, new_course, user_headers
):
    resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "question": "Cau hoi ve mot chu de khong co tai lieu nao lien quan?",
            "top_k": 3,
        },
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["answer"] == INSUFFICIENT_INFORMATION_ANSWER


def test_chat_llm_failure_returns_502(
    client, new_user, new_course, uploaded_document, user_headers, monkeypatch
):
    # chat.py maps RuntimeError -> 503 ("not configured") and any other exception -> 502
    # ("request failed"); raise something other than RuntimeError to exercise the 502 path.
    def _boom(prompt):
        raise ValueError("Gemini API returned a malformed response in this test")

    monkeypatch.setattr("backend.services.rag_pipeline.generate_answer", _boom)

    resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "question": "Khoa chinh la gi?",
            "top_k": 3,
        },
        headers=user_headers,
    )
    assert resp.status_code == 502


def test_chat_forbidden_for_other_users_id(client, new_user, new_course, unique_suffix, admin_headers, user_headers):
    other = client.post(
        "/users/",
        json={
            "full_name": "Impersonation Target",
            "email": f"target_{unique_suffix}@example.com",
            "password": "TestPass@123",
            "role": "student",
            "level": "beginner",
        },
        headers=admin_headers,
    ).json()

    resp = client.post(
        "/chat/",
        json={
            "user_id": other["id"],
            "course_id": new_course["id"],
            "question": "Khoa chinh la gi?",
            "top_k": 3,
        },
        headers=user_headers,
    )
    assert resp.status_code == 403


def test_chat_without_token_is_unauthorized(client, new_user, new_course):
    resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "question": "Khoa chinh la gi?",
        },
    )
    assert resp.status_code == 401


def _ask_and_get_chat_id(client, new_user, course, user_headers, monkeypatch):
    monkeypatch.setattr("backend.services.rag_pipeline.generate_answer", lambda prompt: FAKE_ANSWER)
    resp = client.post(
        "/chat/",
        json={"user_id": new_user["id"], "course_id": course["id"], "question": "Khoa chinh la gi?", "top_k": 3},
        headers=user_headers,
    )
    return resp.json()["chat_id"]


def test_set_and_clear_feedback(client, new_user, uploaded_document, new_course, user_headers, monkeypatch):
    chat_id = _ask_and_get_chat_id(client, new_user, new_course, user_headers, monkeypatch)

    liked = client.patch(f"/chat/{chat_id}/feedback", json={"feedback": "like"}, headers=user_headers)
    assert liked.status_code == 200
    assert liked.json()["feedback"] == "like"

    cleared = client.patch(f"/chat/{chat_id}/feedback", json={"feedback": None}, headers=user_headers)
    assert cleared.status_code == 200
    assert cleared.json()["feedback"] is None


def test_feedback_rejects_invalid_value(client, new_user, uploaded_document, new_course, user_headers, monkeypatch):
    chat_id = _ask_and_get_chat_id(client, new_user, new_course, user_headers, monkeypatch)
    resp = client.patch(f"/chat/{chat_id}/feedback", json={"feedback": "meh"}, headers=user_headers)
    assert resp.status_code == 422


def test_feedback_forbidden_for_other_users_message(
    client, new_user, uploaded_document, new_course, unique_suffix, admin_headers, user_headers, monkeypatch
):
    chat_id = _ask_and_get_chat_id(client, new_user, new_course, user_headers, monkeypatch)

    other = client.post(
        "/users/",
        json={
            "full_name": "Feedback Intruder",
            "email": f"intruder_{unique_suffix}@example.com",
            "password": "TestPass@123",
            "role": "student",
            "level": "beginner",
        },
        headers=admin_headers,
    ).json()
    login = client.post("/auth/login", json={"email": other["email"], "password": "TestPass@123"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = client.patch(f"/chat/{chat_id}/feedback", json={"feedback": "like"}, headers=other_headers)
    assert resp.status_code == 403


def test_clear_history_removes_messages(client, new_user, uploaded_document, new_course, user_headers, monkeypatch):
    _ask_and_get_chat_id(client, new_user, new_course, user_headers, monkeypatch)

    resp = client.delete(f"/chat/history/{new_user['id']}/{new_course['id']}", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["deleted_count"] >= 1

    history = client.get(f"/chat/history/{new_user['id']}", headers=user_headers)
    assert not any(h["course_id"] == new_course["id"] for h in history.json())
