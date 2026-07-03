"""Admin synchronization endpoints (token-guarded).

POST /admin/sync is the target of the GitHub Actions 6-hourly job.
"""

from fastapi import APIRouter, Depends

from app.api.v1.deps import DbSession
from app.core.security import require_admin_token
from app.modules.providers.base import FetchContext
from app.modules.sync.reports import SyncReport
from app.modules.sync.repository import SyncRunRepository
from app.modules.sync.service import SyncOrchestrator

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_token)])

DEFAULT_CITIES = ["San Francisco", "London", "New York", "Bangalore", "Berlin"]


@router.post("/sync", response_model=SyncReport)
async def run_sync(db: DbSession) -> SyncReport:
    ctx = FetchContext(cities=DEFAULT_CITIES)
    return await SyncOrchestrator(db).run(ctx)


@router.get("/sync/runs")
async def list_sync_runs(db: DbSession) -> list[dict]:
    runs = await SyncRunRepository(db).list_recent()
    return [
        {
            "id": str(r.id),
            "status": r.status,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "totals": r.totals,
            "error": r.error,
        }
        for r in runs
    ]
