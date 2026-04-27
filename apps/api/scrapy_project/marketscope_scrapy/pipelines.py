from __future__ import annotations

from typing import Any


class MarketScopeNormalizePipeline:
    def process_item(self, item: dict[str, Any], spider):
        # Keep payload shape deterministic for downstream parser.
        normalized = {
            "source_url": item.get("source_url"),
            "success": bool(item.get("success")),
            "data": item.get("data") or {},
            "error": item.get("error"),
        }
        return normalized

