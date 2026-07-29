from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 120

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING (MODERN DESIGN SYSTEM)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="RAG Learning Chatbot — Smart Learning Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS System with harmonious gradients, glassmorphism, and clean card tokens
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main Gradient Header Card */
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
    
    .doc-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
    }
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


# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & USER CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/chatbot.png", width=64)
    st.title("Hệ thống RAG LMS")
    st.caption("Cá nhân hóa Học tập thông minh")
    
    st.markdown("---")
    st.subheader("⚙️ Cấu hình hệ thống")
    st.text_input("Backend API URL", value=DEFAULT_API_URL, key="api_url")
    
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        user_id = int(st.number_input("User ID", min_value=1, value=1, step=1))
    with col_u2:
        course_id = int(st.number_input("Course ID", min_value=1, value=1, step=1))
        
    top_k = int(st.slider("Số nguồn truy xuất (Top K)", min_value=1, max_value=10, value=3))

    st.markdown("---")
    st.subheader("👤 Hồ sơ học tập (Profile)")
    user_level = st.selectbox(
        "Trình độ người học:",
        ["beginner", "intermediate", "advanced"],
        index=0,
        help="Hệ thống sẽ điều chỉnh độ sâu và từ ngữ giải thích theo trình độ này."
    )
    
    # Sync student level to DB
    if "last_synced_level" not in st.session_state or st.session_state.get("last_synced_level_user") != user_id or st.session_state.last_synced_level != user_level:
        ok, payload, status_code = request_json("PATCH", f"/users/{user_id}/level", params={"level": user_level})
        if not ok and status_code == 404:
            create_ok, _, _ = request_json("POST", "/users/", json_body={
                "full_name": f"Sinh viên {user_id}",
                "email": f"student{user_id}@lms.edu.vn",
                "role": "student",
                "level": user_level
            })
            if create_ok:
                st.session_state.last_synced_level = user_level
                st.session_state.last_synced_level_user = user_id
        elif ok:
            st.session_state.last_synced_level = user_level
            st.session_state.last_synced_level_user = user_id

    st.markdown("---")
    st.subheader("🔍 Bộ lọc Metadata (RAG)")
    docs = load_documents()
    course_docs = [d for d in docs if int(d.get("course_id", 0)) == course_id]
    
    doc_filter_options = {}
    for d in course_docs:
        doc_filter_options[f"#{d['id']} - {d['file_name']}"] = int(d['id'])
        
    selected_docs = st.multiselect(
        "Chỉ tìm trong file:",
        options=list(doc_filter_options.keys()),
        default=[],
        help="Để trống để tìm kiếm trên tất cả tài liệu của môn học."
    )
    filter_doc_ids = [doc_filter_options[label] for label in selected_docs]

    st.markdown("---")
    health_ok, _, _ = request_json("GET", "/health", timeout=5)
    if health_ok:
        st.success("🟢 API Backend: Connected")
    else:
        st.error("🔴 API Backend: Disconnected")


# -----------------------------------------------------------------------------
# 4. MAIN HERO HEADER & STATE INITIALIZATION
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">🎓 Chatbot Hỏi Đáp Tài Liệu Học Tập (RAG)</div>
        <div class="hero-subtitle">
            Hệ thống hỗ trợ sinh viên tra cứu tài liệu, tự động phát hiện lỗ hổng kiến thức, sinh Quiz ôn tập và theo dõi lộ trình học tập cá nhân hóa.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "last_document_id" not in st.session_state:
    st.session_state.last_document_id = 1
if "last_chat_result" not in st.session_state:
    st.session_state.last_chat_result = None
if "last_quiz" not in st.session_state:
    st.session_state.last_quiz = None
if "last_quiz_topic" not in st.session_state:
    st.session_state.last_quiz_topic = "SQL JOIN"
if "dashboard" not in st.session_state:
    st.session_state.dashboard = None


