from __future__ import annotations

import sys
from pathlib import Path

# `streamlit run app/streamlit_app.py` sets sys.path[0] to app/, not the
# project root -- add the root explicitly so `from app.* import ...` and
# `from backend.* import ...` (used in pages/settings.py) resolve regardless
# of the working directory the command was launched from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app.pages import analytics, chat, documents, home, quiz, settings
from app.ui_helpers import (
    LEVEL_LABELS,
    get_api,
    inject_global_css,
    is_admin,
)

st.set_page_config(
    page_title="AI Learning Assistant — RAG",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()


def render_login_page() -> None:
    st.markdown(
        """
        <div class="hero-container" style="max-width:440px;margin:56px auto 20px;text-align:center;">
            <div class="hero-title">🎓 AI Learning Assistant</div>
            <div class="hero-subtitle">Đăng nhập để tiếp tục</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@edu.ai")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("🔐 Đăng nhập", type="primary", width="stretch")

        st.caption(
            "🧪 Tài khoản demo — Admin: `admin@edu.ai` / `Admin@123` · "
            "Student: `student@edu.ai` / `Student@123`"
        )
        # Deliberately no Backend API URL field here: this is a pre-auth
        # screen, so letting anyone repoint it would let a fake backend
        # harvest login credentials. The URL is fixed via RAG_API_URL / config
        # at deploy time (see app/ui_helpers.py DEFAULT_API_URL).

        if submitted:
            if not email.strip() or not password:
                st.warning("Nhập đầy đủ email và mật khẩu.")
            else:
                ok, payload, code = get_api().login(email.strip(), password)
                if ok and isinstance(payload, dict):
                    st.session_state.access_token = payload.get("access_token")
                    st.session_state.current_user = payload.get("user")
                    st.rerun()
                else:
                    detail = payload.get("detail") if isinstance(payload, dict) else payload
                    st.error(f"❌ Đăng nhập thất bại: {detail}")


if not st.session_state.get("access_token"):
    render_login_page()
    st.stop()

current_user = st.session_state.current_user

with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/chatbot.png", width=56)
    st.markdown("**AI Learning Assistant**")
    st.caption("RAG · Cá nhân hóa học tập")
    st.markdown("---")

    role_label = "🛡️ Admin" if is_admin() else "🎓 Student"
    course = st.session_state.get("selected_course")
    st.markdown(
        f"""
        <div class="user-card">
            <div class="user-card-name">{current_user['full_name']}</div>
            <div class="user-card-meta">{role_label} · 📈 {LEVEL_LABELS.get(current_user['level'], current_user['level'])}</div>
            <div class="user-card-meta">📘 Môn học: {course['course_name'] if course else '(chưa chọn)'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚪 Đăng xuất", width="stretch"):
        for key in (
            "access_token", "current_user", "chat_threads", "chat_hydrated_keys",
            "dashboard_key", "selected_course",
        ):
            st.session_state.pop(key, None)
        st.rerun()

    health_ok, _, _ = get_api().health()
    if not health_ok:
        # Only surface backend status when something's actually wrong --
        # a permanent "Connected" caption is implementation detail noise
        # a student has no use for.
        st.error("🔴 Không kết nối được máy chủ.")


pages = {
    "Trang chủ": st.Page(home.render, title="Trang chủ", icon="🏠", url_path="home", default=True),
    "Chat AI": st.Page(chat.render, title="Chat AI", icon="💬", url_path="chat"),
    "Tài liệu": st.Page(documents.render, title="Tài liệu", icon="📁", url_path="documents"),
    "Quiz": st.Page(quiz.render, title="Quiz", icon="📝", url_path="quiz"),
    "Phân tích học tập": st.Page(analytics.render, title="Phân tích học tập", icon="📈", url_path="analytics"),
    "Cài đặt": st.Page(settings.render, title="Cài đặt", icon="⚙️", url_path="settings"),
}
# Registered so ui_helpers.switch_to() can call st.switch_page() from inside
# any page (e.g. "Vào môn học" on Trang chủ, "Tạo Quiz" on Chat AI).
st.session_state["_pages"] = pages

pg = st.navigation(list(pages.values()))
pg.run()
