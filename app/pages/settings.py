from __future__ import annotations

import streamlit as st

from app.ui_helpers import (
    DEFAULT_API_URL,
    LEVEL_LABELS,
    current_user,
    get_api,
    is_admin,
    selected_course,
    user_id,
)


def render() -> None:
    st.subheader("⚙️ Cài đặt")
    user = current_user()
    api = get_api()

    st.markdown("##### 👤 Trình độ học tập")
    st.caption(f"Áp dụng cho **{user['full_name']}** — ảnh hưởng cách Chatbot diễn giải câu trả lời.")
    picked_level = st.segmented_control(
        "Trình độ",
        options=list(LEVEL_LABELS.keys()),
        format_func=lambda v: LEVEL_LABELS[v],
        default=user["level"],
        key=f"settings_level_{user['id']}",
        label_visibility="collapsed",
    )
    if picked_level and picked_level != user["level"]:
        ok, payload, code = api.update_level(user["id"], picked_level)
        if ok:
            st.session_state.current_user["level"] = picked_level
            st.rerun()
        else:
            st.error(f"Cập nhật trình độ thất bại: {payload}")

    st.markdown("---")
    st.markdown("##### 🔒 Đổi mật khẩu")
    with st.form("change_password_form"):
        current_password = st.text_input("Mật khẩu hiện tại", type="password")
        new_password = st.text_input("Mật khẩu mới (ít nhất 8 ký tự)", type="password")
        confirm_password = st.text_input("Nhập lại mật khẩu mới", type="password")
        submitted = st.form_submit_button("Đổi mật khẩu", type="primary")

    if submitted:
        if not current_password or not new_password:
            st.warning("Nhập đầy đủ mật khẩu hiện tại và mật khẩu mới.")
        elif new_password != confirm_password:
            st.warning("Mật khẩu mới nhập lại không khớp.")
        else:
            ok, payload, code = api.change_password(current_password, new_password)
            if ok:
                st.success("Đổi mật khẩu thành công. Lần đăng nhập sau hãy dùng mật khẩu mới.")
            else:
                detail = payload.get("detail") if isinstance(payload, dict) else payload
                st.error(f"Đổi mật khẩu thất bại: {detail}")

    st.markdown("---")
    st.markdown("##### 🧹 Lịch sử hội thoại")
    course = selected_course()
    if course:
        st.caption(f"Xóa toàn bộ lịch sử chat của bạn trong môn học **{course['course_name']}**.")
        confirm_clear = st.checkbox("Xác nhận xóa lịch sử hội thoại của môn học này")
        if st.button("🗑️ Xóa lịch sử hội thoại", disabled=not confirm_clear):
            ok, payload, code = api.clear_chat_history(user_id(), course["id"])
            if ok:
                thread_key = f"{user_id()}:{course['id']}"
                st.session_state.get("chat_threads", {}).pop(thread_key, None)
                st.session_state.get("chat_hydrated_keys", set()).discard(thread_key)
                st.success(f"Đã xóa {payload.get('deleted_count', 0)} tin nhắn.")
                st.rerun()
            else:
                st.error(f"Xóa lịch sử thất bại: {payload}")
    else:
        st.caption("Chọn một môn học ở Trang chủ để quản lý lịch sử hội thoại của môn đó.")

    # Backend URL + system internals (model, chunking, retrieval strategy) are
    # deployment/debugging details with no value to a student -- and the URL
    # field is a real phishing vector if left editable. Admin-only.
    if is_admin():
        st.markdown("---")
        st.markdown("##### 🌐 Kết nối Backend *(chỉ Admin)*")
        st.session_state.setdefault("api_url", DEFAULT_API_URL)
        st.text_input("Backend API URL", key="api_url")
        health_ok, _, _ = api.health()
        if health_ok:
            st.success("🟢 API Backend: Connected")
        else:
            st.error("🔴 API Backend: Disconnected")

        st.markdown("---")
        st.markdown("##### 🔧 Thông số hệ thống *(chỉ Admin, chỉ đọc)*")
        st.caption(
            "Các thông số dưới đây được cấu hình cố định ở backend, chưa hỗ trợ chỉnh sửa qua giao diện."
        )
        for label, value in _system_info_rows().items():
            row_c1, row_c2 = st.columns([1, 2])
            row_c1.markdown(f"**{label}**")
            row_c2.write(value)


def _system_info_rows() -> dict[str, str]:
    # Read straight from backend.config instead of hardcoding, so this panel
    # can't silently drift from the model the backend is actually using
    # (this repo previously shipped a UI that said "Gemini 2.0 Flash" while
    # the backend had already moved to gemini-2.5-flash).
    try:
        from backend.config import get_settings

        gemini_model = get_settings().gemini_model
    except Exception:
        gemini_model = "(không đọc được backend.config — kiểm tra biến môi trường)"

    return {
        "Mô hình LLM": f"Google Gemini — {gemini_model}",
        "Mô hình Embedding": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 chiều)",
        "Mô hình Reranker": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        "Cơ sở dữ liệu vector": "ChromaDB (persistent)",
        "Cơ sở dữ liệu quan hệ": "SQLite (SQLAlchemy ORM + Alembic)",
        "Chiến lược Chunking": "Semantic Chunking (percentile 85, dự phòng Fixed-size 700/100)",
        "Chiến lược truy xuất": "Hybrid Search (Dense + BM25 + RRF k=60) + Cross-Encoder Reranker",
    }