# -----------------------------------------------------------------------------
# 5. TABBED INTERFACE (CHAT WITH QUICK UPLOAD & STORED DOCS BOX)
# -----------------------------------------------------------------------------
tab_chat, tab_docs, tab_quiz, tab_dashboard = st.tabs([
    "💬 Chatbot RAG",
    "📚 Danh sách Tài liệu",
    "📝 Quiz Ôn tập Cá nhân",
    "📊 Dashboard Học tập"
])

# -----------------------------------------------------------------------------
# TAB 1: CHATBOT RAG (WITH QUICK UPLOAD IN CHAT & STORED DOCS BOX)
# -----------------------------------------------------------------------------
with tab_chat:
    col_input, col_info = st.columns([7, 3], gap="large")
    
    with col_input:
        st.subheader("💬 Đặt câu hỏi cho Chatbot")
        
        # Sample prompt suggestions for quick click
        st.caption("💡 Câu hỏi gợi ý:")
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        prompt_preset = None
        if btn_col1.button("🔑 Khóa chính là gì?", use_container_width=True):
            prompt_preset = "Khóa chính là gì?"
        if btn_col2.button("🔀 INNER vs LEFT JOIN?", use_container_width=True):
            prompt_preset = "INNER JOIN khác LEFT JOIN như thế nào?"
        if btn_col3.button("📐 Chuẩn hóa 3NF?", use_container_width=True):
            prompt_preset = "3NF giúp giải quyết phụ thuộc hàm nào?"

        question_input = st.text_area(
            "Nhập câu hỏi của bạn:",
            value=prompt_preset if prompt_preset else "",
            placeholder="Ví dụ: Khóa ngoại dùng để làm gì và có thể chứa giá trị trùng lặp không?",
            height=100,
        )

        col_act1, col_act2 = st.columns([4, 6])
        with col_act1:
            send_click = st.button("🚀 Gửi câu hỏi", type="primary", use_container_width=True)

        if send_click:
            if not question_input.strip():
                st.warning("Vui lòng nhập nội dung câu hỏi trước khi gửi.")
            else:
                with st.spinner("🔍 Đang truy xuất tài liệu & sinh câu trả lời..."):
                    ok, payload, status_code = request_json(
                        "POST",
                        "/chat/",
                        json_body={
                            "user_id": user_id,
                            "course_id": course_id,
                            "question": question_input.strip(),
                            "top_k": top_k,
                            "document_ids": filter_doc_ids if filter_doc_ids else None
                        },
                    )

                if ok and isinstance(payload, dict):
                    st.session_state.last_chat_result = payload
                else:
                    st.session_state.last_chat_result = None
                    show_api_error("Hỏi Chatbot", payload, status_code)

        # --- NÚT UPLOAD TẢI LIỆU NHANH NGAY TẠI KHUNG CHAT ---
        with st.expander("📎 **Upload & Đánh chỉ mục (Indexing) Tài liệu Mới ngay tại đây**", expanded=False):
            up_col1, up_col2 = st.columns([6, 4])
            with up_col1:
                chat_upload_file = st.file_uploader(
                    "Chọn file PDF, DOCX, TXT để bổ sung kiến thức:",
                    type=["pdf", "docx", "txt"],
                    key="quick_chat_upload"
                )
                if st.button("📤 Tải lên", type="primary", use_container_width=True):
                    if chat_upload_file is None:
                        st.warning("Vui lòng chọn file trước khi bấm Tải lên.")
                    else:
                        with st.spinner("Đang xử lý tài liệu (upload, chia chunk, tạo embedding)..."):
                            up_ok, up_payload, up_code = request_json(
                                "POST",
                                "/documents/upload",
                                data={"course_id": course_id, "user_id": user_id},
                                files={"file": (chat_upload_file.name, chat_upload_file.getvalue(), chat_upload_file.type or "application/octet-stream")}
                            )
                        if up_ok and isinstance(up_payload, dict):
                            doc_id = int(up_payload.get("document_id", 1))
                            chunk_count = up_payload.get("chunks", "?")
                            st.success(
                                f"✅ Tài liệu '{chat_upload_file.name}' đã sẵn sàng để Chatbot trả lời "
                                f"({chunk_count} đoạn văn bản đã được đánh chỉ mục)."
                            )
                            st.session_state.last_document_id = doc_id
                        else:
                            show_api_error("Upload tài liệu", up_payload, up_code)

            with up_col2:
                st.caption("ℹ️ Hướng dẫn:")
                st.markdown("- File upload sẽ tự động được chia chunk & đánh chỉ mục Vector.")
                st.markdown("- Sau khi upload thành công, Chatbot sẽ có ngay kiến thức từ file này để trả lời bạn!")

        # Display Chat Answer Result
        chat_result = st.session_state.last_chat_result
        if isinstance(chat_result, dict):
            st.markdown("---")
            with st.container(border=True):
                st.markdown("### 🤖 Phản hồi từ Chatbot")
                st.markdown(chat_result.get("answer", ""))
                
                col_meta1, col_meta2 = st.columns(2)
                with col_meta1:
                    st.caption(f"📌 Chủ đề nhận diện: **{chat_result.get('topic', 'Khác')}**")
                with col_meta2:
                    st.caption(f"⚡ Thời gian phản hồi: **{chat_result.get('latency', '?')}s**")

                if chat_result.get("weak_topic"):
                    st.warning(f"⚠️ **Cảnh báo Topic yếu:** Hệ thống ghi nhận bạn đang gặp khó khăn ở chủ đề **{chat_result['weak_topic']}**.")

            sources = chat_result.get("sources", [])
            if sources:
                st.markdown("#### 🔗 Nguồn tài liệu trích dẫn (Citations)")
                for source in sources:
                    if isinstance(source, dict):
                        render_source(source)

    with col_info:
        # --- KHUNG KHO LƯU TRỮ TÀI LIỆU ĐÃ UPLOAD ---
        st.subheader("📂 Kho Tài liệu đã Upload")
        documents = load_documents()
        course_documents = [doc for doc in documents if int(doc.get("course_id", 0)) == course_id]
        
        if course_documents:
            st.caption(f"Đã lưu **{len(course_documents)}** file trong môn học này:")
            for doc in course_documents:
                status = str(doc.get("status", "uploaded")).lower()
                status_icon = "🟢 Sẵn sàng" if status == "indexed" else "🔴 Lỗi xử lý"
                with st.container(border=True):
                    st.markdown(f"📄 **{doc.get('file_name', 'Unnamed')}**")
                    st.caption(f"ID: #{doc.get('id')} | {status_icon}")
                    if status != "indexed":
                        st.caption("Tài liệu này chưa xử lý được (có thể là file ảnh/scan không có chữ).")
                        if st.button(f"🔁 Thử lại #{doc.get('id')}", key=f"btn_idx_{doc.get('id')}", use_container_width=True):
                            with st.spinner("Đang thử lại..."):
                                idx_ok, idx_payload, idx_code = request_json("POST", f"/documents/{doc.get('id')}/index")
                                if idx_ok:
                                    st.success("Đã xử lý xong!")
                                    st.rerun()
                                else:
                                    show_api_error("Thử lại", idx_payload, idx_code)
        else:
            st.info("Chưa có tài liệu nào được upload cho môn học này.")

        st.markdown("---")
        st.subheader("📜 Lịch sử hỏi đáp")
        if st.button("🔄 Tải lại lịch sử", use_container_width=True):
            with st.spinner("Đang tải..."):
                ok, payload, status_code = request_json("GET", f"/chat/history/{user_id}", timeout=30)
                if ok and isinstance(payload, list):
                    st.session_state.history = payload
                else:
                    st.session_state.history = []
                    show_api_error("Tải lịch sử", payload, status_code)

        history = st.session_state.get("history", [])
        if history:
            for item in history[:5]:
                if not isinstance(item, dict):
                    continue
                with st.expander(f"❓ {item.get('question', '')[:35]}..."):
                    st.markdown(f"**Chủ đề:** `{item.get('topic', 'Tổng hợp')}`")
                    st.markdown(f"**Trả lời:** {item.get('answer', '')}")
                    st.caption(f"📅 {item.get('created_at', '')[:16].replace('T', ' ')}")
        else:
            st.info("Chưa có lịch sử câu hỏi gần đây.")


