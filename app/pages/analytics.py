from __future__ import annotations

import streamlit as st

from app.ui_helpers import (
    compute_questions_per_day,
    get_api,
    plotly_feedback_pie,
    plotly_questions_per_day,
    plotly_score_line,
    plotly_topic_bar,
    require_course_selected,
    user_id,
)


def render() -> None:
    course = require_course_selected()
    api = get_api()
    uid = user_id()

    st.subheader(f"📊 Phân tích học tập — {course['course_name']}")

    if st.button("🔄 Làm mới dữ liệu"):
        st.session_state.dashboard_key = None

    key = f"{uid}:{course['id']}"
    if st.session_state.get("dashboard_key") != key:
        with st.spinner("Đang tổng hợp dữ liệu..."):
            _, dashboard, _ = api.get_student_dashboard(uid, course["id"])
        st.session_state.dashboard = dashboard if isinstance(dashboard, dict) else {}
        st.session_state.dashboard_key = key
    dashboard = st.session_state.get("dashboard") or {}

    col1, col2 = st.columns(2, gap="large")
    with col1:
        questions_by_topic = dashboard.get("questions_by_topic", {})
        st.markdown("##### 📊 Tần suất hỏi theo Chủ đề")
        if questions_by_topic:
            st.plotly_chart(plotly_topic_bar(questions_by_topic), width="stretch")
        else:
            st.info("Chưa có dữ liệu thống kê câu hỏi.")

    with col2:
        quiz_results = dashboard.get("quiz_results", [])
        st.markdown("##### 📈 Tiến trình Điểm số Quiz (%)")
        if quiz_results:
            st.plotly_chart(plotly_score_line(quiz_results), width="stretch")
        else:
            st.info("Chưa có lịch sử làm bài quiz.")

    st.markdown("---")
    col3, col4 = st.columns(2, gap="large")
    with col3:
        st.markdown("##### 🗓️ Câu hỏi theo ngày")
        df_daily = compute_questions_per_day(uid, course["id"])
        if not df_daily.empty:
            st.plotly_chart(plotly_questions_per_day(df_daily), width="stretch")
        else:
            st.info("Chưa có dữ liệu câu hỏi theo ngày.")

    with col4:
        st.markdown("##### 👍 Tỷ lệ câu trả lời hữu ích")
        like_count = dashboard.get("feedback_like_count", 0)
        dislike_count = dashboard.get("feedback_dislike_count", 0)
        feedback_rate = dashboard.get("feedback_rate")
        if feedback_rate is not None:
            st.metric("Tỷ lệ hữu ích", f"{feedback_rate * 100:.0f}%")
            st.plotly_chart(plotly_feedback_pie(like_count, dislike_count), width="stretch")
        else:
            st.info("Chưa có phản hồi 👍/👎 nào cho câu trả lời — bấm nút ở khung Chat để đánh giá.")

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
