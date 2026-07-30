from __future__ import annotations

from typing import Any
import json

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit_option_menu import option_menu

DEFAULT_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 120

LEVEL_LABELS = {"beginner": "Mới bắt đầu", "intermediate": "Trung bình", "advanced": "Nâng cao"}
DIFFICULTY_LABELS = {"easy": "Dễ", "medium": "Trung bình", "hard": "Khó"}

PAGE_NAMES = ["Dashboard", "Chat", "Tài liệu", "Kho tri thức", "Quiz", "Phân tích học tập", "Cài đặt"]
PAGE_ICONS = ["speedometer2", "chat-dots", "folder2-open", "database", "pencil-square", "graph-up-arrow", "gear"]

PRIMARY = "#2563EB"
SECONDARY = "#3B82F6"

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Learning Assistant — RAG",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    [data-testid="stAppViewContainer"] > .main {{
        background-color: #F8FAFC;
    }}
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }}

    .hero-container {{
        background: linear-gradient(135deg, {PRIMARY} 0%, {SECONDARY} 100%);
        padding: 1.8rem 2.2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.18);
    }}

    .hero-title {{
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        letter-spacing: -0.02em;
    }}

    .hero-subtitle {{
        font-size: 1.02rem;
        opacity: 0.92;
        font-weight: 400;
    }}

    .stButton > button {{
        border-radius: 12px;
        font-weight: 500;
        transition: all 0.15s ease;
        border-color: #E2E8F0;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        border-color: {PRIMARY};
        color: {PRIMARY};
    }}
    .stButton > button[kind="primary"] {{
        background-color: {PRIMARY};
        border-color: {PRIMARY};
    }}
    .stButton > button[kind="primary"]:hover {{
        background-color: #1D4ED8;
        color: white;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 16px !important;
    }}
    div[data-testid="stMetric"] {{
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 0.9rem 1.1rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }}

    .status-badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        line-height: 1.6;
    }}
    .status-badge.ok {{ background: #dcfce7; color: #15803d; }}
    .status-badge.error {{ background: #fee2e2; color: #b91c1c; }}
    .status-badge.warn {{ background: #fef3c7; color: #92400e; }}

    .user-card {{
        background: #F1F5F9;
        border-radius: 14px;
        padding: 12px 14px;
        margin-top: 8px;
    }}
    .user-card-name {{ font-weight: 700; font-size: 0.92rem; }}
    .user-card-meta {{ font-size: 0.78rem; color: #64748b; margin-top: 2px; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. HELPER FUNCTIONS & BACKEND CLIENT
# -----------------------------------------------------------------------------
def get_api_url() -> str:
    return str(st.session_state.get("api_url", DEFAULT_API_URL)).rstrip("/")


def request_json(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    timeout: int = REQUEST_TIMEOUT,
) -> tuple[bool, dict[str, Any] | list[Any] | str, int | None]:
    headers = {}
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method,
            f"{get_api_url()}{path}",
            params=params,
            data=data,
            json=json_body,
            files=files,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return False, f"Không kết nối được backend API: {exc}", None

    try:
        payload: dict[str, Any] | list[Any] | str = response.json()
    except ValueError:
        payload = response.text

    return response.ok, payload, response.status_code


def show_api_error(action: str, payload: dict[str, Any] | list[Any] | str, status_code: int | None) -> None:
    label = f"{action} thất bại"
    if status_code is not None:
        label = f"{label} (HTTP {status_code})"

    if isinstance(payload, dict) and payload.get("detail"):
        st.error(f"❌ {label}: {payload['detail']}")
    elif payload:
        st.error(f"❌ {label}: {payload}")
    else:
        st.error(f"❌ {label}")


def badge_html(text: str, kind: str = "ok") -> str:
    return f'<span class="status-badge {kind}">{text}</span>'


def load_my_courses() -> list[dict[str, Any]]:
    ok, payload, _ = request_json("GET", "/courses/mine", timeout=15)
    if ok and isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def load_documents() -> list[dict[str, Any]]:
    ok, payload, _ = request_json("GET", "/documents/", timeout=15)
    if ok and isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def parse_history_sources(raw_sources: str | None) -> list[dict[str, Any]]:
    if not raw_sources:
        return []
    try:
        parsed = json.loads(raw_sources)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [source for source in parsed if isinstance(source, dict)]
    return []


def render_source(source: dict[str, Any]) -> None:
    document_name = source.get("document_name", "Tài liệu học tập")
    page = source.get("page", "?")
    content = source.get("content", "")
    distance = source.get("distance")

    with st.container(border=True):
        st.markdown(f"📄 **{document_name}** — *Trang {page}*")
        if distance is not None:
            similarity = max(0.0, 1.0 - float(distance))
            st.progress(min(1.0, similarity), text=f"🎯 Độ tương đồng ngữ nghĩa: {similarity * 100:.1f}%")
        st.caption(f"\"{content}\"")


def ensure_chat_thread(user_id: int, course_id: int) -> str:
    """Return the session_state key for this (user, course) thread, hydrating it
    from /chat/history on first visit so switching courses doesn't lose context."""
    st.session_state.setdefault("chat_threads", {})
    st.session_state.setdefault("chat_hydrated_keys", set())
    key = f"{user_id}:{course_id}"

    if key not in st.session_state.chat_threads:
        st.session_state.chat_threads[key] = []

    if key not in st.session_state.chat_hydrated_keys:
        ok, payload, _ = request_json("GET", f"/chat/history/{user_id}", timeout=15)
        if ok and isinstance(payload, list):
            rows = [r for r in payload if isinstance(r, dict) and int(r.get("course_id", 0)) == course_id]
            rows.sort(key=lambda r: str(r.get("created_at", "")))
            for row in rows:
                st.session_state.chat_threads[key].append({"role": "user", "content": row.get("question", "")})
                st.session_state.chat_threads[key].append(
                    {
                        "role": "assistant",
                        "content": row.get("answer", ""),
                        "topic": row.get("topic"),
                        "latency": row.get("latency"),
                        "sources": parse_history_sources(row.get("sources")),
                    }
                )
        st.session_state.chat_hydrated_keys.add(key)

    return key


def render_assistant_meta(msg: dict[str, Any]) -> None:
    meta_bits = []
    if msg.get("topic"):
        meta_bits.append(f"📌 {msg['topic']}")
    if msg.get("latency"):
        meta_bits.append(f"⚡ {msg['latency']}s")
    sources = msg.get("sources") or []
    if sources:
        meta_bits.append(f"🔗 {len(sources)} nguồn (xem panel bên phải)")
    if meta_bits:
        st.caption(" · ".join(meta_bits))
    if msg.get("weak_topic"):
        st.warning(f"⚠️ Bạn đang gặp khó khăn ở chủ đề **{msg['weak_topic']}**.")


def ensure_dashboard_data(user_id: int, course_id: int, force: bool = False) -> tuple[dict, dict]:
    key = f"{user_id}:{course_id}"
    if not force and st.session_state.get("dashboard_key") == key:
        return st.session_state.get("profile") or {}, st.session_state.get("dashboard") or {}

    with st.spinner("Đang tổng hợp dữ liệu..."):
        prof_ok, prof_payload, _ = request_json("GET", f"/chat/profile/{user_id}/{course_id}", timeout=15)
        dash_ok, dash_payload, dash_code = request_json(
            "GET", f"/dashboard/student/{user_id}", params={"course_id": course_id}, timeout=30
        )
    profile = prof_payload if prof_ok and isinstance(prof_payload, dict) else {}
    dashboard = dash_payload if dash_ok and isinstance(dash_payload, dict) else {}
    st.session_state.profile = profile
    st.session_state.dashboard = dashboard
    st.session_state.dashboard_key = key
    if not dash_ok:
        show_api_error("Tải Dashboard", dash_payload, dash_code)
    return profile, dashboard


def compute_questions_per_day(user_id: int, course_id: int) -> pd.DataFrame:
    ok, payload, _ = request_json("GET", f"/chat/history/{user_id}", timeout=15)
    if not (ok and isinstance(payload, list)):
        return pd.DataFrame(columns=["date", "count"])
    rows = [r for r in payload if isinstance(r, dict) and int(r.get("course_id", 0)) == course_id]
    if not rows:
        return pd.DataFrame(columns=["date", "count"])
    dates = [str(r.get("created_at", ""))[:10] for r in rows]
    counts = pd.Series(dates).value_counts().sort_index()
    return pd.DataFrame({"date": counts.index, "count": counts.values})


def plotly_topic_bar(questions_by_topic: dict[str, int]):
    df = pd.DataFrame(list(questions_by_topic.items()), columns=["topic", "count"]).sort_values("count")
    fig = px.bar(df, x="count", y="topic", orientation="h", color_discrete_sequence=[PRIMARY])
    fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0), height=260,
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="Số lượng", yaxis_title="",
    )
    return fig


def plotly_score_line(quiz_results: list[dict[str, Any]]):
    sorted_res = sorted(quiz_results, key=lambda x: x.get("created_at", ""))
    df = pd.DataFrame(
        {
            "time": [str(r["created_at"])[:16].replace("T", " ") for r in sorted_res],
            "score": [float(r["score"]) for r in sorted_res],
            "topic": [r.get("topic", "") for r in sorted_res],
        }
    )
    fig = px.line(df, x="time", y="score", markers=True, hover_data=["topic"], color_discrete_sequence=[SECONDARY])
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0), height=260,
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="Thời gian", yaxis_title="Điểm số (%)",
    )
    return fig


def plotly_questions_per_day(df: pd.DataFrame):
    fig = px.bar(df, x="date", y="count", color_discrete_sequence=[PRIMARY])
    fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=0), height=240,
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="Ngày", yaxis_title="Số câu hỏi",
    )
    return fig


# -----------------------------------------------------------------------------
# 3. LOGIN — xác thực bắt buộc, thay cho dropdown đổi User tự do trước đây
# -----------------------------------------------------------------------------
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
            submitted = st.form_submit_button("🔐 Đăng nhập", type="primary", use_container_width=True)

        st.caption(
            "🧪 Tài khoản demo — Admin: `admin@edu.ai` / `Admin@123` · "
            "Student: `student@edu.ai` / `Student@123`"
        )
        with st.expander("⚙️ Cấu hình nâng cao (đổi Backend API URL)"):
            st.text_input("Backend API URL", value=DEFAULT_API_URL, key="api_url")

        if submitted:
            if not email.strip() or not password:
                st.warning("Nhập đầy đủ email và mật khẩu.")
            else:
                ok, payload, code = request_json(
                    "POST",
                    "/auth/login",
                    json_body={"email": email.strip(), "password": password},
                    timeout=15,
                )
                if ok and isinstance(payload, dict):
                    st.session_state.access_token = payload.get("access_token")
                    st.session_state.current_user = payload.get("user")
                    st.rerun()
                else:
                    show_api_error("Đăng nhập", payload, code)


if not st.session_state.get("access_token"):
    render_login_page()
    st.stop()

current_user: dict[str, Any] = st.session_state.current_user
is_admin = current_user.get("role") == "admin"


# -----------------------------------------------------------------------------
# 4. SIDEBAR — HỒ SƠ + CHỌN MÔN HỌC + ĐIỀU HƯỚNG
# -----------------------------------------------------------------------------
pending_page_index = st.session_state.pop("pending_page_index", None)

with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/chatbot.png", width=56)
    st.markdown("**AI Learning Assistant**")
    st.caption("RAG · Cá nhân hóa học tập")
    st.markdown("---")

    st.markdown("**📘 Môn học**")
    courses = load_my_courses()
    selected_course: dict[str, Any] | None = None
    if courses:
        course_labels = {f"{c['course_code']} — {c['course_name']}": c for c in courses}
        course_labels_list = list(course_labels.keys())
        default_course_index = 0
        pending_code = st.session_state.get("pending_select_course_code")
        if pending_code:
            for i, c in enumerate(courses):
                if c.get("course_code") == pending_code:
                    default_course_index = i
                    break
            st.session_state["pending_select_course_code"] = None
        picked_course_label = st.selectbox(
            "Chọn môn học:", course_labels_list, index=default_course_index, label_visibility="collapsed"
        )
        selected_course = course_labels[picked_course_label]
    else:
        st.info(
            "Bạn chưa được ghi danh môn học nào."
            if not is_admin
            else "Chưa có môn học nào trong hệ thống — tạo mới bên dưới."
        )

    if is_admin:
        with st.popover("➕ Tạo môn học mới", use_container_width=True):
            new_course_code = st.text_input("Mã môn học (VD: CS101)", key="new_course_code")
            new_course_name = st.text_input("Tên môn học", key="new_course_name")
            new_course_desc = st.text_area("Mô tả (tuỳ chọn)", key="new_course_desc", height=68)
            if st.button("Tạo môn học", key="btn_create_course", use_container_width=True):
                if new_course_code.strip() and new_course_name.strip():
                    ok, payload, code = request_json(
                        "POST",
                        "/courses/",
                        json_body={
                            "course_code": new_course_code.strip(),
                            "course_name": new_course_name.strip(),
                            "description": new_course_desc.strip() or None,
                        },
                    )
                    if ok and isinstance(payload, dict):
                        st.session_state["pending_select_course_code"] = payload.get("course_code")
                        st.rerun()
                    else:
                        show_api_error("Tạo môn học", payload, code)
                else:
                    st.warning("Nhập đầy đủ mã và tên môn học.")

    st.markdown("---")
    selected_page = option_menu(
        menu_title=None,
        options=PAGE_NAMES,
        icons=PAGE_ICONS,
        default_index=pending_page_index if pending_page_index is not None else 0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": PRIMARY, "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "left",
                "margin": "2px 0",
                "border-radius": "10px",
                "--hover-color": "#EFF6FF",
            },
            "nav-link-selected": {"background-color": PRIMARY, "color": "white", "font-weight": "600"},
        },
    )

    st.markdown("---")
    course_documents_count = (
        len([d for d in load_documents() if int(d.get("course_id", 0)) == int(selected_course["id"])])
        if selected_course
        else 0
    )
    role_label = "🛡️ Admin" if is_admin else "🎓 Student"
    st.markdown(
        f"""
        <div class="user-card">
            <div class="user-card-name">{current_user['full_name']}</div>
            <div class="user-card-meta">{role_label} · 📈 {LEVEL_LABELS.get(current_user['level'], current_user['level'])}</div>
            <div class="user-card-meta">📘 {len(courses)} môn học · 📁 {course_documents_count} tài liệu</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🚪 Đăng xuất", use_container_width=True):
        for key in ("access_token", "current_user", "chat_threads", "chat_hydrated_keys", "dashboard_key"):
            st.session_state.pop(key, None)
        st.rerun()

    health_ok, _, _ = request_json("GET", "/health", timeout=5)
    st.caption(("🟢 API Backend: Connected" if health_ok else "🔴 API Backend: Disconnected"))


if not selected_course:
    st.warning("👈 Bạn chưa có môn học nào để bắt đầu. Liên hệ Admin để được ghi danh.")
    st.stop()

user_id = int(current_user["id"])
course_id = int(selected_course["id"])


# -----------------------------------------------------------------------------
# 5. TRANG DASHBOARD
# -----------------------------------------------------------------------------
def render_dashboard_page() -> None:
    st.markdown(
        f"""
        <div class="hero-container">
            <div class="hero-title">👋 Chào mừng, {current_user['full_name']}!</div>
            <div class="hero-subtitle">
                Môn học hiện tại: <b>{selected_course['course_name']}</b> · Trợ lý học tập RAG sẵn sàng hỗ trợ bạn.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    documents = load_documents()
    course_documents = [d for d in documents if int(d.get("course_id", 0)) == course_id]
    profile, dashboard = ensure_dashboard_data(user_id, course_id)

    k1, k2, k3 = st.columns(3)
    k1.metric("📁 Tài liệu", len(course_documents))
    k2.metric("💬 Câu hỏi đã đặt", dashboard.get("total_questions", 0))
    avg_score = dashboard.get("average_quiz_score")
    k3.metric("🎯 Điểm Quiz trung bình", f"{avg_score}%" if avg_score is not None else "N/A")

    st.markdown("---")
    col_recent, col_actions = st.columns([2, 1], gap="large")

    with col_recent:
        st.markdown("##### 📄 Tài liệu mới nhất")
        recent_docs = sorted(course_documents, key=lambda d: str(d.get("uploaded_at", "")), reverse=True)[:3]
        if recent_docs:
            for doc in recent_docs:
                status = str(doc.get("status", "uploaded")).lower()
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"📄 **{doc.get('file_name', 'Unnamed')}**")
                    c1.caption(str(doc.get("uploaded_at", ""))[:10])
                    with c2:
                        st.markdown(
                            badge_html("🟢 Sẵn sàng", "ok") if status == "indexed" else badge_html("🔴 Lỗi", "error"),
                            unsafe_allow_html=True,
                        )
        else:
            st.info("Chưa có tài liệu nào được upload cho môn học này.")

    with col_actions:
        st.markdown("##### ⚡ Thao tác nhanh")
        if st.button("💬 Trò chuyện ngay", use_container_width=True, type="primary"):
            st.session_state["pending_page_index"] = 1
            st.rerun()
        if st.button("📤 Upload tài liệu", use_container_width=True):
            st.session_state["pending_page_index"] = 2
            st.rerun()
        if st.button("📊 Xem phân tích học tập", use_container_width=True):
            st.session_state["pending_page_index"] = 5
            st.rerun()

    weak_topics = dashboard.get("weak_topics", [])
    if weak_topics:
        st.markdown("---")
        st.markdown("##### ⚠️ Chủ đề cần cải thiện")
        for wt in weak_topics[:3]:
            if isinstance(wt, dict):
                st.warning(f"**{wt.get('topic')}** — {wt.get('reason', '')}")