# -----------------------------------------------------------------------------
# TAB 2: DANH SÁCH TÀI LIỆU (DOCUMENT MANAGER)
# -----------------------------------------------------------------------------
with tab_docs:
    st.subheader("📚 Danh sách Chi tiết Tài liệu")
    documents = load_documents()
    course_documents = [doc for doc in documents if int(doc.get("course_id", 0)) == course_id]

    if course_documents:
        for doc in course_documents:
            with st.container(border=True):
                c_d1, c_d2, c_d3 = st.columns([5, 3, 2])
                with c_d1:
                    st.markdown(f"📄 **{doc.get('file_name', 'Unnamed')}** (ID: `{doc.get('id')}`)")
                with c_d2:
                    status = str(doc.get("status", "uploaded")).lower()
                    status_label = "🟢 Sẵn sàng" if status == "indexed" else "🔴 Lỗi xử lý"
                    st.caption(f"Trạng thái: **{status_label}**")
                    st.caption(f"Ngày tạo: {str(doc.get('uploaded_at', ''))[:10]}")
                with c_d3:
                    if status != "indexed":
                        if st.button("🔁 Thử lại", key=f"tab2_idx_{doc.get('id')}", use_container_width=True):
                            with st.spinner("Đang thử lại..."):
                                idx_ok, payload, code = request_json("POST", f"/documents/{doc.get('id')}/index")
                                if idx_ok:
                                    st.success("Đã xử lý xong!")
                                    st.rerun()
                                else:
                                    show_api_error("Thử lại", payload, code)
    else:
        st.info("Chưa có tài liệu nào được tải lên cho môn học này.")


