"""Configuration validation tests (fail-fast behaviour)."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_PG = "postgresql+asyncpg://user:pass@db.example.com:5432/eventmesh"


def _settings(**overrides) -> Settings:
    # _env_file=None isolates tests from any local .env.
    return Settings(_env_file=None, **overrides)


def test_rejects_sqlite() -> None:
    with pytest.raises(ValidationError):
        _settings(database_url="sqlite+aiosqlite:///./eventmesh.db")


def test_production_requires_supabase_and_admin_token() -> None:
    with pytest.raises(ValidationError):
        _settings(environment="production", database_url=_PG)


def test_production_rejects_localhost_database() -> None:
    with pytest.raises(ValidationError):
        _settings(
            environment="production",
            database_url="postgresql+asyncpg://postgres:postgres@localhost:5432/eventmesh",
            supabase_url="https://x.supabase.co",
            admin_sync_token="secret",
        )


def test_production_valid_config_passes() -> None:
    s = _settings(
        environment="production",
        database_url=_PG,
        supabase_url="https://x.supabase.co",
        admin_sync_token="secret",
    )
    assert s.is_production
    assert s.jwks_url == "https://x.supabase.co/auth/v1/.well-known/jwks.json"


def test_cors_origins_parsed_from_csv() -> None:
    s = _settings(cors_origins="http://a.com, http://b.com")
    assert s.cors_origins == ["http://a.com", "http://b.com"]


def test_development_allows_local_defaults() -> None:
    s = _settings()
    assert not s.is_production
    assert s.database_url.startswith("postgresql+asyncpg://")
