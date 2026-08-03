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


def _generate(client, user, course, headers, monkeypatch, num_questions=1):
    monkeypatch.setattr("backend.services.quiz_generator.generate_answer", lambda prompt: FAKE_QUIZ_JSON)
    return client.post(
        "/quiz/generate",
        json={
            "user_id": user["id"],
            "course_id": course["id"],
            "topic": "Khoa chinh",
            "num_questions": num_questions,
            "difficulty": "easy",
        },
        headers=headers,
    )


def test_generate_quiz_hides_correct_answer_and_explanation(
    client, new_user, new_course, uploaded_document, user_headers, monkeypatch
):
    resp = _generate(client, new_user, new_course, user_headers, monkeypatch)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["adaptive_difficulty"] == "easy"
    assert body["quiz_session_id"]
    assert len(body["quiz"]) == 1
    question = body["quiz"][0]
    assert question["question"]
    assert question["options"]["A"]
    assert "correct_answer" not in question
    assert "explanation" not in question


def test_generate_quiz_without_matching_documents_reports_no_context(
    client, new_user, new_course, user_headers
):
    resp = client.post(
        "/quiz/generate",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "topic": "Chu de khong ton tai",
            "num_questions": 3,
            "difficulty": "easy",
        },
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["quiz"]["error"] == "No relevant context found"
    assert "quiz_session_id" not in resp.json()


def test_submit_quiz_grades_against_stored_answer_key(
    client, new_user, new_course, uploaded_document, user_headers, monkeypatch
):
    quiz_session_id = _generate(client, new_user, new_course, user_headers, monkeypatch).json()["quiz_session_id"]

    resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "quiz_session_id": quiz_session_id,
            "answers": ["A"],  # matches FAKE_QUIZ_JSON's correct_answer
        },
        headers=user_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["score"] == 100.0
    assert body["correct_answers"] == 1
    assert body["total_questions"] == 1
    assert body["review"][0]["is_correct"] is True
    assert body["review"][0]["correct"] == "A"
    assert body["review"][0]["explanation"]

    results = client.get(
        f"/quiz/results/{new_user['id']}",
        params={"course_id": new_course["id"]},
        headers=user_headers,
    )
    assert results.status_code == 200
    assert any(r["topic"] == "Khoa chinh" for r in results.json())


def test_submit_quiz_wrong_answer_scores_zero(
    client, new_user, new_course, uploaded_document, user_headers, monkeypatch
):
    quiz_session_id = _generate(client, new_user, new_course, user_headers, monkeypatch).json()["quiz_session_id"]

    resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "quiz_session_id": quiz_session_id,
            "answers": ["B"],
        },
        headers=user_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["score"] == 0.0
    assert resp.json()["review"][0]["is_correct"] is False


def test_submit_quiz_cannot_be_reused(client, new_user, new_course, uploaded_document, user_headers, monkeypatch):
    quiz_session_id = _generate(client, new_user, new_course, user_headers, monkeypatch).json()["quiz_session_id"]
    payload = {
        "user_id": new_user["id"],
        "course_id": new_course["id"],
        "quiz_session_id": quiz_session_id,
        "answers": ["A"],
    }
    first = client.post("/quiz/submit", json=payload, headers=user_headers)
    assert first.status_code == 200

    second = client.post("/quiz/submit", json=payload, headers=user_headers)
    assert second.status_code == 409


def test_submit_quiz_rejects_wrong_answer_count(
    client, new_user, new_course, uploaded_document, user_headers, monkeypatch
):
    quiz_session_id = _generate(client, new_user, new_course, user_headers, monkeypatch).json()["quiz_session_id"]

    resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "quiz_session_id": quiz_session_id,
            "answers": ["A", "B"],  # generated quiz only has 1 question
        },
        headers=user_headers,
    )
    assert resp.status_code == 400


def test_submit_quiz_missing_session_returns_404(client, new_user, new_course, user_headers):
    resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": new_course["id"],
            "quiz_session_id": 999999,
            "answers": ["A"],
        },
        headers=user_headers,
    )
    assert resp.status_code == 404


def test_submit_quiz_forbidden_for_other_users_session(
    client, new_user, new_course, uploaded_document, unique_suffix, admin_headers, user_headers, monkeypatch
):
    quiz_session_id = _generate(client, new_user, new_course, user_headers, monkeypatch).json()["quiz_session_id"]

    other = client.post(
        "/users/",
        json={
            "full_name": "Quiz Intruder",
            "email": f"quiz_intruder_{unique_suffix}@example.com",
            "password": "TestPass@123",
            "role": "student",
            "level": "beginner",
        },
        headers=admin_headers,
    ).json()

    # Admin can act on the course (ownership bypass) and on behalf of `other`
    # (require_self_or_admin) -- this isolates the deeper check under test:
    # the quiz session itself belongs to new_user, not to `other`.
    resp = client.post(
        "/quiz/submit",
        json={
            "user_id": other["id"],
            "course_id": new_course["id"],
            "quiz_session_id": quiz_session_id,
            "answers": ["A"],
        },
        headers=admin_headers,
    )
    assert resp.status_code == 403


def test_submit_quiz_forbidden_for_non_owned_course(
    client, new_user, unique_suffix, admin_headers, user_headers
):
    others_course = client.post(
        "/courses/",
        json={"course_code": f"QZOTH{unique_suffix}", "course_name": "Not yours"},
        headers=admin_headers,
    ).json()
    resp = client.post(
        "/quiz/submit",
        json={
            "user_id": new_user["id"],
            "course_id": others_course["id"],
            "quiz_session_id": 1,
            "answers": ["A"],
        },
        headers=user_headers,
    )
    assert resp.status_code == 403
