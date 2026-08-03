def test_create_course_by_any_authenticated_student(client, unique_suffix, user_headers, new_user):
    resp = client.post(
        "/courses/",
        json={
            "course_code": f"CS{unique_suffix}",
            "course_name": "Co so du lieu",
            "description": "Mon hoc CSDL",
        },
        headers=user_headers,
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["owner_id"] == new_user["id"]

    mine = client.get("/courses/mine", headers=user_headers)
    assert mine.status_code == 200
    assert any(c["id"] == created["id"] for c in mine.json())


def test_create_course_duplicate_code_conflicts(client, new_course, user_headers):
    resp = client.post(
        "/courses/",
        json={
            "course_code": new_course["course_code"],
            "course_name": "Another name",
        },
        headers=user_headers,
    )
    assert resp.status_code == 409


def test_create_course_requires_auth(client, unique_suffix):
    resp = client.post(
        "/courses/",
        json={"course_code": f"NOAUTH{unique_suffix}", "course_name": "Should fail"},
    )
    assert resp.status_code == 401


def test_mine_does_not_show_other_students_courses(client, new_course, second_user_headers):
    resp = client.get("/courses/mine", headers=second_user_headers)
    assert resp.status_code == 200
    assert not any(c["id"] == new_course["id"] for c in resp.json())


def test_mine_shows_own_course(client, new_course, user_headers):
    resp = client.get("/courses/mine", headers=user_headers)
    assert resp.status_code == 200
    assert any(c["id"] == new_course["id"] for c in resp.json())


def test_mine_is_filtered_by_ownership_for_admin_too(client, new_course, admin_headers):
    # Ownership model applies uniformly -- admin's /mine only shows courses
    # admin itself owns, not every course in the system (that's /courses/).
    resp = client.get("/courses/mine", headers=admin_headers)
    assert resp.status_code == 200
    assert not any(c["id"] == new_course["id"] for c in resp.json())


def test_admin_list_endpoint_requires_admin(client, new_course, user_headers):
    resp = client.get("/courses/", headers=user_headers)
    assert resp.status_code == 403


def test_admin_list_endpoint_shows_all_courses(client, new_course, admin_headers):
    resp = client.get("/courses/", headers=admin_headers)
    assert resp.status_code == 200
    assert any(c["id"] == new_course["id"] for c in resp.json())


def test_update_course_by_owner_renames_fields(client, new_course, user_headers):
    resp = client.patch(
        f"/courses/{new_course['id']}",
        json={"course_name": "Renamed course", "description": "New description"},
        headers=user_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["course_name"] == "Renamed course"
    assert body["description"] == "New description"
    assert body["course_code"] == new_course["course_code"]  # code stays immutable


def test_update_course_by_admin_is_allowed(client, new_course, admin_headers):
    resp = client.patch(
        f"/courses/{new_course['id']}", json={"course_name": "Admin renamed"}, headers=admin_headers
    )
    assert resp.status_code == 200


def test_update_course_forbidden_for_non_owner(client, new_course, second_user_headers):
    resp = client.patch(
        f"/courses/{new_course['id']}",
        json={"course_name": "Should fail"},
        headers=second_user_headers,
    )
    assert resp.status_code == 403


def test_update_course_missing_returns_404(client, admin_headers):
    resp = client.patch("/courses/999999", json={"course_name": "Nope"}, headers=admin_headers)
    assert resp.status_code == 404


def test_delete_course_forbidden_for_non_owner(client, new_course, second_user_headers):
    resp = client.delete(f"/courses/{new_course['id']}", headers=second_user_headers)
    assert resp.status_code == 403


def test_delete_course_missing_returns_404(client, admin_headers):
    resp = client.delete("/courses/999999", headers=admin_headers)
    assert resp.status_code == 404


def test_delete_course_by_owner_is_permanent_and_cascades(client, new_user, new_course, user_headers):
    from backend.services.vector_store import search_chunks

    upload = client.post(
        "/documents/upload",
        data={"course_id": new_course["id"], "user_id": new_user["id"]},
        files={"file": ("notes.txt", b"Khoa chinh la thuoc tinh dinh danh duy nhat.", "text/plain")},
        headers=user_headers,
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["document_id"]
    assert search_chunks("Khoa chinh", course_id=new_course["id"], top_k=5)

    resp = client.delete(f"/courses/{new_course['id']}", headers=user_headers)
    assert resp.status_code == 200

    mine = client.get("/courses/mine", headers=user_headers)
    assert not any(c["id"] == new_course["id"] for c in mine.json())

    documents = client.get("/documents/", headers=user_headers)
    assert not any(d["id"] == document_id for d in documents.json())
    assert not search_chunks("Khoa chinh", course_id=new_course["id"], top_k=5)
