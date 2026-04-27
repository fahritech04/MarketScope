from __future__ import annotations

import scrapy

from app.workers.parser_utils import parse_html_content
from marketscope_scrapy.items import MarketScopeScrapedItem


class MarketScopeBatchSpider(scrapy.Spider):
    name = "marketscope_batch"

    def __init__(self, urls: list[str], timeout_seconds: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.urls = urls
        self.timeout_seconds = timeout_seconds

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_page,
                errback=self.parse_error,
                dont_filter=True,
                meta={"download_timeout": self.timeout_seconds},
            )

    def parse_page(self, response: scrapy.http.Response):
        parsed = parse_html_content(url=response.url, html=response.text)
        parsed["metadata"] = {**(parsed.get("metadata") or {}), "engine": "scrapy"}
        yield MarketScopeScrapedItem(
            source_url=response.url,
            success=True,
            data=parsed,
            error=None,
        )

    def parse_error(self, failure):
        request = failure.request
        yield MarketScopeScrapedItem(
            source_url=request.url,
            success=False,
            data={},
            error=str(failure.value),
        )

