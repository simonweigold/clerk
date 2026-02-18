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
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse

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


def _require_auth(request: Request, user: dict | None) -> RedirectResponse | None:
    """Return a redirect if user is not logged in, else None."""
    if not user:
        _flash(request, "Sign in to manage kits.", "error")
        return RedirectResponse("/auth/login", status_code=303)
    return None


def _check_ownership(
    request: Request, db_kit, user: dict | None, slug: str
) -> RedirectResponse | None:
    """Return a redirect if user doesn't own the kit, else None."""
    if db_kit.owner_id and (not user or str(db_kit.owner_id) != user["id"]):
        _flash(request, "You don't have permission to modify this kit.", "error")
        return RedirectResponse(f"/kit/{slug}", status_code=303)
    return None


# =============================================================================
# KIT CRUD
# =============================================================================


@router.post("/kits", response_class=HTMLResponse)
async def create_kit(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    user: dict | None = Depends(get_optional_user),
):
    """Create a new reasoning kit."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

    from ...db.config import get_config

    # Generate slug
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        _flash(request, "Invalid kit name.", "error")
        return RedirectResponse("/kit/new", status_code=303)

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            owner_id = UUID(user["id"]) if user else None

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)

                # Check if slug already exists
                existing = await repo.get_by_slug(slug)
                if existing:
                    _flash(
                        request, f"A kit with slug '{slug}' already exists.", "error"
                    )
                    return RedirectResponse("/kit/new", status_code=303)

                kit = await repo.create(
                    slug=slug,
                    name=name,
                    description=description or None,
                    owner_id=owner_id,
                    is_public=True,
                )

            _flash(request, f"Kit '{name}' created.", "success")
            return RedirectResponse(f"/kit/{slug}", status_code=303)

        except Exception as e:
            _flash(request, f"Error creating kit: {e}", "error")
            return RedirectResponse("/kit/new", status_code=303)
    else:
        # Local filesystem
        try:
            kit_path = Path("reasoning_kits") / slug
            if kit_path.exists():
                _flash(request, f"Kit '{slug}' already exists.", "error")
                return RedirectResponse("/kit/new", status_code=303)

            kit_path.mkdir(parents=True)
            _flash(request, f"Kit '{name}' created.", "success")
            return RedirectResponse(f"/kit/{slug}", status_code=303)

        except Exception as e:
            _flash(request, f"Error creating kit: {e}", "error")
            return RedirectResponse("/kit/new", status_code=303)


@router.post("/kits/{slug}/update", response_class=HTMLResponse)
async def update_kit(
    request: Request,
    slug: str,
    name: str = Form(...),
    description: str = Form(""),
    user: dict | None = Depends(get_optional_user),
):
    """Update a reasoning kit."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)

                if not db_kit:
                    _flash(request, f"Kit '{slug}' not found.", "error")
                    return RedirectResponse("/", status_code=303)

                redirect = _check_ownership(request, db_kit, user, slug)
                if redirect:
                    return redirect

                await repo.update(
                    kit_id=db_kit.id,
                    name=name,
                    description=description or None,
                )

            _flash(request, "Kit updated.", "success")
        except Exception as e:
            _flash(request, f"Error updating kit: {e}", "error")

    return RedirectResponse(f"/kit/{slug}", status_code=303)


