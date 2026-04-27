from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.repositories.local_analysis_repository import LocalAnalysisRepository
from app.services.pipeline_service import PipelineService


def test_pipeline_run_completed_with_mocked_external_workers(tmp_path: Path) -> None:
    store_path = tmp_path / "store.json"
    repository = LocalAnalysisRepository(store_path=store_path)

    analysis = repository.create_analysis(
        {
            "topic": "layananalpha area komunitas",
            "location": "lokasia",
            "category": "jasa",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    analysis_id = analysis["id"]

    mocked_sources = [
        {
            "url": "https://www.contohdirektori.id/alamat/layananalpha-lokasia",
            "title": "Layanan Alpha Lokasia",
            "source_type": "directory",
        },
        {
            "url": "https://www.contohdirektori.id/alamat/layananalpha-plus-lokasia",
            "title": "Layanan Alpha Plus Lokasia",
            "source_type": "directory",
        },
    ]
    mocked_scrapy_results = [
        {
            "url": "https://www.contohdirektori.id/alamat/layananalpha-lokasia",
            "success": True,
            "data": {
                "name": "Layanan Alpha Lokasia",
                "description": "Layanan cepat untuk pelanggan lokal.",
                "address": "Jl. Contoh 1, Lokasia",
                "price_text": "Rp7.000 - Rp12.000",
                "price_min": 7000,
                "price_max": 12000,
                "rating": 4.5,
                "review_count": 82,
                "raw_text": "Layanan alpha populer di lokasia rating 4.5 82 ulasan.",
                "metadata": {"url": "https://www.contohdirektori.id/alamat/layananalpha-lokasia"},
            },
            "error": None,
        },
        {
            "url": "https://www.contohdirektori.id/alamat/layananalpha-plus-lokasia",
            "success": True,
            "data": {
                "name": "Layanan Alpha Plus Lokasia",
                "description": "Layanan antar jemput cepat.",
                "address": "Jl. Contoh 2, Lokasia",
                "price_text": "Rp8.000",
                "price_min": 8000,
                "price_max": 8000,
                "rating": 4.2,
                "review_count": 40,
                "raw_text": "Layanan alpha plus dengan ulasan pelanggan positif.",
                "metadata": {"url": "https://www.contohdirektori.id/alamat/layananalpha-plus-lokasia"},
            },
            "error": None,
        },
    ]
    mocked_insight = {
        "summary": "Segmen layananalpha di lokasia menunjukkan permintaan yang stabil.",
        "opportunities": ["Paket ekspres dengan SLA jelas."],
        "competitors": ["Layanan Alpha Lokasia", "Layanan Alpha Plus Lokasia"],
        "pricing_insight": "Rentang harga dominan Rp7.000-Rp12.000 per kg.",
        "customer_pain_points": ["Pelanggan butuh respons yang konsisten."],
        "strategy_recommendations": ["Fokus promosi paket langganan mingguan."],
    }

    service = PipelineService(repository)
    with (
        patch("app.services.pipeline_service.discover_sources", return_value=mocked_sources),
        patch("app.services.pipeline_service.scrape_with_scrapy_batch", return_value=mocked_scrapy_results),
        patch("app.services.pipeline_service.scrape_url", return_value=None),
        patch("app.services.pipeline_service.generate_insight", return_value=mocked_insight),
    ):
        service.run_analysis(analysis_id)

    updated = repository.get_analysis(analysis_id)
    assert updated is not None
    assert updated["status"] == "completed"

    sources = repository.list_sources(analysis_id)
    items = repository.list_scraped_items(analysis_id)
    insight = repository.get_insight(analysis_id)

    assert len(sources) == 2
    assert len(items) == 2
    assert insight is not None
    assert insight["summary"] == mocked_insight["summary"]
