from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    app_name: str = "MarketScope AI API"
    frontend_origin: str = "http://localhost:3000"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    gemini_api_key: str = ""

    # High-volume defaults (can be overridden from .env)
    max_sources_per_analysis: int = 1000
    max_items_per_analysis: int = 1000
    request_timeout_seconds: int = 12
    crawl_delay_seconds: float = 0.4
    scrapy_concurrent_requests: int = 24
    scrapy_batch_chunk_size: int = 200
    fallback_max_workers: int = 10
    fallback_enable_playwright: bool = False

    discovery_max_queries: int = 120
    discovery_max_requests: int = 1200
    discovery_pages_per_query: int = 8
    discovery_domain_cap: int = 0
    discovery_min_score: int = 8
    discovery_allow_all_domains: bool = True
    scheduler_auth_token: str = ""
    scheduler_default_limit: int = 5

    # Production-safe defaults:
    # - Respect robots.txt
    # - Keep TLS verification ON
    obey_robots_txt: bool = True
    allow_insecure_ssl: bool = False

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
