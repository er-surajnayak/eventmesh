from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.event import Event
from app.schemas.event import EventListResponse, EventResponse

router = APIRouter()

# Category Hues for standard categories
HUES = {
    "Tech": 198,
    "Wellness": 140,
    "Film": 320,
    "Music": 290,
    "Design": 12,
    "Startup": 260,
    "Art": 48,
    "Food": 32,
}

PLATFORM_HUES = {
    "Eventbrite": 20,
    "Meetup": 350,
    "Luma": 210,
}

@router.get("/", response_model=EventListResponse)
async def get_events(
    city: Optional[str] = Query(None),
    free: Optional[bool] = Query(None),
    online: Optional[bool] = Query(None),
    date_range: Optional[str] = Query(None, description="today, week, month"),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(Event).filter(Event.status == "upcoming")

    if city and city.lower() != "all cities":
        query = query.filter(func.lower(Event.city) == city.lower())
    
    if free is not None:
        query = query.filter(Event.is_free == free)
    
    if online is not None:
        query = query.filter(Event.is_online == online)
    
    if date_range:
        now = datetime.utcnow()
        if date_range == "today":
            end_date = now + timedelta(days=1)
            query = query.filter(and_(Event.start_time >= now, Event.start_time < end_date))
        elif date_range == "week":
            end_date = now + timedelta(days=7)
            query = query.filter(and_(Event.start_time >= now, Event.start_time < end_date))
        elif date_range == "month":
            end_date = now + timedelta(days=30)
            query = query.filter(and_(Event.start_time >= now, Event.start_time < end_date))

    if search:
        query = query.filter(
            func.lower(Event.title).contains(search.lower()) | 
            func.lower(Event.description).contains(search.lower())
        )

    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Execute main query
    query = query.order_by(Event.start_time.asc()).limit(limit).offset(offset)
    result = await db.execute(query)
    events = result.scalars().all()

    # Transform to frontend format
    response_events = []
    for e in events:
        # Simple category logic or fallback
        category = "Tech" if any(kw in (e.title + (e.description or "")).lower() for kw in ["code", "tech", "api", "ai", "rust", "dev"]) else "General"
        
        hue = HUES.get(category, PLATFORM_HUES.get(e.platform, 200))
        
        response_events.append(EventResponse(
            id=str(e.id),
            title=e.title,
            platform=e.platform,
            date=e.start_time.isoformat(),
            city=e.city,
            venue=e.location,
            price="Free" if e.is_free else "Paid",
            is_online=e.is_online,
            category=category,
            hue=hue,
            blurb=e.description[:150] + "..." if e.description and len(e.description) > 150 else e.description,
            url=e.url,
            image_url=e.image_url
        ))

    return {"total": total, "events": response_events}
