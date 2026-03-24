"""FastAPI dependencies for database sessions and authentication."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.config import get_async_session, get_config

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session.

    Yields:
        Async database session
    """
    async with get_async_session() as session:
        yield session


def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """Get the current user from the Authorization header, if authenticated.

    Args:
        request: The incoming request
        credentials: Bearer token credentials from Authorization header

    Returns:
        User dict with id, email, display_name or None if not authenticated
    """
    # First try session (for backwards compatibility during transition)
    if hasattr(request.state, "user"):
        return request.state.user

    # Then try Authorization header with Supabase JWT
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        try:
            from ..db.config import get_supabase_client

            client = get_supabase_client()
            if client:
                # Verify the JWT token with Supabase
                response = client.auth.get_user(token)
                if response and response.user:
                    return {
                        "id": str(response.user.id),
                        "email": response.user.email,
                    }
        except Exception:
            # Token verification failed
            pass

    return None


def get_required_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """Get the current user, raising 401 if not authenticated.

    Args:
        request: The incoming request
        credentials: Bearer token credentials from Authorization header

    Returns:
        User dict with id, email, display_name

    Raises:
        HTTPException: If user is not authenticated
    """
    user = get_optional_user(request, credentials)
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
