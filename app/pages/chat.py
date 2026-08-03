"""Chat AI -- trọng tâm của đồ án.

Full width, một cột duy nhất (đã bỏ panel "Ngữ cảnh tri thức" cột phải và
popover "Tuỳ chọn" -- xem cuối mục 2.3 của thiết kế v3). Nguồn tham khảo giờ
hiện inline dưới mỗi câu trả lời (tên file + trang + nút xem đoạn gốc), và
việc upload tài liệu có thể làm ngay tại đây (không cần rẽ sang trang Tài liệu).
"""

from __future__ import annotations

import json

import streamlit as st

from app.ui_helpers import (
    copy_button_html,
    get_api,
    require_course_selected,
    switch_to,
    user_id,
)

DEFAULT_TOP_K = 3
SUPPORTED_UPLOAD_TYPES = ["pdf", "docx", "txt"]


def _parse_history_sources(raw_sources: str | None) -> list[dict]:
    if not raw_sources:
        return []
    try:
        parsed = json.loads(raw_sources)
    except json.JSONDecodeError:
        return []
    return [s for s in parsed if isinstance(s, dict)] if isinstance(parsed, list) else []


def _ensure_thread(uid: int, course_id: int) -> str:
    st.session_state.setdefault("chat_threads", {})
    st.session_state.setdefault("chat_hydrated_keys", set())
    key = f"{uid}:{course_id}"

    if key not in st.session_state.chat_threads:
        st.session_state.chat_threads[key] = []

    if key not in st.session_state.chat_hydrated_keys:
        ok, payload, _ = get_api().get_chat_history(uid)
        if ok and isinstance(payload, list):
            rows = [r for r in payload if isinstance(r, dict) and int(r.get("course_id", 0)) == course_id]
            rows.sort(key=lambda r: str(r.get("created_at", "")))
            for row in rows:
                st.session_state.chat_threads[key].append({"role": "user", "content": row.get("question", "")})
                st.session_state.chat_threads[key].append(
                    {
                        "role": "assistant",
                        "chat_id": row.get("id"),
                        "content": row.get("answer", ""),
                        "topic": row.get("topic"),
                        "feedback": row.get("feedback"),
                        "sources": _parse_history_sources(row.get("sources")),
                    }
                )
        st.session_state.chat_hydrated_keys.add(key)

    return key


def _course_documents(api, course_id: int) -> list[dict]:
    _, payload, _ = api.list_documents()
    documents = [d for d in payload if isinstance(d, dict)] if isinstance(payload, list) else []
    return [d for d in documents if int(d.get("course_id", 0)) == course_id]


def _render_upload_widget(api, course_id: int, uid: int, expanded: bool) -> None:
    with st.expander("📎 Đính kèm tài liệu", expanded=expanded):
        files = st.file_uploader(
            "Kéo thả hoặc chọn tài liệu (PDF, DOCX, TXT) -- có thể chọn nhiều file:",
            type=SUPPORTED_UPLOAD_TYPES,
            accept_multiple_files=True,
            key=f"chat_uploader_{course_id}",
        )

        st.session_state.setdefault("chat_uploaded_keys", set())
        st.session_state.setdefault("chat_upload_results", {})
        results = st.session_state.chat_upload_results.setdefault(course_id, {})

        newly_uploaded = False
        for file in files or []:
            file_key = f"{course_id}:{file.name}:{file.size}"
            if file_key in st.session_state.chat_uploaded_keys:
                continue
            st.session_state.chat_uploaded_keys.add(file_key)
            newly_uploaded = True
            with st.spinner(f"Đang xử lý '{file.name}'..."):
                ok, payload, code = api.upload_document(
                    course_id, uid, file.name, file.getvalue(), file.type or "application/octet-stream"
                )
            if ok and isinstance(payload, dict):
                results[file.name] = {"status": "ok"}
            else:
                detail = payload.get("detail") if isinstance(payload, dict) else payload
                results[file.name] = {"status": "error", "detail": str(detail)}

        if newly_uploaded:
            st.rerun()

        for file_name, result in results.items():
            if result["status"] == "ok":
                st.caption(f"📄 {file_name} — ✅ Sẵn sàng")
            else:
                col_err, col_retry = st.columns([5, 1])
                col_err.caption(f"📄 {file_name} — ❌ Lỗi: {result['detail']}")
                if col_retry.button("🔁", key=f"retry_upload_{course_id}_{file_name}", help="Thử lại"):
                    _, docs_payload, _ = api.list_documents()
                    matches = [
                        d for d in (docs_payload if isinstance(docs_payload, list) else [])
                        if isinstance(d, dict) and d.get("file_name") == file_name
                        and int(d.get("course_id", 0)) == course_id
                    ]
                    if matches:
                        target = sorted(matches, key=lambda d: d.get("id", 0))[-1]
                        idx_ok, idx_payload, _ = api.retry_index(target["id"])
                        results[file_name] = {"status": "ok"} if idx_ok else {
                            "status": "error", "detail": str(idx_payload)
                        }
                        st.rerun()


def _cached_suggested_questions(api, course_id: int, indexed_doc_ids: tuple[int, ...]) -> list[str]:
    st.session_state.setdefault("chat_suggested_questions", {})
    cache = st.session_state.chat_suggested_questions
    cache_key = (course_id, indexed_doc_ids)
    if cache.get("key") == cache_key:
        return cache.get("questions", [])

    ok, payload, _ = api.get_suggested_questions(course_id)
    questions = payload.get("questions", []) if ok and isinstance(payload, dict) else []
    cache["key"] = cache_key
    cache["questions"] = questions
    return questions