# -----------------------------------------------------------------------------
# 5. TRANG CHAT — hội thoại thật + panel Ngữ cảnh tri thức
# -----------------------------------------------------------------------------
def render_chat_page() -> None:
    col_main, col_context = st.columns([7, 3], gap="large")

    with col_main:
        header_col, opts_col = st.columns([8, 2])
        with header_col:
            st.subheader(f"💬 Chat — {selected_course['course_name']}")
        with opts_col:
            with st.popover("⚙️ Tuỳ chọn", use_container_width=True):
                top_k = st.slider("Số nguồn truy xuất (Top K)", min_value=1, max_value=10, value=3)
                documents_for_filter = load_documents()
                course_docs_for_filter = [
                    d for d in documents_for_filter if int(d.get("course_id", 0)) == course_id
                ]
                doc_filter_options = {
                    f"#{d['id']} - {d['file_name']}": int(d["id"]) for d in course_docs_for_filter
                }
                selected_docs = st.multiselect(
                    "Chỉ tìm trong file:",
                    options=list(doc_filter_options.keys()),
                    default=[],
                    help="Để trống để tìm kiếm trên tất cả tài liệu của môn học.",
                )
                filter_doc_ids = [doc_filter_options[label] for label in selected_docs]

        st.caption("💡 Câu hỏi gợi ý — bấm để gửi ngay:")
        p1, p2, p3 = st.columns(3)
        preset_prompt = None
        if p1.button("🔑 Khóa chính là gì?", use_container_width=True):
            preset_prompt = "Khóa chính là gì?"
        if p2.button("🔀 INNER vs LEFT JOIN?", use_container_width=True):
            preset_prompt = "INNER JOIN khác LEFT JOIN như thế nào?"
        if p3.button("📐 Chuẩn hóa 3NF?", use_container_width=True):
            preset_prompt = "3NF giúp giải quyết phụ thuộc hàm nào?"

        thread_key = ensure_chat_thread(user_id, course_id)
        thread = st.session_state.chat_threads[thread_key]

        if thread and thread[-1]["role"] == "assistant":
            st.session_state.last_sources = thread[-1].get("sources", [])
        elif "last_sources" not in st.session_state:
            st.session_state.last_sources = []

        chat_box = st.container(height=420, border=True)
        with chat_box:
            if not thread:
                st.info("Chưa có hội thoại nào trong môn học này. Hãy đặt câu hỏi bên dưới!")
            for msg in thread:
                avatar = "🧑‍🎓" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant":
                        render_assistant_meta(msg)

        typed_prompt = st.chat_input("Nhập câu hỏi của bạn...")
        question_to_send = preset_prompt or typed_prompt

        if question_to_send:
            thread.append({"role": "user", "content": question_to_send})
            with chat_box:
                with st.chat_message("user", avatar="🧑‍🎓"):
                    st.markdown(question_to_send)
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("🔍 Đang truy xuất tài liệu & sinh câu trả lời..."):
                        ok, payload, status_code = request_json(
                            "POST",
                            "/chat/",
                            json_body={
                                "user_id": user_id,
                                "course_id": course_id,
                                "question": question_to_send,
                                "top_k": top_k,
                                "document_ids": filter_doc_ids if filter_doc_ids else None,
                            },
                        )
                    if ok and isinstance(payload, dict):
                        assistant_msg = {
                            "role": "assistant",
                            "content": payload.get("answer", ""),
                            "topic": payload.get("topic"),
                            "latency": payload.get("latency"),
                            "weak_topic": payload.get("weak_topic"),
                            "sources": payload.get("sources", []),
                        }
                        st.markdown(assistant_msg["content"])
                        render_assistant_meta(assistant_msg)
                        thread.append(assistant_msg)
                        st.session_state.last_sources = assistant_msg["sources"]
                    else:
                        detail = payload.get("detail") if isinstance(payload, dict) else payload
                        error_text = f"⚠️ Không lấy được câu trả lời: {detail}"
                        st.error(error_text)
                        thread.append({"role": "assistant", "content": error_text})
                        st.session_state.last_sources = []

    with col_context:
        st.markdown("##### 🧠 Ngữ cảnh tri thức")
        st.caption("Các đoạn tài liệu được dùng để trả lời câu hỏi gần nhất.")
        last_sources = st.session_state.get("last_sources") or []
        if last_sources:
            for source in last_sources:
                if isinstance(source, dict):
                    render_source(source)
        else:
            st.info("Chưa có câu hỏi nào được gửi trong phiên này.")