# -----------------------------------------------------------------------------
# TAB 3: QUIZ ÔN TẬP
# -----------------------------------------------------------------------------
with tab_quiz:
    st.subheader("📝 Tự động sinh Quiz ôn tập từ tài liệu")
    
    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        quiz_topic = st.text_input("Chủ đề ôn tập:", value=st.session_state.last_quiz_topic)
    with col_q2:
        quiz_difficulty = st.selectbox("Độ khó mong muốn:", ["easy", "medium", "hard"], index=0)
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
                    "difficulty": quiz_difficulty,
                },
                timeout=REQUEST_TIMEOUT,
            )

        if ok and isinstance(payload, dict):
            st.session_state.last_quiz = payload.get("quiz")
            st.session_state.last_quiz_topic = topic
            adaptive_diff = payload.get("adaptive_difficulty", "easy")
            st.success(f"🎉 Tạo Quiz thành công! (Độ khó thích ứng theo học lực: **{adaptive_diff.upper()}**)")
        else:
            st.session_state.last_quiz = None
            show_api_error("Tạo Quiz", payload, status_code)

    quiz = st.session_state.last_quiz
    if isinstance(quiz, list) and quiz:
        st.markdown("---")
        with st.form("quiz_form"):
            answers: list[tuple[str, str]] = []
            for idx, item in enumerate(quiz, start=1):
                if not isinstance(item, dict):
                    continue
                st.markdown(f"#### Câu {idx}: {item.get('question', '')}")
                options = item.get("options", {})
                if isinstance(options, dict):
                    labels = [f"{k}. {v}" for k, v in options.items() if k in {"A", "B", "C", "D"}]
                    if labels:
                        selected = st.radio("Chọn đáp án:", labels, key=f"q_{idx}_{quiz_topic}")
                        correct = str(item.get("correct_answer", "")).strip().upper()
                        answers.append((selected[:1], correct))
                if item.get("explanation"):
                    with st.expander("💡 Xem giải thích"):
                        st.write(item["explanation"])
                st.markdown("<br>", unsafe_allow_html=True)

            sub_quiz = st.form_submit_button("📥 Nộp bài Quiz", use_container_width=True, type="primary")

        if sub_quiz and answers:
            correct_count = sum(1 for sel, cor in answers if sel == cor)
            ok, payload, status_code = request_json(
                "POST",
                "/quiz/submit",
                json_body={
                    "user_id": user_id,
                    "course_id": course_id,
                    "topic": str(st.session_state.last_quiz_topic),
                    "total_questions": len(answers),
                    "correct_answers": correct_count,
                },
                timeout=30,
            )
            if ok:
                score_pct = (correct_count / len(answers)) * 100
                st.balloons()
                st.success(f"🏆 Kết quả bài làm: **{correct_count}/{len(answers)}** câu đúng ({score_pct:.0f}%)")
            else:
                show_api_error("Lưu kết quả Quiz", payload, status_code)


