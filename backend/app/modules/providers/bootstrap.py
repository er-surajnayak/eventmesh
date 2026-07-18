"""Provider registration — called once at application startup.

Providers register here once at startup. Credentialed transports degrade to
their configured fallback or skip only that transport when credentials are
absent; credential-free discovery providers remain available.
"""

from app.core.logging import get_logger
from app.modules.providers import registry
from app.modules.providers.eventbrite.provider import EventbriteProvider
from app.modules.providers.luma.provider import LumaProvider
from app.modules.providers.meetup.provider import MeetupProvider

logger = get_logger(__name__)


def register_all() -> None:
    registry._PROVIDERS.clear()
    # Eventbrite uses the official API when a token is configured and falls
    # back to bounded public HTML discovery, so it remains available without
    # credentials.
    registry.register(EventbriteProvider())
    # Scrapers need no credentials.
    registry.register(MeetupProvider())
    registry.register(LumaProvider())
    logger.info("providers_registered", providers=[p.meta.slug for p in registry.all_providers()])
