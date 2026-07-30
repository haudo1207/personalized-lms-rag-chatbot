"""Shared pytest fixtures.

Points the app at a throwaway SQLite file + ChromaDB directory (via env vars,
read by backend.config.Settings) so tests never touch the developer's real
app.db / vector_store/. The env vars must be set before backend.* is imported
for the first time, since backend.database and backend.services.vector_store
build their engine/client at import time.
"""

from __future__ import annotations

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

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture()
def new_user(client: TestClient, unique_suffix: str) -> dict:
    resp = client.post(
        "/users/",
        json={
            "full_name": f"Test User {unique_suffix}",
            "email": f"test_{unique_suffix}@example.com",
            "role": "student",
            "level": "beginner",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def new_course(client: TestClient, unique_suffix: str) -> dict:
    resp = client.post(
        "/courses/",
        json={
            "course_code": f"TST{unique_suffix}",
            "course_name": f"Test Course {unique_suffix}",
            "description": "Course created for automated tests.",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


SAMPLE_DOCUMENT_TEXT = (
    "Khoa chinh la thuoc tinh hoac tap thuoc tinh dung de xac dinh duy nhat "
    "moi ban ghi trong mot bang co so du lieu quan he. Khoa ngoai dung de "
    "lien ket du lieu giua cac bang va tham chieu den khoa chinh cua bang khac."
).encode("utf-8")


@pytest.fixture()
def uploaded_document(client: TestClient, new_user: dict, new_course: dict) -> dict:
    resp = client.post(
        "/documents/upload",
        data={"course_id": new_course["id"], "user_id": new_user["id"]},
        files={"file": ("notes.txt", SAMPLE_DOCUMENT_TEXT, "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
