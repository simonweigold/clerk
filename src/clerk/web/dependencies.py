"""FastAPI dependencies for database sessions and authentication."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.config import get_async_session, get_config


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session.

    Yields:
        Async database session
    """
    async with get_async_session() as session:
        yield session


def get_optional_user(request: Request) -> dict | None:
    """Get the current user from the session, if authenticated.

    Args:
        request: The incoming request

    Returns:
        User dict with id, email, display_name or None if not authenticated
    """
    user_data = request.session.get("user")
    if user_data and "id" in user_data:
        return user_data
    return None


def get_required_user(request: Request) -> dict:
    """Get the current user, raising 401 if not authenticated.

    Args:
        request: The incoming request

    Returns:
        User dict with id, email, display_name

    Raises:
        HTTPException: If user is not authenticated
    """
    from fastapi import HTTPException

    user = get_optional_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def get_supabase_auth():
    """Get Supabase client for auth operations.

    Returns:
        Supabase client or None if not configured
    """
    config = get_config()
    if not config.is_configured:
        return None

    from ..db.config import get_supabase_client

    return get_supabase_client()
