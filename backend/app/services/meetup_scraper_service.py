import httpx
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from app.schemas.event import EventCreate

class MeetupScraperService:
    # Meetup search pages use this structure
    SEARCH_URL = "https://www.meetup.com/find/?source=EVENTS"

    async def fetch_events(self, city: str = "San Francisco") -> List[EventCreate]:
        # Simple slug mapping
        slugs = {
            "San Francisco": "us--ca--san-francisco",
            "London": "gb--greater-london--london",
            "New York": "us--ny--new-york",
            "Bangalore": "in--bangalore",
            "Berlin": "de--berlin"
        }
        loc = slugs.get(city, "us--ca--san-francisco")
        url = f"https://www.meetup.com/find/?location={loc}&source=EVENTS"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Check for ItemList JSON-LD
                scripts = soup.find_all('script', type='application/ld+json')
                events = []
                
                for script in scripts:
                    try:
                        data = json.loads(script.string or '')
                        items = []
                        if isinstance(data, list):
                            items = data
                        elif data.get('@type') == 'ItemList':
                            items = [i.get('item', i) for i in data.get('itemListElement', [])]
                        
                        for item in items:
                            if item.get('@type') == 'Event':
                                events.append(self._normalize(item, city))
                    except:
                        continue
                
                # Fallback to __NEXT_DATA__ if JSON-LD is missing
                if not events:
                    next_data = soup.find('script', id='__NEXT_DATA__')
                    if next_data:
                        data = json.loads(next_data.string)
                        # Search for objects with 'title' and 'dateTime'
                        def find_events(obj):
                            if isinstance(obj, dict):
                                if 'title' in obj and 'dateTime' in obj and 'eventUrl' in obj:
                                    events.append(self._normalize(obj, city))
                                for v in obj.values():
                                    find_events(v)
                            elif isinstance(obj, list):
                                for i in obj:
                                    find_events(i)
                        find_events(data)

                return events
            except Exception as e:
                print(f"Error scraping Meetup: {e}")
                return []

    def _normalize(self, item: dict, city: str) -> EventCreate:
        # Handle both JSON-LD and NEXT_DATA formats
        title = item.get('name') or item.get('title', 'Meetup Event')
        url = item.get('url') or item.get('eventUrl') or f"https://www.meetup.com/events/{item.get('id')}"
        
        try:
            date_str = item.get('startDate') or item.get('dateTime')
            start_time = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            start_time = datetime.utcnow()

        # Check for virtual
        is_online = 'virtual' in title.lower() or 'online' in title.lower() or item.get('eventAttendanceMode') == 'https://schema.org/OnlineEventAttendanceMode'

        return EventCreate(
            title=title,
            description=item.get('description', ''),
            platform="Meetup (Scraped)",
            platform_event_id=str(item.get('id', hash(url))),
            url=url,
            start_time=start_time,
            city=city,
            location=item.get('location', {}).get('name') if isinstance(item.get('location'), dict) else "TBD",
            is_free=True, # Often free for Discovery
            is_online=is_online,
            image_url=item.get('image', [None])[0] if isinstance(item.get('image'), list) else item.get('image')
        )
