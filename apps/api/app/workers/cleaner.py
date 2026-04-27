from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote, urlparse

import pandas as pd


def _normalize_text(value: str | None) -> str | None:
    if not value:
        return None
    normalized = re.sub(r"\s+", " ", value).strip()
    return normalized or None


def _normalize_price(row: pd.Series) -> tuple[float | None, float | None]:
    price_min = row.get("price_min")
    price_max = row.get("price_max")
    if pd.notna(price_min) and pd.notna(price_max):
        return float(price_min), float(price_max)

    text = row.get("price_text")
    if not text:
        return None, None

    matches = re.findall(r"\d[\d.]*", str(text))
    values: list[float] = []
    for match in matches:
        try:
            values.append(float(match.replace(".", "")))
        except ValueError:
            continue
    if not values:
        return None, None
    if len(values) == 1:
        return values[0], values[0]
    return min(values), max(values)


def _fallback_name_from_metadata(meta: Any) -> str | None:
    if not isinstance(meta, dict):
        return None
    url = meta.get("url")
    if not isinstance(url, str) or not url.strip():
        return None
    try:
        parsed = urlparse(url.strip())
        slug = unquote(parsed.path.strip("/").split("/")[-1]).strip()
        if slug:
            candidate = re.sub(r"[-_]+", " ", slug)
            candidate = re.sub(r"\s+", " ", candidate).strip()
            return candidate or parsed.netloc
        return parsed.netloc or None
    except Exception:
        return None


def clean_scraped_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not items:
        return []

    df = pd.DataFrame(items)
    for col in ("name", "description", "address", "price_text", "raw_text"):
        if col in df.columns:
            df[col] = df[col].apply(_normalize_text)

    if "name" in df.columns and "metadata" in df.columns:
        df["name"] = df.apply(
            lambda row: row["name"] if row.get("name") else _fallback_name_from_metadata(row.get("metadata")),
            axis=1,
        )

    if "name" in df.columns:
        df = df[df["name"].notna()]

    # Prioritaskan dedupe berdasarkan URL sumber jika tersedia di metadata.url.
    if "metadata" in df.columns:
        def _meta_url(meta: Any) -> str | None:
            if isinstance(meta, dict):
                url = meta.get("url")
                if isinstance(url, str):
                    normalized = url.strip().lower()
                    return normalized or None
            return None

        df["normalized_url"] = df["metadata"].apply(_meta_url)
    else:
        df["normalized_url"] = None

    dedupe_cols = []
    if "normalized_url" in df.columns and df["normalized_url"].notna().any():
        dedupe_cols = ["normalized_url"]
    else:
        dedupe_cols = [col for col in ["source_id", "name", "address"] if col in df.columns]

    if dedupe_cols:
        df = df.drop_duplicates(subset=dedupe_cols, keep="first")

    if "normalized_url" in df.columns:
        df = df.drop(columns=["normalized_url"])

    normalized_prices = df.apply(_normalize_price, axis=1, result_type="expand")
    if normalized_prices.shape[1] == 2:
        df["price_min"] = normalized_prices[0]
        df["price_max"] = normalized_prices[1]

    if "review_count" in df.columns:
        df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").fillna(0).astype(int)
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    clean = df.where(pd.notnull(df), None).to_dict(orient="records")
    return clean
