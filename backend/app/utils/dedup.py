from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.models.event import Event
from app.schemas.event import EventCreate

async def save_events(db: AsyncSession, events: List[EventCreate]):
    """
    Saves events to the database with deduplication.
    Uses 'url' as the primary key for conflict resolution.
    """
    if not events:
        return

    for event_data in events:
        existing = await db.execute(select(Event).filter(Event.url == event_data.url))
        obj = existing.scalars().first()
        
        if obj:
            # Update existing event
            for key, value in event_data.model_dump().items():
                setattr(obj, key, value)
            obj.is_online = event_data.is_online
            obj.updated_at = func.now()
        else:
            # Create new event
            new_event = Event(**event_data.model_dump())
            db.add(new_event)
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e
