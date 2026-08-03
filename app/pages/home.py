"""Trang chủ: tạo / chọn / đổi tên / xóa môn học.

Ownership model: mỗi môn học thuộc về đúng 1 sinh viên (người tạo ra nó) --
không có bước "ghi danh" hay "admin thiết lập sẵn". Vào môn học đi thẳng vào
Chat (không còn trang Dashboard riêng).
"""

from __future__ import annotations

import streamlit as st

from app.ui_helpers import current_user, get_api, switch_to


def render() -> None:
    user = current_user()
    st.markdown(
        f"""
        <div class="hero-container">
            <div class="hero-title">🎓 Chào mừng, {user.get('full_name', '')}!</div>
            <div class="hero-subtitle">Chọn một môn học để bắt đầu, hoặc tạo môn học của riêng bạn.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    api = get_api()
    ok, payload, code = api.list_my_courses()
    courses = [c for c in payload if isinstance(c, dict)] if ok and isinstance(payload, list) else []

    if not ok:
        st.error(f"Không tải được danh sách môn học (HTTP {code}).")
        if code in (401, 403):
            st.warning("Phiên đăng nhập không hợp lệ hoặc hết hạn — vui lòng đăng xuất và đăng nhập lại.")

    with st.expander("➕ Tạo môn học mới", expanded=not courses):
        c1, c2 = st.columns(2)
        new_code = c1.text_input("Mã môn học (VD: CS101)", key="home_new_course_code")
        new_name = c2.text_input("Tên môn học", key="home_new_course_name")
        new_desc = st.text_area("Mô tả (tuỳ chọn)", key="home_new_course_desc", height=68)
        if st.button("Tạo môn học", type="primary", key="home_btn_create_course"):
            if new_code.strip() and new_name.strip():
                c_ok, c_payload, c_code = api.create_course(
                    new_code.strip(), new_name.strip(), new_desc.strip() or None
                )
                if c_ok:
                    st.success(f"Đã tạo môn học '{new_name}'.")
                    st.rerun()
                else:
                    st.error(f"Tạo môn học thất bại: {c_payload}")
            else:
                st.warning("Nhập đầy đủ mã và tên môn học.")

    st.markdown("---")

    if not courses:
        st.info("👋 Bạn chưa có môn học nào. Tạo môn học đầu tiên ở khối phía trên để bắt đầu.")
        return

    st.markdown("##### 📚 Môn học của bạn")
    cols = st.columns(3)
    for idx, course in enumerate(courses):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{course['course_code']}**")
                st.markdown(course["course_name"])
                if course.get("description"):
                    st.caption(course["description"])

                if st.button("Vào môn học →", key=f"enter_{course['id']}", type="primary", width="stretch"):
                    st.session_state["selected_course"] = course
                    switch_to("Chat AI")

                with st.popover("⋯ Quản lý", width="stretch"):
                    rename = st.text_input(
                        "Đổi tên môn học", value=course["course_name"], key=f"rename_{course['id']}"
                    )
                    if st.button("Lưu tên mới", key=f"save_rename_{course['id']}"):
                        r_ok, r_payload, r_code = api.update_course(course["id"], course_name=rename.strip())
                        if r_ok:
                            st.success("Đã cập nhật.")
                            st.rerun()
                        else:
                            st.error(f"Cập nhật thất bại: {r_payload}")

                    st.markdown("---")
                    st.warning(
                        "⚠️ Xóa môn học sẽ xóa **vĩnh viễn** toàn bộ tài liệu, lịch sử chat và quiz "
                        "của môn này. Không thể hoàn tác."
                    )
                    confirm_delete = st.checkbox(
                        "Tôi hiểu và muốn xóa vĩnh viễn môn học này", key=f"confirm_delete_{course['id']}"
                    )
                    if st.button(
                        "🗑️ Xóa môn học",
                        key=f"delete_{course['id']}",
                        disabled=not confirm_delete,
                        width="stretch",
                    ):
                        d_ok, d_payload, d_code = api.delete_course(course["id"])
                        if d_ok:
                            st.session_state.pop("selected_course", None)
                            st.success("Đã xóa môn học.")
                            st.rerun()
                        else:
                            st.error(f"Xóa thất bại: {d_payload}")
