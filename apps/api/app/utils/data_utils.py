from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_recursive(value: Any) -> Any:
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {key: sanitize_recursive(val) for key, val in value.items()}
    if isinstance(value, list):
        return [sanitize_recursive(item) for item in value]
    return value
