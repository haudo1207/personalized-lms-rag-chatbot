from __future__ import annotations

import requests

from app.ui_helpers import badge_html, get_api, require_course_selected, user_id

import streamlit as st


def render() -> None:
    course = require_course_selected()
    api = get_api()

    st.subheader(f"📁 Tài liệu — {course['course_name']}")

    with st.container(border=True):
        st.markdown("##### 📤 Upload tài liệu mới")
        up_col1, up_col2 = st.columns([7, 3])
        with up_col1:
            upload_file = st.file_uploader(
                "Chọn file PDF, DOCX hoặc TXT:", type=["pdf", "docx", "txt"], key="doc_upload"
            )
        with up_col2:
            st.caption("Hệ thống đang đọc và chuẩn bị tài liệu để bạn có thể hỏi đáp ngay sau khi tải lên.")

        if st.button(
            "📤 Tải lên & Đánh chỉ mục", type="primary", width="stretch", disabled=upload_file is None
        ):
            with st.spinner("Đang xử lý tài liệu (upload, chia chunk, tạo embedding)..."):
                up_ok, up_payload, up_code = api.upload_document(
                    course["id"], user_id(), upload_file.name, upload_file.getvalue(),
                    upload_file.type or "application/octet-stream",
                )
            if up_ok and isinstance(up_payload, dict):
                st.success(
                    f"✅ '{upload_file.name}' đã sẵn sàng để Chatbot trả lời "
                    f"({up_payload.get('chunks', '?')} đoạn văn bản đã được đánh chỉ mục)."
                )
                st.rerun()
            else:
                st.error(f"Upload thất bại (HTTP {up_code}): {up_payload}")

    st.markdown("---")
    st.markdown("##### 📚 Danh sách tài liệu đã upload")

    search_col, filter_col = st.columns([3, 1])
    with search_col:
        search_text = st.text_input("🔍 Tìm theo tên file", "", placeholder="Nhập tên file để lọc...")
    with filter_col:
        status_filter = st.selectbox("Trạng thái", ["Tất cả", "Sẵn sàng", "Lỗi xử lý"])

    _, payload, _ = api.list_documents()
    documents = [d for d in payload if isinstance(d, dict)] if isinstance(payload, list) else []
    course_documents = [d for d in documents if int(d.get("course_id", 0)) == course["id"]]

    if search_text.strip():
        needle = search_text.strip().lower()
        course_documents = [d for d in course_documents if needle in str(d.get("file_name", "")).lower()]
    if status_filter == "Sẵn sàng":
        course_documents = [d for d in course_documents if str(d.get("status", "")).lower() == "indexed"]
    elif status_filter == "Lỗi xử lý":
        course_documents = [d for d in course_documents if str(d.get("status", "")).lower() != "indexed"]

    if not course_documents:
        st.info("Không có tài liệu nào khớp bộ lọc hiện tại.")
        return

    for doc in course_documents:
        status = str(doc.get("status", "uploaded")).lower()
        doc_id = doc.get("id")

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
            with c1:
                st.markdown(f"📄 **{doc.get('file_name', 'Unnamed')}**")
                st.caption(f"ID #{doc_id} · Ngày tải lên: {str(doc.get('uploaded_at', ''))[:10]}")
            with c2:
                if status == "indexed":
                    st.markdown(badge_html("🟢 Sẵn sàng", "ok"), unsafe_allow_html=True)
                else:
                    st.markdown(badge_html("🔴 Lỗi xử lý", "error"), unsafe_allow_html=True)
                    st.caption("Có thể là file ảnh/scan không có chữ.")
            with c3:
                if status != "indexed":
                    if st.button("🔁 Thử lại", key=f"retry_{doc_id}", width="stretch"):
                        with st.spinner("Đang thử lại..."):
                            idx_ok, idx_payload, idx_code = api.retry_index(doc_id)
                        if idx_ok:
                            st.success("Đã xử lý xong!")
                            st.rerun()
                        else:
                            st.error(f"Thử lại thất bại: {idx_payload}")
            with c4:
                with st.popover("⋯", width="stretch"):
                    dl_bytes_key = f"dl_bytes_{doc_id}"
                    if dl_bytes_key in st.session_state:
                        st.download_button(
                            "⬇️ Tải xuống",
                            data=st.session_state[dl_bytes_key],
                            file_name=doc.get("file_name", f"document_{doc_id}"),
                            key=f"download_{doc_id}",
                            width="stretch",
                        )
                    elif st.button("⬇️ Tải xuống", key=f"prep_download_{doc_id}", width="stretch"):
                        # Only fetch the file's bytes now, on explicit click intent --
                        # not eagerly every time this popover is opened.
                        dl_ok, dl_content = _fetch_download_bytes(api, doc_id)
                        if dl_ok:
                            st.session_state[dl_bytes_key] = dl_content
                            st.rerun()
                        else:
                            st.error("Không tải được file gốc.")

                    new_name = st.text_input(
                        "Đổi tên", value=doc.get("file_name", ""), key=f"rename_input_{doc_id}"
                    )
                    if st.button("💾 Lưu tên mới", key=f"save_name_{doc_id}", width="stretch"):
                        r_ok, r_payload, r_code = api.rename_document(doc_id, new_name.strip())
                        if r_ok:
                            st.success("Đã đổi tên.")
                            st.rerun()
                        else:
                            st.error(f"Đổi tên thất bại: {r_payload}")

                    st.markdown("---")
                    confirm = st.checkbox("Xác nhận xóa vĩnh viễn", key=f"confirm_delete_{doc_id}")
                    if st.button(
                        "🗑️ Xóa tài liệu", key=f"delete_{doc_id}", width="stretch", disabled=not confirm
                    ):
                        d_ok, d_payload, d_code = api.delete_document(doc_id)
                        if d_ok:
                            st.success("Đã xóa tài liệu và toàn bộ chunk liên quan.")
                            st.rerun()
                        else:
                            st.error(f"Xóa thất bại: {d_payload}")


def _fetch_download_bytes(api, document_id: int) -> tuple[bool, bytes]:
    """Streamlit's download_button needs bytes upfront (not a URL), and the
    file is behind the same JWT as every other call -- fetch it directly with
    the Authorization header instead of just linking to the raw endpoint."""
    try:
        resp = requests.get(
            api.download_document_url(document_id), headers=api.auth_headers(), timeout=30
        )
    except requests.RequestException:
        return False, b""
    if not resp.ok:
        return False, b""
    return True, resp.content
