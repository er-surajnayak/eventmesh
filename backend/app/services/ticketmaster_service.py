import httpx
from datetime import datetime
from typing import List, Dict, Any
from app.core.config import settings
from app.schemas.event import EventCreate

class TicketmasterService:
    BASE_URL = "https://app.ticketmaster.com/discovery/v2"

    def __init__(self):
        # We can use a public key if available or ask the user for one
        # Ticketmaster has a very generous free tier
        self.api_key = getattr(settings, "TICKETMASTER_API_KEY", "7elS776zZ76j25w4j4Z") # Placeholder for demo or user key

    async def fetch_events(self, city: str = "San Francisco") -> List[EventCreate]:
        if not self.api_key:
            return []

        params = {
            "apikey": self.api_key,
            "city": city,
            "classificationName": "technology,music,arts",
            "size": 20,
            "sort": "date,asc"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.BASE_URL}/events.json", params=params)
                response.raise_for_status()
                data = response.json()
                
                events = []
                embedded = data.get("_embedded", {})
                for item in embedded.get("events", []):
                    events.append(self._normalize(item, city))
                return events
            except Exception as e:
                print(f"Error fetching from Ticketmaster: {e}")
                return []

    def _normalize(self, item: Dict[str, Any], city: str) -> EventCreate:
        start_raw = item["dates"]["start"].get("dateTime")
        if start_raw:
            start_time = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        else:
            # Fallback for local date
            local_date = item["dates"]["start"].get("localDate")
            local_time = item["dates"]["start"].get("localTime", "00:00:00")
            start_time = datetime.fromisoformat(f"{local_date}T{local_time}")

        venue = item.get("_embedded", {}).get("venues", [{}])[0]
        
        return EventCreate(
            title=item["name"],
            description=item.get("info", item.get("description", "")),
            platform="Ticketmaster",
            platform_event_id=item["id"],
            url=item["url"],
            start_time=start_time,
            city=city,
            location=venue.get("name") or venue.get("address", {}).get("line1"),
            is_free=False, # Ticketmaster is mostly paid
            image_url=item.get("images", [{}])[0].get("url")
        )
