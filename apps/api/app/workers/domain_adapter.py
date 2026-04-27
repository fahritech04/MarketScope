from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class DomainAdapter:
    key: str
    topic_terms: tuple[str, ...]
    query_boosters: tuple[str, ...]
    required_terms: tuple[str, ...]
    preferred_domains: tuple[str, ...]
    blocked_terms: tuple[str, ...]
    source_type_map: tuple[tuple[str, str], ...]


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
}

DEFAULT_ADAPTER = DomainAdapter(
    key="general",
    topic_terms=(),
    query_boosters=(),
    required_terms=(),
    preferred_domains=(),
    blocked_terms=(),
    source_type_map=(),
)

LOCATION_MARKER_PATTERN = re.compile(r"\b(?:di|kota|kabupaten|provinsi)\s+([a-zA-Z][a-zA-Z\s]{1,40})")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.lower().strip().split())


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[a-zA-Z0-9]+", text)]
    return [token for token in tokens if len(token) >= 3 and token not in GENERIC_STOPWORDS]


def _safe_terms(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(item for item in (normalize_text(str(v)) for v in value) if item)
    return ()


def _safe_source_type_map(value: Any) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for domain, source_type in value.items():
            domain_clean = normalize_text(str(domain))
            source_type_clean = normalize_text(str(source_type))
            if domain_clean and source_type_clean:
                rows.append((domain_clean, source_type_clean))
    elif isinstance(value, list):
        for item in value:
            if not isinstance(item, dict):
                continue
            domain_clean = normalize_text(str(item.get("domain", "")))
            source_type_clean = normalize_text(str(item.get("type", "")))
            if domain_clean and source_type_clean:
                rows.append((domain_clean, source_type_clean))
    return tuple(rows)


def build_adapters_from_profiles(profile_rows: list[dict[str, Any]] | None) -> tuple[DomainAdapter, ...]:
    if not profile_rows:
        return ()

    adapters: list[DomainAdapter] = []
    for row in profile_rows:
        if row.get("is_active") is False:
            continue

        key = normalize_text(str(row.get("profile_key") or row.get("key") or ""))
        if not key:
            continue

        topic_terms = _safe_terms(row.get("topic_hints") or row.get("topic_terms"))
        query_boosters = _safe_terms(row.get("query_boosters"))
        required_terms = _safe_terms(row.get("required_terms"))
        preferred_domains = _safe_terms(row.get("preferred_domains"))
        blocked_terms = _safe_terms(row.get("blocked_terms"))
        source_type_map = _safe_source_type_map(row.get("source_type_map"))

        adapters.append(
            DomainAdapter(
                key=key,
                topic_terms=topic_terms,
                query_boosters=query_boosters,
                required_terms=required_terms,
                preferred_domains=preferred_domains,
                blocked_terms=blocked_terms,
                source_type_map=source_type_map,
            )
        )
    return tuple(adapters)


def build_location_aliases(location_text: str | None) -> tuple[str, ...]:
    normalized = normalize_text(location_text)
    if not normalized:
        return ()

    aliases: set[str] = {normalized}
    aliases.update(tokenize(normalized))

    # Tambahkan variasi generik tanpa hardcode nama kota/provinsi.
    aliases.add(f"kota {normalized}")
    aliases.add(f"kabupaten {normalized}")
    aliases.add(f"provinsi {normalized}")

    if " " in normalized:
        for part in normalized.split():
            if len(part) >= 3 and part not in GENERIC_STOPWORDS:
                aliases.add(part)

    return tuple(sorted((item for item in aliases if item), key=len, reverse=True))


def has_conflicting_location(haystack: str, location_aliases: tuple[str, ...]) -> bool:
    if not location_aliases:
        return False

    target_set = {alias for alias in location_aliases if alias}
    lower_haystack = normalize_text(haystack)
    for match in LOCATION_MARKER_PATTERN.finditer(lower_haystack):
        candidate = normalize_text(match.group(1))
        if not candidate:
            continue
        candidate = " ".join(candidate.split()[:3])
        if not any(candidate in alias or alias in candidate for alias in target_set):
            return True
    return False


def select_adapter(
    topic: str,
    location: str | None,
    category: str | None,
    keywords: list[str],
    dynamic_profiles: list[dict[str, Any]] | None = None,
) -> DomainAdapter:
    context = " ".join(
        item
        for item in [
            normalize_text(topic),
            normalize_text(location),
            normalize_text(category),
            " ".join(normalize_text(keyword) for keyword in keywords),
        ]
        if item
    )

    candidate_adapters = build_adapters_from_profiles(dynamic_profiles)
    best: DomainAdapter | None = None
    best_score = 0
    for adapter in candidate_adapters:
        score = 0
        for term in adapter.topic_terms:
            if term in context:
                score += 2 if " " in term else 1
        if score > best_score:
            best = adapter
            best_score = score

    if best and best_score > 0:
        return best
    return DEFAULT_ADAPTER


def build_search_queries(
    *,
    topic: str,
    location: str | None,
    category: str | None,
    keywords: list[str],
    adapter: DomainAdapter,
    max_queries: int = 80,
) -> list[str]:
    location_clean = normalize_text(location)
    topic_clean = normalize_text(topic)
    category_clean = normalize_text(category)

    candidates: list[str] = []
    candidates.extend([normalize_text(keyword) for keyword in keywords if normalize_text(keyword)])

    for booster in adapter.query_boosters:
        if booster.startswith("site:"):
            if topic_clean and location_clean:
                candidates.append(f"{topic_clean} {location_clean} {booster}".strip())
            elif topic_clean:
                candidates.append(f"{topic_clean} {booster}".strip())
            continue

        if topic_clean:
            candidates.append(f"{topic_clean} {booster}".strip())
        if location_clean and topic_clean:
            candidates.append(f"{topic_clean} {location_clean} {booster}".strip())
        if category_clean and topic_clean:
            candidates.append(f"{category_clean} {topic_clean} {booster}".strip())

    if location_clean and topic_clean:
        candidates.append(f"{topic_clean} di {location_clean}")

    unique_queries: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = " ".join(candidate.split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_queries.append(normalized)
        if len(unique_queries) >= max_queries:
            break
    return unique_queries


def apply_runtime_overrides(
    adapter: DomainAdapter,
    *,
    required_terms: list[str] | tuple[str, ...] | None = None,
    blocked_terms: list[str] | tuple[str, ...] | None = None,
    preferred_domains: list[str] | tuple[str, ...] | None = None,
) -> DomainAdapter:
    merged_required = list(adapter.required_terms)
    merged_blocked = list(adapter.blocked_terms)
    merged_preferred = list(adapter.preferred_domains)

    for value in required_terms or []:
        term = normalize_text(str(value))
        if term and term not in merged_required:
            merged_required.append(term)

    for value in blocked_terms or []:
        term = normalize_text(str(value))
        if term and term not in merged_blocked:
            merged_blocked.append(term)

    for value in preferred_domains or []:
        domain = normalize_text(str(value))
        if domain and domain not in merged_preferred:
            merged_preferred.append(domain)

    return DomainAdapter(
        key=adapter.key,
        topic_terms=adapter.topic_terms,
        query_boosters=adapter.query_boosters,
        required_terms=tuple(merged_required),
        preferred_domains=tuple(merged_preferred),
        blocked_terms=tuple(merged_blocked),
        source_type_map=adapter.source_type_map,
    )


def is_preferred_domain(url: str, adapter: DomainAdapter) -> bool:
    domain = urlparse(url).netloc.lower()
    return any(pattern in domain for pattern in adapter.preferred_domains)


def infer_source_type(url: str, adapter: DomainAdapter) -> str:
    domain = urlparse(url).netloc.lower()
    for domain_pattern, source_type in adapter.source_type_map:
        if domain_pattern in domain:
            return source_type
    return "web"


def is_blocked_content(url: str, title: str, adapter: DomainAdapter) -> bool:
    haystack = f"{url} {title}".lower()
    return any(blocked in haystack for blocked in adapter.blocked_terms)


def has_required_term(haystack: str, adapter: DomainAdapter, query_tokens: list[str]) -> bool:
    if any(term in haystack for term in adapter.required_terms):
        return True
    if not adapter.required_terms:
        return True
    return any(token in haystack for token in query_tokens)


def score_candidate(
    *,
    url: str,
    title: str,
    query_text: str,
    topic: str,
    adapter: DomainAdapter,
    location_aliases: tuple[str, ...],
) -> tuple[int, bool, bool]:
    haystack = f"{title} {url}".lower()
    query_tokens = tokenize(query_text)
    topic_tokens = tokenize(topic)

    location_match = any(alias in haystack for alias in location_aliases) if location_aliases else True
    conflicting_location = has_conflicting_location(haystack, location_aliases) if location_aliases else False

    score = 0
    if is_preferred_domain(url, adapter):
        score += 30
    if location_aliases and location_match:
        score += 24
    if location_aliases and not location_match:
        score -= 18
    if conflicting_location:
        score -= 45

    score += min(40, 8 * sum(1 for token in topic_tokens if token in haystack))
    score += min(30, 5 * sum(1 for token in query_tokens if token in haystack))
    score += min(16, 8 * sum(1 for term in adapter.required_terms if term in haystack))

    if not has_required_term(haystack, adapter, query_tokens):
        score -= 30
    if is_blocked_content(url, title, adapter):
        score -= 50

    return score, location_match, conflicting_location