# -----------------------------------------------------------------------------
# 6. TRANG TÀI LIỆU — upload + quản lý + tìm kiếm/lọc
# -----------------------------------------------------------------------------
def render_documents_page() -> None:
    st.subheader(f"📁 Tài liệu — {selected_course['course_name']}")

    with st.container(border=True):
        st.markdown("##### 📤 Upload tài liệu mới")
        up_col1, up_col2 = st.columns([7, 3])
        with up_col1:
            upload_file = st.file_uploader(
                "Chọn file PDF, DOCX hoặc TXT:",
                type=["pdf", "docx", "txt"],
                key="doc_upload",
            )
        with up_col2:
            st.caption("File sẽ tự động được chia chunk & đánh chỉ mục — Chatbot có ngay kiến thức mới sau khi tải lên.")

        if st.button(
            "📤 Tải lên & Đánh chỉ mục",
            type="primary",
            use_container_width=True,
            disabled=upload_file is None,
        ):
            with st.spinner("Đang xử lý tài liệu (upload, chia chunk, tạo embedding)..."):
                up_ok, up_payload, up_code = request_json(
                    "POST",
                    "/documents/upload",
                    data={"course_id": course_id, "user_id": user_id},
                    files={
                        "file": (
                            upload_file.name,
                            upload_file.getvalue(),
                            upload_file.type or "application/octet-stream",
                        )
                    },
                )
            if up_ok and isinstance(up_payload, dict):
                st.success(
                    f"✅ '{upload_file.name}' đã sẵn sàng để Chatbot trả lời "
                    f"({up_payload.get('chunks', '?')} đoạn văn bản đã được đánh chỉ mục)."
                )
                st.rerun()
            else:
                show_api_error("Upload tài liệu", up_payload, up_code)

    st.markdown("---")
    st.markdown("##### 📚 Danh sách tài liệu đã upload")

    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search_text = st.text_input("🔍 Tìm theo tên file", "", placeholder="Nhập tên file để lọc...")
    with filter_col:
        status_filter = st.selectbox("Trạng thái", ["Tất cả", "Sẵn sàng", "Lỗi xử lý"])

    documents = load_documents()
    course_documents = [doc for doc in documents if int(doc.get("course_id", 0)) == course_id]

    if search_text.strip():
        needle = search_text.strip().lower()
        course_documents = [d for d in course_documents if needle in str(d.get("file_name", "")).lower()]
    if status_filter == "Sẵn sàng":
        course_documents = [d for d in course_documents if str(d.get("status", "")).lower() == "indexed"]
    elif status_filter == "Lỗi xử lý":
        course_documents = [d for d in course_documents if str(d.get("status", "")).lower() != "indexed"]

    if course_documents:
        for doc in course_documents:
            status = str(doc.get("status", "uploaded")).lower()
            with st.container(border=True):
                c1, c2, c3 = st.columns([5, 3, 2])
                with c1:
                    st.markdown(f"📄 **{doc.get('file_name', 'Unnamed')}**")
                    st.caption(f"ID #{doc.get('id')} · Ngày tải lên: {str(doc.get('uploaded_at', ''))[:10]}")
                with c2:
                    if status == "indexed":
                        st.markdown(badge_html("🟢 Sẵn sàng", "ok"), unsafe_allow_html=True)
                    else:
                        st.markdown(badge_html("🔴 Lỗi xử lý", "error"), unsafe_allow_html=True)
                        st.caption("Có thể là file ảnh/scan không có chữ.")
                with c3:
                    if status != "indexed":
                        if st.button("🔁 Thử lại", key=f"retry_{doc.get('id')}", use_container_width=True):
                            with st.spinner("Đang thử lại..."):
                                idx_ok, idx_payload, idx_code = request_json(
                                    "POST", f"/documents/{doc.get('id')}/index"
                                )
                            if idx_ok:
                                st.success("Đã xử lý xong!")
                                st.rerun()
                            else:
                                show_api_error("Thử lại", idx_payload, idx_code)
    else:
        st.info("Không có tài liệu nào khớp bộ lọc hiện tại.")


