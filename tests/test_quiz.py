import json

FAKE_QUIZ_JSON = json.dumps(
    [
        {
            "question": "Khoa chinh dung de lam gi?",
            "options": {
                "A": "Xac dinh duy nhat moi ban ghi",
                "B": "Lien ket bang khac",
                "C": "Sap xep du lieu",
                "D": "Xoa du lieu trung lap",
            },
            "correct_answer": "A",
            "explanation": "Khoa chinh xac dinh duy nhat moi ban ghi trong bang.",
        }
    ]
)


def test_generate_quiz_returns_questions(client, new_user, new_course, uploaded_document, monkeypatch):
    monkeypatch.setattr("backend.services.quiz_generator.generate_answer", lambda prompt: FAKE_QUIZ_JSON)

    resp = client.post(
        "/quiz/generate",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "topic": "Khoa chinh",
            "num_questions": 1,
            "difficulty": "easy",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["adaptive_difficulty"] == "easy"
    assert len(body["quiz"]) == 1
    assert body["quiz"][0]["correct_answer"] == "A"


def test_generate_quiz_without_matching_documents_reports_no_context(client, new_user, new_course):
    resp = client.post(
        "/quiz/generate",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "topic": "Chu de khong ton tai",
            "num_questions": 3,
            "difficulty": "easy",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["quiz"]["error"] == "No relevant context found"


def test_submit_quiz_and_read_results(client, new_user, new_course):
    resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "topic": "Khoa chinh",
            "total_questions": 5,
            "correct_answers": 4,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] == 80.0

    results = client.get(f"/quiz/results/{new_user['id']}", params={"course_id": new_course["id"]})
    assert results.status_code == 200
    assert any(r["topic"] == "Khoa chinh" for r in results.json())


def test_submit_quiz_rejects_correct_greater_than_total(client, new_user, new_course):
    resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "topic": "Khoa chinh",
            "total_questions": 3,
            "correct_answers": 5,
        },
    )
    assert resp.status_code == 400
