"""Shared pagination primitives.

Offset-based for the MVP, with ``next_offset`` exposed so the API contract is
stable when we move hot feeds to keyset/cursor pagination.
"""

from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class PageParams(BaseModel):
    limit: int = 20
    offset: int = 0


def page_params(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


class Page[T](BaseModel):
    total: int
    items: list[T]
    next_offset: int | None = None

    @classmethod
    def build(cls, *, total: int, items: list[T], params: PageParams) -> "Page[T]":
        consumed = params.offset + len(items)
        return cls(
            total=total,
            items=items,
            next_offset=consumed if consumed < total else None,
        )