# -----------------------------------------------------------------------------
# 7. TRANG KHO TRI THỨC — thống kê + Semantic Search thật (POST /retrieval/search)
# -----------------------------------------------------------------------------
def render_knowledge_base_page() -> None:
    st.subheader(f"📚 Kho tri thức — {selected_course['course_name']}")

    documents = load_documents()
    course_documents = [d for d in documents if int(d.get("course_id", 0)) == course_id]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Tổng tài liệu", len(course_documents))
    c2.metric("🧬 Embedding Model", "MiniLM-L12-v2")
    c3.metric("🗄️ Vector DB", "ChromaDB")
    c4.metric("🤖 LLM", "Gemini 2.0 Flash")

    st.markdown("---")
    st.markdown("##### 🔎 Tìm kiếm ngữ nghĩa (Semantic Search)")
    st.caption("Tìm trực tiếp các đoạn tài liệu (chunk) gần nghĩa nhất với truy vấn, không qua bước sinh câu trả lời của LLM.")

    query = st.text_input("Nhập truy vấn:", placeholder="VD: ràng buộc khóa ngoại")
    kb_top_k = st.slider("Số kết quả", min_value=1, max_value=10, value=5, key="kb_topk")

    if st.button("Tìm kiếm", type="primary") and query.strip():
        with st.spinner("Đang tìm kiếm..."):
            ok, payload, code = request_json(
                "POST",
                "/retrieval/search",
                json_body={"question": query.strip(), "course_id": course_id, "top_k": kb_top_k},
            )
        if ok and isinstance(payload, dict):
            results = payload.get("results", [])
            if results:
                for item in results:
                    if not isinstance(item, dict):
                        continue
                    metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
                    render_source(
                        {
                            "document_name": metadata.get("document_name"),
                            "page": metadata.get("page"),
                            "content": item.get("text", ""),
                            "distance": item.get("distance"),
                        }
                    )
            else:
                st.info("Không tìm thấy đoạn tài liệu nào liên quan trong môn học này.")
        else:
            show_api_error("Semantic Search", payload, code)


