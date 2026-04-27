from types import SimpleNamespace

from app.workers.domain_adapter import DomainAdapter
from app.workers.query_planner import plan_query_bundle


def test_query_planner_fallback_without_api_key(monkeypatch) -> None:
    adapter = DomainAdapter(
        key="general",
        topic_terms=(),
        query_boosters=("harga",),
        required_terms=("layananalpha",),
        preferred_domains=("contohdirektori.id",),
        blocked_terms=("lirik",),
        source_type_map=(("contohdirektori.id", "directory"),),
    )
    monkeypatch.setattr(
        "app.workers.query_planner.get_settings",
        lambda: SimpleNamespace(gemini_api_key=""),
    )

    plan = plan_query_bundle(
        topic="layananalpha area komunitas",
        location="lokasia",
        category="jasa",
        base_queries=["layananalpha lokasia", "layananalpha area komunitas lokasia harga"],
        adapter=adapter,
    )

    assert "layananalpha lokasia" in plan["queries"]
    assert "layananalpha" in plan["required_terms"]
    assert "lirik" in plan["blocked_terms"]