@router.post("/kits/{slug}/delete", response_class=HTMLResponse)
async def delete_kit(
    request: Request,
    slug: str,
    user: dict | None = Depends(get_optional_user),
):
    """Delete a reasoning kit."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

    from ...db.config import get_config

    config = get_config()
    if config.is_database_configured:
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kit = await repo.get_by_slug(slug)

                if db_kit:
                    redirect = _check_ownership(request, db_kit, user, slug)
                    if redirect:
                        return redirect

                    await repo.delete(db_kit.id)
                    _flash(request, f"Kit '{slug}' deleted.", "success")
                else:
                    _flash(request, f"Kit '{slug}' not found.", "error")

        except Exception as e:
            _flash(request, f"Error deleting kit: {e}", "error")
    else:
        # Local filesystem
        import shutil

        kit_path = Path("reasoning_kits") / slug
        if kit_path.exists():
            shutil.rmtree(kit_path)
            _flash(request, f"Kit '{slug}' deleted.", "success")
        else:
            _flash(request, f"Kit '{slug}' not found.", "error")

    return RedirectResponse("/", status_code=303)


# =============================================================================
# RESOURCE MANAGEMENT
# =============================================================================


@router.post("/kits/{slug}/resources", response_class=HTMLResponse)
async def add_resource(
    request: Request,
    slug: str,
    file: UploadFile | None = File(None),
    text_content: str = Form(""),
    is_dynamic: str = Form(""),
    display_name: str = Form(""),
    user: dict | None = Depends(get_optional_user),
):
    """Add a resource to a kit (creates a new version)."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

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

            # Determine source: uploaded file or pasted text
            if text_content.strip():
                # Text input path
                file_content = text_content.encode("utf-8")
                safe_name = (display_name.strip() or "resource").replace(" ", "_")
                filename = f"{safe_name}.txt"
                mime_type = "text/plain"
            elif file and file.filename:
                # File upload path
                file_content = await file.read()
                filename = file.filename
                mime_type = detect_mime_type_from_filename(filename)
            else:
                _flash(request, "Please upload a file or paste text content.", "error")
                return RedirectResponse(f"/kit/{slug}", status_code=303)

            async with get_async_session() as session:
                kit_repo = ReasoningKitRepository(session)
                version_repo = KitVersionRepository(session)
                db_kit = await kit_repo.get_by_slug(slug)

                if not db_kit:
                    _flash(request, f"Kit '{slug}' not found.", "error")
                    return RedirectResponse(f"/kit/{slug}", status_code=303)

                redirect = _check_ownership(request, db_kit, user, slug)
                if redirect:
                    return redirect

                # Determine resource number
                resource_number = 1
                if db_kit.current_version:
                    resource_number = len(db_kit.current_version.resources) + 1

                # Create new version
                commit_msg = f"Added resource: {filename}"
                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=commit_msg,
                )

                # Copy existing resources from previous version
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

                # Upload file to storage
                storage = StorageService(use_service_key=True)
                import tempfile

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=Path(filename).suffix
                ) as tmp:
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

                # Extract text
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

            _flash(request, f"Resource '{filename}' added.", "success")

        except Exception as e:
            _flash(request, f"Error adding resource: {e}", "error")
    else:
        # Local filesystem
        try:
            kit_path = Path("reasoning_kits") / slug
            if not kit_path.exists():
                _flash(request, f"Kit '{slug}' not found.", "error")
                return RedirectResponse(f"/kit/{slug}", status_code=303)

            # Find next resource number
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
                filename = f"resource_{next_num}.txt"
            elif file and file.filename:
                filename = file.filename
                ext = Path(filename).suffix or ".txt"
                content = await file.read()
            else:
                _flash(request, "Please upload a file or paste text content.", "error")
                return RedirectResponse(f"/kit/{slug}", status_code=303)

            dest = kit_path / f"resource_{next_num}{ext}"
            dest.write_bytes(content)

            _flash(
                request,
                f"Resource '{filename}' added as resource_{next_num}.",
                "success",
            )
        except Exception as e:
            _flash(request, f"Error adding resource: {e}", "error")

    return RedirectResponse(f"/kit/{slug}", status_code=303)