# -----------------------------------------------------------------------------
# 8. TRANG QUIZ — sinh quiz + phản hồi đúng/sai theo từng câu sau khi nộp
# -----------------------------------------------------------------------------
def render_quiz_page() -> None:
    st.subheader("📝 Tự động sinh Quiz ôn tập từ tài liệu")

    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        quiz_topic = st.text_input("Chủ đề ôn tập:", value=st.session_state.get("last_quiz_topic", "SQL JOIN"))
    with col_q2:
        quiz_difficulty = st.segmented_control(
            "Độ khó mong muốn:",
            options=list(DIFFICULTY_LABELS.keys()),
            format_func=lambda v: DIFFICULTY_LABELS[v],
            default="easy",
        )
    with col_q3:
        quiz_count = int(st.number_input("Số câu hỏi:", min_value=1, max_value=10, value=5, step=1))

    if st.button("🎯 Tạo bài Quiz mới", type="primary", use_container_width=True):
        topic = quiz_topic.strip() or "SQL JOIN"
        with st.spinner("🤖 AI đang phân tích tài liệu và khởi tạo câu hỏi trắc nghiệm..."):
            ok, payload, status_code = request_json(
                "POST",
                "/quiz/generate",
                json_body={
                    "user_id": user_id,
                    "course_id": course_id,
                    "topic": topic,
                    "num_questions": quiz_count,
                    "difficulty": quiz_difficulty or "easy",
                },
                timeout=REQUEST_TIMEOUT,
            )

        if ok and isinstance(payload, dict):
            st.session_state.last_quiz = payload.get("quiz")
            st.session_state.last_quiz_topic = topic
            st.session_state.quiz_submitted = False
            st.session_state.quiz_review = None
            adaptive_diff = payload.get("adaptive_difficulty", "easy")
            st.success(f"🎉 Tạo Quiz thành công! (Độ khó thích ứng theo học lực: **{adaptive_diff.upper()}**)")
        else:
            st.session_state.last_quiz = None
            show_api_error("Tạo Quiz", payload, status_code)

    quiz = st.session_state.get("last_quiz")
    if isinstance(quiz, list) and quiz:
        st.markdown("---")
        with st.form("quiz_form"):
            selections: dict[int, str | None] = {}
            for idx, item in enumerate(quiz, start=1):
                if not isinstance(item, dict):
                    continue
                st.markdown(f"#### Câu {idx}: {item.get('question', '')}")
                options = item.get("options", {})
                if isinstance(options, dict):
                    labels = [f"{k}. {v}" for k, v in options.items() if k in {"A", "B", "C", "D"}]
                    if labels:
                        selected = st.radio(
                            "Chọn đáp án:",
                            labels,
                            key=f"q_{idx}_{st.session_state.last_quiz_topic}",
                            index=None,
                        )
                        selections[idx] = selected
                if item.get("explanation"):
                    with st.expander("💡 Xem giải thích"):
                        st.write(item["explanation"])

            sub_quiz = st.form_submit_button("📥 Nộp bài Quiz", use_container_width=True, type="primary")

        if sub_quiz:
            review = []
            correct_count = 0
            for idx, item in enumerate(quiz, start=1):
                if not isinstance(item, dict):
                    continue
                selected_label = selections.get(idx)
                selected_letter = selected_label[:1] if selected_label else None
                correct_letter = str(item.get("correct_answer", "")).strip().upper()
                is_correct = selected_letter == correct_letter
                if is_correct:
                    correct_count += 1
                review.append(
                    {
                        "question": item.get("question", ""),
                        "options": item.get("options", {}),
                        "selected": selected_letter,
                        "correct": correct_letter,
                        "is_correct": is_correct,
                    }
                )

            total = len(review)
            if total:
                ok, payload, status_code = request_json(
                    "POST",
                    "/quiz/submit",
                    json_body={
                        "user_id": user_id,
                        "course_id": course_id,
                        "topic": str(st.session_state.last_quiz_topic),
                        "total_questions": total,
                        "correct_answers": correct_count,
                    },
                    timeout=30,
                )
                st.session_state.quiz_review = review
                st.session_state.quiz_submitted = True
                st.session_state.dashboard_key = None  # force dashboard/analytics refresh after a new attempt
                if not ok:
                    show_api_error("Lưu kết quả Quiz", payload, status_code)

    if st.session_state.get("quiz_submitted") and st.session_state.get("quiz_review"):
        review = st.session_state.quiz_review
        correct = sum(1 for r in review if r["is_correct"])
        total = len(review)
        score_pct = (correct / total * 100) if total else 0

        st.markdown("---")
        st.success(f"🏆 Kết quả bài làm: **{correct}/{total}** câu đúng ({score_pct:.0f}%)")
        if score_pct >= 80:
            st.balloons()

        for idx, r in enumerate(review, start=1):
            icon = "✅" if r["is_correct"] else "❌"
            with st.container(border=True):
                st.markdown(f"{icon} **Câu {idx}:** {r['question']}")
                options = r["options"] if isinstance(r["options"], dict) else {}
                for k, v in options.items():
                    if k == r["correct"]:
                        st.markdown(f"- ✅ **{k}. {v}** _(đáp án đúng)_")
                    elif k == r["selected"]:
                        st.markdown(f"- ❌ ~~{k}. {v}~~ _(bạn đã chọn)_")
                    else:
                        st.caption(f"- {k}. {v}")


