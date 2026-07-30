from backend.services.prompt_template import INSUFFICIENT_INFORMATION_ANSWER

FAKE_ANSWER = "Khoa chinh dung de xac dinh duy nhat moi ban ghi trong bang."


def test_chat_returns_answer_with_sources(client, new_user, new_course, uploaded_document, monkeypatch):
    monkeypatch.setattr("backend.services.rag_pipeline.generate_answer", lambda prompt: FAKE_ANSWER)

    resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "question": "Khoa chinh la gi?",
            "top_k": 3,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == FAKE_ANSWER
    assert body["sources"]
    assert body["topic"]

    history = client.get(f"/chat/history/{new_user['id']}")
    assert history.status_code == 200
    assert any(h["question"] == "Khoa chinh la gi?" for h in history.json())


def test_chat_without_matching_documents_returns_insufficient_info(client, new_user, new_course):
    resp = client.post(
        "/chat/",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "question": "Cau hoi ve mot chu de khong co tai lieu nao lien quan?",
            "top_k": 3,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["answer"] == INSUFFICIENT_INFORMATION_ANSWER


def test_chat_llm_failure_returns_502(client, new_user, new_course, uploaded_document, monkeypatch):
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
    )
    assert resp.status_code == 502
