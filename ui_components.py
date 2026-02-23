"""Reusable Streamlit UI components for accessibility-first screens."""

from __future__ import annotations

import streamlit as st


def inject_accessibility_styles() -> None:
    st.markdown(
        """
        <style>
        html, body, [class*="css"]  {font-size: 22px !important;}
        .stButton button {
            font-size: 24px !important;
            padding: 0.8rem 1rem !important;
            border-radius: 14px !important;
            width: 100%;
        }
        .big-card {
            border: 2px solid #d9e8ff;
            border-radius: 16px;
            padding: 16px;
            margin: 8px 0;
            background: #f8fbff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(f"## {text}")


def progress_box(correct_count: int, attempts: int, solved_in_mode: int) -> None:
    st.markdown("### 오늘의 기록")
    st.markdown(
        f"""
<div class="big-card">
✅ 맞힌 문제: <b>{correct_count}</b><br/>
🔁 시도 횟수: <b>{attempts}</b><br/>
📘 현재 모드 진행: <b>{solved_in_mode}</b>
</div>
""",
        unsafe_allow_html=True,
    )


def info_text(message: str) -> None:
    st.info(message)


def success_text(message: str) -> None:
    st.success(message)


def error_text(message: str) -> None:
    st.error(message)
