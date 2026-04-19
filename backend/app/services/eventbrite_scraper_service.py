import httpx
import json
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from app.schemas.event import EventCreate

class EventbriteScraperService:
    BASE_URL = "https://www.eventbrite.com/d"

    async def fetch_events(self, city: str = "San Francisco") -> List[EventCreate]:
        # Clean city name for URL
        city_slug = city.lower().replace(" ", "-")
        keywords = ["tech", "music", "arts", "business"]
        all_events = []
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        }

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for kw in keywords:
                url = f"{self.BASE_URL}/{city_slug}/{kw}--events/"
                try:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Eventbrite often embeds data in a script tag with type="application/ld+json"
                    scripts = soup.find_all('script', type='application/ld+json')
                    
                    for script in scripts:
                        try:
                            data = json.loads(script.string or '')
                            # application/ld+json can be a single object or a list
                            if isinstance(data, list):
                                items = data
                            elif isinstance(data, dict) and data.get('@type') == 'ItemList':
                                items = [i.get('item') for i in data.get('itemListElement', [])]
                            else:
                                items = [data] if data.get('@type') == 'Event' else []

                            for item in items:
                                if item and item.get('@type') == 'Event':
                                    all_events.append(self._normalize(item, city))
                        except:
                            continue
                except Exception as e:
                    print(f"Error scraping Eventbrite ({kw}): {e}")
            
            # Simple dedup of results
            unique_events = {e.url: e for e in all_events}.values()
            return list(unique_events)

    def _normalize(self, item: dict, city: str) -> EventCreate:
        title = item.get('name', 'Unknown Event')
        url = item.get('url')
        
        try:
            start_time = datetime.fromisoformat(item['startDate'].replace('Z', '+00:00'))
        except:
            start_time = datetime.utcnow()

        # Extract location name
        location = item.get('location', {})
        location_name = location.get('name') or location.get('address', {}).get('streetAddress') or "Various Locations"

        return EventCreate(
            title=title,
            description=item.get('description', ''),
            platform="Eventbrite (Scraped)",
            platform_event_id=url.split('-')[-1].replace('/', '') if url else None,
            url=url,
            start_time=start_time,
            city=city,
            location=location_name,
            is_free=True, # Hard to determine from LD+JSON easily, defaulting to true for now
            image_url=item.get('image', [None])[0] if isinstance(item.get('image'), list) else item.get('image')
        )
