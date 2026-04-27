from __future__ import annotations

import re


GENERIC_STOPWORDS = {
    "di",
    "dekat",
    "dan",
    "yang",
    "untuk",
    "jasa",
    "usaha",
    "lokal",
    "indonesia",
    "umum",
    "general",
    "lainnya",
}


def _clean(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.strip().split())


def _has_meaningful_category(value: str) -> bool:
    tokens = [token.lower() for token in re.findall(r"[a-zA-Z0-9]+", value)]
    meaningful = [token for token in tokens if len(token) >= 3 and token not in GENERIC_STOPWORDS]
    return bool(meaningful)


def build_keywords(topic: str, location: str | None = None, category: str | None = None) -> list[str]:
    topic_clean = _clean(topic)
    location_clean = _clean(location)
    category_clean = _clean(category)

    keywords = {
        topic_clean,
        f"{topic_clean} harga",
        f"{topic_clean} review",
        f"{topic_clean} rekomendasi",
        f"{topic_clean} kompetitor",
        f"{topic_clean} daftar usaha",
        f"{topic_clean} alamat",
        f"{topic_clean} rating",
    }

    if location_clean:
        keywords.update(
            {
                f"{topic_clean} di {location_clean}",
                f"{topic_clean} {location_clean}",
                f"{topic_clean} {location_clean} harga",
                f"{topic_clean} {location_clean} review",
                f"{topic_clean} {location_clean} terdekat",
                f"{topic_clean} {location_clean} daftar",
                f"{topic_clean} {location_clean} kompetitor",
                f"{topic_clean} {location_clean} rating",
            }
        )

    if category_clean and _has_meaningful_category(category_clean):
        keywords.update(
            {
                f"{category_clean} {topic_clean}",
                f"{category_clean} {topic_clean} indonesia",
                f"{category_clean} {topic_clean} marketplace",
                f"{category_clean} {topic_clean} directory",
            }
        )

    result = [keyword.strip() for keyword in keywords if keyword.strip()]
    result.sort()
    return result[:32]
