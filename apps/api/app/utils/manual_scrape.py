from __future__ import annotations

import argparse
import json

from app.workers.keyword_builder import build_keywords
from app.workers.scraper import scrape_url
from app.workers.source_discovery import discover_sources


def main() -> None:
    parser = argparse.ArgumentParser(description="Uji discovery + scraping sederhana tanpa API.")
    parser.add_argument("--topic", required=True, help="Topik analisis (bebas sesuai kebutuhan)")
    parser.add_argument("--location", default=None, help="Lokasi opsional")
    parser.add_argument("--category", default=None, help="Kategori opsional")
    args = parser.parse_args()

    keywords = build_keywords(args.topic, args.location, args.category)
    sources = discover_sources(
        keywords=keywords,
        max_results_per_keyword=2,
        location_text=args.location,
        topic=args.topic,
        category=args.category,
    )
    print("Keyword:", keywords)
    print("Jumlah sumber:", len(sources))

    for source in sources[:3]:
        print("\nURL:", source["url"])
        result = scrape_url(source["url"])
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