# -----------------------------------------------------------------------------
# TAB 4: DASHBOARD HỌC TẬP CÁ NHÂN HÓA
# -----------------------------------------------------------------------------
with tab_dashboard:
    st.subheader("📊 Báo cáo & Phân tích Năng lực Học tập")
    
    if st.button("🔄 Tải lại Dashboard", type="primary", use_container_width=True):
        with st.spinner("Đang tổng hợp dữ liệu..."):
            ok, payload, status_code = request_json(
                "GET",
                f"/dashboard/student/{user_id}",
                params={"course_id": course_id},
                timeout=30,
            )
            if ok and isinstance(payload, dict):
                st.session_state.dashboard = payload
            else:
                st.session_state.dashboard = None
                show_api_error("Tải Dashboard", payload, status_code)

    dashboard = st.session_state.dashboard
    if isinstance(dashboard, dict):
        # 1. Top Key Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Tổng câu hỏi đã đặt", dashboard.get("total_questions", 0), delta="Hỏi đáp")
        with m2:
            avg_score = dashboard.get("average_quiz_score")
            st.metric("Điểm Quiz Trung bình", f"{avg_score}%" if avg_score is not None else "N/A", delta="Điểm số")
        with m3:
            weak_count = len(dashboard.get("weak_topics", []))
            st.metric("Chủ đề còn yếu", f"{weak_count} topic", delta="-Cần tập trung" if weak_count > 0 else "Hoàn hảo", delta_color="inverse")

        st.markdown("---")
        c_chart1, c_chart2 = st.columns(2, gap="large")
        
        with c_chart1:
            questions_by_topic = dashboard.get("questions_by_topic", {})
            if questions_by_topic:
                st.markdown("##### 📊 Tần suất hỏi theo Chủ đề")
                import pandas as pd
                df_q = pd.DataFrame(list(questions_by_topic.items()), columns=["Chủ đề", "Số lượng"]).set_index("Chủ đề")
                st.bar_chart(df_q)
            else:
                st.info("Chưa có dữ liệu thống kê câu hỏi.")

        with c_chart2:
            quiz_results = dashboard.get("quiz_results", [])
            if quiz_results:
                st.markdown("##### 📈 Tiến trình Điểm số Quiz (%)")
                import pandas as pd
                sorted_res = sorted(quiz_results, key=lambda x: x.get("created_at", ""))
                df_scores = pd.DataFrame({
                    "Thời gian": [str(r["created_at"])[:16].replace("T", " ") for r in sorted_res],
                    "Điểm số (%)": [float(r["score"]) for r in sorted_res]
                }).set_index("Thời gian")
                st.line_chart(df_scores)
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
