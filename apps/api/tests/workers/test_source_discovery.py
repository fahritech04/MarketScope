from __future__ import annotations

from typing import Any

from app.workers import source_discovery


class _DummyResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_discover_sources_with_location_filter(monkeypatch) -> None:
    html = """
    <html><body>
      <li class="b_algo"><h2><a href="https://www.contohdirektori.id/alamat/layananalpha-lokasia">Layanan Alpha Lokasia</a></h2></li>
      <li class="b_algo"><h2><a href="https://www.contohdirektori.id/alamat/servisalpha-lokasia">Servis Alpha Lokasia</a></h2></li>
      <li class="b_algo"><h2><a href="https://www.contohdirektori.id/alamat/layananalpha-lokasib">Layanan Alpha Lokasib</a></h2></li>
      <li class="b_algo"><h2><a href="https://www.blogcontoh.id/post/layananalpha-lokasic">Ulasan Layanan Alpha Lokasic</a></h2></li>
      <li class="b_algo"><h2><a href="https://www.youtube.com/watch?v=abc123">Video Layanan Alpha</a></h2></li>
    </body></html>
    """

    def fake_get(*args: Any, **kwargs: Any) -> _DummyResponse:
        return _DummyResponse(html)

    monkeypatch.setattr(source_discovery.requests, "get", fake_get)
    monkeypatch.setattr(source_discovery.time, "sleep", lambda *_: None)

    results = source_discovery.discover_sources(
        keywords=["layananalpha sekitar area", "layananalpha lokasia review"],
        topic="layananalpha sekitar area",
        location_text="lokasia",
        category="jasa",
        max_results_per_keyword=1,
        timeout_seconds=2,
        delay_seconds=0.1,
        allow_all_domains=False,
    )

    urls = [item["url"] for item in results]
    assert any("lokasia" in url for url in urls)
    assert not any("youtube.com" in url for url in urls)
    assert not any("lokasib" in url for url in urls)
    assert all(item["source_type"] in {"directory", "web"} for item in results)
