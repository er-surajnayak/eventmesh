"""Search query-building tests — filters + ordering (no DB, pure functions)."""

import pytest

from app.modules.search.base import SearchQuery
from app.modules.search.sql_backend import build_where, order_by


def test_empty_query_has_no_clauses():
    clauses, params = build_where(SearchQuery())
    assert clauses == []
    assert params == {}


def test_query_text_uses_fts_and_binds_trimmed_q():
    clauses, params = build_where(SearchQuery(q="  jazz night  "))
    assert "search_vector @@ websearch_to_tsquery('english', :q)" in clauses
    assert params["q"] == "jazz night"


def test_blank_query_text_is_not_a_search():
    q = SearchQuery(q="   ")
    assert q.has_query is False
    clauses, _ = build_where(q)
    assert not any("websearch_to_tsquery" in c for c in clauses)


def test_city_and_category_are_case_insensitive():
    clauses, params = build_where(SearchQuery(city="Berlin", category="Music"))
    assert "lower(city) = lower(:city)" in clauses
    assert "lower(category) = lower(:category)" in clauses
    assert params == {"city": "Berlin", "category": "Music"}


def test_source_maps_to_provider():
    clauses, params = build_where(SearchQuery(source="meetup"))
    assert "provider = :source" in clauses
    assert params["source"] == "meetup"


def test_boolean_filters_bind_explicit_values():
    clauses, params = build_where(SearchQuery(is_free=True, is_online=False))
    assert "is_free = :is_free" in clauses
    assert "is_online = :is_online" in clauses
    assert params["is_free"] is True
    assert params["is_online"] is False


@pytest.mark.parametrize(
    "date_range,fragment",
    [
        ("today", "date_trunc('day', now()) + interval '1 day'"),
        ("week", "now() + interval '7 days'"),
        ("month", "now() + interval '30 days'"),
    ],
)
def test_date_range_adds_upper_bound(date_range, fragment):
    clauses, params = build_where(SearchQuery(date_range=date_range))
    assert f"start_time < {fragment}" in clauses
    assert params == {}  # window bound is inlined, not a param


def test_date_range_all_adds_no_bound():
    clauses, _ = build_where(SearchQuery(date_range="all"))
    assert not any("start_time <" in c for c in clauses)


def test_filters_compose():
    clauses, params = build_where(
        SearchQuery(q="rust", city="Bangalore", is_free=True, date_range="week")
    )
    assert len(clauses) == 4
    assert params == {"q": "rust", "city": "Bangalore", "is_free": True}


def test_order_by_ranks_when_searching():
    sql = order_by(has_query=True)
    assert "ts_rank_cd" in sql
    assert "start_time ASC" in sql


def test_order_by_browse_is_soonest_first():
    assert order_by(has_query=False) == "ORDER BY start_time ASC"
