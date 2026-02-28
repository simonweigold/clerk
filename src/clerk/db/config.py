"""Supabase database and storage configuration."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import cast

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from supabase import Client, create_client


class DatabaseConfig:
    """Database configuration from environment variables."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.database_url = os.getenv("DATABASE_URL")
        self.database_url_direct = os.getenv("DATABASE_URL_DIRECT")

    def validate(self) -> None:
        """Validate that required configuration is present."""
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL environment variable required")
        if not self.supabase_anon_key:
            raise ValueError("SUPABASE_ANON_KEY environment variable required")

    def validate_database(self) -> None:
        """Validate database connection configuration."""
        self.validate()
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable required for database operations. "
                "Get the connection string from Supabase Dashboard > Settings > Database."
            )

    @property
    def is_configured(self) -> bool:
        """Check if Supabase is configured."""
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def is_database_configured(self) -> bool:
        """Check if direct database connection is configured."""
        return bool(self.database_url)


@lru_cache
def get_config() -> DatabaseConfig:
    """Get cached database configuration."""
    return DatabaseConfig()


def get_supabase_client(use_service_key: bool = False) -> Client:
    """Get Supabase client for storage and auth operations.

    Args:
        use_service_key: If True, use service role key for admin operations.
                         If False, use anon key for public operations.

    Returns:
        Supabase client instance
    """
    config = get_config()
    config.validate()

    if use_service_key:
        if not config.supabase_service_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY required for admin operations")
        key = config.supabase_service_key
    else:
        key = config.supabase_anon_key

    # validate() ensures these are not None
    return create_client(
        cast(str, config.supabase_url),
        cast(str, key),
    )


# Global engine cache with loop tracking
_engine: AsyncEngine | None = None
_engine_loop = None
_engine_direct: AsyncEngine | None = None
_engine_direct_loop = None


def get_async_engine(direct: bool = False) -> AsyncEngine:
    """Get async SQLAlchemy engine for database access.

    Args:
        direct: If True, use direct connection (for migrations).
                If False, use connection pooler (for normal operations).

    Returns:
        Async SQLAlchemy engine
    """
    global _engine, _engine_loop, _engine_direct, _engine_direct_loop
    import asyncio

    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    config = get_config()
    config.validate_database()

    # PgBouncer compatibility: disable prepared statement caching
    # Supabase uses PgBouncer in transaction mode which doesn't support prepared statements
    # Both parameters are needed for full compatibility
    connect_args = {
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    }

    if direct:
        if _engine_direct is not None and _engine_direct_loop is not current_loop:
            _engine_direct = None
            
        if not config.database_url_direct:
            # Fall back to regular URL if direct not specified
            url = cast(str, config.database_url)
        else:
            url = config.database_url_direct

        if _engine_direct is None:
            _engine_direct = create_async_engine(
                url,
                echo=False,
                pool_recycle=300,
                connect_args=connect_args,
            )
            _engine_direct_loop = current_loop
        return _engine_direct
    else:
        if _engine is not None and _engine_loop is not current_loop:
            _engine = None
            
        if _engine is None:
            _engine = create_async_engine(
                cast(str, config.database_url),
                echo=False,
                pool_recycle=300,
                pool_size=5,
                max_overflow=10,
                connect_args=connect_args,
            )
            _engine_loop = current_loop
        return _engine


def get_async_session_factory(direct: bool = False) -> async_sessionmaker[AsyncSession]:
    """Get async session factory.

    Args:
        direct: If True, use direct connection.

    Returns:
        Async session factory
    """
    engine = get_async_engine(direct=direct)
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@asynccontextmanager
async def get_async_session(
    direct: bool = False,
) -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session as a context manager.

    Args:
        direct: If True, use direct connection.

    Yields:
        Async database session

    Example:
        async with get_async_session() as session:
            result = await session.execute(...)
    """
    factory = get_async_session_factory(direct=direct)
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def close_engines() -> None:
    """Close all database engines. Call on application shutdown."""
    global _engine, _engine_direct

    if _engine is not None:
        await _engine.dispose()
        _engine = None

    if _engine_direct is not None:
        await _engine_direct.dispose()
        _engine_direct = None
