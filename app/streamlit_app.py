from __future__ import annotations

from typing import Any
import json

import altair as alt
import pandas as pd
import requests
import streamlit as st

DEFAULT_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 120

LEVEL_LABELS = {"beginner": "Mới bắt đầu", "intermediate": "Trung bình", "advanced": "Nâng cao"}
DIFFICULTY_LABELS = {"easy": "Dễ", "medium": "Trung bình", "hard": "Khó"}

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="RAG Learning Chatbot — Smart Learning Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .hero-container {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #9333ea 100%);
        padding: 1.8rem 2.2rem;
        border-radius: 18px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.3);
    }

    .hero-title {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        font-size: 1.02rem;
        opacity: 0.92;
        font-weight: 400;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
    }

    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        line-height: 1.6;
    }
    .status-badge.ok { background: #dcfce7; color: #15803d; }
    .status-badge.error { background: #fee2e2; color: #b91c1c; }
    .status-badge.warn { background: #fef3c7; color: #92400e; }
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
    try:
        response = requests.request(
            method,
            f"{get_api_url()}{path}",
            params=params,
            data=data,
            json=json_body,
            files=files,
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


def load_users() -> list[dict[str, Any]]:
    ok, payload, _ = request_json("GET", "/users/", timeout=15)
    if ok and isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def load_courses() -> list[dict[str, Any]]:
    ok, payload, _ = request_json("GET", "/courses/", timeout=15)
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
    if meta_bits:
        st.caption(" · ".join(meta_bits))
    if msg.get("weak_topic"):
        st.warning(f"⚠️ Bạn đang gặp khó khăn ở chủ đề **{msg['weak_topic']}**.")
    sources = msg.get("sources") or []
    if sources:
        with st.expander(f"🔗 {len(sources)} nguồn trích dẫn"):
            for source in sources:
                if isinstance(source, dict):
                    render_source(source)


# -----------------------------------------------------------------------------
# 3. SIDEBAR — PHIÊN LÀM VIỆC (chọn Người dùng / Môn học từ dữ liệu thật)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/chatbot.png", width=64)
    st.title("Hệ thống RAG LMS")
    st.caption("Cá nhân hóa Học tập thông minh")
    st.markdown("---")

    st.subheader("👤 Người dùng")
    users = load_users()
    selected_user: dict[str, Any] | None = None
    if users:
        user_labels = {f"{u['full_name']} ({u['email']})": u for u in users}
        labels_list = list(user_labels.keys())
        default_index = 0
        pending_email = st.session_state.get("pending_select_user_email")
        if pending_email:
            for i, u in enumerate(users):
                if u.get("email") == pending_email:
                    default_index = i
                    break
            st.session_state["pending_select_user_email"] = None
        picked_label = st.selectbox("Chọn người dùng:", labels_list, index=default_index)
        selected_user = user_labels[picked_label]
    else:
        st.info("Chưa có người dùng nào — tạo mới bên dưới.")

    with st.popover("➕ Tạo người dùng mới", use_container_width=True):
        new_name = st.text_input("Họ tên", key="new_user_name")
        new_email = st.text_input("Email", key="new_user_email")
        new_level = st.selectbox(
            "Trình độ ban đầu",
            list(LEVEL_LABELS.keys()),
            format_func=lambda v: LEVEL_LABELS[v],
            key="new_user_level",
        )
        if st.button("Tạo người dùng", key="btn_create_user", use_container_width=True):
            if new_name.strip() and new_email.strip():
                ok, payload, code = request_json(
                    "POST",
                    "/users/",
                    json_body={
                        "full_name": new_name.strip(),
                        "email": new_email.strip(),
                        "role": "student",
                        "level": new_level,
                    },
                )
                if ok and isinstance(payload, dict):
                    st.session_state["pending_select_user_email"] = payload.get("email")
                    st.rerun()
                else:
                    show_api_error("Tạo người dùng", payload, code)
            else:
                st.warning("Nhập đầy đủ họ tên & email.")

    if selected_user:
        st.caption(f"Trình độ của **{selected_user['full_name']}**:")
        picked_level = st.segmented_control(
            "Trình độ",
            options=list(LEVEL_LABELS.keys()),
            format_func=lambda v: LEVEL_LABELS[v],
            default=selected_user["level"],
            key=f"level_seg_{selected_user['id']}",
            label_visibility="collapsed",
        )
        if picked_level and picked_level != selected_user["level"]:
            ok, payload, code = request_json(
                "PATCH", f"/users/{selected_user['id']}/level", params={"level": picked_level}
            )
            if ok:
                st.rerun()
            else:
                show_api_error("Cập nhật trình độ", payload, code)

    st.markdown("---")
    st.subheader("📘 Môn học")
    courses = load_courses()
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
        picked_course_label = st.selectbox("Chọn môn học:", course_labels_list, index=default_course_index)
        selected_course = course_labels[picked_course_label]
    else:
        st.info("Chưa có môn học nào — tạo mới bên dưới.")

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
    with st.expander("⚙️ Cấu hình nâng cao"):
        st.text_input("Backend API URL", value=DEFAULT_API_URL, key="api_url")
        health_ok, _, _ = request_json("GET", "/health", timeout=5)
        if health_ok:
            st.success("🟢 API Backend: Connected")
        else:
            st.error("🔴 API Backend: Disconnected")


# -----------------------------------------------------------------------------
# 4. HERO HEADER
# -----------------------------------------------------------------------------
greeting = ""
if selected_user and selected_course:
    greeting = f"Xin chào <b>{selected_user['full_name']}</b> · Môn học: <b>{selected_course['course_name']}</b>"

st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-title">🎓 Chatbot Hỏi Đáp Tài Liệu Học Tập (RAG)</div>
        <div class="hero-subtitle">
            {greeting or "Hệ thống hỗ trợ sinh viên tra cứu tài liệu, tự động phát hiện lỗ hổng kiến thức, sinh Quiz ôn tập và theo dõi lộ trình học tập cá nhân hóa."}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not selected_user or not selected_course:
    st.warning("👈 Vui lòng chọn hoặc tạo **Người dùng** và **Môn học** ở thanh bên trái để bắt đầu.")
    st.stop()

user_id = int(selected_user["id"])
course_id = int(selected_course["id"])


# -----------------------------------------------------------------------------
# 5. TABBED INTERFACE
# -----------------------------------------------------------------------------
tab_chat, tab_docs, tab_quiz, tab_dashboard = st.tabs(
    [
        "💬 Chatbot RAG",
        "📁 Tài liệu",
        "📝 Quiz Ôn tập Cá nhân",
        "📊 Dashboard Học tập",
    ]
)

# -----------------------------------------------------------------------------
# TAB 1: CHATBOT RAG — hội thoại thật, dùng st.chat_message / st.chat_input
# -----------------------------------------------------------------------------
with tab_chat:
    header_col, opts_col = st.columns([8, 2])
    with header_col:
        st.subheader("💬 Đặt câu hỏi cho Chatbot")
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

    chat_box = st.container(height=460, border=True)
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
                else:
                    detail = payload.get("detail") if isinstance(payload, dict) else payload
                    error_text = f"⚠️ Không lấy được câu trả lời: {detail}"
                    st.error(error_text)
                    thread.append({"role": "assistant", "content": error_text})


# -----------------------------------------------------------------------------
# TAB 2: TÀI LIỆU — upload + quản lý gộp thành một luồng duy nhất
# -----------------------------------------------------------------------------
with tab_docs:
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
    documents = load_documents()
    course_documents = [doc for doc in documents if int(doc.get("course_id", 0)) == course_id]

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
        st.info("Chưa có tài liệu nào được upload cho môn học này.")


# -----------------------------------------------------------------------------
# TAB 3: QUIZ ÔN TẬP — sinh quiz + phản hồi đúng/sai theo từng câu sau khi nộp
# -----------------------------------------------------------------------------
with tab_quiz:
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
                st.session_state.dashboard_key = None  # force dashboard refresh after a new attempt
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
# TAB 4: DASHBOARD HỌC TẬP CÁ NHÂN HÓA — kèm hồ sơ học tập
# -----------------------------------------------------------------------------
with tab_dashboard:
    st.subheader(f"📊 Hồ sơ & Tiến độ học tập — {selected_course['course_name']}")

    dash_key = f"{user_id}:{course_id}"
    should_reload = st.session_state.get("dashboard_key") != dash_key
    if st.button("🔄 Làm mới dữ liệu", use_container_width=True):
        should_reload = True

    if should_reload:
        with st.spinner("Đang tổng hợp dữ liệu..."):
            prof_ok, prof_payload, prof_code = request_json(
                "GET", f"/chat/profile/{user_id}/{course_id}", timeout=15
            )
            dash_ok, dash_payload, dash_code = request_json(
                "GET", f"/dashboard/student/{user_id}", params={"course_id": course_id}, timeout=30
            )
        st.session_state.profile = prof_payload if prof_ok and isinstance(prof_payload, dict) else {}
        st.session_state.dashboard = dash_payload if dash_ok and isinstance(dash_payload, dict) else {}
        st.session_state.dashboard_key = dash_key
        if not dash_ok:
            show_api_error("Tải Dashboard", dash_payload, dash_code)

    profile = st.session_state.get("profile") or {}
    if profile:
        with st.container(border=True):
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("👤 Học viên", profile.get("full_name", "—"))
            pc2.metric("📈 Trình độ", LEVEL_LABELS.get(profile.get("level"), profile.get("level", "—")))
            pc3.metric("💬 Câu hỏi gần đây", len(profile.get("recent_questions", [])))

    dashboard = st.session_state.get("dashboard") or {}
    if dashboard:
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Tổng câu hỏi đã đặt", dashboard.get("total_questions", 0), delta="Hỏi đáp")
        with m2:
            avg_score = dashboard.get("average_quiz_score")
            st.metric("Điểm Quiz Trung bình", f"{avg_score}%" if avg_score is not None else "N/A", delta="Điểm số")
        with m3:
            weak_count = len(dashboard.get("weak_topics", []))
            st.metric(
                "Chủ đề còn yếu",
                f"{weak_count} topic",
                delta="Cần tập trung" if weak_count > 0 else "Hoàn hảo",
                delta_color="inverse" if weak_count > 0 else "normal",
            )

        st.markdown("---")
        c_chart1, c_chart2 = st.columns(2, gap="large")

        with c_chart1:
            questions_by_topic = dashboard.get("questions_by_topic", {})
            if questions_by_topic:
                st.markdown("##### 📊 Tần suất hỏi theo Chủ đề")
                df_q = pd.DataFrame(list(questions_by_topic.items()), columns=["topic", "count"])
                chart_q = (
                    alt.Chart(df_q)
                    .mark_bar(cornerRadius=4, color="#7c3aed")
                    .encode(
                        x=alt.X("count:Q", title="Số lượng"),
                        y=alt.Y("topic:N", sort="-x", title="Chủ đề"),
                        tooltip=["topic", "count"],
                    )
                    .properties(height=240)
                )
                st.altair_chart(chart_q, use_container_width=True)
            else:
                st.info("Chưa có dữ liệu thống kê câu hỏi.")

        with c_chart2:
            quiz_results = dashboard.get("quiz_results", [])
            if quiz_results:
                st.markdown("##### 📈 Tiến trình Điểm số Quiz (%)")
                sorted_res = sorted(quiz_results, key=lambda x: x.get("created_at", ""))
                df_scores = pd.DataFrame(
                    {
                        "time": [str(r["created_at"])[:16].replace("T", " ") for r in sorted_res],
                        "score": [float(r["score"]) for r in sorted_res],
                        "topic": [r.get("topic", "") for r in sorted_res],
                    }
                )
                chart_s = (
                    alt.Chart(df_scores)
                    .mark_line(point=True, color="#4f46e5")
                    .encode(
                        x=alt.X("time:N", title="Thời gian", sort=None),
                        y=alt.Y("score:Q", title="Điểm số (%)", scale=alt.Scale(domain=[0, 100])),
                        tooltip=["time", "score", "topic"],
                    )
                    .properties(height=240)
                )
                st.altair_chart(chart_s, use_container_width=True)
            else:
                st.info("Chưa có lịch sử làm bài quiz.")

        st.markdown("---")
        st.markdown("#### ⚠️ Danh sách Chủ đề cần cải thiện & Gợi ý")

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
