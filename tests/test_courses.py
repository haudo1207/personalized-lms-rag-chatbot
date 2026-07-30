def test_create_and_list_course(client, unique_suffix, admin_headers):
    resp = client.post(
        "/courses/",
        json={
            "course_code": f"CS{unique_suffix}",
            "course_name": "Co so du lieu",
            "description": "Mon hoc CSDL",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    created = resp.json()

    listed = client.get("/courses/", headers=admin_headers)
    assert listed.status_code == 200
    assert any(c["id"] == created["id"] for c in listed.json())


def test_create_course_duplicate_code_conflicts(client, new_course, admin_headers):
    resp = client.post(
        "/courses/",
        json={
            "course_code": new_course["course_code"],
            "course_name": "Another name",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_create_course_requires_admin(client, unique_suffix, user_headers):
    resp = client.post(
        "/courses/",
        json={"course_code": f"NOPE{unique_suffix}", "course_name": "Should fail"},
        headers=user_headers,
    )
    assert resp.status_code == 403


def test_mine_shows_only_enrolled_courses_for_student(client, new_course, user_headers):
    resp = client.get("/courses/mine", headers=user_headers)
    assert resp.status_code == 200
    assert not any(c["id"] == new_course["id"] for c in resp.json())


def test_mine_shows_enrolled_course_after_enroll(client, enrolled_course, user_headers):
    resp = client.get("/courses/mine", headers=user_headers)
    assert resp.status_code == 200
    assert any(c["id"] == enrolled_course["id"] for c in resp.json())


def test_mine_shows_all_courses_for_admin(client, new_course, admin_headers):
    resp = client.get("/courses/mine", headers=admin_headers)
    assert resp.status_code == 200
    assert any(c["id"] == new_course["id"] for c in resp.json())


def test_enroll_requires_admin(client, new_course, new_user, user_headers):
    resp = client.post(
        f"/courses/{new_course['id']}/enroll",
        json={"user_id": new_user["id"]},
        headers=user_headers,
    )
    assert resp.status_code == 403
