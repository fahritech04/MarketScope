from __future__ import annotations

import base64
import random
import time
from collections import deque
from typing import Any
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

from app.workers.domain_adapter import (
    apply_runtime_overrides,
    build_location_aliases,
    build_search_queries,
    infer_source_type,
    is_preferred_domain,
    score_candidate,
    select_adapter,
)
from app.workers.query_planner import plan_query_bundle

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

DEFAULT_HEADERS = {
    "User-Agent": "MarketScopeAI/1.0 (+https://localhost; educational mvp crawler)",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}

SEARCH_PROVIDERS = [
    {
        "name": "bing",
        "url_template": "https://www.bing.com/search?setlang=id-id&cc=ID&q={query}&first={offset}",
        "selector": "li.b_algo h2 a",
        "start": 1,
        "step": 10,
    },
    {
        "name": "duckduckgo",
        "url_template": "https://duckduckgo.com/html/?q={query}&s={offset}",
        "selector": "a.result__a",
        "start": 0,
        "step": 30,
    },
]

# Domain hard-block minimal: hanya mencegah loop ke search provider itu sendiri.
HARD_BLOCKED_DOMAINS = {
    "duckduckgo.com",
    "www.bing.com",
    "bing.com",
    "search.brave.com",
}


def _decode_bing_u_param(value: str | None) -> str | None:
    if not value:
        return None

    candidate = value
    if candidate.startswith("a1"):
        candidate = candidate[2:]
    padding = "=" * ((4 - len(candidate) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode(candidate + padding).decode("utf-8", errors="ignore")
    except Exception:
        return None

    if decoded.startswith("http://") or decoded.startswith("https://"):
        return decoded
    return None


def _extract_real_url(href: str | None) -> str | None:
    if not href:
        return None
    if href.startswith("http://") or href.startswith("https://"):
        parsed = urlparse(href)
        query_params = parse_qs(parsed.query)
        if "duckduckgo.com" in parsed.netloc and "uddg" in query_params:
            return query_params.get("uddg", [None])[0]
        if "bing.com" in parsed.netloc and "u" in query_params:
            decoded = _decode_bing_u_param(query_params.get("u", [None])[0])
            if decoded:
                return decoded
        return href

    parsed = urlparse(href)
    query_params = parse_qs(parsed.query)
    if "uddg" in query_params:
        return query_params.get("uddg", [None])[0]
    if "u" in query_params:
        decoded = _decode_bing_u_param(query_params.get("u", [None])[0])
        if decoded:
            return decoded
    return None


def _is_supported_url(url: str | None, allow_all_domains: bool = True) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    domain = parsed.netloc.lower()
    if domain in HARD_BLOCKED_DOMAINS:
        return False
    # allow_all_domains disediakan untuk kompatibilitas config.
    # Tidak ada hardcoded noisy-domain blacklist agar full dinamis.
    _ = allow_all_domains
    return True


def _domain_key(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


def _normalize_page_link(base_url: str, href: str | None) -> str | None:
    if not href:
        return None
    value = href.strip()
    if not value:
        return None
    if value.startswith(("javascript:", "mailto:", "tel:", "#")):
        return None
    if value.startswith("http://") or value.startswith("https://"):
        normalized = value
    elif value.startswith("//"):
        parsed = urlparse(base_url)
        normalized = f"{parsed.scheme}:{value}"
    else:
        normalized = urljoin(base_url, value)

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"}:
        return None
    # Drop fragment untuk menekan duplikasi URL.
    clean = parsed._replace(fragment="").geturl()
    return clean


def _query_variants(query: str) -> list[str]:
    variants = [query, f"{query} indonesia"]
    unique: list[str] = []
    seen: set[str] = set()
    for value in variants:
        normalized = " ".join(value.split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def _provider_offsets(provider: dict[str, Any], pages: int) -> list[int]:
    start = int(provider.get("start", 0))
    step = int(provider.get("step", 10))
    return [start + (idx * step) for idx in range(max(1, pages))]


def discover_sources(
    keywords: list[str],
    max_results_per_keyword: int = 5,
    timeout_seconds: int = 20,
    delay_seconds: float = 1.5,
    allow_insecure_ssl: bool = False,
    location_text: str | None = None,
    topic: str | None = None,
    category: str | None = None,
    discovery_profiles: list[dict[str, Any]] | None = None,
    target_total_results: int | None = None,
    max_requests: int = 120,
    max_pages_per_query: int = 3,
    max_queries: int = 20,
    domain_cap: int = 2,
    min_score: int = 20,
    allow_all_domains: bool = True,
) -> list[dict[str, Any]]:
    if not keywords:
        return []

    topic_text = (topic or keywords[0]).strip()
    adapter = select_adapter(
        topic=topic_text,
        location=location_text,
        category=category,
        keywords=keywords,
        dynamic_profiles=discovery_profiles,
    )
    base_queries = build_search_queries(
        topic=topic_text,
        location=location_text,
        category=category,
        keywords=keywords,
        adapter=adapter,
        max_queries=min(max_queries, max(3, len(keywords) + 2)),
    )
    planned_bundle = plan_query_bundle(
        topic=topic_text,
        location=location_text,
        category=category,
        base_queries=base_queries,
        adapter=adapter,
    )
    search_queries = (planned_bundle.get("queries") or base_queries)[:max_queries]
    adapter = apply_runtime_overrides(
        adapter,
        required_terms=planned_bundle.get("required_terms"),
        blocked_terms=planned_bundle.get("blocked_terms"),
        preferred_domains=planned_bundle.get("preferred_domains"),
    )

    location_aliases = build_location_aliases(location_text)
    require_location = bool(location_aliases)
    if target_total_results and target_total_results > 0:
        max_total_results = target_total_results
    else:
        max_total_results = max(max_results_per_keyword, max_results_per_keyword * max(1, len(keywords)))

    candidates: dict[str, dict[str, Any]] = {}
    relaxed_candidates: dict[str, dict[str, Any]] = {}
    domain_counts: dict[str, int] = {}
    request_count = 0

    should_stop = False
    for query in search_queries:
        for variant in _query_variants(query):
            encoded = quote_plus(variant)
            for provider in SEARCH_PROVIDERS:
                for offset in _provider_offsets(provider, pages=max_pages_per_query):
                    if request_count >= max_requests:
                        should_stop = True
                        break
                    request_count += 1

                    request_url = provider["url_template"].format(query=encoded, offset=offset)
                    try:
                        response = requests.get(
                            request_url,
                            timeout=timeout_seconds,
                            headers=DEFAULT_HEADERS,
                            verify=not allow_insecure_ssl,
                        )
                        response.raise_for_status()
                    except requests.RequestException:
                        continue

                    soup = BeautifulSoup(response.text, "html.parser")
                    anchors = soup.select(provider["selector"])
                    if not anchors:
                        continue

                    for anchor in anchors:
                        real_url = _extract_real_url(anchor.get("href"))
                        if not _is_supported_url(real_url, allow_all_domains=allow_all_domains):
                            continue
                        if not real_url:
                            continue

                        title_text = anchor.get_text(strip=True) or real_url
                        score, location_match, conflicting_location = score_candidate(
                            url=real_url,
                            title=title_text,
                            query_text=variant,
                            topic=topic_text,
                            adapter=adapter,
                            location_aliases=location_aliases,
                        )
                        preferred_domain = is_preferred_domain(real_url, adapter)

                        if score < min_score:
                            continue
                        if require_location and conflicting_location:
                            continue

                        source_type = infer_source_type(real_url, adapter)
                        item = {
                            "url": real_url,
                            "title": title_text,
                            "source_type": source_type,
                            "score": score,
                            "preferred_domain": preferred_domain,
                            "location_match": location_match,
                        }
                        if require_location and not location_match and score < 82:
                            relaxed_item = {**item, "score": score - 20}
                            existing = relaxed_candidates.get(real_url)
                            if not existing or relaxed_item["score"] > existing["score"]:
                                relaxed_candidates[real_url] = relaxed_item
                            continue

                        existing = candidates.get(real_url)
                        if not existing or item["score"] > existing["score"]:
                            candidates[real_url] = item

                    if len(candidates) >= max_total_results * 4:
                        should_stop = True
                        break

                    time.sleep(max(0.05, delay_seconds) + random.uniform(0.02, 0.2))
                if should_stop:
                    break
            if should_stop:
                break
        if should_stop:
            break

    # Expansion pass: ambil outbound link dari kandidat awal agar skala source lebih besar.
    if len(candidates) < max_total_results and request_count < max_requests and candidates:
        seed_candidates = sorted(candidates.values(), key=lambda item: item["score"], reverse=True)
        seed_candidates = seed_candidates[: min(250, len(seed_candidates))]

        # BFS ringan depth<=1 untuk memperluas URL dari seed awal.
        queue: deque[tuple[str, int, int]] = deque()
        visited_pages: set[str] = set()
        for seed in seed_candidates:
            queue.append((seed["url"], 0, seed["score"]))

        while queue and request_count < max_requests:
            page_url, depth, parent_score = queue.popleft()
            if page_url in visited_pages:
                continue
            visited_pages.add(page_url)

            request_count += 1
            try:
                response = requests.get(
                    page_url,
                    timeout=timeout_seconds,
                    headers=DEFAULT_HEADERS,
                    verify=not allow_insecure_ssl,
                )
                response.raise_for_status()
            except requests.RequestException:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            anchors = soup.select("a[href]")
            for anchor in anchors:
                expanded_url = _normalize_page_link(page_url, anchor.get("href"))
                if not _is_supported_url(expanded_url, allow_all_domains=allow_all_domains):
                    continue
                if not expanded_url:
                    continue

                title_text = anchor.get_text(strip=True) or expanded_url
                score, location_match, conflicting_location = score_candidate(
                    url=expanded_url,
                    title=title_text,
                    query_text=topic_text,
                    topic=topic_text,
                    adapter=adapter,
                    location_aliases=location_aliases,
                )
                if require_location and conflicting_location:
                    continue

                source_type = infer_source_type(expanded_url, adapter)
                preferred_domain = is_preferred_domain(expanded_url, adapter)
                relaxed_score = max(score, parent_score - 12, 1)
                item = {
                    "url": expanded_url,
                    "title": title_text,
                    "source_type": source_type,
                    "score": relaxed_score,
                    "preferred_domain": preferred_domain,
                    "location_match": location_match,
                }
                existing = candidates.get(expanded_url)
                if not existing or item["score"] > existing["score"]:
                    candidates[expanded_url] = item

                if depth < 1 and len(queue) < max_total_results * 3:
                    queue.append((expanded_url, depth + 1, relaxed_score))

                if len(candidates) >= max_total_results * 5:
                    break

            if len(candidates) >= max_total_results * 5:
                break

    ranked = sorted(
        candidates.values(),
        key=lambda item: (item["score"], item["location_match"], item["preferred_domain"]),
        reverse=True,
    )

    discovered: list[dict[str, Any]] = []
    for item in ranked:
        domain = _domain_key(item["url"])
        if domain_cap > 0 and domain_counts.get(domain, 0) >= domain_cap:
            continue
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        discovered.append(
            {
                "url": item["url"],
                "title": item["title"],
                "source_type": item["source_type"],
            }
        )
        if len(discovered) >= max_total_results:
            break

    if len(discovered) < max_total_results and relaxed_candidates:
        relaxed_ranked = sorted(
            relaxed_candidates.values(),
            key=lambda item: (item["score"], item["preferred_domain"]),
            reverse=True,
        )
        existing_urls = {item["url"] for item in discovered}
        for item in relaxed_ranked:
            if item["url"] in existing_urls:
                continue
            domain = _domain_key(item["url"])
            if domain_cap > 0 and domain_counts.get(domain, 0) >= max(1, domain_cap // 2):
                continue
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            discovered.append(
                {
                    "url": item["url"],
                    "title": item["title"],
                    "source_type": item["source_type"],
                }
            )
            if len(discovered) >= max_total_results:
                break

    return discovered
