"""Application configuration, sourced entirely from environment variables."""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # App
    app_name: str = "EventMesh API"
    environment: str = "development"
    debug: bool = False
    version: str = "0.1.0"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # Database (Supabase Postgres via asyncpg)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eventmesh"

    # Supabase Auth
    supabase_url: str | None = None
    supabase_jwt_aud: str = "authenticated"
    supabase_jwks_url: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_service_role_key: str | None = None

    # Admin / sync
    admin_sync_token: str | None = None

    # Events: auto-approve on submit for the MVP (pending_review state retained).
    auto_approve_events: bool = True

    # CORS (comma-separated in env; parsed by the validator below)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # Providers
    eventbrite_api_key: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _validate_configuration(self) -> "Settings":
        """Fail fast on invalid/missing configuration.

        Always enforced: the database must be Postgres (asyncpg); SQLite is banned.
        Production additionally requires auth + admin + a non-local database.
        """
        if not self.database_url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg://' scheme (no SQLite)."
            )

        if self.is_production:
            missing: list[str] = []
            if not self.supabase_url and not self.supabase_jwt_secret:
                missing.append("SUPABASE_URL (or SUPABASE_JWT_SECRET)")
            if not self.admin_sync_token:
                missing.append("ADMIN_SYNC_TOKEN")
            if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
                missing.append("DATABASE_URL (must point to the managed database, not localhost)")
            if missing:
                raise ValueError("Missing required production configuration: " + ", ".join(missing))
        return self

    @property
    def jwks_url(self) -> str | None:
        """Resolved JWKS endpoint for asymmetric Supabase JWT verification."""
        if self.supabase_jwks_url:
            return self.supabase_jwks_url
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return None

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
