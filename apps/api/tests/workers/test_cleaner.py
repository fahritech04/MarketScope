from app.workers.cleaner import clean_scraped_items


def test_cleaner_deduplicates_by_metadata_url() -> None:
    items = [
        {
            "source_id": "a",
            "name": "Layanan A",
            "address": "Lokasi A",
            "price_text": "Rp10.000",
            "price_min": None,
            "price_max": None,
            "rating": 4.2,
            "review_count": 10,
            "raw_text": "Layanan bagus",
            "metadata": {"url": "https://contoh.com/layanan-a"},
        },
        {
            "source_id": "b",
            "name": "Layanan A Duplicate",
            "address": "Lokasi A",
            "price_text": "Rp12.000",
            "price_min": None,
            "price_max": None,
            "rating": 4.0,
            "review_count": 8,
            "raw_text": "Layanan duplikat",
            "metadata": {"url": "https://contoh.com/layanan-a"},
        },
    ]

    cleaned = clean_scraped_items(items)
    assert len(cleaned) == 1
    assert cleaned[0]["metadata"]["url"] == "https://contoh.com/layanan-a"
