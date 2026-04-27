from app.workers.domain_adapter import (
    build_location_aliases,
    build_search_queries,
    score_candidate,
    select_adapter,
)


def _dynamic_profiles() -> list[dict]:
    return [
        {
            "profile_key": "profile_alpha",
            "topic_hints": ["layananalpha", "servisalpha"],
            "query_boosters": ["harga layananalpha", "layananalpha terdekat", "site:contohdirektori.id"],
            "required_terms": ["layananalpha"],
            "preferred_domains": ["contohdirektori.id", ".id"],
            "blocked_terms": ["video", "lirik"],
            "source_type_map": {"contohdirektori.id": "directory"},
            "is_active": True,
        },
        {
            "profile_key": "profile_beta",
            "topic_hints": ["produkbeta", "konsultanbeta"],
            "query_boosters": ["jasa produkbeta", "site:contohmarket.id"],
            "required_terms": ["produkbeta", "konsultan"],
            "preferred_domains": ["contohmarket.id", ".id"],
            "blocked_terms": ["template gratis"],
            "source_type_map": {"contohmarket.id": "marketplace"},
            "is_active": True,
        },
    ]


def test_select_adapter_alpha_topic() -> None:
    adapter = select_adapter(
        topic="layananalpha area komunitas",
        location="lokasia",
        category="jasa",
        keywords=["layananalpha area komunitas", "layananalpha lokasia"],
        dynamic_profiles=_dynamic_profiles(),
    )
    assert adapter.key == "profile_alpha"


def test_select_adapter_beta_topic() -> None:
    adapter = select_adapter(
        topic="konsultan produkbeta untuk usaha kecil",
        location="lokasib",
        category="jasa digital",
        keywords=["jasa produkbeta", "konsultanbeta lokasib"],
        dynamic_profiles=_dynamic_profiles(),
    )
    assert adapter.key == "profile_beta"


def test_build_search_queries_contains_location_booster() -> None:
    adapter = select_adapter(
        topic="topik umum",
        location="lokasiutama",
        category="kategoriumum",
        keywords=["topik umum lokasiutama"],
        dynamic_profiles=_dynamic_profiles(),
    )
    queries = build_search_queries(
        topic="topik umum",
        location="lokasiutama",
        category="kategoriumum",
        keywords=["topik umum lokasiutama"],
        adapter=adapter,
    )
    assert any("lokasiutama" in query for query in queries)
    assert len(queries) <= 80


def test_score_candidate_prefers_location_and_domain() -> None:
    adapter = select_adapter(
        topic="layananalpha area komunitas",
        location="lokasia",
        category=None,
        keywords=["layananalpha lokasia"],
        dynamic_profiles=_dynamic_profiles(),
    )
    location_aliases = build_location_aliases("lokasia")
    score_local, location_match, conflicting = score_candidate(
        url="https://www.contohdirektori.id/alamat/layananalpha-lokasia",
        title="Layananalpha di Lokasia",
        query_text="layananalpha lokasia",
        topic="layananalpha area komunitas",
        adapter=adapter,
        location_aliases=location_aliases,
    )
    score_other, non_location_match, non_location_conflicting = score_candidate(
        url="https://www.contohdirektori.id/alamat/layananalpha-lokasib",
        title="Layananalpha di Lokasib",
        query_text="layananalpha lokasia",
        topic="layananalpha area komunitas",
        adapter=adapter,
        location_aliases=location_aliases,
    )

    assert location_match is True
    assert conflicting is False
    assert non_location_match is False
    assert non_location_conflicting is True
    assert score_local > score_other


def test_score_candidate_penalizes_conflicting_location() -> None:
    adapter = select_adapter(
        topic="produkbeta di lokasia",
        location="lokasia",
        category=None,
        keywords=["produkbeta lokasia"],
        dynamic_profiles=_dynamic_profiles(),
    )
    aliases = build_location_aliases("lokasia")
    score_good, _, _ = score_candidate(
        url="https://contohmarket.id/produkbeta-lokasia",
        title="Produkbeta di Lokasia",
        query_text="produkbeta lokasia",
        topic="produkbeta",
        adapter=adapter,
        location_aliases=aliases,
    )
    score_conflict, _, conflicting = score_candidate(
        url="https://contohmarket.id/produkbeta-lokasib",
        title="Produkbeta di Lokasib",
        query_text="produkbeta lokasia",
        topic="produkbeta",
        adapter=adapter,
        location_aliases=aliases,
    )
    assert conflicting is True
    assert score_good > score_conflict
