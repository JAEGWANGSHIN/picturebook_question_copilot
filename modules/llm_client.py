"""LLM client abstraction.

The app must run in mock mode without an API key.  When a real provider is
configured, only this file needs to be changed or extended.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """
    환경변수 → Streamlit Secrets 순서로 값을 읽습니다.
    Streamlit Cloud 배포 시 st.secrets에서 자동으로 읽습니다.
    """
    # 1순위: 일반 환경변수 (.env 또는 OS 환경변수)
    val = os.getenv(key, "").strip()
    if val:
        return val
    # 2순위: Streamlit Secrets (Streamlit Cloud 배포 시)
    try:
        import streamlit as st
        val = st.secrets.get(key, default)
        return str(val).strip() if val else default
    except Exception:
        return default


def get_provider() -> str:
    """Return configured provider name."""
    return _get_secret("LLM_PROVIDER", "mock").lower() or "mock"


def is_mock_mode() -> bool:
    """True when the app should not call an external LLM API."""
    provider = get_provider()
    if provider == "mock":
        return True
    if provider == "openai" and not _get_secret("OPENAI_API_KEY"):
        return True
    return False


def _mock_generate(prompt: str) -> str:
    """A deterministic fallback for demos and offline testing."""
    prompt_preview = prompt[:220].replace("\n", " ")
    return (
        "[MOCK MODE] API 키 없이 실행 중입니다. "
        "앱은 내부 점수화, 규칙 기반 질문 생성, 정서 안전 규칙으로 결과를 만들었습니다.\n\n"
        f"프롬프트 미리보기: {prompt_preview}..."
    )


def generate_text(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Generate text using the configured LLM provider."""
    if is_mock_mode():
        return _mock_generate(prompt)

    provider = get_provider()
    temperature = float(_get_secret("LLM_TEMPERATURE", "0.2"))

    if provider == "openai":
        api_key = _get_secret("OPENAI_API_KEY")
        model = _get_secret("OPENAI_MODEL") or "gpt-4o-mini"
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            try:
                response = client.responses.create(
                    model=model,
                    input=(system_prompt + "\n\n" + prompt) if system_prompt else prompt,
                    temperature=temperature,
                )
                return getattr(response, "output_text", "") or str(response)
            except Exception:
                response = client.chat.completions.create(
                    model=model,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt or "You are a helpful educational assistant."},
                        {"role": "user", "content": prompt},
                    ],
                )
                return response.choices[0].message.content or ""
        except Exception as exc:
            return (
                "[LLM ERROR - FALLBACK]\n"
                f"외부 LLM 호출 중 오류가 발생했습니다: {exc}\n"
                "mock mode 결과로 계속 진행하세요."
            )

    return _mock_generate(prompt)
