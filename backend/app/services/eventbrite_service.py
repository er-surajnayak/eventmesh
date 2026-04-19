import httpx
from datetime import datetime
from typing import List, Dict, Any
from app.core.config import settings
from app.schemas.event import EventCreate

class EventbriteService:
    BASE_URL = "https://www.eventbriteapi.com/v3"

    def __init__(self):
        self.api_key = settings.EVENTBRITE_API_KEY

    async def fetch_events(self, city: str = "San Francisco") -> List[EventCreate]:
        if not self.api_key:
            return []

        # Eventbrite uses a Private Token as a Bearer token
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # We search for organizations/events or uses discovery endpoints
        # Note: Eventbrite search API is restricted to users/orgs usually.
        # For public discovery, they often expect coordinate-based search.
        params = {
            "location.address": city,
            "expand": "venue",
            "status": "live",
            "sort_by": "date"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Organizations endpoint or discovery (requires specific permissions)
                # This is the standard search endpoint for organizations
                response = await client.get(f"{self.BASE_URL}/events/search/", params=params, headers=headers)
                
                if response.status_code == 401:
                    print("Eventbrite: Unauthorized. Please check your API key.")
                    return []
                
                response.raise_for_status()
                data = response.json()
                
                events = []
                for item in data.get("events", []):
                    events.append(self._normalize(item, city))
                return events
            except Exception as e:
                print(f"Error fetching from Eventbrite: {e}")
                return []

    def _normalize(self, item: Dict[str, Any], city: str) -> EventCreate:
        # Standard Eventbrite UTC format: "2026-04-24T18:30:00Z"
        start_raw = item["start"]["utc"]
        end_raw = item.get("end", {}).get("utc")
        
        start_time = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(end_raw.replace("Z", "+00:00")) if end_raw else None
        
        return EventCreate(
            title=item["name"]["text"],
            description=item.get("description", {}).get("text", ""),
            platform="Eventbrite",
            platform_event_id=item["id"],
            url=item["url"],
            start_time=start_time,
            end_time=end_time,
            city=city,
            location=item.get("venue", {}).get("name") or "Various Locations",
            is_free=item.get("is_free", True),
            image_url=item.get("logo", {}).get("original", {}).get("url")
        )
