"""API routes for CLERK web UI.

Handles kit CRUD operations, resource/step management, execution streaming, and auth.
"""

import asyncio
import json
import re
import time
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse

from ..dependencies import get_optional_user

router = APIRouter()


def _check_auth(user: dict | None) -> JSONResponse | None:
    """Return a 401 JSON response if user is not logged in, else None."""
    if not user:
        return JSONResponse({"ok": False, "error": "Sign in to manage kits."}, status_code=401)
    return None


def _check_kit_ownership(db_kit, user: dict | None) -> JSONResponse | None:
    """Return a 403 JSON response if user doesn't own the kit, else None."""
    if db_kit.owner_id and (not user or str(db_kit.owner_id) != user["id"]):
        return JSONResponse(
            {"ok": False, "error": "You don't have permission to modify this kit."},
            status_code=403,
        )
    return None




# =============================================================================
# KIT CRUD
# =============================================================================


@router.post("/kits")
async def create_kit(
    request: Request,
    user: dict | None = Depends(get_optional_user),
):
    """Create a new reasoning kit. Accepts JSON body {name, description}."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)

    name = body.get("name", "").strip()
    description = body.get("description", "").strip()
    if not name:
        return JSONResponse({"ok": False, "error": "Kit name is required."}, status_code=400)

    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        return JSONResponse({"ok": False, "error": "Invalid kit name."}, status_code=400)

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            owner_id = UUID(user["id"]) if user else None

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)

                existing = await repo.get_by_slug(slug)
                if existing:
                    return JSONResponse(
                        {"ok": False, "error": f"A kit with slug '{slug}' already exists."},
                        status_code=409,
                    )

                kit = await repo.create(
                    slug=slug,
                    name=name,
                    description=description or None,
                    owner_id=owner_id,
                    is_public=True,
                )

            return {"ok": True, "slug": slug}

        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error creating kit: {e}"}, status_code=500)
    else:
        try:
            kit_path = Path("reasoning_kits") / slug
            if kit_path.exists():
                return JSONResponse(
                    {"ok": False, "error": f"Kit '{slug}' already exists."},
                    status_code=409,
                )
            kit_path.mkdir(parents=True)
            return {"ok": True, "slug": slug}
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error creating kit: {e}"}, status_code=500)


@router.put("/kits/{slug}")
async def update_kit(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Update a reasoning kit. Accepts JSON body {name, description}."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)

    name = body.get("name", "").strip()
    description = body.get("description", "").strip()

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)

                if not db_kit:
                    return JSONResponse({"ok": False, "error": f"Kit '{slug}' not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                await repo.update(
                    kit_id=db_kit.id,
                    name=name,
                    description=description or None,
                )

            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error updating kit: {e}"}, status_code=500)

    return JSONResponse({"ok": False, "error": "Database not configured"}, status_code=500)


@router.delete("/kits/{slug}")
async def delete_kit(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Delete a reasoning kit."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)

                if not db_kit:
                    return JSONResponse({"ok": False, "error": f"Kit '{slug}' not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                await repo.delete(db_kit.id)

            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error deleting kit: {e}"}, status_code=500)
    else:
        import shutil

        kit_path = Path("reasoning_kits") / slug
        if kit_path.exists():
            shutil.rmtree(kit_path)
            return {"ok": True}
        else:
            return JSONResponse({"ok": False, "error": f"Kit '{slug}' not found."}, status_code=404)


# =============================================================================
# RESOURCE MANAGEMENT
# =============================================================================


@router.post("/kits/{slug}/resources")
async def add_resource(
    request: Request,
    slug: str,
    file: UploadFile | None = File(None),
    text_content: str = Form(""),
    is_dynamic: str = Form(""),
    display_name: str = Form(""),
    user: dict | None = Depends(get_optional_user),
):
    """Add a resource to a kit (creates a new version). Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import (
                KitVersionRepository,
                ReasoningKitRepository,
                StorageService,
                detect_mime_type_from_filename,
                extract_text_from_bytes,
                get_async_session,
            )

            if text_content.strip():
                file_content = text_content.encode("utf-8")
                safe_name = (display_name.strip() or "resource").replace(" ", "_")
                filename = f"{safe_name}.txt"
                mime_type = "text/plain"
            elif file and file.filename:
                file_content = await file.read()
                filename = file.filename
                mime_type = detect_mime_type_from_filename(filename)
            else:
                return JSONResponse(
                    {"ok": False, "error": "Please upload a file or paste text content."},
                    status_code=400,
                )

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit:
                    return JSONResponse({"ok": False, "error": f"Kit '{slug}' not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                resource_number = 1
                if db_kit.current_version and db_kit.current_version.resources:
                    resource_number = max(r.resource_number for r in db_kit.current_version.resources) + 1

                commit_msg = f"Added resource: {filename}"
                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=commit_msg,
                )

                if db_kit.current_version:
                    old_version = db_kit.current_version
                    for r in old_version.resources:
                        await version_repo.add_resource(
                            version_id=version.id,
                            resource_number=r.resource_number,
                            filename=r.filename,
                            storage_path=r.storage_path,
                            mime_type=r.mime_type,
                            extracted_text=r.extracted_text,
                            file_size_bytes=r.file_size_bytes,
                            is_dynamic=getattr(r, "is_dynamic", False),
                            display_name=r.display_name,
                        )
                    for s in old_version.workflow_steps:
                        await version_repo.add_workflow_step(
                            version_id=version.id,
                            step_number=s.step_number,
                            prompt_template=s.prompt_template,
                            display_name=s.display_name,
                        )

                storage = StorageService(use_service_key=True)
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
                    tmp.write(file_content)
                    tmp_path = Path(tmp.name)

                try:
                    storage_path = storage.upload_resource(
                        kit_id=db_kit.id,
                        version_id=version.id,
                        filename=f"resource_{resource_number}{Path(filename).suffix}",
                        file_path=tmp_path,
                    )
                finally:
                    tmp_path.unlink(missing_ok=True)

                extracted = extract_text_from_bytes(file_content, mime_type)

                await version_repo.add_resource(
                    version_id=version.id,
                    resource_number=resource_number,
                    filename=f"resource_{resource_number}{Path(filename).suffix}",
                    storage_path=storage_path,
                    mime_type=mime_type,
                    extracted_text=extracted,
                    file_size_bytes=len(file_content),
                    is_dynamic=bool(is_dynamic),
                    display_name=display_name.strip() or None,
                )

            return {"ok": True}

        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error adding resource: {e}"}, status_code=500)
    else:
        try:
            kit_path = Path("reasoning_kits") / slug
            if not kit_path.exists():
                return JSONResponse({"ok": False, "error": f"Kit '{slug}' not found."}, status_code=404)

            existing = list(kit_path.glob("resource_*.*"))
            numbers = []
            for f in existing:
                match = re.search(r"resource_(\d+)\.", f.name)
                if match:
                    numbers.append(int(match.group(1)))
            next_num = max(numbers, default=0) + 1

            if text_content.strip():
                ext = ".txt"
                content = text_content.encode("utf-8")
            elif file and file.filename:
                ext = Path(file.filename).suffix or ".txt"
                content = await file.read()
            else:
                return JSONResponse(
                    {"ok": False, "error": "Please upload a file or paste text content."},
                    status_code=400,
                )

            dest = kit_path / f"resource_{next_num}{ext}"
            dest.write_bytes(content)

            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error adding resource: {e}"}, status_code=500)


@router.delete("/kits/{slug}/resources/{number}")
async def delete_resource(
    request: Request,
    slug: str,
    number: int,
    user: dict | None = Depends(get_optional_user),
):
    """Delete a resource from a kit. Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        kit_path = Path("reasoning_kits") / slug
        matches = list(kit_path.glob(f"resource_{number}.*"))
        if matches:
            matches[0].unlink()
            return {"ok": True}
        else:
            return JSONResponse({"ok": False, "error": f"Resource {number} not found."}, status_code=404)
    else:
        try:
            from ...db import (
                KitVersionRepository,
                ReasoningKitRepository,
                get_async_session,
            )

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit or not db_kit.current_version:
                    return JSONResponse({"ok": False, "error": "Kit or version not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Deleted resource {number}",
                )

                for r in db_kit.current_version.resources:
                    if r.resource_number != number:
                        await version_repo.add_resource(
                            version_id=version.id,
                            resource_number=r.resource_number,
                            filename=r.filename,
                            storage_path=r.storage_path,
                            mime_type=r.mime_type,
                            extracted_text=r.extracted_text,
                            file_size_bytes=r.file_size_bytes,
                            is_dynamic=getattr(r, "is_dynamic", False),
                            display_name=r.display_name,
                        )

                for s in db_kit.current_version.workflow_steps:
                    await version_repo.add_workflow_step(
                        version_id=version.id,
                        step_number=s.step_number,
                        prompt_template=s.prompt_template,
                        display_name=s.display_name,
                    )
                for t in db_kit.current_version.tools:
                    await version_repo.add_tool(
                        version_id=version.id,
                        tool_number=t.tool_number,
                        tool_name=t.tool_name,
                        display_name=t.display_name,
                        configuration=t.configuration,
                    )

            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.post("/kits/{slug}/resources/{number}/update")
async def update_resource(
    request: Request,
    slug: str,
    number: int,
    display_name: str = Form(""),
    is_dynamic: str = Form(""),
    text_content: str = Form(""),
    file: UploadFile | None = File(None),
    user: dict | None = Depends(get_optional_user),
):
    """Update a resource in a kit (creates a new version). Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import (
                KitVersionRepository,
                ReasoningKitRepository,
                StorageService,
                detect_mime_type_from_filename,
                extract_text_from_bytes,
                get_async_session,
            )

            new_file_content = None
            new_filename = None
            if text_content.strip():
                new_file_content = text_content.encode("utf-8")
                safe_name = (display_name.strip() or f"resource_{number}").replace(" ", "_")
                new_filename = f"{safe_name}.txt"
            elif file and file.filename:
                new_file_content = await file.read()
                new_filename = file.filename

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit or not db_kit.current_version:
                    return JSONResponse({"ok": False, "error": "Kit or version not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Updated resource {number}",
                )

                for r in db_kit.current_version.resources:
                    if r.resource_number == number:
                        res_display_name = display_name.strip() or None
                        res_is_dynamic = bool(is_dynamic)

                        if new_file_content and new_filename:
                            mime_type = detect_mime_type_from_filename(new_filename)
                            extracted = extract_text_from_bytes(
                                new_file_content, mime_type
                            )

                            storage = StorageService(use_service_key=True)
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(new_filename).suffix) as tmp:
                                tmp.write(new_file_content)
                                tmp_path = Path(tmp.name)

                            try:
                                storage_path = storage.upload_resource(
                                    kit_id=db_kit.id,
                                    version_id=version.id,
                                    filename=f"resource_{number}{Path(new_filename).suffix}",
                                    file_path=tmp_path,
                                )
                            finally:
                                tmp_path.unlink(missing_ok=True)

                            await version_repo.add_resource(
                                version_id=version.id,
                                resource_number=number,
                                filename=f"resource_{number}{Path(new_filename).suffix}",
                                storage_path=storage_path,
                                mime_type=mime_type,
                                extracted_text=extracted,
                                file_size_bytes=len(new_file_content),
                                is_dynamic=res_is_dynamic,
                                display_name=res_display_name,
                            )
                        else:
                            await version_repo.add_resource(
                                version_id=version.id,
                                resource_number=r.resource_number,
                                filename=r.filename,
                                storage_path=r.storage_path,
                                mime_type=r.mime_type,
                                extracted_text=r.extracted_text,
                                file_size_bytes=r.file_size_bytes,
                                is_dynamic=res_is_dynamic,
                                display_name=res_display_name,
                            )
                    else:
                        await version_repo.add_resource(
                            version_id=version.id,
                            resource_number=r.resource_number,
                            filename=r.filename,
                            storage_path=r.storage_path,
                            mime_type=r.mime_type,
                            extracted_text=r.extracted_text,
                            file_size_bytes=r.file_size_bytes,
                            is_dynamic=getattr(r, "is_dynamic", False),
                            display_name=r.display_name,
                        )

                for s in db_kit.current_version.workflow_steps:
                    await version_repo.add_workflow_step(
                        version_id=version.id,
                        step_number=s.step_number,
                        prompt_template=s.prompt_template,
                        display_name=s.display_name,
                    )
                for t in db_kit.current_version.tools:
                    await version_repo.add_tool(
                        version_id=version.id,
                        tool_number=t.tool_number,
                        tool_name=t.tool_name,
                        display_name=t.display_name,
                        configuration=t.configuration,
                    )

            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error updating resource: {e}"}, status_code=500)

    return JSONResponse({"ok": False, "error": "Database not configured"}, status_code=500)

# =============================================================================
# STEP MANAGEMENT
# =============================================================================


@router.post("/kits/{slug}/steps")
async def add_step(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Add a workflow step to a kit. Accepts JSON body {prompt, display_name}. Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)

    prompt = body.get("prompt", "")
    display_name = body.get("display_name", "")

    if not prompt:
        return JSONResponse({"ok": False, "error": "Prompt is required."}, status_code=400)

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import (
                KitVersionRepository,
                ReasoningKitRepository,
                get_async_session,
            )

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit:
                    return JSONResponse({"ok": False, "error": f"Kit '{slug}' not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                step_number = 1
                if db_kit.current_version and db_kit.current_version.workflow_steps:
                    step_number = max(s.step_number for s in db_kit.current_version.workflow_steps) + 1

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Added step {step_number}",
                )

                if db_kit.current_version:
                    for r in db_kit.current_version.resources:
                        await version_repo.add_resource(
                            version_id=version.id,
                            resource_number=r.resource_number,
                            filename=r.filename,
                            storage_path=r.storage_path,
                            mime_type=r.mime_type,
                            extracted_text=r.extracted_text,
                            file_size_bytes=r.file_size_bytes,
                            is_dynamic=getattr(r, "is_dynamic", False),
                            display_name=r.display_name,
                        )
                    for s in db_kit.current_version.workflow_steps:
                        await version_repo.add_workflow_step(
                            version_id=version.id,
                            step_number=s.step_number,
                            prompt_template=s.prompt_template,
                            display_name=s.display_name,
                        )
                    for t in db_kit.current_version.tools:
                        await version_repo.add_tool(
                            version_id=version.id,
                            tool_number=t.tool_number,
                            tool_name=t.tool_name,
                            display_name=t.display_name,
                            configuration=t.configuration,
                        )

                await version_repo.add_workflow_step(
                    version_id=version.id,
                    step_number=step_number,
                    prompt_template=prompt,
                    display_name=display_name.strip() or None,
                )

            return {"ok": True}

        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error adding step: {e}"}, status_code=500)
    else:
        try:
            kit_path = Path("reasoning_kits") / slug
            if not kit_path.exists():
                return JSONResponse({"ok": False, "error": f"Kit '{slug}' not found."}, status_code=404)

            existing = list(kit_path.glob("instruction_*.txt"))
            numbers = []
            for f in existing:
                match = re.search(r"instruction_(\d+)\.txt", f.name)
                if match:
                    numbers.append(int(match.group(1)))
            next_num = max(numbers, default=0) + 1

            dest = kit_path / f"instruction_{next_num}.txt"
            dest.write_text(prompt)
            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error adding step: {e}"}, status_code=500)


@router.post("/kits/{slug}/steps/{number}/update")
async def update_step(
    request: Request,
    slug: str,
    number: int,
    user: dict | None = Depends(get_optional_user),
    # Note: frontend sends FormData for updates here, checking request type
):
    """Update a workflow step. Supports JSON or FormData. Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    # Handle both FormData and JSON for smooth frontend migration
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        prompt = form.get("prompt", "")
        display_name = form.get("display_name", "")
    else:
        try:
            body = await request.json()
            prompt = body.get("prompt", "")
            display_name = body.get("display_name", "")
        except Exception:
            return JSONResponse({"ok": False, "error": "Invalid request body"}, status_code=400)

    if not prompt:
        return JSONResponse({"ok": False, "error": "Prompt is required."}, status_code=400)

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import (
                KitVersionRepository,
                ReasoningKitRepository,
                get_async_session,
            )

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit or not db_kit.current_version:
                    return JSONResponse({"ok": False, "error": "Kit or version not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Updated step {number}",
                )

                for r in db_kit.current_version.resources:
                    await version_repo.add_resource(
                        version_id=version.id,
                        resource_number=r.resource_number,
                        filename=r.filename,
                        storage_path=r.storage_path,
                        mime_type=r.mime_type,
                        extracted_text=r.extracted_text,
                        file_size_bytes=r.file_size_bytes,
                        is_dynamic=getattr(r, "is_dynamic", False),
                        display_name=r.display_name,
                    )

                for s in db_kit.current_version.workflow_steps:
                    template = prompt if s.step_number == number else s.prompt_template
                    step_display = (
                        display_name.strip() or None
                        if s.step_number == number
                        else s.display_name
                    )
                    await version_repo.add_workflow_step(
                        version_id=version.id,
                        step_number=s.step_number,
                        prompt_template=template,
                        display_name=step_display,
                    )
                for t in db_kit.current_version.tools:
                    await version_repo.add_tool(
                        version_id=version.id,
                        tool_number=t.tool_number,
                        tool_name=t.tool_name,
                        display_name=t.display_name,
                        configuration=t.configuration,
                    )

            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    else:
        step_file = Path("reasoning_kits") / slug / f"instruction_{number}.txt"
        if step_file.exists():
            step_file.write_text(prompt)
            return {"ok": True}
        else:
            return JSONResponse({"ok": False, "error": f"Step {number} not found."}, status_code=404)


@router.delete("/kits/{slug}/steps/{number}")
async def delete_step(
    request: Request,
    slug: str,
    number: int,
    user: dict | None = Depends(get_optional_user),
):
    """Delete a workflow step. Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        step_file = Path("reasoning_kits") / slug / f"instruction_{number}.txt"
        if step_file.exists():
            step_file.unlink()
            return {"ok": True}
        else:
            return JSONResponse({"ok": False, "error": f"Step {number} not found."}, status_code=404)
    else:
        try:
            from ...db import (
                KitVersionRepository,
                ReasoningKitRepository,
                get_async_session,
            )

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit or not db_kit.current_version:
                    return JSONResponse({"ok": False, "error": "Kit or version not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Deleted step {number}",
                )

                for r in db_kit.current_version.resources:
                    await version_repo.add_resource(
                        version_id=version.id,
                        resource_number=r.resource_number,
                        filename=r.filename,
                        storage_path=r.storage_path,
                        mime_type=r.mime_type,
                        extracted_text=r.extracted_text,
                        file_size_bytes=r.file_size_bytes,
                        is_dynamic=getattr(r, "is_dynamic", False),
                        display_name=r.display_name,
                    )

                for s in db_kit.current_version.workflow_steps:
                    if s.step_number != number:
                        await version_repo.add_workflow_step(
                            version_id=version.id,
                            step_number=s.step_number,
                            prompt_template=s.prompt_template,
                            display_name=s.display_name,
                        )
                for t in db_kit.current_version.tools:
                    await version_repo.add_tool(
                        version_id=version.id,
                        tool_number=t.tool_number,
                        tool_name=t.tool_name,
                        display_name=t.display_name,
                        configuration=t.configuration,
                    )

            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# =============================================================================
# TOOL MANAGEMENT
# =============================================================================


@router.get("/tools/available")
async def list_available_tools(
    request: Request,
    user: dict | None = Depends(get_optional_user),
):
    """List all globally available tools from the registry."""
    from ...tools import list_tools

    tools = list_tools()
    
    active_mcp_servers = set()
    if user and "id" in user:
        try:
            from ...db import get_async_session
            from ...db.models import McpServerConfig
            from sqlalchemy import select
            
            async with get_async_session() as session:
                stmt = select(McpServerConfig.server_name).where(
                    McpServerConfig.user_id == user["id"],
                    McpServerConfig.is_active == True
                )
                result = await session.execute(stmt)
                active_mcp_servers = set(result.scalars().all())
        except Exception:
            pass
            
    filtered_tools = []
    for t in tools:
        source = getattr(t, "source", "builtin")
        if source == "builtin" or source in active_mcp_servers:
            filtered_tools.append({
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "source": source,
            })

    return {
        "tools": filtered_tools
    }


@router.post("/kits/{slug}/tools")
async def add_tool(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Add a tool to a kit (from global registry). Accepts JSON body {tool_name, display_name}. Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)

    tool_name = body.get("tool_name", "")
    display_name = body.get("display_name", "")
    configuration = body.get("configuration")

    if not tool_name:
        return JSONResponse({"ok": False, "error": "tool_name is required."}, status_code=400)

    # Verify tool exists in global registry
    from ...tools import get_tool as get_global_tool

    if get_global_tool(tool_name) is None:
        return JSONResponse(
            {"ok": False, "error": f"Tool '{tool_name}' is not available."},
            status_code=400,
        )

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import (
                KitVersionRepository,
                ReasoningKitRepository,
                get_async_session,
            )

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit:
                    return JSONResponse({"ok": False, "error": f"Kit '{slug}' not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                tool_number = 1
                if db_kit.current_version and db_kit.current_version.tools:
                    tool_number = max(t.tool_number for t in db_kit.current_version.tools) + 1

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Added tool {tool_name}",
                )

                if db_kit.current_version:
                    for r in db_kit.current_version.resources:
                        await version_repo.add_resource(
                            version_id=version.id,
                            resource_number=r.resource_number,
                            filename=r.filename,
                            storage_path=r.storage_path,
                            mime_type=r.mime_type,
                            extracted_text=r.extracted_text,
                            file_size_bytes=r.file_size_bytes,
                            is_dynamic=getattr(r, "is_dynamic", False),
                            display_name=r.display_name,
                        )
                    for s in db_kit.current_version.workflow_steps:
                        await version_repo.add_workflow_step(
                            version_id=version.id,
                            step_number=s.step_number,
                            prompt_template=s.prompt_template,
                            display_name=s.display_name,
                        )
                    for t in db_kit.current_version.tools:
                        await version_repo.add_tool(
                            version_id=version.id,
                            tool_number=t.tool_number,
                            tool_name=t.tool_name,
                            display_name=t.display_name,
                            configuration=t.configuration,
                        )

                await version_repo.add_tool(
                    version_id=version.id,
                    tool_number=tool_number,
                    tool_name=tool_name,
                    display_name=display_name.strip() or None,
                    configuration=configuration,
                )

            return {"ok": True}

        except Exception as e:
            return JSONResponse({"ok": False, "error": f"Error adding tool: {e}"}, status_code=500)

    return JSONResponse({"ok": False, "error": "Database not configured"}, status_code=500)


@router.post("/kits/{slug}/tools/{number}/update")
async def update_tool(
    request: Request,
    slug: str,
    number: int,
    user: dict | None = Depends(get_optional_user),
):
    """Update a tool in a kit (creates a new version). Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body"}, status_code=400)

    display_name = body.get("display_name")
    configuration = body.get("configuration")

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import (
                KitVersionRepository,
                ReasoningKitRepository,
                get_async_session,
            )

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit or not db_kit.current_version:
                    return JSONResponse({"ok": False, "error": "Kit or version not found."}, status_code=404)

                own_err = _check_kit_ownership(db_kit, user)
                if own_err:
                    return own_err

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Updated tool {number}",
                )

                for r in db_kit.current_version.resources:
                    await version_repo.add_resource(
                        version_id=version.id,
                        resource_number=r.resource_number,
                        filename=r.filename,
                        storage_path=r.storage_path,
                        mime_type=r.mime_type,
                        extracted_text=r.extracted_text,
                        file_size_bytes=r.file_size_bytes,
                        is_dynamic=getattr(r, "is_dynamic", False),
                        display_name=r.display_name,
                    )

                for s in db_kit.current_version.workflow_steps:
                    await version_repo.add_workflow_step(
                        version_id=version.id,
                        step_number=s.step_number,
                        prompt_template=s.prompt_template,
                        display_name=s.display_name,
                    )

                for t in db_kit.current_version.tools:
                    t_display = display_name.strip() if t.tool_number == number and display_name is not None else t.display_name
                    t_config = configuration if t.tool_number == number and configuration is not None else t.configuration
                    await version_repo.add_tool(
                        version_id=version.id,
                        tool_number=t.tool_number,
                        tool_name=t.tool_name,
                        display_name=t_display,
                        configuration=t_config,
                    )

            return {"ok": True}
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    return JSONResponse({"ok": False, "error": "Database not configured"}, status_code=500)


@router.delete("/kits/{slug}/tools/{number}")
async def delete_tool(
    request: Request,
    slug: str,
    number: int,
    user: dict | None = Depends(get_optional_user),
):
    """Delete a tool from a kit. Returns JSON."""
    auth_err = _check_auth(user)
    if auth_err:
        return auth_err

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        return JSONResponse({"ok": False, "error": "Database not configured"}, status_code=500)

    try:
        from ...db import (
            KitVersionRepository,
            ReasoningKitRepository,
            get_async_session,
        )

        async with get_async_session() as session:
            kit_repo = ReasoningKitRepository(session)
            version_repo = KitVersionRepository(session)
            db_kit = await kit_repo.get_by_slug(slug)

            if not db_kit or not db_kit.current_version:
                return JSONResponse({"ok": False, "error": "Kit or version not found."}, status_code=404)

            own_err = _check_kit_ownership(db_kit, user)
            if own_err:
                return own_err

            version = await version_repo.create(
                kit_id=db_kit.id,
                commit_message=f"Deleted tool {number}",
            )

            for r in db_kit.current_version.resources:
                await version_repo.add_resource(
                    version_id=version.id,
                    resource_number=r.resource_number,
                    filename=r.filename,
                    storage_path=r.storage_path,
                    mime_type=r.mime_type,
                    extracted_text=r.extracted_text,
                    file_size_bytes=r.file_size_bytes,
                    is_dynamic=getattr(r, "is_dynamic", False),
                    display_name=r.display_name,
                )

            for s in db_kit.current_version.workflow_steps:
                await version_repo.add_workflow_step(
                    version_id=version.id,
                    step_number=s.step_number,
                    prompt_template=s.prompt_template,
                    display_name=s.display_name,
                )

            for t in db_kit.current_version.tools:
                if t.tool_number != number:
                    await version_repo.add_tool(
                        version_id=version.id,
                        tool_number=t.tool_number,
                        tool_name=t.tool_name,
                        display_name=t.display_name,
                        configuration=t.configuration,
                    )

        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


# =============================================================================
# EXECUTION — SSE Streaming (two-step: POST config, then GET SSE stream)
# =============================================================================

# In-memory execution state: {execution_id: {kit, config, events, ...}}
_executions: dict[str, dict] = {}


@router.post("/kits/{slug}/execute")
async def start_execution(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Start a kit execution. Returns an execution_id for SSE streaming.

    Accepts JSON body:
        {
            "evaluate": bool,
            "evaluation_mode": "transparent" | "anonymous",
            "dynamic_resources": {"resource_1": "content", ...}
        }
    """
    import uuid as _uuid

    from ...db.config import get_config

    # Parse config
    content_type = request.headers.get("content-type", "")
    
    evaluate = False
    evaluation_mode = "transparent"
    dynamic_resources = {}

    if "multipart/form-data" in content_type:
        form = await request.form()
        evaluate = str(form.get("evaluate", "")).lower() == "true"
        evaluation_mode = str(form.get("evaluation_mode", "transparent"))
        
        try:
            from ...db import detect_mime_type_from_filename, extract_text_from_bytes
        except ImportError:
            pass  # Fallback logic if needed, but db should be available
            
        for key, value in form.multi_items():
            if key.startswith("dynamic_resource_text_"):
                res_id = key.replace("dynamic_resource_text_", "")
                dynamic_resources[res_id] = str(value)
            elif key.startswith("dynamic_resource_file_"):
                res_id = key.replace("dynamic_resource_file_", "")
                if hasattr(value, "filename") and value.filename:
                    file_bytes = await value.read()
                    try:
                        from ...db import detect_mime_type_from_filename, extract_text_from_bytes
                        mime_type = detect_mime_type_from_filename(value.filename)
                        extracted = extract_text_from_bytes(file_bytes, mime_type)
                        dynamic_resources[res_id] = extracted
                    except ImportError:
                        pass
    else:
        try:
            body = await request.json()
            evaluate = body.get("evaluate", False)
            evaluation_mode = body.get("evaluation_mode", "transparent")
            dynamic_resources = body.get("dynamic_resources", {})
        except Exception:
            pass

    # Load kit
    kit = None
    db_version_id = None
    save_to_db = False

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session as _get_session

            # Check private kit access
            async with _get_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)
                if db_kit and not db_kit.is_public:
                    if not user or (
                        db_kit.owner_id and str(db_kit.owner_id) != user["id"]
                    ):
                        return {"error": "This kit is private."}
        except Exception:
            pass

        try:
            from ...loader import load_reasoning_kit_from_db

            loaded = await load_reasoning_kit_from_db(slug)
            kit = loaded.kit
            db_version_id = loaded.version_id
            save_to_db = True
        except Exception:
            pass

    if kit is None:
        try:
            from ...loader import load_reasoning_kit
            from ...cli import resolve_kit_path

            kit_path = resolve_kit_path(slug, "reasoning_kits")
            kit = load_reasoning_kit(kit_path)
        except FileNotFoundError:
            return {"error": f"Kit '{slug}' not found."}

    # Inject dynamic resource content
    for resource in kit.resources.values():
        if resource.is_dynamic and resource.resource_id in dynamic_resources:
            resource.content = dynamic_resources[resource.resource_id]

    # Validate all dynamic resources are provided
    missing = [
        r.resource_id for r in kit.resources.values() if r.is_dynamic and not r.content
    ]
    if missing:
        return {"error": f"Missing dynamic resources: {', '.join(missing)}"}

    # Create execution entry
    execution_id = str(_uuid.uuid4())
    _executions[execution_id] = {
        "kit": kit,
        "slug": slug,
        "evaluate": evaluate,
        "evaluation_mode": evaluation_mode,
        "db_version_id": db_version_id,
        "save_to_db": save_to_db,
        "eval_event": asyncio.Event() if evaluate else None,
        "eval_score": None,
        "user_id": user["id"] if user else None,
        "db_run_id": None, # Will be created in stream
        "resume_outputs": None,
        "resume_step": None,
    }

    return {"execution_id": execution_id}


@router.post("/kits/{slug}/execute/resume")
async def resume_execution(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Resume a paused kit execution. Returns an execution_id for SSE streaming.

    Accepts JSON body: {"run_id": str}
    """
    try:
        body = await request.json()
        run_id = body.get("run_id")
        if not run_id:
            return {"error": "run_id is required"}
    except Exception:
        return {"error": "Invalid request body"}

    import uuid as _uuid
    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        return {"error": "Database is not configured, cannot resume."}

    user_id = UUID(user["id"]) if user else None

    try:
        from ...db import ExecutionRepository, get_async_session as _get_session
        from ...loader import load_reasoning_kit_from_db

        async with _get_session() as session:
            repo = ExecutionRepository(session)
            db_run = await repo.get_by_id(UUID(run_id))
            
            if not db_run:
                return {"error": "Execution run not found."}
                
            if db_run.user_id and user_id and db_run.user_id != user_id:
                return {"error": "Access denied."}
                
            if db_run.status != "paused":
                return {"error": f"Cannot resume run with status '{db_run.status}'."}

            version_id = db_run.version_id
            storage_mode = db_run.storage_mode
            evaluate = storage_mode != "transparent"
            evaluation_mode = storage_mode

            # Load past outputs to inject into context
            past_outputs = {}
            for step in db_run.step_executions:
                # Find output_id for this step in version
                output_id = f"workflow_{step.step_number}" # fallback
                if db_run.version and db_run.version.workflow_steps:
                    for ws in db_run.version.workflow_steps:
                        if ws.step_number == step.step_number:
                            output_id = ws.output_id
                            break
                past_outputs[output_id] = step.output_text
            
            # Highest step number done
            highest_step = max([s.step_number for s in db_run.step_executions], default=0)

        # We must load the kit matching the exact DB version we are resuming
        loaded = await load_reasoning_kit_from_db(slug, version_id=version_id)
        kit = loaded.kit

    except Exception as e:
        return {"error": f"Failed to resume execution: {e}"}

    # Set run status back to running
    try:
        async with _get_session() as session:
            repo = ExecutionRepository(session)
            db_run = await repo.get_by_id(UUID(run_id))
            if db_run:
                db_run.status = "running"
                await session.flush()
    except Exception:
        pass


    # Create execution entry
    execution_id = str(_uuid.uuid4())
    _executions[execution_id] = {
        "kit": kit,
        "slug": slug,
        "evaluate": evaluate,
        "evaluation_mode": evaluation_mode,
        "db_version_id": version_id,
        "save_to_db": True,
        "eval_event": asyncio.Event() if evaluate else None,
        "eval_score": None,
        "user_id": str(user_id) if user_id else None,
        "db_run_id": UUID(run_id), # Resume flag tells stream not to create new run
        "resume_outputs": past_outputs,
        "resume_step": highest_step + 1,
    }

    return {"execution_id": execution_id}


@router.get("/kits/{slug}/execute/{execution_id}/stream")
async def execute_kit_stream(
    request: Request,
    slug: str,
    execution_id: str,
    user: dict | None = Depends(get_optional_user),
):
    """Stream execution results as SSE events for a previously started execution."""
    exec_state = _executions.get(execution_id)
    if not exec_state:

        async def error_stream():
            yield f"event: error\ndata: {json.dumps({'message': 'Execution not found'})}\n\n"

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    kit = exec_state["kit"]
    evaluate = exec_state["evaluate"]
    evaluation_mode = exec_state["evaluation_mode"]
    db_version_id = exec_state["db_version_id"]
    save_to_db = exec_state["save_to_db"]
    eval_event = exec_state["eval_event"]

    async def execution_stream():
        """Stream execution results as SSE events."""
        from ...graph import DEFAULT_MODEL, resolve_placeholders
        from ...evaluation import (
            create_execution_run,
            save_step_to_db,
            complete_execution_run,
        )

        persist = save_to_db  # local copy to allow mutation

        # Create DB run if needed or use existing
        db_run_id = exec_state.get("db_run_id")
        user_id_str = exec_state.get("user_id")
        if persist and db_version_id and not db_run_id:
            try:
                db_run_id = await create_execution_run(
                    version_id=db_version_id,
                    storage_mode=evaluation_mode if evaluate else "transparent",
                    user_id=UUID(user_id_str) if user_id_str else None,
                )
            except Exception:
                persist = False

        # Send initial event
        past_steps = []
        if exec_state.get("db_run_id") and exec_state.get("resume_outputs"):
            resume_step = exec_state.get("resume_step", 1) or 1
            for step_key in sorted(kit.workflow.keys(), key=int):
                step_num = int(step_key)
                if step_num < resume_step:
                    step = kit.workflow[step_key]
                    output_text = exec_state["resume_outputs"].get(step.output_id, "")
                    past_steps.append({
                        "step": step_num,
                        "output_id": step.output_id,
                        "display_name": step.display_name,
                        "status": "done",
                        "result": output_text,
                    })
        
        yield f"event: start\ndata: {json.dumps({'kit_name': kit.name, 'total_steps': len(kit.workflow), 'past_steps': past_steps})}\n\n"

        # Execute step by step
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, ToolMessage

        llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0)
        resources = {r.resource_id: r.content for r in kit.resources.values()}
        outputs: dict[str, str] = exec_state.get("resume_outputs") or {}
        resume_step = exec_state.get("resume_step", 1) or 1

        # Build tool data from kit
        kit_tools = {
            k: {
                "tool_name": v.tool_name,
                "tool_id": v.tool_id,
                "display_name": v.display_name,
                "configuration": v.configuration,
            }
            for k, v in kit.tools.items()
        }

        for step_key in sorted(kit.workflow.keys(), key=int):
            step = kit.workflow[step_key]
            step_num = int(step_key)

            if step_num < resume_step:
                continue

            # Check for pause before sending step-start
            if exec_state.get("pause_requested"):
                if persist and db_run_id:
                    try:
                        from ...evaluation import pause_execution_run
                        await pause_execution_run(db_run_id)
                    except Exception:
                        pass
                yield f"event: done\ndata: {json.dumps({'status': 'paused', 'total_steps': len(kit.workflow), 'run_id': str(db_run_id) if db_run_id else None})}\n\n"
                _executions.pop(execution_id, None)
                return

            # Send step-start event
            yield f"event: step-start\ndata: {json.dumps({'step': step_num, 'output_id': step.output_id, 'display_name': step.display_name})}\n\n"

            # Resolve placeholders
            prompt = resolve_placeholders(step.prompt, resources, outputs)

            # Check for tool references and prepare tool-aware LLM
            from ...graph import extract_tool_refs, remove_tool_placeholders
            from ...tools import get_tool as get_tool_def

            openai_tools = extract_tool_refs(step.prompt, kit_tools)
            clean_prompt = remove_tool_placeholders(prompt, kit_tools)

            # Execute LLM call (with or without tools)
            start_time = time.time()
            try:
                if openai_tools:
                    # Tool-aware execution: bind tools and handle call loop
                    llm_with_tools = llm.bind_tools(
                        [t["function"] for t in openai_tools]
                    )
                    messages = [HumanMessage(content=clean_prompt)]
                    response = await llm_with_tools.ainvoke(messages)
                    messages.append(response)

                    # Tool-call loop: execute tools, feed back, repeat
                    max_tool_rounds = 5
                    for _ in range(max_tool_rounds):
                        if not response.tool_calls:
                            break

                        # Execute each tool call
                        for tool_call in response.tool_calls:
                            tool_def = get_tool_def(tool_call["name"])
                            if tool_def:
                                try:
                                    user_id = exec_state.get("user_id")
                                    tool_result = await tool_def.execute(tool_call["args"], user_id=user_id)
                                except Exception as te:
                                    tool_result = f"Error executing tool: {te}"
                            else:
                                tool_result = f"Unknown tool: {tool_call['name']}"

                            messages.append(
                                ToolMessage(
                                    content=tool_result,
                                    tool_call_id=tool_call["id"],
                                )
                            )

                        # Get LLM response with tool results
                        response = await llm_with_tools.ainvoke(messages)
                        messages.append(response)

                    result = str(response.content)
                else:
                    # Standard execution without tools
                    response = await llm.ainvoke(clean_prompt)
                    result = str(response.content)

                latency_ms = int((time.time() - start_time) * 1000)

                # Get token usage
                tokens_used = None
                if hasattr(response, "response_metadata"):
                    metadata = response.response_metadata
                    if "token_usage" in metadata:
                        tokens_used = metadata["token_usage"].get("total_tokens")

                outputs[step.output_id] = result

                # Save to DB if enabled
                if persist and db_run_id:
                    try:
                        await save_step_to_db(
                            run_id=db_run_id,
                            step_number=step_num,
                            prompt=clean_prompt,
                            output=result,
                            mode=evaluation_mode if evaluate else "transparent",
                            model_used=DEFAULT_MODEL,
                            tokens_used=tokens_used,
                            latency_ms=latency_ms,
                        )
                    except Exception:
                        pass

                # Send step-complete event
                yield f"event: step-complete\ndata: {json.dumps({'step': step_num, 'output_id': step.output_id, 'display_name': step.display_name, 'prompt_preview': clean_prompt, 'result': result, 'latency_ms': latency_ms, 'tokens_used': tokens_used})}\n\n"

                # Check for pause right after step completion before evaluation
                if exec_state.get("pause_requested"):
                    if persist and db_run_id:
                        try:
                            from ...evaluation import pause_execution_run
                            await pause_execution_run(db_run_id)
                        except Exception:
                            pass
                    yield f"event: done\ndata: {json.dumps({'status': 'paused', 'total_steps': len(kit.workflow), 'run_id': str(db_run_id) if db_run_id else None})}\n\n"
                    _executions.pop(execution_id, None)
                    return

                # Evaluation pause: wait for user score
                if evaluate and eval_event:
                    exec_state["eval_score"] = None
                    eval_event.clear()
                    yield f"event: step-await-eval\ndata: {json.dumps({'step': step_num})}\n\n"

                    # Wait for user to submit score (timeout after 10 minutes)
                    try:
                        while not eval_event.is_set():
                            # Check for pause requested while waiting for eval
                            if exec_state.get("pause_requested"):
                                if persist and db_run_id:
                                    try:
                                        from ...evaluation import pause_execution_run
                                        await pause_execution_run(db_run_id)
                                    except Exception:
                                        pass
                                yield f"event: done\ndata: {json.dumps({'status': 'paused', 'total_steps': len(kit.workflow), 'run_id': str(db_run_id) if db_run_id else None})}\n\n"
                                _executions.pop(execution_id, None)
                                return
                            # Wait in small increments to allow checking pause flag
                            try:
                                await asyncio.wait_for(eval_event.wait(), timeout=0.5)
                            except asyncio.TimeoutError:
                                pass
                            
                            # Timeout checking happens in an outer wrapping try block in a real system,
                            # but for now we'll rely on the client or let it wait indefinitely up to 10 mins
                            # Not implemented here to keep it simple, but would usually maintain a start_time
                    except asyncio.TimeoutError:
                        yield f"event: done\ndata: {json.dumps({'status': 'failed', 'error': 'Evaluation timed out'})}\n\n"
                        return

                    # Persist the evaluation score
                    score = exec_state.get("eval_score")
                    if score is not None and persist and db_run_id:
                        try:
                            from ...evaluation import update_step_evaluation_in_db

                            await update_step_evaluation_in_db(
                                run_id=db_run_id,
                                step_number=step_num,
                                score=score,
                            )
                        except Exception:
                            pass

            except Exception as e:
                yield f"event: step-error\ndata: {json.dumps({'step': step_num, 'error': str(e)})}\n\n"

                # Complete run as failed
                if persist and db_run_id:
                    try:
                        await complete_execution_run(db_run_id, error=str(e))
                    except Exception:
                        pass

                yield f"event: done\ndata: {json.dumps({'status': 'failed', 'error': str(e)})}\n\n"
                # Clean up
                _executions.pop(execution_id, None)
                return

        # Complete run successfully
        if persist and db_run_id:
            try:
                await complete_execution_run(db_run_id, error=None)
            except Exception:
                pass

        yield f"event: done\ndata: {json.dumps({'status': 'completed', 'total_steps': len(kit.workflow), 'run_id': str(db_run_id) if db_run_id else None})}\n\n"
        # Clean up
        _executions.pop(execution_id, None)

    return StreamingResponse(
        execution_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/kits/{slug}/evaluate-step")
async def evaluate_step(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Submit an evaluation score for a step, unblocking the SSE stream.

    Accepts JSON body: {"execution_id": str, "step": int, "score": int}
    """
    try:
        body = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON body"}

    execution_id = body.get("execution_id")
    step = body.get("step")
    score = body.get("score")

    if not execution_id or step is None or score is None:
        return {"ok": False, "error": "Missing execution_id, step, or score"}

    score = int(score)
    if score < 0 or score > 100:
        return {"ok": False, "error": "Score must be between 0 and 100"}

    exec_state = _executions.get(execution_id)
    if not exec_state:
        return {"ok": False, "error": "Execution not found or already finished"}

    eval_event = exec_state.get("eval_event")
    if not eval_event:
        return {"ok": False, "error": "Evaluation is not enabled for this execution"}

    # Store the score and signal the SSE generator to continue
    exec_state["eval_score"] = score
    eval_event.set()

    return {"ok": True}


@router.post("/kits/{slug}/executions/{execution_id}/pause")
async def pause_execution(
    request: Request,
    slug: str,
    execution_id: str,
    user: dict | None = Depends(get_optional_user),
):
    """Pause an active execution run."""
    exec_state = _executions.get(execution_id)
    if not exec_state:
        return {"ok": False, "error": "Execution not found or already finished"}

    # Signal the SSE stream to break and pause the run
    exec_state["pause_requested"] = True

    return {"ok": True}


@router.delete("/kits/{slug}/executions/{run_id}")
async def delete_execution(
    request: Request,
    slug: str,
    run_id: str,
    user: dict | None = Depends(get_optional_user),
):
    """Delete an execution run from history."""
    if not user:
        return {"ok": False, "error": "Sign in required."}

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        return {"ok": False, "error": "Database not configured."}

    try:
        from ...evaluation import delete_execution_run
        from ...db import ExecutionRepository, get_async_session

        async with get_async_session() as session:
            repo = ExecutionRepository(session)
            run = await repo.get_by_id(UUID(run_id))

            if not run:
                return {"ok": False, "error": "Execution not found."}

            if str(run.user_id) != user["id"]:
                return {"ok": False, "error": "Access denied."}

        deleted = await delete_execution_run(UUID(run_id))
        return {"ok": deleted}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =============================================================================
# EXECUTION HISTORY & DOWNLOAD
# =============================================================================


@router.get("/kits/{slug}/executions")
async def list_executions(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """List past execution runs for a kit (per-user).

    Returns JSON array of execution runs.
    """
    if not user:
        return {"error": "Sign in to view execution history.", "runs": []}

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        return {"runs": []}

    try:
        from ...db import (
            ExecutionRepository,
            ReasoningKitRepository,
            get_async_session as _get_session,
        )

        async with _get_session() as session:
            kit_repo = ReasoningKitRepository(session)
            db_kit = await kit_repo.get_by_slug(slug)
            if not db_kit:
                return {"error": f"Kit '{slug}' not found.", "runs": []}

            exec_repo = ExecutionRepository(session)
            runs = await exec_repo.list_for_kit(
                kit_id=db_kit.id,
                user_id=UUID(user["id"]),
            )

            return {
                "runs": [
                    {
                        "id": str(run.id),
                        "status": run.status,
                        "label": run.label,
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                        "storage_mode": run.storage_mode,
                        "total_steps": len(run.step_executions),
                        "error_message": run.error_message,
                    }
                    for run in runs
                ]
            }
    except Exception as e:
        return {"error": str(e), "runs": []}


@router.get("/kits/{slug}/executions/{run_id}")
async def get_execution(
    request: Request,
    slug: str,
    run_id: str,
    user: dict | None = Depends(get_optional_user),
):
    """Get execution run detail with all step outputs."""
    if not user:
        return {"error": "Sign in to view execution details."}

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        return {"error": "Database not configured."}

    try:
        from ...db import ExecutionRepository, get_async_session as _get_session

        async with _get_session() as session:
            repo = ExecutionRepository(session)
            run = await repo.get_by_id(UUID(run_id))

            if not run:
                return {"error": "Execution not found."}

            # Per-user access check
            if str(run.user_id) != user["id"]:
                return {"error": "Access denied."}

            # Build step data with version step info for display names
            step_display_names = {}
            if run.version and run.version.workflow_steps:
                for ws in run.version.workflow_steps:
                    step_display_names[ws.step_number] = {
                        "display_name": ws.display_name,
                        "output_id": ws.output_id,
                    }

            steps = []
            for step in sorted(run.step_executions, key=lambda s: s.step_number):
                ws_info = step_display_names.get(step.step_number, {})
                steps.append(
                    {
                        "step_number": step.step_number,
                        "display_name": ws_info.get("display_name"),
                        "output_id": ws_info.get("output_id", f"workflow_{step.step_number}"),
                        "input_text": step.input_text,
                        "output_text": step.output_text,
                        "evaluation_score": step.evaluation_score,
                        "model_used": step.model_used,
                        "tokens_used": step.tokens_used,
                        "latency_ms": step.latency_ms,
                        "executed_at": step.executed_at.isoformat() if step.executed_at else None,
                    }
                )

            kit_name = None
            if run.version and run.version.kit:
                kit_name = run.version.kit.name

            return {
                "id": str(run.id),
                "kit_name": kit_name,
                "status": run.status,
                "label": run.label,
                "storage_mode": run.storage_mode,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error_message": run.error_message,
                "steps": steps,
            }
    except Exception as e:
        return {"error": str(e)}


@router.get("/kits/{slug}/executions/{run_id}/download")
async def download_execution(
    request: Request,
    slug: str,
    run_id: str,
    format: str = "md",
    user: dict | None = Depends(get_optional_user),
):
    """Download execution results as Markdown or JSON.

    Query params:
        format: "md" (default) or "json"
    """
    if not user:
        return {"error": "Sign in to download results."}

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        return {"error": "Database not configured."}

    try:
        from ...db import ExecutionRepository, get_async_session as _get_session

        async with _get_session() as session:
            repo = ExecutionRepository(session)
            run = await repo.get_by_id(UUID(run_id))

            if not run:
                return {"error": "Execution not found."}

            if str(run.user_id) != user["id"]:
                return {"error": "Access denied."}

            # Get kit name
            kit_name = slug
            if run.version and run.version.kit:
                kit_name = run.version.kit.name

            # Build step display names
            step_display_names = {}
            if run.version and run.version.workflow_steps:
                for ws in run.version.workflow_steps:
                    step_display_names[ws.step_number] = {
                        "display_name": ws.display_name,
                        "output_id": ws.output_id,
                    }

            sorted_steps = sorted(run.step_executions, key=lambda s: s.step_number)

            if format == "json":
                content = _build_json_download(run, kit_name, sorted_steps, step_display_names)
                media_type = "application/json"
                ext = "json"
            else:
                content = _build_markdown_download(run, kit_name, sorted_steps, step_display_names)
                media_type = "text/markdown"
                ext = "md"

            label_slug = run.label.replace(" ", "_").lower() if run.label else ""
            ts = run.started_at.strftime("%Y%m%d_%H%M%S") if run.started_at else "unknown"
            filename = f"{slug}_{ts}"
            if label_slug:
                filename += f"_{label_slug}"
            filename += f".{ext}"

            from starlette.responses import Response

            return Response(
                content=content,
                media_type=media_type,
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
    except Exception as e:
        return {"error": str(e)}


@router.post("/kits/{slug}/executions/{run_id}/label")
async def update_execution_label(
    request: Request,
    slug: str,
    run_id: str,
    user: dict | None = Depends(get_optional_user),
):
    """Update execution label.

    Accepts JSON body: {"label": "My custom label"}
    """
    if not user:
        return {"ok": False, "error": "Sign in required."}

    try:
        body = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON body."}

    label = body.get("label", "").strip() or None

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        return {"ok": False, "error": "Database not configured."}

    try:
        from ...db import ExecutionRepository, get_async_session as _get_session

        async with _get_session() as session:
            repo = ExecutionRepository(session)
            run = await repo.get_by_id(UUID(run_id))

            if not run:
                return {"ok": False, "error": "Execution not found."}

            if str(run.user_id) != user["id"]:
                return {"ok": False, "error": "Access denied."}

            await repo.update_label(UUID(run_id), label)
            return {"ok": True, "label": label}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _build_markdown_download(run, kit_name, sorted_steps, step_display_names):
    """Build a Markdown report for an execution run."""
    lines = [f"# {kit_name} — Execution Results"]
    if run.label:
        lines.append(f"\n**Label:** {run.label}")
    lines.append(f"\n**Status:** {run.status}")
    if run.started_at:
        lines.append(f"**Started:** {run.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if run.completed_at:
        lines.append(f"**Completed:** {run.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Storage Mode:** {run.storage_mode}")
    lines.append("")

    for step in sorted_steps:
        ws_info = step_display_names.get(step.step_number, {})
        display_name = ws_info.get("display_name")
        output_id = ws_info.get("output_id", f"workflow_{step.step_number}")

        header = f"## Step {step.step_number}"
        if display_name:
            header += f" — {display_name}"
        header += f" ({output_id})"
        lines.append(header)
        lines.append("")

        meta_parts = []
        if step.model_used:
            meta_parts.append(f"Model: {step.model_used}")
        if step.latency_ms:
            meta_parts.append(f"Latency: {step.latency_ms / 1000:.1f}s")
        if step.tokens_used:
            meta_parts.append(f"Tokens: {step.tokens_used}")
        if step.evaluation_score is not None:
            meta_parts.append(f"Evaluation: {step.evaluation_score}/100")
        if meta_parts:
            lines.append(f"*{' · '.join(meta_parts)}*")
            lines.append("")

        if step.output_text:
            lines.append(step.output_text)
        elif step.output_char_count is not None:
            lines.append(f"*[Anonymous mode — {step.output_char_count} characters]*")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _build_json_download(run, kit_name, sorted_steps, step_display_names):
    """Build a JSON report for an execution run."""
    data = {
        "kit_name": kit_name,
        "run_id": str(run.id),
        "status": run.status,
        "label": run.label,
        "storage_mode": run.storage_mode,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "steps": [],
    }

    for step in sorted_steps:
        ws_info = step_display_names.get(step.step_number, {})
        data["steps"].append(
            {
                "step_number": step.step_number,
                "display_name": ws_info.get("display_name"),
                "output_id": ws_info.get("output_id", f"workflow_{step.step_number}"),
                "input_text": step.input_text,
                "output_text": step.output_text,
                "input_char_count": step.input_char_count,
                "output_char_count": step.output_char_count,
                "evaluation_score": step.evaluation_score,
                "model_used": step.model_used,
                "tokens_used": step.tokens_used,
                "latency_ms": step.latency_ms,
                "executed_at": step.executed_at.isoformat() if step.executed_at else None,
            }
        )

    return json.dumps(data, indent=2, ensure_ascii=False)


# =============================================================================
# JSON API (for React SPA frontend)
# =============================================================================


@router.get("/auth/me")
async def get_current_user(
    request: Request,
    user: dict | None = Depends(get_optional_user),
):
    """Return current user and config state for SPA auth."""
    from ...db.config import get_config

    config = get_config()
    return {
        "user": user,
        "supabase_configured": config.is_configured,
    }


@router.get("/kits")
async def list_kits_json(
    request: Request,
    user: dict | None = Depends(get_optional_user),
):
    """List all kits as JSON for the React frontend."""
    from ...db.config import get_config

    kits = []
    config = get_config()

    if config.is_database_configured:
        try:
            from ...db import BookmarkRepository, ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kits = await repo.list_public()

                # Get bookmarked kit IDs for logged-in user
                bookmarked_ids: set = set()
                if user:
                    bm_repo = BookmarkRepository(session)
                    bookmarked_ids = await bm_repo.get_bookmarked_kit_ids(UUID(user["id"]))

                for kit in db_kits:
                    kits.append(
                        {
                            "slug": kit.slug,
                            "name": kit.name,
                            "description": kit.description,
                            "is_public": kit.is_public,
                            "created_at": kit.created_at.isoformat() if kit.created_at else None,
                            "updated_at": kit.updated_at.isoformat() if kit.updated_at else None,
                            "owner_id": str(kit.owner_id) if kit.owner_id else None,
                            "is_bookmarked": kit.id in bookmarked_ids,
                        }
                    )
        except Exception:
            pass

    if not kits:
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
                        "owner_id": None,
                        "is_bookmarked": False,
                    }
                )
        except Exception:
            pass

    return {"kits": kits}


@router.get("/kits/search")
async def search_kits_json(
    request: Request,
    q: str = "",
    filter: str = "all",
    user: dict | None = Depends(get_optional_user),
):
    """Search kits and return JSON for the React frontend."""
    from ...db.config import get_config

    kits = []
    config = get_config()

    # "My Kits" filter — owned + bookmarked
    if filter == "mine" and user:
        if config.is_database_configured:
            try:
                from ...db import BookmarkRepository, ReasoningKitRepository, get_async_session

                async with get_async_session() as session:
                    repo = ReasoningKitRepository(session)
                    bm_repo = BookmarkRepository(session)
                    user_id = UUID(user["id"])

                    bookmarked_ids = await bm_repo.get_bookmarked_kit_ids(user_id)

                    if q.strip():
                        db_kits = await repo.search(
                            q.strip(), include_private=True, owner_id=user_id
                        )
                        # Keep only owned OR bookmarked kits
                        db_kits = [
                            k for k in db_kits
                            if str(k.owner_id) == user["id"] or k.id in bookmarked_ids
                        ]
                    else:
                        owned = await repo.list_by_owner(user_id)
                        bookmarked = await bm_repo.list_bookmarked_kits(user_id)
                        # Merge, avoiding duplicates (owned takes priority)
                        seen_ids = set()
                        db_kits = []
                        for k in owned:
                            db_kits.append(k)
                            seen_ids.add(k.id)
                        for k in bookmarked:
                            if k.id not in seen_ids:
                                db_kits.append(k)
                        db_kits.sort(key=lambda k: k.name)

                    for kit in db_kits:
                        kits.append(
                            {
                                "slug": kit.slug,
                                "name": kit.name,
                                "description": kit.description,
                                "is_public": kit.is_public,
                                "created_at": kit.created_at.isoformat() if kit.created_at else None,
                                "updated_at": kit.updated_at.isoformat() if kit.updated_at else None,
                                "owner_id": str(kit.owner_id) if kit.owner_id else None,
                                "is_bookmarked": kit.id in bookmarked_ids,
                            }
                        )
            except Exception:
                pass
        return {"kits": kits}

    if config.is_database_configured and q.strip():
        try:
            from ...db import BookmarkRepository, ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kits = await repo.search(q.strip())

                bookmarked_ids: set = set()
                if user:
                    bm_repo = BookmarkRepository(session)
                    bookmarked_ids = await bm_repo.get_bookmarked_kit_ids(UUID(user["id"]))

                for kit in db_kits:
                    kits.append(
                        {
                            "slug": kit.slug,
                            "name": kit.name,
                            "description": kit.description,
                            "is_public": kit.is_public,
                            "created_at": kit.created_at.isoformat() if kit.created_at else None,
                            "updated_at": kit.updated_at.isoformat() if kit.updated_at else None,
                            "owner_id": str(kit.owner_id) if kit.owner_id else None,
                            "is_bookmarked": kit.id in bookmarked_ids,
                        }
                    )
        except Exception:
            pass
    elif not q.strip():
        # Empty search = return all (delegate to list endpoint logic)
        result = await list_kits_json(request, user)
        return result

    return {"kits": kits}


@router.post("/kits/{slug}/bookmark")
async def toggle_bookmark_json(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Toggle bookmark on a kit. Returns the new bookmark state."""
    if not user:
        return {"ok": False, "error": "Login required"}

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        return {"ok": False, "error": "Database not configured"}

    try:
        from ...db import BookmarkRepository, ReasoningKitRepository, get_async_session

        async with get_async_session() as session:
            repo = ReasoningKitRepository(session)
            kit = await repo.get_by_slug(slug)
            if not kit:
                return {"ok": False, "error": "Kit not found"}

            bm_repo = BookmarkRepository(session)
            is_bookmarked, _ = await bm_repo.toggle(UUID(user["id"]), kit.id)
            await session.commit()

            return {"ok": True, "is_bookmarked": is_bookmarked}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =============================================================================
# JSON AUTH API (for React SPA)
# =============================================================================


@router.post("/auth/login")
async def login_json(request: Request):
    """JSON login for SPA — accepts JSON body, returns JSON."""
    try:
        body = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON body"}

    email = body.get("email", "")
    password = body.get("password", "")
    if not email or not password:
        return {"ok": False, "error": "Email and password are required."}

    from ...db.config import get_config

    config = get_config()
    if not config.is_configured:
        return {"ok": False, "error": "Supabase is not configured."}

    try:
        from ...db.config import get_supabase_client

        client = get_supabase_client()
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if response.user:
            request.session["user"] = {
                "id": str(response.user.id),
                "email": response.user.email,
            }
            return {
                "ok": True,
                "user": {
                    "id": str(response.user.id),
                    "email": response.user.email,
                },
            }
        else:
            return {"ok": False, "error": "Invalid credentials."}

    except Exception as e:
        error_msg = str(e)
        if "Invalid login" in error_msg or "invalid" in error_msg.lower():
            return {"ok": False, "error": "Invalid email or password."}
        return {"ok": False, "error": f"Sign in error: {error_msg}"}


@router.post("/auth/signup")
async def signup_json(request: Request):
    """JSON signup for SPA — accepts JSON body, returns JSON."""
    try:
        body = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON body"}

    email = body.get("email", "")
    password = body.get("password", "")
    if not email or not password:
        return {"ok": False, "error": "Email and password are required."}

    from ...db.config import get_config

    config = get_config()
    if not config.is_configured:
        return {"ok": False, "error": "Supabase is not configured."}

    try:
        from ...db.config import get_supabase_client

        client = get_supabase_client()
        response = client.auth.sign_up({"email": email, "password": password})

        if response.user:
            identities = getattr(response.user, "identities", None)
            if identities is not None and len(identities) == 0:
                return {
                    "ok": False,
                    "error": "An account with this email already exists. Try signing in instead.",
                }
            return {
                "ok": True,
                "message": "Account created. Please check your email for confirmation.",
            }
        else:
            return {"ok": False, "error": "Could not create account."}

    except Exception as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg or "already been registered" in error_msg:
            return {
                "ok": False,
                "error": "An account with this email already exists. Try signing in instead.",
            }
        return {"ok": False, "error": f"Sign up error: {e}"}


@router.post("/auth/logout")
async def logout_json(request: Request):
    """JSON logout for SPA."""
    request.session.clear()
    return {"ok": True}


@router.post("/auth/reset-password")
async def reset_password_json(request: Request):
    """JSON password reset for SPA."""
    try:
        body = await request.json()
    except Exception:
        return {"ok": False, "error": "Invalid JSON body"}

    email = body.get("email", "")
    if not email:
        return {"ok": False, "error": "Email is required."}

    from ...db.config import get_config

    config = get_config()
    if not config.is_configured:
        return {"ok": False, "error": "Supabase is not configured."}

    try:
        from ...db.config import get_supabase_client

        client = get_supabase_client()
        client.auth.reset_password_email(email)
    except Exception:
        pass

    # Don't reveal whether the email exists
    return {
        "ok": True,
        "message": "If an account with that email exists, a reset link has been sent.",
    }


# =============================================================================
# JSON KIT DETAIL API (for React SPA)
# =============================================================================


@router.get("/kits/{slug}/detail")
async def get_kit_detail_json(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Get full kit detail as JSON for the React frontend."""
    from ...db.config import get_config

    config = get_config()
    kit_data = None
    resources = []
    steps = []
    tools = []
    source = "local"
    is_owner = False

    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)
                if db_kit:
                    version = db_kit.current_version
                    kit_data = {
                        "id": str(db_kit.id),
                        "name": db_kit.name,
                        "slug": db_kit.slug,
                        "description": db_kit.description,
                        "is_public": db_kit.is_public,
                        "created_at": db_kit.created_at.isoformat() if db_kit.created_at else None,
                        "version_number": version.version_number if version else None,
                    }
                    source = "database"
                    is_owner = (
                        user is not None
                        and db_kit.owner_id is not None
                        and str(db_kit.owner_id) == user["id"]
                    )

                    if version:
                        for r in sorted(version.resources, key=lambda x: x.resource_number):
                            resources.append(
                                {
                                    "number": r.resource_number,
                                    "resource_id": r.resource_id,
                                    "filename": r.filename,
                                    "display_name": r.display_name,
                                    "is_dynamic": getattr(r, "is_dynamic", False),
                                    "extracted_text": r.extracted_text,
                                    "file_size_bytes": r.file_size_bytes,
                                    "mime_type": r.mime_type,
                                }
                            )
                        for s in sorted(version.workflow_steps, key=lambda x: x.step_number):
                            steps.append(
                                {
                                    "number": s.step_number,
                                    "output_id": s.output_id,
                                    "prompt_template": s.prompt_template,
                                    "display_name": s.display_name,
                                }
                            )
                        from ...tools import get_tool
                        for t in sorted(version.tools, key=lambda x: x.tool_number):
                            tool_def = get_tool(t.tool_name)
                            tools.append(
                                {
                                    "number": t.tool_number,
                                    "tool_name": t.tool_name,
                                    "tool_id": t.tool_id,
                                    "display_name": t.display_name,
                                    "configuration": t.configuration,
                                    "source": getattr(tool_def, "source", "builtin") if tool_def else "unknown",
                                }
                            )
        except Exception:
            pass

    if not kit_data:
        # Fall back to local filesystem
        try:
            from ...loader import load_reasoning_kit
            from ...cli import resolve_kit_path

            kit_path = resolve_kit_path(slug, "reasoning_kits")
            kit = load_reasoning_kit(kit_path)
            kit_data = {
                "id": slug,
                "name": kit.name,
                "slug": slug,
                "description": "",
                "is_public": True,
                "created_at": None,
                "version_number": None,
            }
            source = "local"
            for key in sorted(kit.resources.keys(), key=int):
                r = kit.resources[key]
                resources.append(
                    {
                        "number": int(key),
                        "resource_id": r.resource_id,
                        "filename": r.file,
                        "display_name": getattr(r, "display_name", None),
                        "is_dynamic": getattr(r, "is_dynamic", False),
                        "extracted_text": r.content,
                        "file_size_bytes": len(r.content.encode()) if r.content else 0,
                        "mime_type": "text/plain",
                    }
                )
            for key in sorted(kit.workflow.keys(), key=int):
                s = kit.workflow[key]
                steps.append(
                    {
                        "number": int(key),
                        "output_id": s.output_id,
                        "prompt_template": s.prompt,
                        "display_name": getattr(s, "display_name", None),
                    }
                )
        except Exception:
            return {"error": f"Kit '{slug}' not found."}

    return {
        "kit": kit_data,
        "resources": resources,
        "steps": steps,
        "tools": tools,
        "source": source,
        "is_owner": is_owner,
    }

# ---------------------------------------------------------------------------
# MCP Config (Per-User Credentials)
# ---------------------------------------------------------------------------


@router.get("/mcp/config")
async def get_mcp_configs(user: dict | None = Depends(get_optional_user)):
    """Get all user-specific MCP server configurations."""
    from ...db.config import get_config
    if not get_config().is_database_configured:
        return JSONResponse({"ok": False, "error": "Database not configured"}, status_code=500)

    try:
        from ...db import get_async_session
        from ...db.models import McpServerConfig
        from sqlalchemy import select

        async with get_async_session() as session:
            if not user or "id" not in user:
                return {"ok": True, "configs": []}
                
            stmt = select(McpServerConfig).where(McpServerConfig.user_id == user["id"])
            result = await session.execute(stmt)
            configs = result.scalars().all()
            
            return {
                "ok": True,
                "configs": [
                    {
                        "server_name": c.server_name,
                        "env_vars": c.env_vars,
                        "is_active": c.is_active,
                    }
                    for c in configs
                ]
            }
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Error fetching MCP configs: {e}"}, status_code=500)


@router.put("/mcp/config/{server_name}")
async def update_mcp_config(request: Request, server_name: str, user: dict | None = Depends(get_optional_user)):
    """Update or create a user-specific MCP server configuration."""
    from ...db.config import get_config
    if not get_config().is_database_configured:
        return JSONResponse({"ok": False, "error": "Database not configured"}, status_code=500)

    try:
        data = await request.json()
        env_vars = data.get("env_vars", {})
        
        from ...db import get_async_session
        from ...db.models import McpServerConfig
        from sqlalchemy import select
        
        async with get_async_session() as session:
            if not user or "id" not in user:
                return JSONResponse({"ok": False, "error": "Unauthorized"}, status_code=401)
                
            stmt = select(McpServerConfig).where(
                McpServerConfig.user_id == user["id"],
                McpServerConfig.server_name == server_name
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                config.env_vars = env_vars
                if "is_active" in data:
                    config.is_active = data["is_active"]
            else:
                config = McpServerConfig(
                    user_id=user["id"],
                    server_name=server_name,
                    env_vars=env_vars,
                    is_active=data.get("is_active", False)
                )
                session.add(config)
                
            await session.commit()
            return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Error updating MCP config: {e}"}, status_code=500)


@router.delete("/mcp/config/{server_name}")
async def delete_mcp_config(server_name: str, user: dict | None = Depends(get_optional_user)):
    """Delete a user-specific MCP server configuration."""
    from ...db.config import get_config
    if not get_config().is_database_configured:
        return JSONResponse({"ok": False, "error": "Database not configured"}, status_code=500)

    try:
        from ...db import get_async_session
        from ...db.models import McpServerConfig
        from sqlalchemy import select
        
        async with get_async_session() as session:
            if not user or "id" not in user:
                return JSONResponse({"ok": False, "error": "Unauthorized"}, status_code=401)
                
            stmt = select(McpServerConfig).where(
                McpServerConfig.user_id == user["id"],
                McpServerConfig.server_name == server_name
            )
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            
            if config:
                await session.delete(config)
                await session.commit()
            return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Error deleting MCP config: {e}"}, status_code=500)

