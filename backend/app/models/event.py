import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    platform = Column(String(50), nullable=False) # eventbrite, meetup, etc.
    platform_event_id = Column(String(100), nullable=True)
    url = Column(String(512), unique=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    city = Column(String(100), nullable=False)
    location = Column(String(512), nullable=True) # venue
    is_free = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    image_url = Column(String(1024), nullable=True)
    status = Column(String(20), default="upcoming") # upcoming, past
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for performance
    __table_args__ = (
        Index("ix_events_start_time", "start_time"),
        Index("ix_events_city", "city"),
        Index("ix_events_status", "status"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "platform": self.platform,
            "date": self.start_time.isoformat(),
            "city": self.city,
            "venue": self.location,
            "price": "Free" if self.is_free else "Paid",
            "blurb": self.description,
            "url": self.url,
            "image_url": self.image_url,
        }
