"""Course-aware topic taxonomy (backend/services/topic_taxonomy.py).

Taxonomy generation itself is exercised indirectly by every test that uploads
a document (see conftest.py's autouse _mock_topic_taxonomy_llm) -- these tests
check the resulting behavior directly: one-time generation, idempotency, and
that classification actually uses it (vs. the old hardcoded keyword list it
replaced).
"""

from backend.database import SessionLocal
from backend.models.course_topic import CourseTopic
from backend.services.topic_taxonomy import classify_topic, ensure_taxonomy_for_course


def test_upload_generates_taxonomy_once(client, new_user, new_course, user_headers, uploaded_document):
    # The tiny sample document (conftest.SAMPLE_DOCUMENT_TEXT) produces very
    # few chunks -> very few clusters, so only a prefix of the mocked LLM's
    # 5 labels actually gets stored (see topic_taxonomy._extract_labels'
    # expected_count truncation) -- assert a non-empty, ordered subset
    # rather than the full fake label set.
    db = SessionLocal()
    try:
        topics = db.query(CourseTopic).filter(CourseTopic.course_id == new_course["id"]).all()
        labels = {t.label for t in topics}
        assert labels, "expected at least one topic label"
        assert labels <= {"Khoa chinh", "Khoa ngoai", "SQL JOIN", "Chuan hoa CSDL", "ERD"}
        assert "Khoa chinh" in labels  # always the first label, survives any truncation
    finally:
        db.close()


def test_ensure_taxonomy_is_idempotent(client, new_user, new_course, user_headers, uploaded_document):
    db = SessionLocal()
    try:
        before = db.query(CourseTopic).filter(CourseTopic.course_id == new_course["id"]).count()
        ensure_taxonomy_for_course(new_course["id"], db)  # course already has a taxonomy -- must no-op
        after = db.query(CourseTopic).filter(CourseTopic.course_id == new_course["id"]).count()
        assert before == after > 0
    finally:
        db.close()


def test_classify_topic_matches_own_course_taxonomy(client, new_user, new_course, user_headers, uploaded_document):
    db = SessionLocal()
    try:
        topic = classify_topic("Khoa chinh la gi?", new_course["id"], db)
        assert topic == "Khoa chinh"
    finally:
        db.close()


def test_classify_topic_falls_back_without_taxonomy(client, new_course):
    # new_course here has no uploaded_document -> no chunks -> no taxonomy generated.
    db = SessionLocal()
    try:
        topic = classify_topic("Cau hoi bat ky", new_course["id"], db)
        assert topic == "Khác"
    finally:
        db.close()
