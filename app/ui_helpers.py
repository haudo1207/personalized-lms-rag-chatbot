"""Shared session-state accessors and small render helpers used across pages.

Kept deliberately thin: pages call get_api()/current_user()/selected_course()
to read shared context, and call the render_* helpers for the handful of
UI snippets (source card, status badge) reused in more than one page.
"""

from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

from app.api_client import ApiClient

# Deliberately not exposed as a UI input (esp. not on the pre-auth login
# screen): pointing an unauthenticated login form at an attacker-controlled
# backend is a credential-harvesting risk. Deploy-time config only.
DEFAULT_API_URL = os.environ.get("RAG_API_URL", "http://127.0.0.1:8000")
PRIMARY = "#2563EB"
SECONDARY = "#3B82F6"

LEVEL_LABELS = {"beginner": "Mới bắt đầu", "intermediate": "Trung bình", "advanced": "Nâng cao"}
DIFFICULTY_LABELS = {"easy": "Dễ", "medium": "Trung bình", "hard": "Khó"}


def get_api() -> ApiClient:
    base_url = str(st.session_state.get("api_url", DEFAULT_API_URL)).rstrip("/")
    return ApiClient(base_url, st.session_state.get("access_token"))


def current_user() -> dict[str, Any]:
    return st.session_state.get("current_user") or {}


def is_admin() -> bool:
    return current_user().get("role") == "admin"


def user_id() -> int:
    return int(current_user()["id"])


def selected_course() -> dict[str, Any] | None:
    return st.session_state.get("selected_course")


def require_course_selected() -> dict[str, Any]:
    """Call at the top of any workspace page. Stops the script with a
    friendly prompt if the user hasn't entered a course from Trang chủ yet."""
    course = selected_course()
    if not course:
        st.warning("👈 Bạn chưa chọn môn học nào. Vào **Trang chủ** để chọn hoặc tạo môn học.")
        st.stop()
    return course


def switch_to(page_key: str) -> None:
    """Programmatic navigation -- pages are registered in st.session_state['_pages']
    by the entrypoint (app/streamlit_app.py) right after st.navigation() builds them."""
    pages = st.session_state.get("_pages", {})
    target = pages.get(page_key)
    if target is not None:
        st.switch_page(target)


def show_api_error(action: str, payload: Any, status_code: int | None) -> None:
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


def copy_button_html(text: str, key: str) -> str:
    """One-click copy-to-clipboard, no extra component dependency: a plain
    HTML button whose onclick calls navigator.clipboard.writeText() directly.
    The text is embedded via json.dumps so quotes/newlines/backticks in the
    answer can't break out of the JS string literal."""
    payload = json.dumps(text)
    return f"""
    <button class="ghost-action-btn" id="copy-btn-{key}" onclick="
        navigator.clipboard.writeText({payload});
        var b = document.getElementById('copy-btn-{key}');
        var original = b.innerText;
        b.innerText = '✅ Đã copy';
        setTimeout(function() {{ b.innerText = original; }}, 1500);
    ">\U0001F4CB Copy</button>
    """


def inject_global_css() -> None:
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

        .ghost-action-btn {{
            background: transparent;
            border: none;
            color: #64748B;
            font-size: 0.82rem;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 8px;
            cursor: pointer;
        }}
        .ghost-action-btn:hover {{
            background: #F1F5F9;
            color: {PRIMARY};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def plotly_feedback_pie(like_count: int, dislike_count: int):
    df = pd.DataFrame({"label": ["Hữu ích 👍", "Chưa hữu ích 👎"], "count": [like_count, dislike_count]})
    fig = px.pie(df, names="label", values="count", color_discrete_sequence=[PRIMARY, "#F87171"], hole=0.55)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=240)
    return fig


def compute_questions_per_day(user_id_: int, course_id: int) -> pd.DataFrame:
    ok, payload, _ = get_api().get_chat_history(user_id_)
    if not (ok and isinstance(payload, list)):
        return pd.DataFrame(columns=["date", "count"])
    rows = [r for r in payload if isinstance(r, dict) and int(r.get("course_id", 0)) == course_id]
    if not rows:
        return pd.DataFrame(columns=["date", "count"])
    dates = [str(r.get("created_at", ""))[:10] for r in rows]
    counts = pd.Series(dates).value_counts().sort_index()
    return pd.DataFrame({"date": counts.index, "count": counts.values})
