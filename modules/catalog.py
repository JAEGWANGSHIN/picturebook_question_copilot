"""Picturebook catalog helpers."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CATALOG_PATH = DATA_DIR / "picturebook_catalog.json"
METHODOLOGY_PATH = DATA_DIR / "methodology_summary.json"


@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_methodology() -> dict[str, Any]:
    with METHODOLOGY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_titles() -> list[str]:
    return [book.get("title", "") for book in load_catalog()]


def find_book(title: str) -> dict[str, Any] | None:
    normalized = (title or "").strip()
    for book in load_catalog():
        if book.get("title") == normalized:
            return book
    return None


def catalog_to_dataframe_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for b in load_catalog():
        records.append(
            {
                "그림책 제목": b.get("title", ""),
                "적합 학년": b.get("recommended_grade_band", ""),
                "핵심 주제": ", ".join(b.get("main_themes", [])),
                "정서 키워드": ", ".join(b.get("emotion_keywords", [])),
                "추천 근거": b.get("source", ""),
            }
        )
    return records
