from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scrapy.utils.project import get_project_settings


def _build_settings(
    timeout_seconds: int,
    delay_seconds: float,
    concurrent_requests: int,
    obey_robots_txt: bool,
    allow_insecure_ssl: bool,
) -> Settings:
    project_settings = get_project_settings()
    runtime_overrides = {
        "USER_AGENT": "MarketScopeAI/1.0 (+https://localhost; educational mvp crawler)",
        "ROBOTSTXT_OBEY": obey_robots_txt,
        "DOWNLOAD_TIMEOUT": timeout_seconds,
        "DOWNLOAD_DELAY": delay_seconds,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": concurrent_requests,
        "RETRY_TIMES": 1,
        "LOG_ENABLED": False,
        "DOWNLOADER_CLIENT_TLS_VERIFY": not allow_insecure_ssl,
    }
    for key, value in runtime_overrides.items():
        project_settings.set(key, value, priority="cmdline")
    return project_settings


def crawl_urls(
    urls: list[str],
    timeout_seconds: int,
    delay_seconds: float,
    concurrent_requests: int,
    obey_robots_txt: bool,
    allow_insecure_ssl: bool,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    settings = _build_settings(
        timeout_seconds=timeout_seconds,
        delay_seconds=delay_seconds,
        concurrent_requests=concurrent_requests,
        obey_robots_txt=obey_robots_txt,
        allow_insecure_ssl=allow_insecure_ssl,
    )
    process = CrawlerProcess(settings=settings)

    def _collect_item(item, response, spider):
        results.append(
            {
                "url": item.get("source_url"),
                "success": bool(item.get("success")),
                "data": item.get("data") or {},
                "error": item.get("error"),
            }
        )

    crawler = process.create_crawler("marketscope_batch")
    crawler.signals.connect(_collect_item, signal=signals.item_scraped)
    process.crawl(crawler, urls=urls, timeout_seconds=timeout_seconds)
    process.start(stop_after_crawl=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Scrapy batch crawl for MarketScope.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--obey-robots", type=int, default=1)
    parser.add_argument("--allow-insecure-ssl", type=int, default=0)
    args = parser.parse_args()

    api_root = Path(__file__).resolve().parents[2]
    scrapy_project_root = api_root / "scrapy_project"
    os.environ["SCRAPY_SETTINGS_MODULE"] = "marketscope_scrapy.settings"
    if str(scrapy_project_root) not in sys.path:
        sys.path.insert(0, str(scrapy_project_root))
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    input_path = Path(args.input)
    output_path = Path(args.output)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    urls = payload.get("urls", [])
    results = crawl_urls(
        urls=urls,
        timeout_seconds=args.timeout,
        delay_seconds=args.delay,
        concurrent_requests=args.concurrency,
        obey_robots_txt=bool(args.obey_robots),
        allow_insecure_ssl=bool(args.allow_insecure_ssl),
    )
    output_path.write_text(json.dumps({"results": results}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()

