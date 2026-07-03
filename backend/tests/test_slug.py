"""Unit tests for slug generation (pure function, no DB)."""

import pytest

from app.shared.slugs import slugify


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Acme Events", "acme-events"),
        ("  Spaces   Everywhere  ", "spaces-everywhere"),
        ("Weird!!!Chars@@@Here", "weird-chars-here"),
        ("UPPER lower 123", "upper-lower-123"),
        ("---leading-and-trailing---", "leading-and-trailing"),
        ("é", "item"),  # non-ascii stripped -> fallback
        ("", "item"),  # empty -> fallback
    ],
)
def test_slugify(value: str, expected: str) -> None:
    assert slugify(value) == expected
