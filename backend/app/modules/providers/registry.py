"""Registry of enabled providers.

Populated in Phase 4. Providers can ship "dark" behind the ``enabled`` flag so
scaffolded sources (Devfolio, Townscript, Ticketmaster) don't run until ready.
"""

from app.modules.providers.base import EventProvider

_PROVIDERS: list[EventProvider] = []


def enabled_providers() -> list[EventProvider]:
    return [p for p in _PROVIDERS if p.meta.enabled]