# -----------------------------------------------------------------------------
# 9. TRANG PHÂN TÍCH HỌC TẬP — Plotly + câu hỏi theo ngày
# -----------------------------------------------------------------------------
def render_analytics_page() -> None:
    st.subheader(f"📊 Phân tích học tập — {selected_course['course_name']}")

    if st.button("🔄 Làm mới dữ liệu"):
        ensure_dashboard_data(user_id, course_id, force=True)
    _, dashboard = ensure_dashboard_data(user_id, course_id)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        questions_by_topic = dashboard.get("questions_by_topic", {})
        st.markdown("##### 📊 Tần suất hỏi theo Chủ đề")
        if questions_by_topic:
            st.plotly_chart(plotly_topic_bar(questions_by_topic), use_container_width=True)
        else:
            st.info("Chưa có dữ liệu thống kê câu hỏi.")

    with col2:
        quiz_results = dashboard.get("quiz_results", [])
        st.markdown("##### 📈 Tiến trình Điểm số Quiz (%)")
        if quiz_results:
            st.plotly_chart(plotly_score_line(quiz_results), use_container_width=True)
        else:
            st.info("Chưa có lịch sử làm bài quiz.")

    st.markdown("---")
    st.markdown("##### 🗓️ Câu hỏi theo ngày")
    df_daily = compute_questions_per_day(user_id, course_id)
    if not df_daily.empty:
        st.plotly_chart(plotly_questions_per_day(df_daily), use_container_width=True)
    else:
        st.info("Chưa có dữ liệu câu hỏi theo ngày.")

    st.markdown("---")
    st.markdown("#### ⚠️ Chủ đề cần cải thiện & Gợi ý")
    col_w, col_r = st.columns(2, gap="large")
    with col_w:
        weak_topics = dashboard.get("weak_topics", [])
        if weak_topics:
            for wt in weak_topics:
                if isinstance(wt, dict):
                    with st.container(border=True):
                        st.markdown(f"🔴 **Chủ đề: {wt.get('topic')}**")
                        st.caption(wt.get("reason", ""))
        else:
            st.success("🎉 Bạn chưa có chủ đề yếu nào!")

    with col_r:
        recommendations = dashboard.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                if isinstance(rec, dict):
                    with st.container(border=True):
                        st.markdown(f"💡 **Gợi ý học tập: {rec.get('topic')}**")
                        st.markdown(rec.get("recommendation", ""))
        else:
            st.caption("Chưa có gợi ý bài tập cụ thể.")


