"""Utilities for reading uploaded files.

Images are accepted for MVP workflow, but OCR is intentionally not mandatory.
Teachers can paste vFlat OCR text into the text area.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import BinaryIO, Optional


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


def extract_text_from_upload(uploaded_file) -> str:
    """Extract text from PDF/TXT uploads. Images return an OCR 안내문."""
    if uploaded_file is None:
        return ""

    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()

    if name.endswith(".txt") or name.endswith(".md"):
        for enc in ("utf-8", "cp949", "euc-kr"):
            try:
                return data.decode(enc).strip()
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="ignore").strip()

    if name.endswith(".pdf"):
        try:
            uploaded_file.seek(0)
            text = _read_pdf_with_pypdf(uploaded_file)
            if text:
                return text
        except Exception:
            pass
        try:
            return _read_pdf_with_fitz(data)
        except Exception:
            return ""

    if name.endswith((".jpg", ".jpeg", ".png")):
        return (
            "[이미지 파일이 업로드되었습니다. MVP에서는 이미지 OCR을 자동 수행하지 않습니다.]\n"
            "vFlat SCAN에서 추출한 OCR 텍스트를 아래 입력창에 붙여넣어 주세요."
        )

    return "지원하지 않는 파일 형식입니다. PDF, TXT, JPG, PNG 파일 또는 OCR 텍스트를 사용해 주세요."


def trim_text_for_prompt(text: str, max_chars: int = 6000) -> str:
    """Keep prompts small and avoid reproducing long copyrighted text."""
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n\n[중간 원문 생략: 저작권 보호와 토큰 절약을 위해 일부만 분석에 사용]\n\n" + tail
