from __future__ import annotations

from typing import Any

import streamlit as st

from gemini_client import (
    GeminiAuthError,
    GeminiClient,
    GeminiClientError,
    GeminiKeyMissingError,
    GeminiNetworkError,
    GeminiQuotaError,
    GeminiResponseFormatError,
)
from prompts import (
    ALLOWED_INTERESTS,
    ALLOWED_LEVELS,
    ALLOWED_MODES,
    INTEREST_NONE,
    LEVEL_EASY,
    LEVEL_NORMAL,
    LEVEL_VERY_EASY,
    MODE_MATH,
    MODE_READING,
    MODE_VOCAB,
    PromptContext,
    build_generation_prompt,
)
from ui_components import (
    error_text,
    info_text,
    inject_accessibility_styles,
    progress_box,
    section_title,
    success_text,
)

MAX_INPUT_LEN = 200

MODE_LABELS = {
    MODE_VOCAB: "어휘 학습",
    MODE_READING: "짧은 문장 읽기",
    MODE_MATH: "기초 수학",
}
LEVEL_LABELS = {
    LEVEL_VERY_EASY: "매우 쉬움",
    LEVEL_EASY: "쉬움",
    LEVEL_NORMAL: "보통",
}
INTEREST_LABELS = {
    "animals": "동물",
    "food": "음식",
    "school": "학교",
    "family": "가족",
    "traffic": "교통",
    "none": "선택 안 함",
}


