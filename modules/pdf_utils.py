"""Utilities for reading uploaded files.

이미지(JPG/PNG)와 PDF는 Claude Vision API로 자동 OCR합니다.
API 키가 없는 mock mode에서는 안내 메시지를 반환합니다.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import BinaryIO


# ── PDF 텍스트 추출 (텍스트 레이어가 있는 PDF) ──────────────────────────

def _read_pdf_with_pypdf(file_obj: BinaryIO) -> str:
    from pypdf import PdfReader
    reader = PdfReader(file_obj)
    chunks: list[str] = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            chunks.append("")
    return "\n".join(chunks).strip()


def _read_pdf_with_fitz(file_bytes: bytes) -> str:
    import fitz
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        temp_path = tmp.name
    try:
        doc = fitz.open(temp_path)
        return "\n".join(page.get_text("text") for page in doc).strip()
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass


# ── PDF → 이미지 변환 (스캔 PDF 대응) ───────────────────────────────────

def _pdf_to_images(file_bytes: bytes, max_pages: int = 6) -> list[bytes]:
    """PDF 각 페이지를 PNG 바이트 리스트로 변환. fitz(PyMuPDF) 사용."""
    try:
        import fitz
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            temp_path = tmp.name
        try:
            doc = fitz.open(temp_path)
            images: list[bytes] = []
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                mat = fitz.Matrix(1.5, 1.5)  # 1.5x 배율 → 적당한 해상도
                pix = page.get_pixmap(matrix=mat)
                images.append(pix.tobytes("png"))
            return images
        finally:
            Path(temp_path).unlink(missing_ok=True)
    except Exception:
        return []


# ── OpenAI Vision OCR ────────────────────────────────────────────────────

def _vision_ocr(image_bytes: bytes, media_type: str = "image/png") -> str:
    """OpenAI Vision API로 이미지에서 텍스트를 추출합니다."""
    import os
    from openai import OpenAI

    from modules.llm_client import _get_secret
    api_key = _get_secret("OPENAI_API_KEY")
    if not api_key:
        return ""

    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=_get_secret("OPENAI_MODEL") or "gpt-4o-mini",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{b64}",
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "이 이미지는 그림책의 스캔 또는 사진입니다. "
                                "이미지에 있는 모든 텍스트(한국어·영어 포함)를 빠짐없이 추출해 주세요. "
                                "그림 설명은 하지 말고 텍스트만 줄바꿈 포함해서 원문 그대로 출력하세요."
                            ),
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip() if response.choices else ""
    except Exception as e:
        return f"[Vision OCR 오류: {e}]"


def _has_vision_api() -> bool:
    from modules.llm_client import _get_secret
    return bool(_get_secret("OPENAI_API_KEY"))


# ── 공개 인터페이스 ──────────────────────────────────────────────────────

def extract_text_from_upload(uploaded_file) -> tuple[str, str]:
    """
    업로드 파일에서 텍스트를 추출합니다.

    Returns
    -------
    (text, status_message)
      text           : 추출된 텍스트 (없으면 빈 문자열)
      status_message : UI에 표시할 처리 결과 메시지
    """
    if uploaded_file is None:
        return "", ""

    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    # ── TXT / MD ──
    if name.endswith((".txt", ".md")):
        for enc in ("utf-8", "cp949", "euc-kr"):
            try:
                text = data.decode(enc).strip()
                return text, f"✅ 텍스트 파일에서 {len(text):,}자를 읽었습니다."
            except UnicodeDecodeError:
                continue
        text = data.decode("utf-8", errors="ignore").strip()
        return text, f"✅ 텍스트 파일에서 {len(text):,}자를 읽었습니다."

    # ── PDF ──
    if name.endswith(".pdf"):
        # 1단계: 텍스트 레이어 추출 시도
        try:
            uploaded_file.seek(0)
            text = _read_pdf_with_pypdf(uploaded_file)
            if len(text.strip()) > 100:
                return text, f"✅ PDF 텍스트 레이어에서 {len(text):,}자를 추출했습니다."
        except Exception:
            pass
        try:
            text = _read_pdf_with_fitz(data)
            if len(text.strip()) > 100:
                return text, f"✅ PDF에서 {len(text):,}자를 추출했습니다."
        except Exception:
            pass

        # 2단계: 스캔 PDF → 이미지 변환 후 Vision OCR
        if _has_vision_api():
            images = _pdf_to_images(data, max_pages=6)
            if images:
                all_text: list[str] = []
                for i, img_bytes in enumerate(images):
                    page_text = _vision_ocr(img_bytes, "image/png")
                    if page_text and not page_text.startswith("[Vision OCR 오류"):
                        all_text.append(f"[{i+1}페이지]\n{page_text}")
                combined = "\n\n".join(all_text)
                if combined.strip():
                    return combined, f"✅ 스캔 PDF {len(images)}페이지를 Vision OCR로 추출했습니다. ({len(combined):,}자)"
            return "", "⚠️ PDF에서 텍스트를 추출하지 못했습니다. OCR 텍스트를 직접 붙여넣어 주세요."
        else:
            return "", (
                "⚠️ 스캔 PDF입니다. OPENAI_API_KEY를 설정하면 자동 OCR이 가능합니다. "
                "지금은 OCR 텍스트를 직접 붙여넣어 주세요."
            )

    # ── JPG / PNG ──
    if name.endswith((".jpg", ".jpeg", ".png")):
        if _has_vision_api():
            media_type = "image/jpeg" if name.endswith((".jpg", ".jpeg")) else "image/png"
            text = _vision_ocr(data, media_type)
            if text and not text.startswith("[Vision OCR 오류"):
                return text, f"✅ 이미지 Vision OCR 완료. {len(text):,}자를 추출했습니다."
            else:
                return "", f"⚠️ OCR 결과가 없습니다. 이미지 품질을 확인하거나 텍스트를 직접 붙여넣어 주세요."
        else:
            return "", (
                "⚠️ OPENAI_API_KEY를 설정하면 이미지를 자동 OCR합니다. "
                "지금은 vFlat SCAN 등에서 추출한 텍스트를 직접 붙여넣어 주세요."
            )

    return "", "지원하지 않는 파일 형식입니다. PDF, TXT, JPG, PNG 파일을 사용해 주세요."


def trim_text_for_prompt(text: str, max_chars: int = 6000) -> str:
    """저작권 보호와 토큰 절약을 위해 프롬프트용 텍스트를 자릅니다."""
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n\n[중간 원문 생략: 저작권 보호와 토큰 절약을 위해 일부만 분석에 사용]\n\n" + tail
