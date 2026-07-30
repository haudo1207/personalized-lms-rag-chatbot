def test_create_and_list_user(client, unique_suffix):
    resp = client.post(
        "/users/",
        json={
            "full_name": "Nguyen Van Test",
            "email": f"nvt_{unique_suffix}@example.com",
            "role": "student",
            "level": "beginner",
        },
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["level"] == "beginner"

    listed = client.get("/users/")
    assert listed.status_code == 200
    assert any(u["id"] == created["id"] for u in listed.json())


def test_create_user_duplicate_email_conflicts(client, new_user):
    resp = client.post(
        "/users/",
        json={
            "full_name": "Duplicate",
            "email": new_user["email"],
            "role": "student",
            "level": "beginner",
        },
    )
    assert resp.status_code == 409


def test_update_user_level(client, new_user):
    resp = client.patch(f"/users/{new_user['id']}/level", params={"level": "advanced"})
    assert resp.status_code == 200
    assert resp.json()["level"] == "advanced"


def test_update_user_level_rejects_invalid_value(client, new_user):
    resp = client.patch(f"/users/{new_user['id']}/level", params={"level": "expert"})
    assert resp.status_code == 400


def test_update_user_level_missing_user_returns_404(client):
    resp = client.patch("/users/999999/level", params={"level": "beginner"})
    assert resp.status_code == 404
