"""Prompt templates for generating learner-friendly questions."""

from __future__ import annotations

from dataclasses import dataclass

MODEL_NAME = "gemini-3-flash-preview"

MODE_VOCAB = "vocab"
MODE_READING = "reading"
MODE_MATH = "math"

LEVEL_VERY_EASY = "very_easy"
LEVEL_EASY = "easy"
LEVEL_NORMAL = "normal"

INTEREST_NONE = "none"

ALLOWED_MODES = {MODE_VOCAB, MODE_READING, MODE_MATH}
ALLOWED_LEVELS = {LEVEL_VERY_EASY, LEVEL_EASY, LEVEL_NORMAL}
ALLOWED_INTERESTS = {"animals", "food", "school", "family", "traffic", INTEREST_NONE}

JSON_SCHEMA_TEXT = """
반드시 아래 JSON 형태만 출력하세요. 코드블록(```) 없이 JSON 객체만 출력하세요.
{
  "mode": "vocab|reading|math",
  "level": "very_easy|easy|normal",
  "interest": "animals|food|school|family|traffic|none",
  "question": "학습자에게 보여줄 질문(짧게)",
  "choices": ["보기1","보기2","보기3"],
  "answer_index": 0,
  "hint": "오답 시 보여줄 아주 쉬운 힌트(짧게)",
  "praise_correct": "정답 시 칭찬(짧게)",
  "explanation_teacher": "교사용 짧은 해설"
}
""".strip()


@dataclass(frozen=True)
class PromptContext:
    mode: str
    level: str
    interest: str
    reading_level: str
    emoji_on: bool


def _mode_guide(mode: str) -> str:
    if mode == MODE_VOCAB:
        return "생활 어휘 중심의 문제 1개를 만드세요. 짧은 명사 위주 선택지 2~3개를 사용하세요."
    if mode == MODE_READING:
        return "아주 짧은 한두 문장 지문 + 질문 1개 형식으로 만드세요. 선택지 2~3개를 사용하세요."
    return "한 자리 덧셈 또는 뺄셈 문제 1개를 만드세요. 계산이 아주 쉬워야 합니다."


def build_generation_prompt(context: PromptContext) -> str:
    """Return system-style Korean instruction for a single question JSON."""
    emoji_text = "이모지 사용 가능" if context.emoji_on else "이모지 사용 금지"
    prompt = f"""
너는 지적발달장애 학습자를 돕는 따뜻한 한국어 학습 도우미야.
목표: 한 번에 한 문제만 제시하고, 아주 쉬운 문장으로 안내해.

안전 규칙:
- 개인정보(이름/연락처/주소/계정) 요청 금지
- 폭력/성/자해/혐오 조장 내용 금지
- 의료/법률 조언 금지

작성 규칙:
- 모드: {context.mode}
- 난이도: {context.level}
- 관심사: {context.interest}
- 읽기 수준: {context.reading_level}
- 표현 옵션: {emoji_text}
- 학습자 문장은 초등 저학년 수준의 한국어로 매우 짧게 작성
- 보기 개수는 기본 3개, 필요 시 2개 또는 4개 허용
- 정답은 choices 범위 안 index로 작성
- hint는 매우 짧고 쉬워야 함
- praise_correct는 짧고 따뜻하게 작성
- 오답을 비난하지 말 것

모드 세부 규칙:
{_mode_guide(context.mode)}

{JSON_SCHEMA_TEXT}
""".strip()
    return prompt


def self_check_prompt_schema() -> bool:
    """Lightweight self-check for required schema hints in prompt template."""
    sample = build_generation_prompt(
        PromptContext(
            mode=MODE_VOCAB,
            level=LEVEL_VERY_EASY,
            interest=INTEREST_NONE,
            reading_level=LEVEL_VERY_EASY,
            emoji_on=False,
        )
    )
    required_keys = [
        '"mode"',
        '"level"',
        '"interest"',
        '"question"',
        '"choices"',
        '"answer_index"',
        '"hint"',
        '"praise_correct"',
        '"explanation_teacher"',
    ]
    return all(key in sample for key in required_keys)


if __name__ == "__main__":
    ok = self_check_prompt_schema()
    print("prompts self-check:", "PASS" if ok else "FAIL")
