"""Render each workspace page in isolation (session_state pre-seeded with a
logged-in admin + selected course) to catch import/runtime errors without
having to click through full navigation. Requires the real backend running
on http://127.0.0.1:8000 with the admin@edu.ai demo account and >=1 course.
"""

import sys

from streamlit.testing.v1 import AppTest

sys.path.insert(0, ".")


def _seed_and_run(page_module_name: str) -> tuple[bool, list[str]]:
    # AppTest.from_file needs an actual script path; generate a tiny one that
    # seeds session_state (login + pick first course) then calls the target
    # page's render() -- simpler than trying to inject state into an
    # AppTest instance from outside.
    src = f"""
import sys
sys.path.insert(0, ".")
import streamlit as st
from app.api_client import ApiClient

api = ApiClient("http://127.0.0.1:8000")
ok, payload, _ = api.login("admin@edu.ai", "Admin@123")
if not ok:
    raise RuntimeError(f"login failed: {{payload}}")
st.session_state["access_token"] = payload["access_token"]
st.session_state["current_user"] = payload["user"]

api2 = ApiClient("http://127.0.0.1:8000", st.session_state["access_token"])
ok2, courses, _ = api2.list_my_courses()
if not (ok2 and courses):
    raise RuntimeError(f"no courses available: {{courses}}")
st.session_state["selected_course"] = courses[0]
st.session_state["api_url"] = "http://127.0.0.1:8000"

from app.pages import {page_module_name}
{page_module_name}.render()
"""
    path = f"scratch_page_{page_module_name}.py"
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)

    at = AppTest.from_file(path, default_timeout=30)
    at.run()
    errors = [repr(exc.value) for exc in at.exception]
    return (len(errors) == 0), errors


def main() -> None:
    for page_name in ["settings", "analytics", "documents", "quiz", "chat"]:
        ok, errors = _seed_and_run(page_name)
        status = "OK" if ok else "FAILED"
        print(f"[{page_name}] {status}")
        for e in errors:
            print(f"    {e}")


if __name__ == "__main__":
    main()
