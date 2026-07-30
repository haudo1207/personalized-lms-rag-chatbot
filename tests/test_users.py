from tests.conftest import TEST_PASSWORD


def test_create_and_list_user(client, unique_suffix, admin_headers):
    resp = client.post(
        "/users/",
        json={
            "full_name": "Nguyen Van Test",
            "email": f"nvt_{unique_suffix}@example.com",
            "password": TEST_PASSWORD,
            "role": "student",
            "level": "beginner",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["level"] == "beginner"
    assert "password" not in created and "password_hash" not in created

    listed = client.get("/users/", headers=admin_headers)
    assert listed.status_code == 200
    assert any(u["id"] == created["id"] for u in listed.json())


def test_create_user_duplicate_email_conflicts(client, new_user, admin_headers):
    resp = client.post(
        "/users/",
        json={
            "full_name": "Duplicate",
            "email": new_user["email"],
            "password": TEST_PASSWORD,
            "role": "student",
            "level": "beginner",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_create_user_requires_admin(client, unique_suffix, user_headers):
    resp = client.post(
        "/users/",
        json={
            "full_name": "Should Fail",
            "email": f"nope_{unique_suffix}@example.com",
            "password": TEST_PASSWORD,
            "role": "student",
            "level": "beginner",
        },
        headers=user_headers,
    )
    assert resp.status_code == 403


def test_create_user_without_token_is_unauthorized(client, unique_suffix):
    resp = client.post(
        "/users/",
        json={
            "full_name": "Anonymous",
            "email": f"anon_{unique_suffix}@example.com",
            "password": TEST_PASSWORD,
        },
    )
    assert resp.status_code == 401


def test_update_own_level(client, new_user, user_headers):
    resp = client.patch(
        f"/users/{new_user['id']}/level", params={"level": "advanced"}, headers=user_headers
    )
    assert resp.status_code == 200
    assert resp.json()["level"] == "advanced"


def test_update_level_rejects_invalid_value(client, new_user, user_headers):
    resp = client.patch(
        f"/users/{new_user['id']}/level", params={"level": "expert"}, headers=user_headers
    )
    assert resp.status_code == 400


def test_update_level_forbidden_for_other_user(client, new_user, unique_suffix, admin_headers, user_headers):
    other = client.post(
        "/users/",
        json={
            "full_name": "Other User",
            "email": f"other_{unique_suffix}@example.com",
            "password": TEST_PASSWORD,
            "role": "student",
            "level": "beginner",
        },
        headers=admin_headers,
    ).json()

    resp = client.patch(f"/users/{other['id']}/level", params={"level": "advanced"}, headers=user_headers)
    assert resp.status_code == 403


def test_update_level_missing_user_returns_404(client, admin_headers):
    resp = client.patch("/users/999999/level", params={"level": "beginner"}, headers=admin_headers)
    assert resp.status_code == 404
