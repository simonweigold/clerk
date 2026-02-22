"""FastAPI application factory for CLERK web UI."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from ..db.config import close_engines, get_config

# Paths
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"
# React SPA build output — checked at startup
SPA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"


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

    # Static files (legacy)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Templates (shared instance accessible via app.state)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    # Inject config into templates
    config = get_config()
    templates.env.globals["supabase_configured"] = config.is_configured
    templates.env.globals["db_configured"] = config.is_database_configured

    # Register API routes
    from .routes.api import router as api_router

    app.include_router(api_router, prefix="/api")

    # Serve React SPA if build exists
    spa_index = SPA_DIR / "index.html"
    if SPA_DIR.is_dir() and spa_index.is_file():
        # Serve SPA static assets (JS, CSS, images)
        app.mount(
            "/assets",
            StaticFiles(directory=str(SPA_DIR / "assets")),
            name="spa-assets",
        )
        # Serve files from SPA public dir (fonts, vite.svg, etc.)
        app.mount(
            "/fonts",
            StaticFiles(directory=str(SPA_DIR / "fonts")),
            name="spa-fonts",
        )

        # SPA fallback: serve index.html for all non-API, non-static routes
        @app.get("/{full_path:path}")
        async def spa_fallback(request: Request, full_path: str) -> FileResponse:
            """Serve React SPA for client-side routing."""
            # Check if a specific file exists in dist
            file_path = SPA_DIR / full_path
            if full_path and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(spa_index)

    else:
        # No SPA build — use legacy Jinja pages
        from .routes.pages import router as pages_router

        app.include_router(pages_router)

    return app