@router.post("/kits/{slug}/resources/{number}/delete", response_class=HTMLResponse)
async def delete_resource(
    request: Request,
    slug: str,
    number: int,
    user: dict | None = Depends(get_optional_user),
):
    """Delete a resource from a kit."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        # Local filesystem
        kit_path = Path("reasoning_kits") / slug
        matches = list(kit_path.glob(f"resource_{number}.*"))
        if matches:
            matches[0].unlink()
            _flash(request, f"Resource {number} deleted.", "success")
        else:
            _flash(request, f"Resource {number} not found.", "error")
    else:
        # Database: create new version without this resource
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
                    _flash(request, "Kit or version not found.", "error")
                    return RedirectResponse(f"/kit/{slug}", status_code=303)

                redirect = _check_ownership(request, db_kit, user, slug)
                if redirect:
                    return redirect

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Deleted resource {number}",
                )

                # Copy resources except deleted one
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

                # Copy all steps
                for s in db_kit.current_version.workflow_steps:
                    await version_repo.add_workflow_step(
                        version_id=version.id,
                        step_number=s.step_number,
                        prompt_template=s.prompt_template,
                        display_name=s.display_name,
                    )

            _flash(request, f"Resource {number} deleted.", "success")
        except Exception as e:
            _flash(request, f"Error: {e}", "error")

    return RedirectResponse(f"/kit/{slug}", status_code=303)


@router.post("/kits/{slug}/resources/{number}/update", response_class=HTMLResponse)
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
    """Update a resource in a kit (creates a new version)."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

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

            # Determine new content source: pasted text or uploaded file
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
                    _flash(request, "Kit or version not found.", "error")
                    return RedirectResponse(f"/kit/{slug}", status_code=303)

                redirect = _check_ownership(request, db_kit, user, slug)
                if redirect:
                    return redirect

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Updated resource {number}",
                )

                # Copy resources, replacing the updated one
                for r in db_kit.current_version.resources:
                    if r.resource_number == number:
                        # Updated resource
                        res_display_name = display_name.strip() or None
                        res_is_dynamic = bool(is_dynamic)

                        # If a new file was uploaded, handle storage
                        if new_file_content and new_filename:
                            mime_type = detect_mime_type_from_filename(new_filename)
                            extracted = extract_text_from_bytes(
                                new_file_content, mime_type
                            )

                            # Upload new file
                            storage = StorageService(use_service_key=True)
                            import tempfile

                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=Path(new_filename).suffix
                            ) as tmp:
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
                            # Keep existing file, just update metadata
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
                        # Copy unchanged resource
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

                # Copy all steps
                for s in db_kit.current_version.workflow_steps:
                    await version_repo.add_workflow_step(
                        version_id=version.id,
                        step_number=s.step_number,
                        prompt_template=s.prompt_template,
                        display_name=s.display_name,
                    )

            _flash(request, f"Resource {number} updated.", "success")
        except Exception as e:
            _flash(request, f"Error updating resource: {e}", "error")

    return RedirectResponse(f"/kit/{slug}", status_code=303)


# =============================================================================
# STEP MANAGEMENT
# =============================================================================


@router.post("/kits/{slug}/steps", response_class=HTMLResponse)
async def add_step(
    request: Request,
    slug: str,
    prompt: str = Form(...),
    display_name: str = Form(""),
    user: dict | None = Depends(get_optional_user),
):
    """Add a workflow step to a kit."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

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
                    _flash(request, f"Kit '{slug}' not found.", "error")
                    return RedirectResponse(f"/kit/{slug}", status_code=303)

                redirect = _check_ownership(request, db_kit, user, slug)
                if redirect:
                    return redirect

                step_number = 1
                if db_kit.current_version:
                    step_number = len(db_kit.current_version.workflow_steps) + 1

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Added step {step_number}",
                )

                # Copy existing resources and steps
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

                # Add new step
                await version_repo.add_workflow_step(
                    version_id=version.id,
                    step_number=step_number,
                    prompt_template=prompt,
                    display_name=display_name.strip() or None,
                )

            _flash(request, f"Step {step_number} added.", "success")

        except Exception as e:
            _flash(request, f"Error adding step: {e}", "error")
    else:
        # Local filesystem
        try:
            kit_path = Path("reasoning_kits") / slug
            if not kit_path.exists():
                _flash(request, f"Kit '{slug}' not found.", "error")
                return RedirectResponse(f"/kit/{slug}", status_code=303)

            existing = list(kit_path.glob("instruction_*.txt"))
            numbers = []
            for f in existing:
                match = re.search(r"instruction_(\d+)\.txt", f.name)
                if match:
                    numbers.append(int(match.group(1)))
            next_num = max(numbers, default=0) + 1

            dest = kit_path / f"instruction_{next_num}.txt"
            dest.write_text(prompt)
            _flash(request, f"Step {next_num} added.", "success")
        except Exception as e:
            _flash(request, f"Error adding step: {e}", "error")

    return RedirectResponse(f"/kit/{slug}", status_code=303)


@router.post("/kits/{slug}/steps/{number}/update", response_class=HTMLResponse)
async def update_step(
    request: Request,
    slug: str,
    number: int,
    prompt: str = Form(...),
    display_name: str = Form(""),
    user: dict | None = Depends(get_optional_user),
):
    """Update a workflow step."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

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
                    _flash(request, "Kit or version not found.", "error")
                    return RedirectResponse(f"/kit/{slug}", status_code=303)

                redirect = _check_ownership(request, db_kit, user, slug)
                if redirect:
                    return redirect

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Updated step {number}",
                )

                # Copy resources
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

                # Copy steps, replacing the updated one
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

            _flash(request, f"Step {number} updated.", "success")
        except Exception as e:
            _flash(request, f"Error: {e}", "error")
    else:
        # Local filesystem
        step_file = Path("reasoning_kits") / slug / f"instruction_{number}.txt"
        if step_file.exists():
            step_file.write_text(prompt)
            _flash(request, f"Step {number} updated.", "success")
        else:
            _flash(request, f"Step {number} not found.", "error")

    return RedirectResponse(f"/kit/{slug}", status_code=303)


