"""Gemini API wrapper with simple error mapping and JSON parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from prompts import MODEL_NAME


class GeminiClientError(Exception):
    """Base error for Gemini client wrapper."""


class GeminiKeyMissingError(GeminiClientError):
    pass


class GeminiAuthError(GeminiClientError):
    pass


class GeminiQuotaError(GeminiClientError):
    pass


class GeminiNetworkError(GeminiClientError):
    pass


class GeminiResponseFormatError(GeminiClientError):
    pass


@dataclass
class GeminiClient:
    api_key: str

    def _build_client(self) -> Any:
        key = (self.api_key or "").strip()
        if not key:
            raise GeminiKeyMissingError("API key is required.")
        from google import genai

        return genai.Client(api_key=key)

    def validate_key(self) -> None:
        """Tiny generation call to verify key validity."""
        client = self._build_client()
        from google.genai import types

        try:
            client.models.generate_content(
                model=MODEL_NAME,
                contents="키 확인 테스트: ok 한 단어만 출력",
                config=types.GenerateContentConfig(max_output_tokens=8),
            )
        except Exception as exc:  # SDK error surface is provider-dependent
            raise _map_provider_error(exc) from exc

    def generate_json(self, prompt: str, retry_on_parse: bool = True) -> dict[str, Any]:
        """Generate and parse strict JSON response from Gemini."""
        client = self._build_client()
        from google.genai import types

        attempts = 2 if retry_on_parse else 1
        last_error: Exception | None = None

        for _ in range(attempts):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=400),
                )
                text = (response.text or "").strip()
                parsed = _parse_json_text(text)
                _validate_min_schema(parsed)
                return parsed
            except GeminiResponseFormatError as exc:
                last_error = exc
                continue
            except Exception as exc:
                raise _map_provider_error(exc) from exc

        assert last_error is not None
        raise last_error


def _parse_json_text(text: str) -> dict[str, Any]:
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.strip("`")
        clean = clean.replace("json", "", 1).strip()
    try:
        data = json.loads(clean)
        if not isinstance(data, dict):
            raise GeminiResponseFormatError("JSON object expected")
        return data
    except json.JSONDecodeError as exc:
        raise GeminiResponseFormatError("Invalid JSON format") from exc


def _validate_min_schema(data: dict[str, Any]) -> None:
    required = {
        "mode",
        "level",
        "interest",
        "question",
        "choices",
        "answer_index",
        "hint",
        "praise_correct",
        "explanation_teacher",
    }
    if not required.issubset(set(data.keys())):
        raise GeminiResponseFormatError("Missing required fields")


def _map_provider_error(exc: Exception) -> GeminiClientError:
    msg = str(exc).lower()
    if "api key" in msg or "permission" in msg or "unauth" in msg or "401" in msg or "403" in msg:
        return GeminiAuthError("Invalid or unauthorized API key")
    if "quota" in msg or "429" in msg or "rate" in msg:
        return GeminiQuotaError("Quota exceeded")
    if "timeout" in msg or "network" in msg or "connection" in msg or "dns" in msg:
        return GeminiNetworkError("Network error")
    return GeminiClientError(str(exc))


def self_check_missing_key() -> bool:
    """Self-check: missing key should raise GeminiKeyMissingError."""
    try:
        GeminiClient(api_key="").validate_key()
    except GeminiKeyMissingError:
        return True
    except Exception:
        return False
    return False


if __name__ == "__main__":
    ok = self_check_missing_key()
    print("gemini_client self-check:", "PASS" if ok else "FAIL")