def _render_weak_topic_banner(api, uid: int, course_id: int) -> str | None:
    dismiss_key = f"weak_banner_dismissed_{course_id}"
    if st.session_state.get(dismiss_key):
        return None

    ok, payload, _ = api.get_weak_topics(uid, course_id)
    weak_topics = [w for w in payload if isinstance(w, dict)] if ok and isinstance(payload, list) else []
    if not weak_topics:
        return None

    topic = weak_topics[0].get("topic", "")
    col_msg, col_ask, col_dismiss = st.columns([7, 2, 1])
    col_msg.warning(f"⚠️ Bạn đang yếu ở chủ đề **{topic}** — thử hỏi về chủ đề này?")
    preset = None
    if col_ask.button("Hỏi ngay", key=f"weak_ask_{course_id}", width="stretch"):
        preset = f"Giải thích chi tiết về {topic}"
    if col_dismiss.button("✕", key=f"weak_dismiss_{course_id}"):
        st.session_state[dismiss_key] = True
        st.rerun()
    return preset


def _render_action_bar(msg: dict) -> None:
    chat_id = msg.get("chat_id")
    if not chat_id:
        return  # message not saved yet (shouldn't happen for assistant turns)

    current = msg.get("feedback")
    col_copy, col_like, col_dislike, col_quiz, col_topic = st.columns([1, 1, 1, 1, 5])
    with col_copy:
        st.markdown(copy_button_html(msg.get("content", ""), key=str(chat_id)), unsafe_allow_html=True)
    with col_like:
        if st.button("👍" if current != "like" else "✅👍", key=f"like_{chat_id}", help="Câu trả lời hữu ích"):
            new_value = None if current == "like" else "like"
            ok, _, _ = get_api().set_chat_feedback(chat_id, new_value)
            if ok:
                msg["feedback"] = new_value
                st.rerun()
    with col_dislike:
        if st.button("👎" if current != "dislike" else "✅👎", key=f"dislike_{chat_id}", help="Câu trả lời chưa tốt"):
            new_value = None if current == "dislike" else "dislike"
            ok, _, _ = get_api().set_chat_feedback(chat_id, new_value)
            if ok:
                msg["feedback"] = new_value
                st.rerun()
    with col_quiz:
        if msg.get("topic") and st.button("📝", key=f"quiz_from_{chat_id}", help="Tạo Quiz ôn tập chủ đề này"):
            st.session_state["quiz_prefill_topic"] = msg["topic"]
            switch_to("Quiz")
    with col_topic:
        if msg.get("topic"):
            st.caption(f"📌 {msg['topic']}")

    sources = msg.get("sources") or []
    if sources:
        st.caption("📚 Nguồn tham khảo:")
        source_cols = st.columns(min(len(sources), 4))
        for idx, source in enumerate(sources):
            if not isinstance(source, dict):
                continue
            with source_cols[idx % len(source_cols)]:
                label = f"📄 {source.get('document_name', 'Tài liệu')} · tr.{source.get('page', '?')}"
                with st.popover(label, width="stretch"):
                    st.caption(f"\"{source.get('content', '')}\"")


def render() -> None:
    course = require_course_selected()
    uid = user_id()
    api = get_api()

    thread_key = _ensure_thread(uid, course["id"])
    thread = st.session_state.chat_threads[thread_key]
    course_documents = _course_documents(api, course["id"])
    indexed_doc_ids = tuple(sorted(int(d["id"]) for d in course_documents if d.get("status") == "indexed"))

    st.subheader(f"💬 Chat — {course['course_name']}")

    preset_prompt = None
    if not thread:
        if not course_documents:
            st.markdown(
                "<div style='text-align:center; padding: 12px 0 4px; color:#64748B;'>"
                "Kéo thả tài liệu vào đây để bắt đầu hỏi đáp về môn học này.</div>",
                unsafe_allow_html=True,
            )
            _render_upload_widget(api, course["id"], uid, expanded=True)
        else:
            _render_upload_widget(api, course["id"], uid, expanded=False)

        preset_prompt = _render_weak_topic_banner(api, uid, course["id"])

        if indexed_doc_ids:
            questions = _cached_suggested_questions(api, course["id"], indexed_doc_ids)
            if questions:
                st.caption("💡 Gợi ý câu hỏi dựa trên tài liệu của bạn:")
                cols = st.columns(len(questions))
                for idx, question in enumerate(questions):
                    if cols[idx].button(question, key=f"suggested_{idx}", width="stretch"):
                        preset_prompt = question
    else:
        _render_upload_widget(api, course["id"], uid, expanded=False)
        for msg in thread:
            avatar = "🧑‍🎓" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
                if msg["role"] == "assistant":
                    _render_action_bar(msg)

    typed_prompt = st.chat_input("Nhập câu hỏi của bạn...")
    question_to_send = preset_prompt or typed_prompt

    if question_to_send:
        thread.append({"role": "user", "content": question_to_send})
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(question_to_send)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔍 Đang truy xuất tài liệu & sinh câu trả lời..."):
                ok, payload, status_code = api.send_chat(uid, course["id"], question_to_send, DEFAULT_TOP_K, None)
            if ok and isinstance(payload, dict):
                assistant_msg = {
                    "role": "assistant",
                    "chat_id": payload.get("chat_id"),
                    "content": payload.get("answer", ""),
                    "topic": payload.get("topic"),
                    "feedback": None,
                    "sources": payload.get("sources", []),
                }
                st.markdown(assistant_msg["content"])
                _render_action_bar(assistant_msg)
                thread.append(assistant_msg)
            else:
                detail = payload.get("detail") if isinstance(payload, dict) else payload
                error_text = f"⚠️ Không lấy được câu trả lời: {detail}"
                st.error(error_text)
                thread.append({"role": "assistant", "content": error_text})
        st.rerun()
