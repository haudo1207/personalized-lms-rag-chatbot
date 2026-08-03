from tests.conftest import TEST_PASSWORD


def test_login_success_returns_token_and_user(client, new_user):
    resp = client.post("/auth/login", json={"email": new_user["email"], "password": TEST_PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["id"] == new_user["id"]


def test_login_wrong_password_is_unauthorized(client, new_user):
    resp = client.post("/auth/login", json={"email": new_user["email"], "password": "WrongPass@123"})
    assert resp.status_code == 401


def test_login_unknown_email_is_unauthorized(client):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401


def test_change_password_success_then_login_with_new_password(client, new_user, user_headers):
    resp = client.post(
        "/auth/change-password",
        json={"current_password": TEST_PASSWORD, "new_password": "NewPass@456"},
        headers=user_headers,
    )
    assert resp.status_code == 200

    old_login = client.post("/auth/login", json={"email": new_user["email"], "password": TEST_PASSWORD})
    assert old_login.status_code == 401

    new_login = client.post("/auth/login", json={"email": new_user["email"], "password": "NewPass@456"})
    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password(client, new_user, user_headers):
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "NotTheRealPassword", "new_password": "NewPass@456"},
        headers=user_headers,
    )
    assert resp.status_code == 401


def test_change_password_rejects_too_short_new_password(client, new_user, user_headers):
    resp = client.post(
        "/auth/change-password",
        json={"current_password": TEST_PASSWORD, "new_password": "short"},
        headers=user_headers,
    )
    assert resp.status_code == 400


def test_change_password_requires_auth(client):
    resp = client.post(
        "/auth/change-password",
        json={"current_password": "x", "new_password": "NewPass@456"},
    )
    assert resp.status_code == 401
