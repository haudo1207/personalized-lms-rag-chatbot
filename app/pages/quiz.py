"""Quiz -- chấm điểm hoàn toàn ở server (mục backend/routers/quiz.py).

Client không bao giờ thấy correct_answer/explanation trước khi nộp bài --
/quiz/generate chỉ trả question+options, /quiz/submit nhận list lựa chọn và
trả về review (đúng/sai/đáp án đúng) sau khi đã chấm bằng answer_key lưu
server-side (QuizSession).
"""

from __future__ import annotations

from app.ui_helpers import DIFFICULTY_LABELS, get_api, require_course_selected, user_id

import streamlit as st


def render() -> None:
    course = require_course_selected()
    api = get_api()
    uid = user_id()

    st.subheader("📝 Tự động sinh Quiz ôn tập từ tài liệu")

    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        default_topic = st.session_state.pop("quiz_prefill_topic", None) or st.session_state.get(
            "last_quiz_topic", "SQL JOIN"
        )
        quiz_topic = st.text_input("Chủ đề ôn tập:", value=default_topic)
    with col_q2:
        quiz_difficulty = st.segmented_control(
            "Độ khó mong muốn:",
            options=list(DIFFICULTY_LABELS.keys()),
            format_func=lambda v: DIFFICULTY_LABELS[v],
            default="easy",
        )
    with col_q3:
        quiz_count = int(st.number_input("Số câu hỏi:", min_value=1, max_value=10, value=5, step=1))

    if st.button("🎯 Tạo bài Quiz mới", type="primary", width="stretch"):
        topic = quiz_topic.strip() or "SQL JOIN"
        with st.spinner("🤖 AI đang phân tích tài liệu và khởi tạo câu hỏi trắc nghiệm..."):
            ok, payload, status_code = api.generate_quiz(
                uid, course["id"], topic, quiz_count, quiz_difficulty or "easy"
            )

        if ok and isinstance(payload, dict) and "quiz_session_id" in payload:
            st.session_state.quiz_session_id = payload["quiz_session_id"]
            st.session_state.last_quiz = payload.get("quiz")
            st.session_state.last_quiz_topic = topic
            st.session_state.quiz_submitted = False
            st.session_state.quiz_review = None
            adaptive_diff = payload.get("adaptive_difficulty", "easy")
            st.success(f"🎉 Tạo Quiz thành công! (Độ khó thích ứng theo học lực: **{adaptive_diff.upper()}**)")
        elif ok and isinstance(payload, dict):
            # generate_quiz() found no usable context for this topic.
            st.session_state.last_quiz = None
            st.warning(payload.get("quiz", {}).get("raw_response", "Không tìm thấy nội dung phù hợp."))
        else:
            st.session_state.last_quiz = None
            st.error(f"Tạo Quiz thất bại (HTTP {status_code}): {payload}")

    quiz = st.session_state.get("last_quiz")
    if isinstance(quiz, list) and quiz and not st.session_state.get("quiz_submitted"):
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
                            key=f"q_{idx}_{st.session_state.get('quiz_session_id')}",
                            index=None,
                        )
                        selections[idx] = selected
                # Không hiện giải thích trước khi nộp bài -- sẽ lộ đáp án đúng.

            sub_quiz = st.form_submit_button("📥 Nộp bài Quiz", width="stretch", type="primary")

        if sub_quiz:
            answers = [
                (selections.get(idx)[:1] if selections.get(idx) else None) for idx in range(1, len(quiz) + 1)
            ]
            ok, payload, status_code = api.submit_quiz(
                uid, course["id"], st.session_state["quiz_session_id"], answers
            )
            if ok and isinstance(payload, dict):
                st.session_state.quiz_review = payload.get("review", [])
                st.session_state.quiz_score = payload.get("score", 0)
                st.session_state.quiz_submitted = True
                st.session_state.dashboard_key = None  # force dashboard/analytics refresh after a new attempt
                st.rerun()
            else:
                st.error(f"Nộp bài thất bại (HTTP {status_code}): {payload}")

    if st.session_state.get("quiz_submitted") and st.session_state.get("quiz_review"):
        review = st.session_state.quiz_review
        correct = sum(1 for r in review if r["is_correct"])
        total = len(review)
        score_pct = st.session_state.get("quiz_score", 0)

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
                if r.get("explanation"):
                    st.caption(f"💡 {r['explanation']}")

        if st.button("🔄 Làm bài Quiz mới", width="stretch"):
            st.session_state.last_quiz = None
            st.session_state.quiz_submitted = False
            st.session_state.quiz_review = None
            st.rerun()
