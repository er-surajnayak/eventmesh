"""Meetup HTTP fetcher — the shared responsible-scraping client."""

from app.modules.providers.scrape_client import ScrapeClient


class MeetupClient(ScrapeClient):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(source="meetup", **kwargs)
