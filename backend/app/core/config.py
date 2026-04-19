from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "EventMesh Backend"
    VERSION: str = "1.0.0"
    DATABASE_URL: str
    EVENTBRITE_API_KEY: Optional[str] = None
    MEETUP_API_KEY: Optional[str] = None
    DEBUG: bool = False
    
    # Scheduler Settings
    FETCH_INTERVAL_MINUTES: int = 30
    CLEANUP_INTERVAL_DAYS: int = 1
    EVENT_RETENTION_DAYS: int = 30

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
