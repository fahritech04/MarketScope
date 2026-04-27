from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

import google.generativeai as genai

from app.core.config import get_settings

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "insight_prompt.txt"


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _default_insight() -> dict[str, Any]:
    return {
        "summary": "Data belum cukup untuk menarik kesimpulan pasar yang kuat.",
        "opportunities": ["Perlu menambah sumber data publik agar insight lebih akurat."],
        "competitors": [],
        "pricing_insight": "Belum ada cukup informasi harga dari sumber yang berhasil di-scrape.",
        "customer_pain_points": ["Belum ada sinyal kuat dari review pelanggan."],
        "strategy_recommendations": [
            "Tambah jumlah sumber scraping untuk topik ini.",
            "Fokus pada sumber dengan data harga dan review yang lebih lengkap.",
        ],
    }


def _build_summary_payload(topic: str, location: str | None, category: str | None, items: list[dict[str, Any]]) -> dict[str, Any]:
    prices = [float(item["price_min"]) for item in items if item.get("price_min") is not None]
    ratings = [float(item["rating"]) for item in items if item.get("rating") is not None]
    sample_items = [
        {
            "name": item.get("name"),
            "address": item.get("address"),
            "price_text": item.get("price_text"),
            "rating": item.get("rating"),
            "review_count": item.get("review_count"),
            "description": item.get("description"),
            "source_url": (item.get("metadata") or {}).get("url"),
        }
        for item in items[:20]
    ]

    return {
        "topic": topic,
        "location": location,
        "category": category,
        "total_items": len(items),
        "average_price_min": round(mean(prices), 2) if prices else None,
        "average_rating": round(mean(ratings), 2) if ratings else None,
        "sample_items": sample_items,
    }


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.replace("```json", "").replace("```", "").strip()
    return json.loads(stripped)


def generate_insight(
    topic: str,
    location: str | None,
    category: str | None,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    if not items:
        return _default_insight()

    if not PROMPT_PATH.exists():
        return _default_insight()

    settings = get_settings()
    if not settings.gemini_api_key:
        return _default_insight()

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    payload = _build_summary_payload(topic, location, category, items)

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-flash-latest")
        prompt = (
            f"{system_prompt}\n\n"
            "Berikut data ringkas hasil scraping:\n"
            f"{json.dumps(payload, ensure_ascii=False)}"
        )
        response = model.generate_content(prompt)
        text = response.text or ""
        parsed = _extract_json(text)
    except Exception:
        return _default_insight()

    return {
        "summary": str(parsed.get("summary", "")),
        "opportunities": _safe_list(parsed.get("opportunities")),
        "competitors": _safe_list(parsed.get("competitors")),
        "pricing_insight": str(parsed.get("pricing_insight", "")),
        "customer_pain_points": _safe_list(parsed.get("customer_pain_points")),
        "strategy_recommendations": _safe_list(parsed.get("strategy_recommendations")),
    }
