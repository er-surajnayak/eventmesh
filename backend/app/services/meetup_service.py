import httpx
from datetime import datetime
from typing import List, Dict, Any
from app.schemas.event import EventCreate
from app.core.config import settings

class MeetupService:
    GRAPHQL_URL = "https://api.meetup.com/gql"

    def __init__(self):
        # Meetup uses OAuth or specific API tokens
        self.api_key = getattr(settings, "MEETUP_API_KEY", None)

    async def fetch_events(self, city: str = "Bangalore") -> List[EventCreate]:
        # Meetup GraphQL query
        query = """
        query ($lat: Float!, $lon: Float!) {
          keywordSearch(filter: { lat: $lat, lon: $lon, radius: 50 }, query: "tech") {
            edges {
              node {
                id
                title
                description
                dateTime
                eventUrl
                isFree
              }
            }
          }
        }
        """
        
        coords = {
            "Bangalore": (12.9716, 77.5946),
            "San Francisco": (37.7749, -122.4194),
            "London": (51.5074, -0.1278),
            "New York": (40.7128, -74.0060),
            "Berlin": (52.5200, 13.4050)
        }
        lat, lon = coords.get(city, (37.7749, -122.4194))

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Content-Type": "application/json"
                }
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                # Try the common GraphQL endpoint
                response = await client.post(
                    "https://www.meetup.com/gql", 
                    json={"query": query, "variables": {"lat": lat, "lon": lon}},
                    headers=headers
                )
                
                if response.status_code == 401:
                    print("Meetup: Unauthorized. Continuing with empty list.")
                    return []
                    
                response.raise_for_status()
                data = response.json()
                
                events = []
                edges = data.get("data", {}).get("keywordSearch", {}).get("edges", [])
                for edge in edges:
                    item = edge["node"]
                    events.append(self._normalize(item, city))
                return events
            except Exception as e:
                print(f"Error fetching from Meetup: {e}")
                return []

    def _normalize(self, item: Dict[str, Any], city: str) -> EventCreate:
        try:
            # Meetup dateTime usually ISO: "2026-04-24T18:30:00Z"
            dt_str = item["dateTime"]
            start_time = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            start_time = datetime.utcnow()

        return EventCreate(
            title=item["title"],
            description=item.get("description", ""),
            platform="Meetup",
            platform_event_id=item["id"],
            url=item["eventUrl"],
            start_time=start_time,
            city=city,
            location=item.get("venue", {}).get("name") if item.get("venue") else "TBD",
            is_free=item.get("isFree", True),
            image_url=item.get("images", [{}])[0].get("baseUrl") if item.get("images") else None
        )
