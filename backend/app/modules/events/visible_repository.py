"""Read access to the visible_events VIEW (native + canonical-imported).

Browse and search operate here — never on provider-specific imported records.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_COLUMNS = (
    "kind, id, slug, title, description, image_url, start_time, end_time, timezone, "
    "city, venue, is_online, is_free, price_cents, currency, category, url, provider, "
    "sources, organization_id"
)


class VisibleEventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        q: str | None = None,
        city: str | None = None,
        is_free: bool | None = None,
        is_online: bool | None = None,
    ) -> tuple[int, list[dict]]:
        clauses: list[str] = []
        params: dict = {"limit": limit, "offset": offset}
        if q:
            clauses.append("title ILIKE :q")
            params["q"] = f"%{q}%"
        if city:
            clauses.append("lower(city) = lower(:city)")
            params["city"] = city
        if is_free is not None:
            clauses.append("is_free = :is_free")
            params["is_free"] = is_free
        if is_online is not None:
            clauses.append("is_online = :is_online")
            params["is_online"] = is_online

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        total = (
            await self._db.execute(text(f"SELECT count(*) FROM visible_events {where}"), params)
        ).scalar() or 0
        rows = (
            (
                await self._db.execute(
                    text(
                        f"SELECT {_COLUMNS} FROM visible_events {where} "
                        "ORDER BY start_time ASC LIMIT :limit OFFSET :offset"
                    ),
                    params,
                )
            )
            .mappings()
            .all()
        )
        return total, [dict(r) for r in rows]