def init_state() -> None:
    defaults: dict[str, Any] = {
        "api_key": "",
        "api_ok": False,
        "persist_notice": False,
        "mode": MODE_VOCAB,
        "difficulty": LEVEL_VERY_EASY,
        "interest": INTEREST_NONE,
        "emoji_on": False,
        "reading_level": LEVEL_VERY_EASY,
        "question_data": None,
        "selected_choice": None,
        "feedback": "",
        "correct_count": 0,
        "attempt_count": 0,
        "mode_progress": {MODE_VOCAB: 0, MODE_READING: 0, MODE_MATH: 0},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clamp_text(value: str, max_len: int = MAX_INPUT_LEN) -> str:
    return (value or "").strip()[:max_len]


def easier_level(level: str) -> str:
    if level == LEVEL_NORMAL:
        return LEVEL_EASY
    if level == LEVEL_EASY:
        return LEVEL_VERY_EASY
    return LEVEL_VERY_EASY


def map_error_to_message(exc: Exception) -> str:
    if isinstance(exc, GeminiKeyMissingError):
        return "키를 먼저 입력해 주세요."
    if isinstance(exc, GeminiAuthError):
        return "키가 맞지 않아요. 다시 확인해 주세요."
    if isinstance(exc, GeminiQuotaError):
        return "사용량이 잠시 많아요. 조금 뒤에 다시 해요."
    if isinstance(exc, GeminiNetworkError):
        return "인터넷 연결이 불안정해요. 다시 시도해 주세요."
    return "문제를 만드는 중 오류가 났어요. 다시 해 볼까요?"


def get_client() -> GeminiClient:
    return GeminiClient(api_key=st.session_state.api_key)


def request_new_question() -> None:
    context = PromptContext(
        mode=st.session_state.mode,
        level=st.session_state.difficulty,
        interest=st.session_state.interest,
        reading_level=st.session_state.reading_level,
        emoji_on=st.session_state.emoji_on,
    )
    prompt = build_generation_prompt(context)
    client = get_client()
    try:
        data = client.generate_json(prompt=prompt, retry_on_parse=True)
    except GeminiResponseFormatError:
        info_text("문제를 다시 만들게요.")
        st.session_state.question_data = None
        return
    except GeminiClientError as exc:
        error_text(map_error_to_message(exc))
        st.session_state.question_data = None
        return

    if not _basic_question_guard(data):
        info_text("문제를 다시 만들게요.")
        st.session_state.question_data = None
        return

    st.session_state.question_data = data
    st.session_state.selected_choice = None
    st.session_state.feedback = ""


def _basic_question_guard(data: dict[str, Any]) -> bool:
    mode = data.get("mode")
    level = data.get("level")
    interest = data.get("interest")
    choices = data.get("choices")
    answer_index = data.get("answer_index")

    if mode not in ALLOWED_MODES:
        return False
    if level not in ALLOWED_LEVELS:
        return False
    if interest not in ALLOWED_INTERESTS:
        return False
    if not isinstance(choices, list) or not (2 <= len(choices) <= 4):
        return False
    if not isinstance(answer_index, int) or not (0 <= answer_index < len(choices)):
        return False
    return True


def render_api_section() -> None:
    section_title("1) Gemini 연결")
    st.text_input(
        "Gemini API Key",
        key="api_key_input",
        type="password",
        help="키는 기본 저장되지 않아요.",
    )
    st.checkbox("이 브라우저에 저장하기(세션 유지)", key="persist_notice")
    if st.session_state.persist_notice:
        info_text("브라우저를 닫으면 키가 사라져요.")

    if st.button("연결 테스트"):
        st.session_state.api_key = clamp_text(st.session_state.api_key_input)
        try:
            get_client().validate_key()
            st.session_state.api_ok = True
            success_text("연결이 되었어요!")
        except GeminiClientError as exc:
            st.session_state.api_ok = False
            error_text(map_error_to_message(exc))


def render_settings() -> None:
    section_title("2) 학습 설정")
    st.selectbox("학습 모드", options=list(MODE_LABELS.keys()), format_func=lambda x: MODE_LABELS[x], key="mode")
    st.selectbox(
        "난이도",
        options=[LEVEL_VERY_EASY, LEVEL_EASY, LEVEL_NORMAL],
        format_func=lambda x: LEVEL_LABELS[x],
        key="difficulty",
    )
    st.selectbox(
        "관심사 (선택)",
        options=list(INTEREST_LABELS.keys()),
        format_func=lambda x: INTEREST_LABELS[x],
        key="interest",
    )
    st.toggle("이모지 사용", key="emoji_on")
    st.selectbox(
        "읽기 수준",
        options=[LEVEL_VERY_EASY, LEVEL_EASY, LEVEL_NORMAL],
        format_func=lambda x: LEVEL_LABELS[x],
        key="reading_level",
    )


def evaluate_answer(choice_index: int) -> None:
    data = st.session_state.question_data
    st.session_state.attempt_count += 1
    if choice_index == data["answer_index"]:
        st.session_state.correct_count += 1
        st.session_state.mode_progress[st.session_state.mode] += 1
        st.session_state.feedback = data.get("praise_correct", "잘했어요!")
    else:
        hint = data.get("hint", "힌트를 보고 다시 해 봐요.")
        st.session_state.feedback = f"괜찮아요! 같이 한 번 더 해 볼까요?\n힌트: {hint}"


def render_question_area() -> None:
    section_title("3) 학습")
    if st.session_state.question_data is None:
        if st.button("문제 만들기"):
            request_new_question()
        return

    data = st.session_state.question_data
    st.markdown(f"### 문제\n{data['question']}")

    selected = st.radio("정답을 골라요", options=range(len(data["choices"])), format_func=lambda i: data["choices"][i], index=None)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("정답 확인"):
            if selected is None:
                info_text("보기 하나를 선택해 주세요.")
            else:
                evaluate_answer(selected)
    with col2:
        if st.button("다시 풀기"):
            st.session_state.feedback = "다시 천천히 풀어봐요."

    if st.session_state.feedback:
        if "괜찮아요" in st.session_state.feedback:
            info_text(st.session_state.feedback)
        else:
            success_text(st.session_state.feedback)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("다음 문제"):
            request_new_question()
    with c2:
        if st.button("더 쉽게"):
            st.session_state.difficulty = easier_level(st.session_state.difficulty)
            info_text("난이도를 낮췄어요.")
            request_new_question()

    with st.expander("교사용 해설 보기"):
        st.write(data.get("explanation_teacher", ""))


def main() -> None:
    st.set_page_config(page_title="쉬운 학습 도우미", page_icon="📘", layout="centered")
    inject_accessibility_styles()
    init_state()

    st.title("지적발달장애 학습자를 위한 쉬운 학습")
    st.caption("한 번에 한 문제씩, 천천히 함께 해요.")

    render_api_section()

    if not st.session_state.api_ok:
        info_text("먼저 연결 테스트를 해 주세요.")
        return

    render_settings()
    progress_box(
        correct_count=st.session_state.correct_count,
        attempts=st.session_state.attempt_count,
        solved_in_mode=st.session_state.mode_progress[st.session_state.mode],
    )
    render_question_area()


if __name__ == "__main__":
    main()
