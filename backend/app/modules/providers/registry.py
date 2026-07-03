"""Registry of providers.

Providers register here (in their module import) so the sync orchestrator can
enumerate them without importing each concretely. Empty until 4B+ land.
"""

from app.modules.providers.base import BaseProvider

_PROVIDERS: list[BaseProvider] = []


def register(provider: BaseProvider) -> None:
    _PROVIDERS.append(provider)


def enabled_providers() -> list[BaseProvider]:
    return [p for p in _PROVIDERS if p.meta.enabled]


def all_providers() -> list[BaseProvider]:
    return list(_PROVIDERS)
