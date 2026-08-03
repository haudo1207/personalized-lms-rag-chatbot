"""Shared pytest fixtures.

Points the app at a throwaway SQLite file + ChromaDB directory (via env vars,
read by backend.config.Settings) so tests never touch the developer's real
app.db / vector_store/. The env vars must be set before backend.* is imported
for the first time, since backend.database and backend.services.vector_store
build their engine/client at import time.

Auth note: every user/course-scoped endpoint now requires a Bearer token (see
backend/security_deps.py). Creating users is admin-only; creating courses is
NOT (ownership model -- any authenticated user owns the courses they create).
Since a fresh test database has no admin yet, `_admin_bootstrap` creates one
directly via the DB session (bypassing the API, which is exactly the
chicken-and-egg problem an admin-only /users/ endpoint has on a brand new
system) and logs in through the real /auth/login endpoint to get a genuine
JWT for the rest of the fixtures to use.

Course access note: a course belongs to whoever created it (`owner_id`).
`new_course` is created by `user_headers` (the primary test student), so it
is automatically accessible to that student -- there is no separate
enrollment step anymore. `second_user_headers` is a distinct student who does
NOT own `new_course`, for testing the ownership boundary (403s).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))
os.chdir(_PROJECT_ROOT)

_TEST_DIR = Path(tempfile.mkdtemp(prefix="rag_test_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DIR / 'test_app.db').as_posix()}"
os.environ["VECTOR_DB_PATH"] = str(_TEST_DIR / "vector_store")
os.environ["RAW_DIR"] = str(_TEST_DIR / "data_raw")
os.environ["PROCESSED_DIR"] = str(_TEST_DIR / "data_processed")
os.environ["JWT_SECRET"] = "test-secret-not-for-production"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database import SessionLocal  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models.user import User  # noqa: E402
from backend.services.auth_service import hash_password  # noqa: E402

TEST_PASSWORD = "TestPass@123"
ADMIN_EMAIL = "test_admin@example.com"

FAKE_TAXONOMY_JSON = json.dumps(["Khoa chinh", "Khoa ngoai", "SQL JOIN", "Chuan hoa CSDL", "ERD"])


@pytest.fixture(autouse=True)
def _mock_topic_taxonomy_llm(monkeypatch):
    """Document upload now triggers one-time per-course topic-taxonomy
    generation (backend/services/topic_taxonomy.py), which calls the LLM.
    Every test that uploads a document would otherwise make a real Gemini
    call -- mocked here globally, same convention as the other generate_answer
    monkeypatches in individual tests (mock the name bound in the *consuming*
    module, not llm_service itself)."""
    monkeypatch.setattr("backend.services.topic_taxonomy.generate_answer", lambda prompt: FAKE_TAXONOMY_JSON)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="session", autouse=True)
def _admin_bootstrap():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not existing:
            db.add(
                User(
                    full_name="Test Admin",
                    email=ADMIN_EMAIL,
                    password_hash=hash_password(TEST_PASSWORD),
                    role="admin",
                    level="advanced",
                )
            )
            db.commit()
    finally:
        db.close()


@pytest.fixture()
def admin_headers(client: TestClient) -> dict:
    resp = client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": TEST_PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def new_user(client: TestClient, unique_suffix: str, admin_headers: dict) -> dict:
    resp = client.post(
        "/users/",
        json={
            "full_name": f"Test User {unique_suffix}",
            "email": f"test_{unique_suffix}@example.com",
            "password": TEST_PASSWORD,
            "role": "student",
            "level": "beginner",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def user_headers(client: TestClient, new_user: dict) -> dict:
    resp = client.post("/auth/login", json={"email": new_user["email"], "password": TEST_PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def second_user(client: TestClient, unique_suffix: str, admin_headers: dict) -> dict:
    resp = client.post(
        "/users/",
        json={
            "full_name": f"Second User {unique_suffix}",
            "email": f"second_{unique_suffix}@example.com",
            "password": TEST_PASSWORD,
            "role": "student",
            "level": "beginner",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def second_user_headers(client: TestClient, second_user: dict) -> dict:
    resp = client.post("/auth/login", json={"email": second_user["email"], "password": TEST_PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def new_course(client: TestClient, unique_suffix: str, user_headers: dict) -> dict:
    """Owned by `user_headers` (the primary test student) -- ownership model,
    so no separate enrollment step is needed for that student to use it."""
    resp = client.post(
        "/courses/",
        json={
            "course_code": f"TST{unique_suffix}",
            "course_name": f"Test Course {unique_suffix}",
            "description": "Course created for automated tests.",
        },
        headers=user_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


SAMPLE_DOCUMENT_TEXT = (
    "Khoa chinh la thuoc tinh hoac tap thuoc tinh dung de xac dinh duy nhat "
    "moi ban ghi trong mot bang co so du lieu quan he. Khoa ngoai dung de "
    "lien ket du lieu giua cac bang va tham chieu den khoa chinh cua bang khac."
).encode("utf-8")


@pytest.fixture()
def uploaded_document(
    client: TestClient,
    new_user: dict,
    new_course: dict,
    user_headers: dict,
) -> dict:
    resp = client.post(
        "/documents/upload",
        data={"course_id": new_course["id"], "user_id": new_user["id"]},
        files={"file": ("notes.txt", SAMPLE_DOCUMENT_TEXT, "text/plain")},
        headers=user_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
