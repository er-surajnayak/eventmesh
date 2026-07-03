"""Responsible HTML fetcher for Meetup.

Realistic headers, retry/backoff on 429/5xx, and a minimum delay between requests
(rate limiting) so we stay a well-behaved client. Returns HTML text for the
scraper to parse — no browser needed (Meetup server-renders JSON-LD).
"""

import asyncio
import time

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class MeetupClient:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient | None = None,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        max_backoff: float = 20.0,
        min_delay: float = 1.0,
    ) -> None:
        self._client = client
        self._owns_client = client is None
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._max_backoff = max_backoff
        self._min_delay = min_delay
        self._last_request: float | None = None

    async def __aenter__(self) -> "MeetupClient":
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _throttle(self) -> None:
        if self._min_delay > 0 and self._last_request is not None:
            elapsed = time.monotonic() - self._last_request
            if elapsed < self._min_delay:
                await asyncio.sleep(self._min_delay - elapsed)
        self._last_request = time.monotonic()

    def _retry_delay(self, attempt: int, response: httpx.Response) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), self._max_backoff)
            except ValueError:
                pass
        return min(self._backoff_base * (2**attempt), self._max_backoff)

    async def get_html(self, url: str) -> str:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
        last: httpx.Response | None = None
        for attempt in range(self._max_retries + 1):
            await self._throttle()
            response = await self._client.get(url, headers=_HEADERS)
            if response.status_code == 429 or response.status_code >= 500:
                last = response
                if attempt < self._max_retries:
                    delay = self._retry_delay(attempt, response)
                    logger.warning(
                        "meetup_retry", status=response.status_code, attempt=attempt, delay=delay
                    )
                    await asyncio.sleep(delay)
                    continue
            response.raise_for_status()
            return response.text
        assert last is not None
        last.raise_for_status()
        return ""  # unreachable
