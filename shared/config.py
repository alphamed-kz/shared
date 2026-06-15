"""Base pydantic-settings configuration shared across server components."""
from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_asyncpg_query(value: str) -> str:
    """Translate common psycopg/provider URL params to asyncpg-compatible params."""
    if not value.startswith("postgresql+asyncpg://"):
        return value

    parts = urlsplit(value)
    query_items = parse_qsl(parts.query, keep_blank_values=True)
    normalized: list[tuple[str, str]] = []
    has_ssl = False

    for key, item_value in query_items:
        if key == "ssl":
            has_ssl = True
            normalized.append((key, item_value))
        elif key == "sslmode":
            if not has_ssl and item_value and item_value != "disable":
                normalized.append(("ssl", item_value))
                has_ssl = True
        elif key == "channel_binding":
            continue
        else:
            normalized.append((key, item_value))

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(normalized),
            parts.fragment,
        )
    )


class SharedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/alphamed"
    db_schema: str = "alphamed"
    debug: bool = False

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Accept common provider Postgres URLs and normalize to async SQLAlchemy."""
        if value.startswith("postgres://"):
            value = "postgresql+asyncpg://" + value.removeprefix("postgres://")
        elif value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        return _normalize_asyncpg_query(value)


settings = SharedSettings()
