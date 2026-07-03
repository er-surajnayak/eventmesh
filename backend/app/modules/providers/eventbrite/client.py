"""Thin Eventbrite v3 client: Bearer auth, pagination, retry/backoff, rate-limit."""

import asyncio

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class EventbriteClient:
    def __init__(
        self,
        token: str,
        base_url: str,
        *,
        client: httpx.AsyncClient | None = None,
        max_retries: int = 4,
        backoff_base: float = 0.5,
        max_backoff: float = 30.0,
        max_pages: int = 50,
    ) -> None:
        self._token = token
        self._base = base_url.rstrip("/")
        self._client = client
        self._owns_client = client is None
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._max_backoff = max_backoff
        self._max_pages = max_pages

    async def __aenter__(self) -> "EventbriteClient":
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0)
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}

    def _retry_delay(self, attempt: int, response: httpx.Response) -> float:
        # Rate-limit awareness: honour Retry-After when present, else exponential backoff.
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), self._max_backoff)
            except ValueError:
                pass
        return min(self._backoff_base * (2**attempt), self._max_backoff)

    async def get(self, path: str, params: dict | None = None) -> dict:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=20.0)
        url = f"{self._base}{path}"
        last: httpx.Response | None = None
        for attempt in range(self._max_retries + 1):
            response = await self._client.get(url, params=params, headers=self._headers)
            if response.status_code == 429 or response.status_code >= 500:
                last = response
                if attempt < self._max_retries:
                    delay = self._retry_delay(attempt, response)
                    logger.warning(
                        "eventbrite_retry",
                        status=response.status_code,
                        attempt=attempt,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
                    continue
            response.raise_for_status()
            return response.json()
        # Retries exhausted on a retryable status.
        assert last is not None
        last.raise_for_status()
        return {}  # unreachable; keeps type checkers happy

    async def paginate(self, path: str, params: dict, key: str) -> list[dict]:
        """Collect ``key`` items across continuation-token pages (bounded)."""
        items: list[dict] = []
        continuation: str | None = None
        for _ in range(self._max_pages):
            page_params = dict(params)
            if continuation:
                page_params["continuation"] = continuation
            data = await self.get(path, page_params)
            items.extend(data.get(key, []))
            pagination = data.get("pagination") or {}
            if pagination.get("has_more_items") and pagination.get("continuation"):
                continuation = pagination["continuation"]
            else:
                break
        return items
