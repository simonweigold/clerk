"""FastAPI application factory for CLERK web UI."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from ..db.config import close_engines, get_config

# Paths
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    yield
    await close_engines()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="CLERK",
        description="Community Library of Executable Reasoning Kits",
        lifespan=lifespan,
    )

    # Session middleware for auth cookies
    app.add_middleware(
        SessionMiddleware,
        secret_key="clerk-session-secret-change-in-production",
        session_cookie="clerk_session",
        max_age=60 * 60 * 24 * 7,  # 1 week
    )

    # Static files
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Templates (shared instance accessible via app.state)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    # Inject config into templates
    config = get_config()
    templates.env.globals["supabase_configured"] = config.is_configured
    templates.env.globals["db_configured"] = config.is_database_configured

    # Register routes
    from .routes.pages import router as pages_router
    from .routes.api import router as api_router

    app.include_router(pages_router)
    app.include_router(api_router, prefix="/api")

    return app