# -----------------------------------------------------------------------------
# 10. TRANG CÀI ĐẶT — trình độ (thật) + thông số hệ thống (chỉ đọc, trung thực)
# -----------------------------------------------------------------------------
def render_settings_page() -> None:
    st.subheader("⚙️ Cài đặt")

    st.markdown("##### 👤 Trình độ học tập")
    st.caption(f"Áp dụng cho **{current_user['full_name']}** — ảnh hưởng cách Chatbot diễn giải câu trả lời.")
    picked_level = st.segmented_control(
        "Trình độ",
        options=list(LEVEL_LABELS.keys()),
        format_func=lambda v: LEVEL_LABELS[v],
        default=current_user["level"],
        key=f"settings_level_{current_user['id']}",
        label_visibility="collapsed",
    )
    if picked_level and picked_level != current_user["level"]:
        ok, payload, code = request_json(
            "PATCH", f"/users/{current_user['id']}/level", params={"level": picked_level}
        )
        if ok:
            st.session_state.current_user["level"] = picked_level
            st.rerun()
        else:
            show_api_error("Cập nhật trình độ", payload, code)

    st.markdown("---")
    st.markdown("##### 🌐 Kết nối Backend")
    st.text_input("Backend API URL", value=DEFAULT_API_URL, key="api_url")
    health_ok, _, _ = request_json("GET", "/health", timeout=5)
    if health_ok:
        st.success("🟢 API Backend: Connected")
    else:
        st.error("🔴 API Backend: Disconnected")

    st.markdown("---")
    st.markdown("##### 🔧 Thông số hệ thống (chỉ đọc)")
    st.caption(
        "Các thông số dưới đây được cấu hình cố định ở backend, chưa hỗ trợ chỉnh sửa qua giao diện — "
        "đây là hướng phát triển trong tương lai."
    )
    info_rows = {
        "Mô hình LLM": "Google Gemini — gemini-2.0-flash",
        "Mô hình Embedding": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 chiều)",
        "Cơ sở dữ liệu vector": "ChromaDB (persistent)",
        "Cơ sở dữ liệu quan hệ": "SQLite (SQLAlchemy ORM)",
        "Kích thước chunk": "700 ký tự",
        "Độ chồng lấp chunk": "100 ký tự",
        "Chiến lược truy xuất": "Hybrid Search (Dense + BM25 + RRF k=60) + Reranker",
    }
    for label, value in info_rows.items():
        row_c1, row_c2 = st.columns([1, 2])
        row_c1.markdown(f"**{label}**")
        row_c2.write(value)

    if is_admin:
        st.markdown("---")
        st.markdown("##### 🛡️ Quản trị hệ thống")
        st.caption("Chỉ tài khoản Admin mới thấy được khối này.")
        ok_users, all_users, _ = request_json("GET", "/users/", timeout=15)
        ok_courses, all_courses, _ = request_json("GET", "/courses/", timeout=15)
        a1, a2, a3 = st.columns(3)
        a1.metric("👥 Tổng người dùng", len(all_users) if ok_users and isinstance(all_users, list) else "N/A")
        a2.metric("📘 Tổng môn học", len(all_courses) if ok_courses and isinstance(all_courses, list) else "N/A")
        health_ok, _, _ = request_json("GET", "/health", timeout=5)
        a3.metric("🩺 Backend", "OK" if health_ok else "Lỗi")


# -----------------------------------------------------------------------------
# 11. ĐIỀU HƯỚNG
# -----------------------------------------------------------------------------
PAGE_RENDERERS = {
    "Dashboard": render_dashboard_page,
    "Chat": render_chat_page,
    "Tài liệu": render_documents_page,
    "Kho tri thức": render_knowledge_base_page,
    "Quiz": render_quiz_page,
    "Phân tích học tập": render_analytics_page,
    "Cài đặt": render_settings_page,
}

PAGE_RENDERERS[selected_page]()
