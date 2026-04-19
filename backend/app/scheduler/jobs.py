import logging
from datetime import datetime, timedelta
from sqlalchemy.future import select
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.services.eventbrite_scraper_service import EventbriteScraperService
from app.services.meetup_scraper_service import MeetupScraperService
from app.services.luma_scraper_service import LumaScraperService
from app.services.ticketmaster_service import TicketmasterService
from app.utils.dedup import save_events
from app.models.event import Event
from app.core.config import settings

logger = logging.getLogger(__name__)

async def fetch_and_store_events():
    """Job to fetch events from external APIs or Scrapers and store them."""
    logger.info("Starting event sync job...")
    
    eb_scraper = EventbriteScraperService()
    mu_scraper = MeetupScraperService()
    luma_scraper = LumaScraperService()
    tm_service = TicketmasterService()
    
    cities = ["San Francisco", "London", "New York", "Bangalore", "Berlin"]
    
    async with AsyncSessionLocal() as db:
        for city in cities:
            logger.info(f"Fetching events for {city}...")
            
            # Fetch from Eventbrite (Scraping)
            eb_events = await eb_scraper.fetch_events(city)
            await save_events(db, eb_events)
            
            # Fetch from Meetup (Scraping)
            mu_events = await mu_scraper.fetch_events(city)
            await save_events(db, mu_events)

            # Fetch from Luma (Scraping)
            luma_events = await luma_scraper.fetch_events(city)
            await save_events(db, luma_events)

            # Fetch from Ticketmaster
            tm_events = await tm_service.fetch_events(city)
            await save_events(db, tm_events)
            
    logger.info("Event sync job completed.")

async def cleanup_old_events():
    """Job to remove events older than specified retention period."""
    logger.info("Starting cleanup job...")
    
    retention_date = datetime.utcnow() - timedelta(days=settings.EVENT_RETENTION_DAYS)
    
    async with AsyncSessionLocal() as db:
        # Delete old events
        query = delete(Event).where(Event.start_time < retention_date)
        await db.execute(query)
        
        # Update status for finished events
        now = datetime.utcnow()
        status_update = (
            select(Event)
            .where(Event.start_time < now)
            .where(Event.status == "upcoming")
        )
        result = await db.execute(status_update)
        to_update = result.scalars().all()
        for e in to_update:
            e.status = "past"
            
        await db.commit()
    
    logger.info("Cleanup job completed.")
