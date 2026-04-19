from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    platform: str
    url: str
    start_time: datetime
    end_time: Optional[datetime] = None
    city: str
    location: Optional[str] = None
    is_free: bool = True
    is_online: bool = False
    image_url: Optional[str] = None

class EventCreate(EventBase):
    platform_event_id: Optional[str] = None

class EventResponse(BaseModel):
    id: str
    title: str
    platform: str
    date: str  # ISO Format for frontend
    city: str
    venue: Optional[str] = None
    price: str # "Free" or "Paid"
    is_online: bool = False
    category: str = "Uncategorized"
    hue: int = 200 # Default color
    blurb: Optional[str] = None
    url: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class EventListResponse(BaseModel):
    total: int
    events: List[EventResponse]
