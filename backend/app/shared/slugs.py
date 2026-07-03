"""Shared slug helpers used across domains (organizations, events)."""

import re
from collections.abc import Awaitable, Callable

_NON_SLUG = re.compile(r"[^a-z0-9]+")
_MAX_ATTEMPTS = 50


def slugify(value: str) -> str:
    """Lowercase, hyphenate, strip non-alphanumerics. Never returns empty."""
    slug = _NON_SLUG.sub("-", value.lower().strip()).strip("-")
    return slug or "item"


async def unique_slug(base: str, exists: Callable[[str], Awaitable[bool]]) -> str:
    """Generate a slug from ``base`` that is unique per the async ``exists`` check."""
    root = slugify(base)
    candidate = root
    suffix = 2
    while await exists(candidate):
        candidate = f"{root}-{suffix}"
        suffix += 1
        if suffix > _MAX_ATTEMPTS:
            candidate = f"{root}-{suffix}"
            break
    return candidate
