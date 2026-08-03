"""Thin HTTP client for the FastAPI backend.

Every function here does exactly one thing: call one backend endpoint and
return its (ok, payload, status_code) result. No Streamlit imports, no
session_state access -- this module is plain Python so it can be unit
tested and reused independently of the UI layer.
"""

from __future__ import annotations

from typing import Any

import requests

REQUEST_TIMEOUT = 120


class ApiClient:
    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def auth_headers(self) -> dict[str, str]:
        """Public accessor for callers that need to make a raw request outside
        this client (e.g. Streamlit's download_button needs bytes upfront)."""
        return self._headers()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: int = REQUEST_TIMEOUT,
    ) -> tuple[bool, dict[str, Any] | list[Any] | str, int | None]:
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                params=params,
                data=data,
                json=json_body,
                files=files,
                headers=self._headers(),
                timeout=timeout,
            )
        except requests.RequestException as exc:
            return False, f"Không kết nối được backend API: {exc}", None

        try:
            payload: dict[str, Any] | list[Any] | str = response.json()
        except ValueError:
            payload = response.text

        return response.ok, payload, response.status_code

    # -- auth ---------------------------------------------------------------
    def login(self, email: str, password: str):
        return self._request(
            "POST", "/auth/login", json_body={"email": email, "password": password}, timeout=15
        )

    def change_password(self, current_password: str, new_password: str):
        return self._request(
            "POST",
            "/auth/change-password",
            json_body={"current_password": current_password, "new_password": new_password},
        )

    def health(self):
        return self._request("GET", "/health", timeout=5)

    # -- users ----------------------------------------------------------------
    def update_level(self, user_id: int, level: str):
        return self._request("PATCH", f"/users/{user_id}/level", params={"level": level})

    def list_users(self):
        return self._request("GET", "/users/", timeout=15)

    # -- courses --------------------------------------------------------------
    def list_my_courses(self):
        return self._request("GET", "/courses/mine", timeout=15)

    def create_course(self, course_code: str, course_name: str, description: str | None):
        return self._request(
            "POST",
            "/courses/",
            json_body={"course_code": course_code, "course_name": course_name, "description": description},
        )

    def update_course(self, course_id: int, course_name: str | None = None, description: str | None = None):
        body: dict[str, Any] = {}
        if course_name is not None:
            body["course_name"] = course_name
        if description is not None:
            body["description"] = description
        return self._request("PATCH", f"/courses/{course_id}", json_body=body)

    def delete_course(self, course_id: int):
        """Permanent: cascades to the course's documents, chat history and
        quiz data server-side. There is no archive/undo in this model."""
        return self._request("DELETE", f"/courses/{course_id}")

    # -- documents --------------------------------------------------------------
    def list_documents(self):
        return self._request("GET", "/documents/", timeout=15)

    def get_suggested_questions(self, course_id: int):
        return self._request(
            "GET", "/documents/suggested-questions", params={"course_id": course_id}, timeout=30
        )

    def upload_document(self, course_id: int, user_id: int, filename: str, content: bytes, content_type: str):
        return self._request(
            "POST",
            "/documents/upload",
            data={"course_id": course_id, "user_id": user_id},
            files={"file": (filename, content, content_type or "application/octet-stream")},
        )

    def retry_index(self, document_id: int):
        return self._request("POST", f"/documents/{document_id}/index")

    def rename_document(self, document_id: int, file_name: str):
        return self._request("PATCH", f"/documents/{document_id}", json_body={"file_name": file_name})

    def delete_document(self, document_id: int):
        return self._request("DELETE", f"/documents/{document_id}")

    def download_document_url(self, document_id: int) -> str:
        """Returns the raw URL; Streamlit's download button fetches it directly."""
        return f"{self.base_url}/documents/{document_id}/download"

    # -- chat --------------------------------------------------------------
    def send_chat(
        self,
        user_id: int,
        course_id: int,
        question: str,
        top_k: int,
        document_ids: list[int] | None,
    ):
        return self._request(
            "POST",
            "/chat/",
            json_body={
                "user_id": user_id,
                "course_id": course_id,
                "question": question,
                "top_k": top_k,
                "document_ids": document_ids,
            },
        )

    def get_chat_history(self, user_id: int):
        return self._request("GET", f"/chat/history/{user_id}", timeout=15)

    def get_profile(self, user_id: int, course_id: int):
        return self._request("GET", f"/chat/profile/{user_id}/{course_id}", timeout=15)

    def get_weak_topics(self, user_id: int, course_id: int):
        return self._request("GET", f"/chat/weak-topics/{user_id}/{course_id}", timeout=15)

    def set_chat_feedback(self, chat_id: int, feedback: str | None):
        return self._request("PATCH", f"/chat/{chat_id}/feedback", json_body={"feedback": feedback})

    def clear_chat_history(self, user_id: int, course_id: int):
        return self._request("DELETE", f"/chat/history/{user_id}/{course_id}")

    # -- retrieval (search-only, no LLM) --------------------------------------
    def search_chunks(self, question: str, course_id: int, top_k: int = 5):
        return self._request(
            "POST",
            "/retrieval/search",
            json_body={"question": question, "course_id": course_id, "top_k": top_k},
        )

    # -- quiz --------------------------------------------------------------
    def generate_quiz(self, user_id: int, course_id: int, topic: str, num_questions: int, difficulty: str):
        return self._request(
            "POST",
            "/quiz/generate",
            json_body={
                "user_id": user_id,
                "course_id": course_id,
                "topic": topic,
                "num_questions": num_questions,
                "difficulty": difficulty,
            },
            timeout=REQUEST_TIMEOUT,
        )

    def submit_quiz(self, user_id: int, course_id: int, quiz_session_id: int, answers: list[str | None]):
        return self._request(
            "POST",
            "/quiz/submit",
            json_body={
                "user_id": user_id,
                "course_id": course_id,
                "quiz_session_id": quiz_session_id,
                "answers": answers,
            },
            timeout=30,
        )

    def get_quiz_results(self, user_id: int, course_id: int | None = None):
        params = {"course_id": course_id} if course_id is not None else None
        return self._request("GET", f"/quiz/results/{user_id}", params=params, timeout=15)

    # -- dashboard --------------------------------------------------------------
    def get_student_dashboard(self, user_id: int, course_id: int):
        return self._request(
            "GET", f"/dashboard/student/{user_id}", params={"course_id": course_id}, timeout=30
        )
