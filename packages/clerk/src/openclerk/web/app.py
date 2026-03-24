"""FastAPI application factory for OpenClerk API."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from openclerk.db.config import close_engines, init_engines, get_config
from openclerk.mcp_client import close_mcp_servers, init_mcp_servers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    # Initialize database engines
    await init_engines()
    # Initialize MCP servers
    await init_mcp_servers()
    yield
    # Cleanup
    await close_mcp_servers()
    await close_engines()


class AuthStateMiddleware(BaseHTTPMiddleware):
    """Middleware to copy session user to request.state for auth dependencies."""

    async def dispatch(self, request: Request, call_next):
        # Copy user from session to state so get_optional_user can find it
        user = request.session.get("user")
        if user:
            request.state.user = user
        return await call_next(request)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="OpenClerk API",
        description="API for Community Library of Executable Reasoning Kits",
        version="0.1.0",
        docs_url="/docs" if os.getenv("ENV") == "development" else None,
        redoc_url="/redoc" if os.getenv("ENV") == "development" else None,
        lifespan=lifespan,
    )

    # CORS middleware for web frontend (add first - runs last/wraps everything)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth state middleware - copies session user to request.state
    # Must be added before SessionMiddleware so it runs AFTER SessionMiddleware
    app.add_middleware(AuthStateMiddleware)

    # Session middleware for auth cookies (add last - runs first/innermost)
    app.add_middleware(
        SessionMiddleware,
        secret_key=get_config().session_secret_key,
        session_cookie="clerk_session",
        max_age=60 * 60 * 24 * 7,  # 1 week
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": "openclerk-api"}

    # Register API routes
    from openclerk.web.routes.api import router as api_router

    # Include API router with version prefix
    app.include_router(api_router, prefix="/api/v1")

    # Also include at /api for backwards compatibility during transition
    app.include_router(api_router, prefix="/api")

    return app
