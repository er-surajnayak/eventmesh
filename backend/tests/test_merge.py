"""Merge engine tests — deterministic canonical selection (no DB)."""

from app.modules.sync.merge import _completeness, select_canonical
from app.modules.sync.models import ImportedEvent


def _ev(provider: str, external_id: str, **fields) -> ImportedEvent:
    event = ImportedEvent(provider=provider, external_id=external_id)
    for key, value in fields.items():
        setattr(event, key, value)
    return event


def test_canonical_prefers_higher_provider_priority():
    luma = _ev("luma", "a", description="x", image_url="y", venue="v", city="c")  # complete
    eventbrite = _ev("eventbrite", "b")  # sparse, but higher priority
    assert select_canonical([luma, eventbrite]) is eventbrite
    assert select_canonical([eventbrite, luma]) is eventbrite  # order-independent


def test_completeness_breaks_priority_tie():
    sparse = _ev("meetup", "a", description="d")  # completeness 1
    rich = _ev("meetup", "b", description="d", image_url="i", city="c")  # completeness 3
    assert select_canonical([sparse, rich]) is rich


def test_stable_tiebreak_on_provider_external_id():
    a = _ev("meetup", "zzz")
    b = _ev("meetup", "aaa")
    assert select_canonical([a, b]).external_id == "aaa"
    assert select_canonical([b, a]).external_id == "aaa"  # deterministic regardless of order


def test_completeness_counts_present_fields():
    assert _completeness(_ev("meetup", "a")) == 0
    assert _completeness(_ev("meetup", "a", description="d", image_url="i", price_cents=100)) == 3
