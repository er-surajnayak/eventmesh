"""Supabase JWT verification.

FastAPI is a pure resource server: it never issues or refreshes tokens, it only
validates them. Asymmetric (JWKS) verification is preferred; a legacy HS256
shared secret is supported as a fallback for projects not yet migrated.

Wired into protected routes in Phase 1 (Authentication).
"""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.logging import get_logger

logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)
_jwks_client: jwt.PyJWKClient | None = None


class AuthUser(BaseModel):
    """Identity extracted from a verified Supabase JWT."""

    id: str
    email: str | None = None
    role: str | None = None
    claims: dict


def _get_jwks_client() -> jwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not settings.jwks_url:
            raise UnauthorizedError("Authentication is not configured (missing SUPABASE_URL/JWKS).")
        _jwks_client = jwt.PyJWKClient(settings.jwks_url)
    return _jwks_client


def _decode(token: str) -> dict:
    common = {"audience": settings.supabase_jwt_aud, "options": {"require": ["exp", "sub"]}}
    # Prefer asymmetric verification via JWKS.
    if settings.jwks_url:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token).key
        return jwt.decode(token, signing_key, algorithms=["ES256", "RS256"], **common)
    # Fallback: legacy symmetric shared secret.
    if settings.supabase_jwt_secret:
        return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **common)
    raise UnauthorizedError("Authentication is not configured.")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AuthUser:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token.")
    try:
        payload = _decode(credentials.credentials)
    except UnauthorizedError:
        raise
    except Exception as exc:  # noqa: BLE001 - any decode failure is an auth failure
        logger.warning("jwt_verification_failed", error=str(exc))
        raise UnauthorizedError("Invalid or expired token.") from exc

    return AuthUser(
        id=str(payload["sub"]),
        email=payload.get("email"),
        role=payload.get("role"),
        claims=payload,
    )


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
