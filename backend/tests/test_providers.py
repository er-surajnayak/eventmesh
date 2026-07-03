"""Unit tests for the provider framework (dedup, validation, BaseProvider)."""

from datetime import UTC, datetime

from app.modules.providers.base import (
    BaseProvider,
    FetchContext,
    NormalizedEvent,
    ProviderMeta,
)
from app.modules.providers.dedup import PROVIDER_PRIORITY, dedup_hash, provider_rank


def _event(**over) -> NormalizedEvent:
    base = dict(
        provider="meetup",
        external_id="abc",
        url="https://x/e/abc",
        title="Rust Meetup!",
        start_time=datetime(2027, 1, 1, 18, 30, tzinfo=UTC),
        city="Berlin",
    )
    base.update(over)
    return NormalizedEvent(**base)


def test_dedup_hash_is_stable_and_buckets_by_hour():
    a = _event(start_time=datetime(2027, 1, 1, 18, 0, tzinfo=UTC))
    b = _event(start_time=datetime(2027, 1, 1, 18, 59, tzinfo=UTC), external_id="def")
    assert dedup_hash(a) == dedup_hash(b)  # same hour bucket


def test_dedup_hash_normalizes_title_and_city():
    a = _event(title="Rust  Meetup!!!")
    b = _event(title="rust meetup", city="berlin")
    assert dedup_hash(a) == dedup_hash(b)


def test_dedup_hash_differs_on_different_event():
    a = _event()
    b = _event(title="Totally Different", city="Paris")
    assert dedup_hash(a) != dedup_hash(b)


def test_provider_rank_priority():
    assert provider_rank("eventbrite") > provider_rank("luma")
    assert provider_rank("unknown") == 0
    assert set(PROVIDER_PRIORITY) >= {"eventbrite", "meetup", "luma"}


class _FakeProvider(BaseProvider):
    meta = ProviderMeta(slug="fake", display_name="Fake", kind="api")

    async def fetch(self, ctx: FetchContext) -> list[dict]:
        return [
            {"id": "1", "title": "Good"},
            {"id": "2", "title": ""},  # invalid -> dropped by validate
            {"id": "bad"},  # raises in normalize -> counted as error
        ]

    def normalize(self, raw: dict) -> NormalizedEvent | None:
        return NormalizedEvent(
            provider="fake",
            external_id=raw["id"],
            url=f"https://fake/{raw['id']}",
            title=raw["title"],  # KeyError for the 'bad' item
            start_time=datetime(2027, 1, 1, tzinfo=UTC),
        )


async def test_base_provider_sync_is_fail_soft():
    result = await _FakeProvider().sync(FetchContext())
    assert result.fetched == 3
    assert len(result.events) == 1  # only the valid one
    assert len(result.errors) == 2  # one invalid + one normalize error
