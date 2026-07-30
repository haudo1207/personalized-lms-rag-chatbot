"""One-time migration + seed for authentication.

SQLite + Base.metadata.create_all() only creates tables that don't exist yet -- it never
ALTERs an existing table to add a new column. Since `users` already has real rows in
app.db, adding `password_hash` to the SQLAlchemy model alone would not add the column to
the actual database file, and every query touching it would fail with
"no such column: users.password_hash". This script does the one-off ALTER TABLE, then lets
create_all() add the brand-new `user_courses` table normally, then seeds the two demo
accounts (admin@edu.ai / student@edu.ai) and enrolls the student in an existing course so
the app isn't empty on first login.

Safe to re-run: every step checks current state first.

Usage:
    python scripts/seed_auth.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from sqlalchemy import text  # noqa: E402

from backend.database import Base, SessionLocal, engine  # noqa: E402
from backend.models.chat_history import ChatHistory  # noqa: E402
from backend.models.course import Course  # noqa: E402
from backend.models.document import Document  # noqa: E402
from backend.models.quiz_result import QuizResult  # noqa: E402
from backend.models.recommendation_history import RecommendationHistory  # noqa: E402
from backend.models.user import User  # noqa: E402
from backend.models.user_course import UserCourse  # noqa: E402
from backend.models.user_profile import UserProfile  # noqa: E402
from backend.models.weak_topic import WeakTopic  # noqa: E402
from backend.services.auth_service import hash_password  # noqa: E402

ADMIN_EMAIL = "admin@edu.ai"
ADMIN_PASSWORD = "Admin@123"
STUDENT_EMAIL = "student@edu.ai"
STUDENT_PASSWORD = "Student@123"


def ensure_password_hash_column() -> None:
    with engine.connect() as conn:
        columns = [row[1] for row in conn.execute(text("PRAGMA table_info(users)"))]
        if "password_hash" in columns:
            print("[skip] users.password_hash already exists.")
            return
        conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
        conn.commit()
        print("[ok] Added users.password_hash column.")


def ensure_new_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("[ok] Base.metadata.create_all() applied (creates user_courses if missing).")


def seed_accounts() -> None:
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if admin:
            admin.password_hash = hash_password(ADMIN_PASSWORD)
            admin.role = "admin"
            print(f"[ok] Updated existing account: {ADMIN_EMAIL}")
        else:
            admin = User(
                full_name="Quản trị viên",
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role="admin",
                level="advanced",
            )
            db.add(admin)
            print(f"[ok] Created admin account: {ADMIN_EMAIL}")

        student = db.query(User).filter(User.email == STUDENT_EMAIL).first()
        if student:
            student.password_hash = hash_password(STUDENT_PASSWORD)
            student.role = "student"
            print(f"[ok] Updated existing account: {STUDENT_EMAIL}")
        else:
            student = User(
                full_name="Sinh viên Demo",
                email=STUDENT_EMAIL,
                password_hash=hash_password(STUDENT_PASSWORD),
                role="student",
                level="beginner",
            )
            db.add(student)
            print(f"[ok] Created student account: {STUDENT_EMAIL}")

        db.commit()
        db.refresh(student)

        first_course = db.query(Course).order_by(Course.id).first()
        if first_course:
            enrolled = (
                db.query(UserCourse)
                .filter(UserCourse.user_id == student.id, UserCourse.course_id == first_course.id)
                .first()
            )
            if not enrolled:
                db.add(UserCourse(user_id=student.id, course_id=first_course.id))
                db.commit()
                print(f"[ok] Enrolled {STUDENT_EMAIL} in course '{first_course.course_name}'.")
            else:
                print(f"[skip] {STUDENT_EMAIL} already enrolled in '{first_course.course_name}'.")
        else:
            print("[warn] No course exists yet -- nothing to enroll the demo student in.")
    finally:
        db.close()


def main() -> None:
    ensure_password_hash_column()
    ensure_new_tables()
    seed_accounts()
    print("\n--- Demo accounts ---")
    print(f"Admin:   {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"Student: {STUDENT_EMAIL} / {STUDENT_PASSWORD}")


if __name__ == "__main__":
    main()
