from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import google.generativeai as genai

from app.core.config import get_settings
from app.workers.domain_adapter import DomainAdapter, normalize_text

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "query_planner_prompt.txt"


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.replace("```json", "").replace("```", "").strip()
    return json.loads(stripped)


def _sanitize_terms(value: Any, limit: int = 20) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        normalized = normalize_text(str(item))
        if normalized and normalized not in cleaned:
            cleaned.append(normalized)
        if len(cleaned) >= limit:
            break
    return cleaned


def _fallback_plan(base_queries: list[str], adapter: DomainAdapter) -> dict[str, list[str]]:
    return {
        "queries": base_queries[:120],
        "required_terms": list(adapter.required_terms[:40]),
        "blocked_terms": list(adapter.blocked_terms[:80]),
        "preferred_domains": list(adapter.preferred_domains[:80]),
    }


def plan_query_bundle(
    *,
    topic: str,
    location: str | None,
    category: str | None,
    base_queries: list[str],
    adapter: DomainAdapter,
) -> dict[str, list[str]]:
    if not base_queries:
        return _fallback_plan(base_queries, adapter)

    settings = get_settings()
    if not settings.gemini_api_key or not PROMPT_PATH.exists():
        return _fallback_plan(base_queries, adapter)

    payload = {
        "topic": topic,
        "location": location,
        "category": category,
            "base_queries": base_queries[:120],
        "adapter_key": adapter.key,
            "adapter_required_terms": list(adapter.required_terms[:60]),
            "adapter_blocked_terms": list(adapter.blocked_terms[:120]),
            "adapter_preferred_domains": list(adapter.preferred_domains[:120]),
    }
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = (
        f"{system_prompt}\n\n"
        "Berikut konteks analisis:\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(prompt)
        parsed = _extract_json(response.text or "")
    except Exception:
        return _fallback_plan(base_queries, adapter)

    planned_queries = _sanitize_terms(parsed.get("queries"), limit=140)
    planned_required = _sanitize_terms(parsed.get("required_terms"), limit=80)
    planned_blocked = _sanitize_terms(parsed.get("blocked_terms"), limit=120)
    planned_domains = _sanitize_terms(parsed.get("preferred_domains"), limit=120)

    if not planned_queries:
        planned_queries = base_queries[:120]

    return {
        "queries": planned_queries,
        "required_terms": planned_required,
        "blocked_terms": planned_blocked,
        "preferred_domains": planned_domains,
    }
