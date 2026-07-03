"""Slug helpers."""

import re

_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Lowercase, hyphenate, strip non-alphanumerics. Never returns empty."""
    slug = _NON_SLUG.sub("-", value.lower().strip()).strip("-")
    return slug or "org"
