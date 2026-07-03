"""Parse Meetup HTML into raw event dicts.

BeautifulSoup-first: Meetup server-renders schema.org JSON-LD (an ItemList of
Events), so no headless browser is required. If Meetup ever moves this behind
client-side hydration, a Playwright fallback would slot in at ``fetch`` time
(the scraper/mapper stay unchanged).
"""

import json

from bs4 import BeautifulSoup


def _extract_events(data: object) -> list[dict]:
    events: list[dict] = []
    items: list = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        node_type = data.get("@type")
        if node_type == "ItemList":
            items = [el.get("item", el) for el in data.get("itemListElement", [])]
        elif node_type == "Event":
            items = [data]
        elif "@graph" in data:
            items = data["@graph"]
    for item in items:
        if isinstance(item, dict) and item.get("@type") == "Event":
            events.append(item)
    return events


def parse_events(html: str) -> list[dict]:
    """Return raw schema.org Event dicts found in the page's JSON-LD."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        events.extend(_extract_events(data))
    return events
