"""Provider registration — called once at application startup.

Providers register only when their credentials/config are present, so a missing
key simply means that source is skipped (not an error).
"""

from app.core.config import settings
from app.core.logging import get_logger
from app.modules.providers import registry
from app.modules.providers.eventbrite.provider import EventbriteProvider

logger = get_logger(__name__)


def register_all() -> None:
    registry._PROVIDERS.clear()
    if settings.eventbrite_api_key:
        registry.register(EventbriteProvider())
    logger.info("providers_registered", providers=[p.meta.slug for p in registry.all_providers()])