@router.post("/kits/{slug}/steps/{number}/delete", response_class=HTMLResponse)
async def delete_step(
    request: Request,
    slug: str,
    number: int,
    user: dict | None = Depends(get_optional_user),
):
    """Delete a workflow step."""
    redirect = _require_auth(request, user)
    if redirect:
        return redirect

    from ...db.config import get_config

    config = get_config()
    if not config.is_database_configured:
        step_file = Path("reasoning_kits") / slug / f"instruction_{number}.txt"
        if step_file.exists():
            step_file.unlink()
            _flash(request, f"Step {number} deleted.", "success")
        else:
            _flash(request, f"Step {number} not found.", "error")
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
                    _flash(request, "Kit or version not found.", "error")
                    return RedirectResponse(f"/kit/{slug}", status_code=303)

                redirect = _check_ownership(request, db_kit, user, slug)
                if redirect:
                    return redirect

                version = await version_repo.create(
                    kit_id=db_kit.id,
                    commit_message=f"Deleted step {number}",
                )

                # Copy resources
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

                # Copy steps except deleted one
                for s in db_kit.current_version.workflow_steps:
                    if s.step_number != number:
                        await version_repo.add_workflow_step(
                            version_id=version.id,
                            step_number=s.step_number,
                            prompt_template=s.prompt_template,
                            display_name=s.display_name,
                        )

            _flash(request, f"Step {number} deleted.", "success")
        except Exception as e:
            _flash(request, f"Error: {e}", "error")

    return RedirectResponse(f"/kit/{slug}", status_code=303)


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
    try:
        body = await request.json()
    except Exception:
        body = {}

    evaluate = body.get("evaluate", False)
    evaluation_mode = body.get("evaluation_mode", "transparent")
    dynamic_resources = body.get("dynamic_resources", {})

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

        # Create DB run if needed
        db_run_id = None
        if persist and db_version_id:
            try:
                db_run_id = await create_execution_run(
                    version_id=db_version_id,
                    storage_mode=evaluation_mode if evaluate else "transparent",
                )
            except Exception:
                persist = False

        # Send initial event
        yield f"event: start\ndata: {json.dumps({'kit_name': kit.name, 'total_steps': len(kit.workflow)})}\n\n"

        # Execute step by step
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0)
        resources = {r.resource_id: r.content for r in kit.resources.values()}
        outputs: dict[str, str] = {}

        for step_key in sorted(kit.workflow.keys(), key=int):
            step = kit.workflow[step_key]
            step_num = int(step_key)

            # Send step-start event
            yield f"event: step-start\ndata: {json.dumps({'step': step_num, 'output_id': step.output_id, 'display_name': step.display_name})}\n\n"

            # Resolve placeholders
            prompt = resolve_placeholders(step.prompt, resources, outputs)

            # Execute LLM call
            start_time = time.time()
            try:
                response = await llm.ainvoke(prompt)
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
                            prompt=prompt,
                            output=result,
                            mode=evaluation_mode if evaluate else "transparent",
                            model_used=DEFAULT_MODEL,
                            tokens_used=tokens_used,
                            latency_ms=latency_ms,
                        )
                    except Exception:
                        pass

                # Send step-complete event
                yield f"event: step-complete\ndata: {json.dumps({'step': step_num, 'output_id': step.output_id, 'display_name': step.display_name, 'prompt_preview': prompt[:200], 'result': result, 'latency_ms': latency_ms, 'tokens_used': tokens_used})}\n\n"

                # Evaluation pause: wait for user score
                if evaluate and eval_event:
                    exec_state["eval_score"] = None
                    eval_event.clear()
                    yield f"event: step-await-eval\ndata: {json.dumps({'step': step_num})}\n\n"

                    # Wait for user to submit score (timeout after 10 minutes)
                    try:
                        await asyncio.wait_for(eval_event.wait(), timeout=600)
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

        yield f"event: done\ndata: {json.dumps({'status': 'completed', 'total_steps': len(kit.workflow)})}\n\n"
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


