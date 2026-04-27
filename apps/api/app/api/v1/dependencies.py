from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings
from app.core.supabase_client import get_supabase_client
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.local_analysis_repository import LocalAnalysisRepository


def get_repository() -> AnalysisRepository | LocalAnalysisRepository:
    settings = get_settings()
    if settings.supabase_url.strip() and settings.supabase_service_role_key.strip():
        client = get_supabase_client()
        return AnalysisRepository(client)

    store_path = Path(__file__).resolve().parents[4] / "local_store.json"
    return LocalAnalysisRepository(store_path=store_path)

