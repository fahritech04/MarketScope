from __future__ import annotations

import scrapy


class MarketScopeScrapedItem(scrapy.Item):
    source_url = scrapy.Field()
    success = scrapy.Field()
    data = scrapy.Field()
    error = scrapy.Field()

