"""Async SQLAlchemy engine, session factory, and dependency helper."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config import settings


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5,
    max_overflow=10,
)


@event.listens_for(engine.sync_engine, "connect")
def set_search_path(dbapi_connection, _connection_record) -> None:
    """Route unqualified ORM tables to the configured project schema."""
    schema = settings.db_schema.strip()
    if not schema:
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute(f"SET search_path TO {_quote_identifier(schema)}, public")
    finally:
        cursor.close()


AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager / FastAPI dependency that yields a DB session."""
    async with AsyncSessionLocal() as session:
        yield session
