from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.utils.data_utils import sanitize_recursive, utc_now_iso


def _empty_store() -> dict[str, list[Any]]:
    return {
        "analyses": [],
        "sources": [],
        "scraped_items": [],
        "insights": [],
        "discovery_profiles": [],
    }


class LocalAnalysisRepository:
    def __init__(self, store_path: Path):
        self.store_path = store_path
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self._save(_empty_store())

    def _load(self) -> dict[str, Any]:
        with self.store_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def _save(self, data: dict[str, Any]) -> None:
        with self.store_path.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)

    @staticmethod
    def _build_source_record(item: dict[str, Any]) -> dict[str, Any]:
        return sanitize_recursive(
            {
                "id": str(uuid4()),
                "analysis_id": item["analysis_id"],
                "url": item["url"],
                "title": item.get("title"),
                "source_type": item.get("source_type", "web"),
                "status": item.get("status", "pending"),
                "created_at": item.get("created_at", utc_now_iso()),
            }
        )

    @staticmethod
    def _build_scraped_item_record(item: dict[str, Any], analysis_id: str | None = None) -> dict[str, Any]:
        return sanitize_recursive(
            {
                "id": str(uuid4()),
                "analysis_id": analysis_id or item["analysis_id"],
                "source_id": item.get("source_id"),
                "name": item.get("name"),
                "description": item.get("description"),
                "address": item.get("address"),
                "price_text": item.get("price_text"),
                "price_min": item.get("price_min"),
                "price_max": item.get("price_max"),
                "rating": item.get("rating"),
                "review_count": item.get("review_count"),
                "raw_text": item.get("raw_text"),
                "metadata": item.get("metadata") or {},
                "created_at": item.get("created_at", utc_now_iso()),
            }
        )

    def create_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._load()
        now = utc_now_iso()
        analysis = {
            "id": str(uuid4()),
            "topic": payload.get("topic"),
            "location": payload.get("location"),
            "category": payload.get("category"),
            "status": payload.get("status", "pending"),
            "created_at": payload.get("created_at", now),
            "updated_at": payload.get("updated_at", now),
        }
        data["analyses"].append(analysis)
        self._save(data)
        return analysis

    def list_analyses(self) -> list[dict[str, Any]]:
        data = self._load()
        return sorted(data["analyses"], key=lambda item: item["created_at"], reverse=True)

    def list_analyses_by_status(self, statuses: list[str], limit: int = 20) -> list[dict[str, Any]]:
        if not statuses:
            return []
        data = self._load()
        filtered = [item for item in data["analyses"] if item.get("status") in set(statuses)]
        filtered = sorted(filtered, key=lambda item: item["created_at"])
        return filtered[:limit]

    def list_discovery_profiles(self, active_only: bool = True) -> list[dict[str, Any]]:
        data = self._load()
        profiles = data.get("discovery_profiles", [])
        if not active_only:
            return profiles
        return [item for item in profiles if item.get("is_active", True)]

    def get_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        data = self._load()
        return next((item for item in data["analyses"] if item["id"] == analysis_id), None)

    def update_analysis_status(self, analysis_id: str, status: str) -> None:
        data = self._load()
        for analysis in data["analyses"]:
            if analysis["id"] == analysis_id:
                analysis["status"] = status
                analysis["updated_at"] = utc_now_iso()
                break
        self._save(data)

    def create_sources(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not payload:
            return []
        data = self._load()
        created_items: list[dict[str, Any]] = []
        for item in payload:
            source = self._build_source_record(item)
            data["sources"].append(source)
            created_items.append(source)
        self._save(data)
        return created_items

    def clear_analysis_data(self, analysis_id: str) -> None:
        data = self._load()
        data["sources"] = [item for item in data["sources"] if item["analysis_id"] != analysis_id]
        data["scraped_items"] = [item for item in data["scraped_items"] if item["analysis_id"] != analysis_id]
        data["insights"] = [item for item in data["insights"] if item["analysis_id"] != analysis_id]
        self._save(data)

    def list_sources(self, analysis_id: str) -> list[dict[str, Any]]:
        data = self._load()
        items = [item for item in data["sources"] if item["analysis_id"] == analysis_id]
        return sorted(items, key=lambda item: item["created_at"])

    def update_source_status(self, source_id: str, status: str) -> None:
        data = self._load()
        for source in data["sources"]:
            if source["id"] == source_id:
                source["status"] = status
                break
        self._save(data)

    def create_scraped_items(self, payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not payload:
            return []
        data = self._load()
        created_items: list[dict[str, Any]] = []
        for item in payload:
            scraped_item = self._build_scraped_item_record(item)
            data["scraped_items"].append(scraped_item)
            created_items.append(scraped_item)
        self._save(data)
        return created_items

    def list_scraped_items(self, analysis_id: str) -> list[dict[str, Any]]:
        data = self._load()
        items = [item for item in data["scraped_items"] if item["analysis_id"] == analysis_id]
        return sorted(items, key=lambda item: item["created_at"])

    def replace_scraped_items(self, analysis_id: str, items: list[dict[str, Any]]) -> None:
        data = self._load()
        data["scraped_items"] = [item for item in data["scraped_items"] if item["analysis_id"] != analysis_id]
        for item in items:
            copied = self._build_scraped_item_record(item, analysis_id=analysis_id)
            data["scraped_items"].append(copied)
        self._save(data)

    def upsert_insight(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._load()
        data["insights"] = [
            item for item in data["insights"] if item["analysis_id"] != payload["analysis_id"]
        ]
        insight = {
            "id": str(uuid4()),
            "analysis_id": payload["analysis_id"],
            "summary": payload.get("summary"),
            "opportunities": payload.get("opportunities", []),
            "competitors": payload.get("competitors", []),
            "pricing_insight": payload.get("pricing_insight"),
            "customer_pain_points": payload.get("customer_pain_points", []),
            "strategy_recommendations": payload.get("strategy_recommendations", []),
            "raw_ai_response": payload.get("raw_ai_response", {}),
            "created_at": utc_now_iso(),
        }
        insight = sanitize_recursive(insight)
        data["insights"].append(insight)
        self._save(data)
        return insight

    def get_insight(self, analysis_id: str) -> dict[str, Any] | None:
        data = self._load()
        return next((item for item in data["insights"] if item["analysis_id"] == analysis_id), None)

    def count_sources(self, analysis_id: str) -> int:
        return len(self.list_sources(analysis_id))

    def count_items(self, analysis_id: str) -> int:
        return len(self.list_scraped_items(analysis_id))
