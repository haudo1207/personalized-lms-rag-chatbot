def test_create_and_list_course(client, unique_suffix):
    resp = client.post(
        "/courses/",
        json={
            "course_code": f"CS{unique_suffix}",
            "course_name": "Co so du lieu",
            "description": "Mon hoc CSDL",
        },
    )
    assert resp.status_code == 201
    created = resp.json()

    listed = client.get("/courses/")
    assert listed.status_code == 200
    assert any(c["id"] == created["id"] for c in listed.json())


def test_create_course_duplicate_code_conflicts(client, new_course):
    resp = client.post(
        "/courses/",
        json={
            "course_code": new_course["course_code"],
            "course_name": "Another name",
        },
    )
    assert resp.status_code == 409
