"""
Async SQLAlchemy engine + session factory.

Design notes
------------
* The engine is created **lazily** via ``init_db()`` so tests can inject a
  test-specific URL before the first session is opened.
* ``get_db()`` is a FastAPI dependency; tests override it via
  ``app.dependency_overrides``.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def init_db(database_url: str, echo: bool = False, **engine_kwargs) -> None:
    """
    Initialise the global engine + session factory.

    Call this once at application startup (lifespan) or in test fixtures.
    Calling it a second time replaces the existing engine — useful in tests.
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,
        **engine_kwargs,
    )
    _session_factory = async_sessionmaker(
        _engine, expire_on_commit=False, class_=AsyncSession
    )


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database not initialised — call init_db() first.")
    return _engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a DB session with auto-commit / rollback."""
    if _session_factory is None:
        raise RuntimeError("Database not initialised — call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
