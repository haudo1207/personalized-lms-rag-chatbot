from __future__ import annotations

import json
from typing import Any

import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 120


st.set_page_config(
    page_title="RAG Learning Chatbot",
    layout="wide",
    initial_sidebar_state="expanded",
)


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
        return False, f"Không kết nối được backend: {exc}", None

    try:
        payload: dict[str, Any] | list[Any] | str = response.json()
    except ValueError:
        payload = response.text

    return response.ok, payload, response.status_code


def show_api_error(action: str, payload: dict[str, Any] | list[Any] | str, status_code: int | None) -> None:
    label = f"{action} thất bại"
    if status_code is not None:
        label = f"{label} - HTTP {status_code}"

    if isinstance(payload, dict) and payload.get("detail"):
        st.error(f"{label}: {payload['detail']}")
    elif payload:
        st.error(f"{label}: {payload}")
    else:
        st.error(label)


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
    document_name = source.get("document_name", "Tài liệu")
    page = source.get("page", "?")
    content = source.get("content", "")

    with st.container(border=True):
        st.markdown(f"**{document_name}** - Trang {page}")
        st.write(content)


def render_quiz(quiz: list[Any], topic: str, user_id: int, course_id: int) -> None:
    with st.form("quiz_submit_form"):
        answers: list[tuple[str, str]] = []

        for index, item in enumerate(quiz, start=1):
            if not isinstance(item, dict):
                continue

            st.markdown(f"**Câu {index}: {item.get('question', '')}**")
            options = item.get("options", {})
            if isinstance(options, dict):
                labels = [
                    f"{key}. {value}"
                    for key, value in options.items()
                    if key in {"A", "B", "C", "D"}
                ]
                if labels:
                    selected = st.radio(
                        "Chọn đáp án",
                        labels,
                        key=f"quiz_answer_{index}_{topic}",
                    )
                    correct = str(item.get("correct_answer", "")).strip().upper()
                    answers.append((selected[:1], correct))

            if item.get("explanation"):
                with st.expander("Giải thích"):
                    st.write(item["explanation"])

        submitted = st.form_submit_button("Nộp kết quả quiz", use_container_width=True)

    if submitted and answers:
        correct_answers = sum(1 for selected, correct in answers if selected == correct)
        ok, payload, status_code = request_json(
            "POST",
            "/quiz/submit",
            json_body={
                "user_id": user_id,
                "course_id": course_id,
                "topic": topic,
                "total_questions": len(answers),
                "correct_answers": correct_answers,
            },
            timeout=30,
        )
        if ok:
            st.success(f"Đã lưu kết quả: {correct_answers}/{len(answers)} câu đúng")
            st.json(payload)
        else:
            show_api_error("Lưu kết quả quiz", payload, status_code)


with st.sidebar:
    st.title("Thiết lập")
    st.text_input("Backend API", value=DEFAULT_API_URL, key="api_url")
    user_id = int(st.number_input("User ID", min_value=1, value=1, step=1))
    course_id = int(st.number_input("Course ID", min_value=1, value=1, step=1))
    top_k = int(st.slider("Số nguồn truy xuất", min_value=1, max_value=10, value=5))

    health_ok, health_payload, _ = request_json("GET", "/health", timeout=5)
    if health_ok:
        st.success("Backend đang chạy")
    else:
        st.warning("Chưa kết nối backend")
        if health_payload:
            st.caption(str(health_payload))


st.title("Chatbot hỏi đáp tài liệu học tập sử dụng RAG")
st.caption("Demo upload tài liệu, index vector, hỏi chatbot, xem nguồn, lịch sử, quiz và dashboard học tập.")

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


doc_col, chat_col = st.columns([1, 2], gap="large")

with doc_col:
    st.subheader("1. Upload tài liệu")
    uploaded_file = st.file_uploader(
        "Chọn tài liệu PDF/DOCX/TXT",
        type=["pdf", "docx", "txt"],
    )

    if st.button("Upload tài liệu", use_container_width=True):
        if uploaded_file is None:
            st.warning("Bạn cần chọn một tài liệu trước khi upload.")
        else:
            with st.spinner("Đang upload và xử lý tài liệu..."):
                ok, payload, status_code = request_json(
                    "POST",
                    "/documents/upload",
                    data={"course_id": course_id, "user_id": user_id},
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                    },
                )

            if ok and isinstance(payload, dict):
                st.success("Upload thành công")
                st.session_state.last_document_id = int(payload.get("document_id", 1))
                st.json(payload)
            else:
                show_api_error("Upload", payload, status_code)

    st.subheader("2. Index tài liệu")
    documents = load_documents()
    course_documents = [
        doc for doc in documents if int(doc.get("course_id", 0)) == course_id
    ]

    if course_documents:
        options = {
            f"#{doc['id']} - {doc['file_name']} ({doc['status']})": int(doc["id"])
            for doc in course_documents
            if "id" in doc and "file_name" in doc
        }
        selected_label = st.selectbox("Chọn tài liệu đã upload", list(options.keys()))
        st.session_state.last_document_id = options[selected_label]
    else:
        st.info("Chưa có tài liệu trong course này. Có thể nhập Document ID thủ công.")

    document_id = int(
        st.number_input(
            "Document ID",
            min_value=1,
            value=int(st.session_state.last_document_id),
            step=1,
        )
    )

    if st.button("Index tài liệu", use_container_width=True):
        with st.spinner("Đang tạo chunks, embedding và lưu vào ChromaDB..."):
            ok, payload, status_code = request_json(
                "POST",
                f"/documents/{document_id}/index",
            )

        if ok:
            st.success("Index thành công")
            st.json(payload)
        else:
            show_api_error("Index", payload, status_code)


