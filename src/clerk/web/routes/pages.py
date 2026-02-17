"""Page routes for CLERK web UI.

Serves HTML pages for kit listing, detail, creation, editing, and execution.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ..dependencies import get_optional_user

router = APIRouter()


def _templates(request: Request):
    """Get templates instance from app state."""
    return request.app.state.templates


def _flash(request: Request, text: str, type: str = "info") -> None:
    """Add a flash message to the session."""
    if "flash" not in request.session:
        request.session["flash"] = []
    request.session["flash"].append({"text": text, "type": type})


def _get_flash(request: Request) -> list[dict]:
    """Get and clear flash messages from the session."""
    messages = request.session.pop("flash", [])
    return messages


# =============================================================================
# HOME — Kit Listing
# =============================================================================


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: dict | None = Depends(get_optional_user)):
    """Kit listing page."""
    from ...db.config import get_config

    templates = _templates(request)
    kits = []

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kits = await repo.list_public()
                for kit in db_kits:
                    kits.append(
                        {
                            "slug": kit.slug,
                            "name": kit.name,
                            "description": kit.description,
                            "is_public": kit.is_public,
                            "created_at": kit.created_at,
                            "updated_at": kit.updated_at,
                        }
                    )
        except Exception:
            # Fall back to local
            pass

    if not kits:
        # Fall back to local filesystem
        try:
            from ...loader import list_reasoning_kits

            local_kits = list_reasoning_kits("reasoning_kits")
            for name in sorted(local_kits):
                kits.append(
                    {
                        "slug": name,
                        "name": name.replace("-", " ").replace("_", " ").title(),
                        "description": None,
                        "is_public": True,
                        "created_at": None,
                        "updated_at": None,
                    }
                )
        except Exception:
            pass

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "kits": kits,
            "user": user,
            "active_page": "home",
            "flash_messages": _get_flash(request),
        },
    )


# =============================================================================
# KIT DETAIL
# =============================================================================


@router.get("/kit/new", response_class=HTMLResponse)
async def kit_create_page(
    request: Request, user: dict | None = Depends(get_optional_user)
):
    """Kit creation form."""
    if not user:
        _flash(request, "Sign in to create kits.", "error")
        return RedirectResponse("/auth/login", status_code=303)

    templates = _templates(request)
    return templates.TemplateResponse(
        request,
        "kit/create.html",
        {
            "user": user,
            "active_page": "create",
            "flash_messages": _get_flash(request),
        },
    )


@router.get("/kit/{slug}", response_class=HTMLResponse)
async def kit_detail(
    request: Request, slug: str, user: dict | None = Depends(get_optional_user)
):
    """Kit detail page."""
    from ...db.config import get_config

    templates = _templates(request)
    kit_data = None
    resources = []
    steps = []
    source = "local"

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)
                if db_kit:
                    source = "database"
                    kit_data = {
                        "id": str(db_kit.id),
                        "slug": db_kit.slug,
                        "name": db_kit.name,
                        "description": db_kit.description,
                        "is_public": db_kit.is_public,
                        "created_at": db_kit.created_at,
                        "updated_at": db_kit.updated_at,
                        "owner_id": str(db_kit.owner_id) if db_kit.owner_id else None,
                    }
                    if db_kit.current_version:
                        version = db_kit.current_version
                        kit_data["version_number"] = version.version_number
                        kit_data["version_id"] = str(version.id)
                        kit_data["commit_message"] = version.commit_message

                        resources = sorted(
                            [
                                {
                                    "id": str(r.id),
                                    "number": r.resource_number,
                                    "filename": r.filename,
                                    "mime_type": r.mime_type,
                                    "file_size_bytes": r.file_size_bytes,
                                    "extracted_text": r.extracted_text,
                                    "is_dynamic": getattr(r, "is_dynamic", False),
                                    "display_name": r.display_name,
                                }
                                for r in version.resources
                            ],
                            key=lambda r: int(r["number"]),
                        )

                        steps = sorted(
                            [
                                {
                                    "id": str(s.id),
                                    "number": s.step_number,
                                    "prompt_template": s.prompt_template,
                                    "output_id": f"workflow_{s.step_number}",
                                    "display_name": s.display_name,
                                }
                                for s in version.workflow_steps
                            ],
                            key=lambda s: int(s["number"]),
                        )
        except Exception:
            pass

    # Fall back to local
    if kit_data is None:
        try:
            from ...loader import load_reasoning_kit
            from ...cli import resolve_kit_path

            kit_path = resolve_kit_path(slug, "reasoning_kits")
            kit = load_reasoning_kit(kit_path)
            source = "local"
            kit_data = {
                "slug": slug,
                "name": kit.name,
                "description": None,
                "is_public": True,
                "created_at": None,
                "updated_at": None,
            }
            resources = [
                {
                    "number": int(k),
                    "filename": r.file,
                    "mime_type": None,
                    "file_size_bytes": None,
                    "extracted_text": r.content[:500] if r.content else None,
                }
                for k, r in kit.resources.items()
            ]
            steps = [
                {
                    "number": int(k),
                    "prompt_template": s.prompt,
                    "output_id": s.output_id,
                }
                for k, s in kit.workflow.items()
            ]
        except FileNotFoundError:
            _flash(request, f"Kit '{slug}' not found.", "error")
            return RedirectResponse("/", status_code=303)

    # Compute ownership
    is_owner = False
    if user and kit_data and kit_data.get("owner_id"):
        is_owner = kit_data["owner_id"] == user["id"]

    return templates.TemplateResponse(
        request,
        "kit/detail.html",
        {
            "kit": kit_data,
            "resources": resources,
            "steps": steps,
            "source": source,
            "user": user,
            "is_owner": is_owner,
            "active_page": "detail",
            "flash_messages": _get_flash(request),
        },
    )


# =============================================================================
# KIT EDIT
# =============================================================================


@router.get("/kit/{slug}/edit", response_class=HTMLResponse)
async def kit_edit_page(
    request: Request, slug: str, user: dict | None = Depends(get_optional_user)
):
    """Kit edit form."""
    if not user:
        _flash(request, "Sign in to edit kits.", "error")
        return RedirectResponse("/auth/login", status_code=303)

    from ...db.config import get_config

    templates = _templates(request)
    kit_data = None

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)
                if db_kit:
                    # Ownership check
                    if db_kit.owner_id and str(db_kit.owner_id) != user["id"]:
                        _flash(
                            request,
                            "You don't have permission to edit this kit.",
                            "error",
                        )
                        return RedirectResponse(f"/kit/{slug}", status_code=303)

                    kit_data = {
                        "id": str(db_kit.id),
                        "slug": db_kit.slug,
                        "name": db_kit.name,
                        "description": db_kit.description or "",
                        "is_public": db_kit.is_public,
                    }
        except Exception:
            pass

    if kit_data is None:
        _flash(request, f"Kit '{slug}' not found.", "error")
        return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        request,
        "kit/edit.html",
        {
            "kit": kit_data,
            "user": user,
            "active_page": "edit",
            "flash_messages": _get_flash(request),
        },
    )


# =============================================================================
# EXECUTION PAGE
# =============================================================================


@router.get("/kit/{slug}/run", response_class=HTMLResponse)
async def kit_run_page(
    request: Request, slug: str, user: dict | None = Depends(get_optional_user)
):
    """Kit execution page."""
    from ...db.config import get_config

    templates = _templates(request)
    kit_data = None
    total_steps = 0
    dynamic_resources = []

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)
                if db_kit and db_kit.current_version:
                    # Private kit: only owner can run
                    if not db_kit.is_public:
                        if not user or (
                            db_kit.owner_id and str(db_kit.owner_id) != user["id"]
                        ):
                            _flash(request, "This kit is private.", "error")
                            return RedirectResponse(f"/kit/{slug}", status_code=303)

                    kit_data = {
                        "slug": db_kit.slug,
                        "name": db_kit.name,
                        "version_id": str(db_kit.current_version.id),
                    }
                    total_steps = len(db_kit.current_version.workflow_steps)
                    dynamic_resources = [
                        {
                            "resource_id": r.resource_id,
                            "resource_number": r.resource_number,
                            "filename": r.filename,
                            "display_name": r.display_name,
                        }
                        for r in db_kit.current_version.resources
                        if getattr(r, "is_dynamic", False)
                    ]
        except Exception:
            pass

    if kit_data is None:
        try:
            from ...loader import load_reasoning_kit
            from ...cli import resolve_kit_path

            kit_path = resolve_kit_path(slug, "reasoning_kits")
            kit = load_reasoning_kit(kit_path)
            kit_data = {
                "slug": slug,
                "name": kit.name,
            }
            total_steps = len(kit.workflow)
            dynamic_resources = [
                {
                    "resource_id": r.resource_id,
                    "resource_number": int(r.resource_id.split("_")[-1]),
                    "filename": r.file,
                    "display_name": r.display_name,
                }
                for r in kit.resources.values()
                if r.is_dynamic
            ]
        except FileNotFoundError:
            _flash(request, f"Kit '{slug}' not found.", "error")
            return RedirectResponse("/", status_code=303)

    return templates.TemplateResponse(
        request,
        "execution/run.html",
        {
            "kit": kit_data,
            "total_steps": total_steps,
            "dynamic_resources": dynamic_resources,
            "user": user,
            "active_page": "run",
            "flash_messages": _get_flash(request),
        },
    )


# =============================================================================
# AUTH PAGES
# =============================================================================


@router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request, user: dict | None = Depends(get_optional_user)):
    """Login page."""
    if user:
        return RedirectResponse("/", status_code=303)
    templates = _templates(request)
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {
            "user": user,
            "active_page": "login",
            "flash_messages": _get_flash(request),
        },
    )


@router.get("/auth/signup", response_class=HTMLResponse)
async def signup_page(request: Request, user: dict | None = Depends(get_optional_user)):
    """Signup page."""
    if user:
        return RedirectResponse("/", status_code=303)
    templates = _templates(request)
    return templates.TemplateResponse(
        request,
        "auth/signup.html",
        {
            "user": user,
            "active_page": "signup",
            "flash_messages": _get_flash(request),
        },
    )


@router.get("/auth/reset-password", response_class=HTMLResponse)
async def reset_password_page(
    request: Request, user: dict | None = Depends(get_optional_user)
):
    """Password reset page."""
    if user:
        return RedirectResponse("/", status_code=303)
    templates = _templates(request)
    return templates.TemplateResponse(
        request,
        "auth/reset_password.html",
        {
            "user": user,
            "active_page": "reset-password",
            "flash_messages": _get_flash(request),
        },
    )


@router.get("/auth/logout", response_class=HTMLResponse)
async def logout_page(
    request: Request, user: dict | None = Depends(get_optional_user)
):
    """Logout confirmation page."""
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    templates = _templates(request)
    return templates.TemplateResponse(
        request,
        "auth/logout.html",
        {
            "user": user,
            "active_page": "logout",
            "flash_messages": _get_flash(request),
        },
    )
