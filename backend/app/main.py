import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

from app.api.routes import events
from app.core.config import settings
from app.core.database import engine, Base
from app.scheduler.jobs import fetch_and_store_events, cleanup_old_events

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Setup Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        fetch_and_store_events, 
        "interval", 
        minutes=settings.FETCH_INTERVAL_MINUTES,
        id="sync_events"
    )
    scheduler.add_job(
        cleanup_old_events, 
        "interval", 
        days=settings.CLEANUP_INTERVAL_DAYS,
        id="cleanup_events"
    )
    
    scheduler.start()
    logger.info("Scheduler started.")
    
    # Run initial sync in background
    # Note: In production, you might want to handle this differently to not block startup
    # asyncio.create_task(fetch_and_store_events())
    
    yield
    
    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler shut down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://eventmesh-chi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(events.router, prefix="/events", tags=["events"])

@app.get("/sync")
async def trigger_sync(api_key: str = None):
    # Simple check to prevent unauthorized heavy scraping
    if settings.DEBUG or api_key == settings.EVENTBRITE_API_KEY[:8]: 
        from app.scheduler.jobs import fetch_and_store_events
        await fetch_and_store_events()
        return {"status": "sync_completed"}
    return {"status": "unauthorized"}, 401

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

@app.get("/")
async def root():
    return {"message": "Welcome to EventMesh API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