with chat_col:
    st.subheader("3. Hỏi chatbot")
    question = st.text_area(
        "Nhập câu hỏi của bạn",
        placeholder='Ví dụ: "Khóa chính là gì?"',
        height=100,
    )

    if st.button("Gửi câu hỏi", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Bạn cần nhập câu hỏi trước khi gửi.")
        else:
            with st.spinner("Đang truy xuất tài liệu và sinh câu trả lời..."):
                ok, payload, status_code = request_json(
                    "POST",
                    "/chat/",
                    json_body={
                        "user_id": user_id,
                        "course_id": course_id,
                        "question": question.strip(),
                        "top_k": top_k,
                    },
                )

            if ok and isinstance(payload, dict):
                st.session_state.last_chat_result = payload
            else:
                st.session_state.last_chat_result = None
                show_api_error("Chatbot", payload, status_code)

    chat_result = st.session_state.last_chat_result
    if isinstance(chat_result, dict):
        st.markdown("#### Câu trả lời")
        st.write(chat_result.get("answer", ""))
        st.caption(
            f"Topic: {chat_result.get('topic', 'Khác')} | "
            f"Thời gian phản hồi: {chat_result.get('latency', '?')} giây"
        )

        if chat_result.get("weak_topic"):
            st.warning(f"Topic yếu đang được theo dõi: {chat_result['weak_topic']}")

        user_profile = chat_result.get("user_profile")
        if isinstance(user_profile, dict):
            with st.expander("Thông tin cá nhân hóa đã dùng"):
                st.write(f"Trình độ: {user_profile.get('level', 'beginner')}")
                st.write(f"Chủ đề còn yếu: {user_profile.get('weak_topics', [])}")
                st.write(f"Câu hỏi gần đây: {user_profile.get('recent_questions', [])}")

        sources = chat_result.get("sources", [])
        if sources:
            st.markdown("#### Nguồn tham khảo")
            for source in sources:
                if isinstance(source, dict):
                    render_source(source)

    st.subheader("4. Lịch sử hỏi đáp")
    if st.button("Xem lịch sử", use_container_width=True):
        with st.spinner("Đang tải lịch sử hỏi đáp..."):
            ok, payload, status_code = request_json(
                "GET",
                f"/chat/history/{user_id}",
                timeout=30,
            )

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

            with st.container(border=True):
                st.markdown(f"**Câu hỏi:** {item.get('question', '')}")
                if item.get("topic"):
                    st.caption(f"Topic: {item['topic']}")
                answer = str(item.get("answer", ""))
                st.markdown(f"**Trả lời:** {answer[:700]}{'...' if len(answer) > 700 else ''}")
                created_at = item.get("created_at")
                latency = item.get("latency")
                if created_at or latency:
                    st.caption(f"Thời gian tạo: {created_at or '?'} | Latency: {latency or '?'} giây")

                history_sources = parse_history_sources(item.get("sources"))
                if history_sources:
                    with st.expander("Nguồn đã dùng"):
                        for source in history_sources:
                            render_source(source)
    else:
        st.caption("Chưa tải lịch sử hoặc chưa có lịch sử hỏi đáp.")


st.divider()

quiz_col, dashboard_col = st.columns([1, 1], gap="large")

with quiz_col:
    st.subheader("5. Tạo quiz ôn tập")
    quiz_topic = st.text_input("Nhập topic muốn ôn", value=st.session_state.last_quiz_topic)
    quiz_difficulty = st.selectbox("Độ khó", ["easy", "medium", "hard"], index=0)
    quiz_count = int(st.number_input("Số câu hỏi", min_value=1, max_value=10, value=5, step=1))

    if st.button("Tạo quiz", use_container_width=True):
        topic = quiz_topic.strip() or "SQL JOIN"
        with st.spinner("Đang tạo quiz từ tài liệu..."):
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
            st.success("Tạo quiz thành công")
        else:
            st.session_state.last_quiz = None
            show_api_error("Tạo quiz", payload, status_code)

    quiz = st.session_state.last_quiz
    if isinstance(quiz, dict):
        st.warning(quiz.get("error", "Quiz chưa ở định dạng danh sách câu hỏi."))
        if quiz.get("raw_response"):
            st.text_area("Phản hồi gốc", value=str(quiz["raw_response"]), height=180)
    elif isinstance(quiz, list) and quiz:
        render_quiz(
            quiz=quiz,
            topic=str(st.session_state.last_quiz_topic),
            user_id=user_id,
            course_id=course_id,
        )


with dashboard_col:
    st.subheader("6. Dashboard học tập")

    if st.button("Xem dashboard cá nhân", use_container_width=True):
        with st.spinner("Đang tải dashboard học tập..."):
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
            show_api_error("Tải dashboard", payload, status_code)

    dashboard = st.session_state.dashboard
    if isinstance(dashboard, dict):
        metric_col_1, metric_col_2 = st.columns(2)
        metric_col_1.metric("Tổng số câu hỏi", dashboard.get("total_questions", 0))
        avg_score = dashboard.get("average_quiz_score")
        metric_col_2.metric("Điểm quiz TB", avg_score if avg_score is not None else "Chưa có")

        st.markdown("#### Topic yếu")
        weak_topics = dashboard.get("weak_topics", [])
        if weak_topics:
            st.write(weak_topics)
        else:
            st.caption("Chưa phát hiện topic yếu.")

        st.markdown("#### Kết quả quiz")
        quiz_results = dashboard.get("quiz_results", [])
        if quiz_results:
            st.dataframe(quiz_results, use_container_width=True)
        else:
            st.caption("Chưa có kết quả quiz.")

        st.markdown("#### Gợi ý ôn tập")
        for rec in dashboard.get("recommendations", []):
            if isinstance(rec, dict):
                st.info(rec.get("recommendation", ""))
