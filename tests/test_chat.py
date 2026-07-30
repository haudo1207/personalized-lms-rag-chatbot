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
    client, new_user, enrolled_course, user_headers
):
    resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": enrolled_course["id"],
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


def test_chat_forbidden_for_other_users_id(client, new_user, enrolled_course, unique_suffix, admin_headers, user_headers):
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
            "course_id": enrolled_course["id"],
            "question": "Khoa chinh la gi?",
            "top_k": 3,
        },
        headers=user_headers,
    )
    assert resp.status_code == 403


def test_chat_without_token_is_unauthorized(client, new_user, enrolled_course):
    resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": enrolled_course["id"],
            "question": "Khoa chinh la gi?",
        },
    )
    assert resp.status_code == 401
