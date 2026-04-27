from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.local_analysis_repository import LocalAnalysisRepository
from app.workers.ai_analyzer import generate_insight
from app.workers.cleaner import clean_scraped_items
from app.workers.keyword_builder import build_keywords
from app.workers.scraper import scrape_url
from app.workers.scrapy_batch import scrape_with_scrapy_batch
from app.workers.source_discovery import discover_sources


class PipelineService:
    def __init__(self, repository: AnalysisRepository | LocalAnalysisRepository):
        self.repository = repository
        self.settings = get_settings()

    @staticmethod
    def _build_scraped_item_payload(
        *,
        analysis_id: str,
        source_id: str | None,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "analysis_id": analysis_id,
            "source_id": source_id,
            "name": result.get("name"),
            "description": result.get("description"),
            "address": result.get("address"),
            "price_text": result.get("price_text"),
            "price_min": result.get("price_min"),
            "price_max": result.get("price_max"),
            "rating": result.get("rating"),
            "review_count": result.get("review_count"),
            "raw_text": result.get("raw_text"),
            "metadata": result.get("metadata", {}),
        }

    @staticmethod
    def _build_discovery_fallback_item(
        *,
        analysis_id: str,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "analysis_id": analysis_id,
            "source_id": source["id"],
            "name": source.get("title") or source.get("url"),
            "description": "Fallback item dari discovery source ketika scraping penuh tidak berhasil.",
            "address": None,
            "price_text": None,
            "price_min": None,
            "price_max": None,
            "rating": None,
            "review_count": None,
            "raw_text": source.get("title"),
            "metadata": {
                "url": source.get("url"),
                "engine": "source_discovery_fallback",
                "source_type": source.get("source_type"),
            },
        }

    @staticmethod
    def _build_clean_item_payload(
        *,
        analysis_id: str,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "analysis_id": analysis_id,
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
            "metadata": item.get("metadata", {}),
            "created_at": item.get("created_at", datetime.now(timezone.utc).isoformat()),
        }

    def run_analysis(self, analysis_id: str) -> None:
        analysis = self.repository.get_analysis(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} tidak ditemukan.")

        try:
            self.repository.update_analysis_status(analysis_id, "crawling")
            self.repository.clear_analysis_data(analysis_id)
            keywords = build_keywords(
                topic=analysis["topic"],
                location=analysis.get("location"),
                category=analysis.get("category"),
            )
            discovery_profiles = self.repository.list_discovery_profiles(active_only=True)

            discovered_sources = discover_sources(
                keywords=keywords,
                max_results_per_keyword=max(3, self.settings.max_sources_per_analysis // max(1, len(keywords))),
                timeout_seconds=self.settings.request_timeout_seconds,
                delay_seconds=self.settings.crawl_delay_seconds,
                allow_insecure_ssl=self.settings.allow_insecure_ssl,
                location_text=analysis.get("location"),
                topic=analysis.get("topic"),
                category=analysis.get("category"),
                discovery_profiles=discovery_profiles,
                target_total_results=self.settings.max_sources_per_analysis,
                max_requests=self.settings.discovery_max_requests,
                max_pages_per_query=self.settings.discovery_pages_per_query,
                max_queries=self.settings.discovery_max_queries,
                domain_cap=self.settings.discovery_domain_cap,
                min_score=self.settings.discovery_min_score,
                allow_all_domains=self.settings.discovery_allow_all_domains,
            )

            sources_payload = [
                {
                    "analysis_id": analysis_id,
                    "url": source["url"],
                    "title": source.get("title"),
                    "source_type": source.get("source_type", "web"),
                    "status": "pending",
                }
                for source in discovered_sources[: self.settings.max_sources_per_analysis]
            ]
            saved_sources = self.repository.create_sources(sources_payload)

            self.repository.update_analysis_status(analysis_id, "scraping")
            scraped_payload: list[dict[str, Any]] = []
            source_url_map = {source["url"]: source for source in saved_sources}
            max_items = max(1, self.settings.max_items_per_analysis)
            high_volume_mode = len(saved_sources) >= 300

            # First pass: Scrapy for fast multi-page crawl on mostly static HTML.
            scrapy_success_by_url: dict[str, dict[str, Any]] = {}
            urls = [source["url"] for source in saved_sources]
            chunk_size = max(50, self.settings.scrapy_batch_chunk_size)
            for start_idx in range(0, len(urls), chunk_size):
                chunk_urls = urls[start_idx : start_idx + chunk_size]
                scrapy_results = scrape_with_scrapy_batch(
                    urls=chunk_urls,
                    timeout_seconds=self.settings.request_timeout_seconds,
                    delay_seconds=self.settings.crawl_delay_seconds,
                    concurrent_requests=self.settings.scrapy_concurrent_requests,
                    obey_robots_txt=self.settings.obey_robots_txt,
                    allow_insecure_ssl=self.settings.allow_insecure_ssl,
                )
                for result in scrapy_results:
                    if result.get("success") and result.get("url") in source_url_map:
                        scrapy_success_by_url[result["url"]] = result

            fallback_candidates: list[dict[str, Any]] = []
            for source in saved_sources:
                source_id = source["id"]
                url = source["url"]
                self.repository.update_source_status(source_id, "scraping")

                result = None
                if url in scrapy_success_by_url:
                    result = scrapy_success_by_url[url].get("data")
                    if result and isinstance(result.get("metadata"), dict):
                        result["metadata"]["engine"] = "scrapy"
                else:
                    fallback_candidates.append(source)
                    continue

                # Fallback: Playwright + BeautifulSoup when Scrapy misses or fails.
                if not result:
                    self.repository.update_source_status(source_id, "failed")
                    continue

                if len(scraped_payload) >= max_items:
                    self.repository.update_source_status(source_id, "skipped")
                    continue

                self.repository.update_source_status(source_id, "completed")
                scraped_payload.append(
                    self._build_scraped_item_payload(
                        analysis_id=analysis_id,
                        source_id=source_id,
                        result=result,
                    )
                )
            # Second pass fallback: paralel untuk URL yang gagal di Scrapy.
            if len(scraped_payload) < max_items and fallback_candidates and not high_volume_mode:
                remaining_quota = max_items - len(scraped_payload)
                fallback_batch = fallback_candidates[: max(remaining_quota * 2, remaining_quota)]
                skipped_rest = fallback_candidates[len(fallback_batch) :]
                for source in skipped_rest:
                    self.repository.update_source_status(source["id"], "skipped")

                def _fallback_task(source: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
                    item = scrape_url(
                        url=source["url"],
                        timeout_seconds=self.settings.request_timeout_seconds,
                        delay_seconds=self.settings.crawl_delay_seconds,
                        obey_robots_txt=self.settings.obey_robots_txt,
                        allow_insecure_ssl=self.settings.allow_insecure_ssl,
                        enable_playwright=self.settings.fallback_enable_playwright,
                        prefer_requests_first=True,
                    )
                    return source["id"], item

                with ThreadPoolExecutor(max_workers=max(1, self.settings.fallback_max_workers)) as executor:
                    futures = {executor.submit(_fallback_task, source): source for source in fallback_batch}
                    for future in as_completed(futures):
                        source = futures[future]
                        source_id = source["id"]
                        try:
                            _, result = future.result()
                        except Exception:
                            result = None

                        if not result:
                            if len(scraped_payload) >= max_items:
                                self.repository.update_source_status(source_id, "skipped")
                            else:
                                self.repository.update_source_status(source_id, "failed")
                            continue

                        if isinstance(result.get("metadata"), dict):
                            result["metadata"]["engine"] = "fallback_parallel"
                        if len(scraped_payload) >= max_items:
                            self.repository.update_source_status(source_id, "skipped")
                            continue

                        self.repository.update_source_status(source_id, "completed")
                        scraped_payload.append(
                            self._build_scraped_item_payload(
                                analysis_id=analysis_id,
                                source_id=source_id,
                                result=result,
                            )
                        )

            # Final fallback high-volume: tetap simpan item minimal dari source discovery
            # agar target volume data bisa tercapai walau fetch halaman gagal.
            if len(scraped_payload) < max_items and fallback_candidates:
                existing_source_ids = {item.get("source_id") for item in scraped_payload}
                for source in fallback_candidates:
                    if source["id"] in existing_source_ids:
                        continue
                    if len(scraped_payload) >= max_items:
                        self.repository.update_source_status(source["id"], "skipped")
                        continue
                    self.repository.update_source_status(source["id"], "completed")
                    scraped_payload.append(
                        self._build_discovery_fallback_item(
                            analysis_id=analysis_id,
                            source=source,
                        )
                    )

            scraped_payload = scraped_payload[:max_items]

            self.repository.create_scraped_items(scraped_payload)

            clean_items = clean_scraped_items(self.repository.list_scraped_items(analysis_id))
            if len(clean_items) < max_items:
                existing_source_ids = {item.get("source_id") for item in clean_items}
                for raw_item in scraped_payload:
                    source_id = raw_item.get("source_id")
                    if source_id in existing_source_ids:
                        continue
                    clean_items.append(raw_item)
                    existing_source_ids.add(source_id)
                    if len(clean_items) >= max_items:
                        break
            clean_items = clean_items[:max_items]
            clean_payload = [
                self._build_clean_item_payload(analysis_id=analysis_id, item=item) for item in clean_items
            ]
            self.repository.replace_scraped_items(analysis_id, clean_payload)

            self.repository.update_analysis_status(analysis_id, "analyzing")
            latest_items = self.repository.list_scraped_items(analysis_id)
            insight = generate_insight(
                topic=analysis["topic"],
                location=analysis.get("location"),
                category=analysis.get("category"),
                items=latest_items,
            )

            self.repository.upsert_insight(
                {
                    "analysis_id": analysis_id,
                    "summary": insight.get("summary"),
                    "opportunities": insight.get("opportunities", []),
                    "competitors": insight.get("competitors", []),
                    "pricing_insight": insight.get("pricing_insight"),
                    "customer_pain_points": insight.get("customer_pain_points", []),
                    "strategy_recommendations": insight.get("strategy_recommendations", []),
                    "raw_ai_response": insight,
                }
            )
            self.repository.update_analysis_status(analysis_id, "completed")
        except Exception:
            self.repository.update_analysis_status(analysis_id, "failed")
            raise
