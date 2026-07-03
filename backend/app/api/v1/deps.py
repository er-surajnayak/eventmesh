"""Shared FastAPI dependencies for API v1 (re-exported for convenient imports)."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.pagination import PageParams, page_params
from app.core.security import AuthUser, get_current_user

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
Pagination = Annotated[PageParams, Depends(page_params)]

__all__ = ["DbSession", "CurrentUser", "Pagination"]