# =============================================================================
# AUTH API
# =============================================================================


@router.post("/auth/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """Authenticate with Supabase."""
    from ...db.config import get_config

    config = get_config()
    if not config.is_configured:
        _flash(request, "Supabase is not configured.", "error")
        return RedirectResponse("/auth/login", status_code=303)

    try:
        from ...db.config import get_supabase_client

        client = get_supabase_client()
        response = client.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user:
            request.session["user"] = {
                "id": str(response.user.id),
                "email": response.user.email,
            }
            _flash(request, "Signed in.", "success")
            return RedirectResponse("/", status_code=303)
        else:
            _flash(request, "Invalid credentials.", "error")
            return RedirectResponse("/auth/login", status_code=303)

    except Exception as e:
        error_msg = str(e)
        if "Invalid login" in error_msg or "invalid" in error_msg.lower():
            _flash(request, "Invalid email or password.", "error")
        else:
            _flash(request, f"Sign in error: {error_msg}", "error")
        return RedirectResponse("/auth/login", status_code=303)


@router.post("/auth/signup", response_class=HTMLResponse)
async def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """Register with Supabase."""
    from ...db.config import get_config

    config = get_config()
    if not config.is_configured:
        _flash(request, "Supabase is not configured.", "error")
        return RedirectResponse("/auth/signup", status_code=303)

    try:
        from ...db.config import get_supabase_client

        client = get_supabase_client()
        response = client.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user:
            # Check for already-registered user (Supabase returns user
            # with empty identities list if email is already taken)
            identities = getattr(response.user, "identities", None)
            if identities is not None and len(identities) == 0:
                _flash(
                    request,
                    "An account with this email already exists. Try signing in instead.",
                    "error",
                )
                return RedirectResponse("/auth/login", status_code=303)

            _flash(
                request,
                "Account created. Please check your email for confirmation.",
                "success",
            )
            return RedirectResponse("/auth/login", status_code=303)
        else:
            _flash(request, "Could not create account.", "error")
            return RedirectResponse("/auth/signup", status_code=303)

    except Exception as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg or "already been registered" in error_msg:
            _flash(
                request,
                "An account with this email already exists. Try signing in instead.",
                "error",
            )
            return RedirectResponse("/auth/login", status_code=303)
        _flash(request, f"Sign up error: {e}", "error")
        return RedirectResponse("/auth/signup", status_code=303)


@router.get("/auth/logout")
async def logout(request: Request):
    """Clear session and log out."""
    request.session.clear()
    _flash(request, "Signed out.", "info")
    return RedirectResponse("/", status_code=303)


@router.post("/auth/reset-password", response_class=HTMLResponse)
async def reset_password(
    request: Request,
    email: str = Form(...),
):
    """Send a password reset email via Supabase."""
    from ...db.config import get_config

    config = get_config()
    if not config.is_configured:
        _flash(request, "Supabase is not configured.", "error")
        return RedirectResponse("/auth/reset-password", status_code=303)

    try:
        from ...db.config import get_supabase_client

        client = get_supabase_client()
        client.auth.reset_password_email(email)
        _flash(
            request,
            "If an account with that email exists, a reset link has been sent.",
            "success",
        )
    except Exception:
        # Don't reveal whether the email exists
        _flash(
            request,
            "If an account with that email exists, a reset link has been sent.",
            "success",
        )

    return RedirectResponse("/auth/login", status_code=303)


# =============================================================================
# SEARCH (HTMX partial)
# =============================================================================


@router.get("/search", response_class=HTMLResponse)
async def search_kits(
    request: Request,
    q: str = "",
    user: dict | None = Depends(get_optional_user),
):
    """Search kits and return partial HTML for HTMX swap."""
    from ...db.config import get_config

    templates = _templates(request)
    kits = []

    config = get_config()
    if config.is_database_configured and q.strip():
        try:
            from ...db import ReasoningKitRepository, get_async_session

            async with get_async_session() as session:
                repo = ReasoningKitRepository(session)
                db_kits = await repo.search(q.strip())
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
            pass
    elif not q.strip():
        # Empty search = show all
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
                        }
                    )
            except Exception:
                pass

    return templates.TemplateResponse(
        request,
        "partials/kit_list.html",
        {
            "kits": kits,
        },
    )
