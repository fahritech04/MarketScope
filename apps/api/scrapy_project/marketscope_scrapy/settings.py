BOT_NAME = "marketscope_scrapy"

SPIDER_MODULES = ["marketscope_scrapy.spiders"]
NEWSPIDER_MODULE = "marketscope_scrapy.spiders"

ROBOTSTXT_OBEY = True
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}

ITEM_PIPELINES = {
    "marketscope_scrapy.pipelines.MarketScopeNormalizePipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

