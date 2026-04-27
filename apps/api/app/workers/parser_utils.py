from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup


def extract_price(raw_text: str) -> tuple[str | None, float | None, float | None]:
    matches = re.findall(
        r"(?:Rp|IDR)[\s.]?[\d.]+(?:\s*(?:-|sampai|to)\s*(?:Rp|IDR)?[\s.]?[\d.]+)?",
        raw_text,
        flags=re.IGNORECASE,
    )
    if not matches:
        return None, None, None

    price_text = matches[0]
    numbers = re.findall(r"\d[\d.]*", price_text)
    parsed: list[float] = []
    for number in numbers:
        try:
            parsed.append(float(number.replace(".", "")))
        except ValueError:
            continue
    if not parsed:
        return price_text, None, None
    if len(parsed) == 1:
        return price_text, parsed[0], parsed[0]
    return price_text, min(parsed), max(parsed)


def extract_rating_and_review_count(raw_text: str) -> tuple[float | None, int | None]:
    rating_patterns = [
        r"\b([0-5](?:[.,]\d)?)\s*(?:/5|bintang|stars?)\b",
        r"\brating[:\s]*([0-5](?:[.,]\d)?)\b",
    ]
    rating: float | None = None
    for pattern in rating_patterns:
        rating_match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        if rating_match:
            rating = float(rating_match.group(1).replace(",", "."))
            break

    review_patterns = [
        r"(\d{1,6})\s*(?:ulasan|reviews?)\b",
        r"(?:review|ulasan)[:\s]*(\d{1,6})\b",
    ]
    review_count: int | None = None
    for pattern in review_patterns:
        review_match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        if review_match:
            review_count = int(review_match.group(1))
            break
    return rating, review_count


def extract_address(raw_text: str) -> str | None:
    patterns = [
        r"(Jl\.\s*[^,\n]+(?:,\s*[^,\n]+){0,4})",
        r"(Jalan\s+[^,\n]+(?:,\s*[^,\n]+){0,4})",
        r"((?:Kel\.|Kec\.|Kota|Kabupaten|Provinsi)\s+[^,\n]+(?:,\s*[^,\n]+){0,3})",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def parse_html_content(url: str, html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    og_title = soup.find("meta", property="og:title")
    og_desc = soup.find("meta", property="og:description")
    title = soup.title.get_text(strip=True) if soup.title else None

    h1 = soup.find("h1")
    name = (
        (h1.get_text(strip=True) if h1 else None)
        or (og_title.get("content", "").strip() if og_title else None)
        or title
    )

    text_nodes = soup.select("p, li, h2, h3, article, section, main")
    text_chunks = [node.get_text(" ", strip=True) for node in text_nodes]
    text_chunks = [chunk for chunk in text_chunks if len(chunk) > 20]
    raw_text = re.sub(r"\s+", " ", " ".join(text_chunks[:180])).strip()

    description = (
        (og_desc.get("content", "").strip() if og_desc else None)
        or (raw_text[:500] if raw_text else None)
    )
    price_text, price_min, price_max = extract_price(raw_text)
    rating, review_count = extract_rating_and_review_count(raw_text)
    address = extract_address(raw_text)

    return {
        "name": name,
        "description": description,
        "address": address,
        "price_text": price_text,
        "price_min": price_min,
        "price_max": price_max,
        "rating": rating,
        "review_count": review_count,
        "raw_text": raw_text[:4000] if raw_text else None,
        "metadata": {
            "url": url,
            "title": title,
            "parser": "html_heuristic_v2",
        },
    }
