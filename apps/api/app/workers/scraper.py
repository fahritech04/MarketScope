from __future__ import annotations

import asyncio
import random
import time
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from urllib3.exceptions import InsecureRequestWarning

from app.workers.parser_utils import parse_html_content

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

USER_AGENT = "MarketScopeAI/1.0 (+https://localhost; educational mvp crawler)"


def is_allowed_by_robots(url: str, obey_robots_txt: bool = True, allow_insecure_ssl: bool = False) -> bool:
    if not obey_robots_txt:
        return True

    parsed = urlparse(url)
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    rp = RobotFileParser()
    try:
        response = requests.get(
            robots_url,
            timeout=6,
            headers={"User-Agent": USER_AGENT},
            verify=not allow_insecure_ssl,
        )
        if response.status_code >= 400:
            return allow_insecure_ssl
        rp.parse(response.text.splitlines())
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        # Production-safe behavior: deny when robots check is unavailable.
        # Local dev can opt-in to insecure SSL and bypass this strict policy.
        return allow_insecure_ssl


async def _fetch_with_playwright(
    url: str,
    timeout_seconds: int,
    allow_insecure_ssl: bool,
) -> str | None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            ignore_https_errors=allow_insecure_ssl,
        )
        page = await context.new_page()
        try:
            await page.goto(url, timeout=timeout_seconds * 1000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1200)
            return await page.content()
        except PlaywrightTimeoutError:
            return None
        except Exception:
            return None
        finally:
            await context.close()
            await browser.close()


def _fetch_with_requests(
    url: str,
    timeout_seconds: int,
    allow_insecure_ssl: bool,
) -> str | None:
    try:
        response = requests.get(
            url,
            timeout=timeout_seconds,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            verify=not allow_insecure_ssl,
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def scrape_url(
    url: str,
    timeout_seconds: int = 20,
    delay_seconds: float = 1.5,
    obey_robots_txt: bool = True,
    allow_insecure_ssl: bool = False,
    enable_playwright: bool = True,
    prefer_requests_first: bool = False,
) -> dict[str, Any] | None:
    if not is_allowed_by_robots(
        url=url,
        obey_robots_txt=obey_robots_txt,
        allow_insecure_ssl=allow_insecure_ssl,
    ):
        return None

    time.sleep(max(0.5, delay_seconds) + random.uniform(0.1, 0.7))

    html: str | None = None
    if prefer_requests_first:
        html = _fetch_with_requests(url, timeout_seconds, allow_insecure_ssl)
        if not html and enable_playwright:
            try:
                html = asyncio.run(_fetch_with_playwright(url, timeout_seconds, allow_insecure_ssl))
            except RuntimeError:
                html = None
    else:
        if enable_playwright:
            try:
                html = asyncio.run(_fetch_with_playwright(url, timeout_seconds, allow_insecure_ssl))
            except RuntimeError:
                html = None
        if not html:
            html = _fetch_with_requests(url, timeout_seconds, allow_insecure_ssl)

    if not html:
        return None

    try:
        return parse_html_content(url=url, html=html)
    except Exception:
        return None
