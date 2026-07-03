"""Provider health metrics and synchronization report models."""

from datetime import datetime

from pydantic import BaseModel


class ProviderHealth(BaseModel):
    provider: str
    ok: bool
    fetched: int = 0
    valid: int = 0
    stored: int = 0
    duplicates: int = 0
    errors: list[str] = []
    duration_ms: int = 0


class SyncReport(BaseModel):
    run_id: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    providers: list[ProviderHealth] = []
    totals: dict = {}
