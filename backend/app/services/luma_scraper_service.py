import httpx
import json
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List
from app.schemas.event import EventCreate

class LumaScraperService:
    BASE_URL = "https://lu.ma/discover"

    async def fetch_events(self, city: str = "San Francisco") -> List[EventCreate]:
        # Luma often uses specific slugs for discovery
        city_slug = city.lower().replace(" ", "-")
        url = f"https://lu.ma/{city_slug}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        }

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=headers)
                # Luma often returns 200 even if page is somewhat different
                if response.status_code != 200:
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Luma embeds data in a script tag with id="__NEXT_DATA__"
                script_tag = soup.find('script', id='__NEXT_DATA__')
                
                events = []
                if script_tag:
                    data = json.loads(script_tag.string)
                    # Luma's Next.js structure
                    props = data.get('props', {}).get('pageProps', {})
                    initial_events = props.get('initialEvents', []) or props.get('events', [])
                    
                    if not initial_events and 'apolloState' in props:
                        # Alternative structure sometimes used
                        apollo = props['apolloState']
                        for key, val in apollo.items():
                            if key.startswith('Event:'):
                                initial_events.append(val)

                    for item in initial_events:
                        events.append(self._normalize(item, city))
                
                return events
            except Exception as e:
                print(f"Error scraping Luma: {e}")
                return []

    def _normalize(self, item: dict, city: str) -> EventCreate:
        title = item.get('name') or item.get('title', 'Luma Event')
        url_slug = item.get('url_slug') or item.get('id')
        url = f"https://lu.ma/{url_slug}"
        
        # Luma dates are usually ISO or timestamp
        try:
            start_str = item.get('start_at') or item.get('start_time')
            start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        except:
            start_time = datetime.utcnow()

        is_online = item.get('is_online', False) or any(kw in title.lower() for kw in ['online', 'virtual', 'zoom'])
        
        return EventCreate(
            title=title,
            description=item.get('description_short', item.get('description', '')),
            platform="Luma (Scraped)",
            platform_event_id=item.get('id'),
            url=url,
            start_time=start_time,
            city=city,
            location=item.get('location_name', 'Online' if is_online else 'TBD'),
            is_free=item.get('price_cents', 0) == 0,
            is_online=is_online,
            image_url=item.get('cover_url') or item.get('image_url')
        )
