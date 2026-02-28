"""Loader for reasoning kits from filesystem and database."""

import re
from pathlib import Path
from uuid import UUID

from .db import (
    KitVersionRepository,
    ReasoningKitRepository,
    StorageService,
    get_async_session,
)
from .db.models import KitVersion
from .db.models import ReasoningKit as DBReasoningKit
from .models import ReasoningKit, Resource, Tool, WorkflowStep


class LoadedKit:
    """Container for a loaded kit with optional database metadata."""

    def __init__(
        self,
        kit: ReasoningKit,
        version_id: UUID | None = None,
        kit_id: UUID | None = None,
    ) -> None:
        self.kit = kit
        self.version_id = version_id
        self.kit_id = kit_id


def load_reasoning_kit(kit_path: str | Path) -> ReasoningKit:
    """Load a reasoning kit from a local directory by auto-discovering files.

    The loader discovers:
    - resource_*.* files as resources (resource_id derived from filename)
    - instruction_*.txt files as workflow steps (ordered by number)

    Args:
        kit_path: Path to the reasoning kit directory

    Returns:
        A fully loaded ReasoningKit with all resources and workflow steps
    """
    kit_path = Path(kit_path)

    if not kit_path.exists():
        raise FileNotFoundError(f"Reasoning kit not found: {kit_path}")

    # Auto-discover resources (resource_*.* and dynamic_resource_*.*)
    resources: dict[str, Resource] = {}
    resource_files = sorted(kit_path.glob("resource_*.*"))
    dynamic_resource_files = sorted(kit_path.glob("dynamic_resource_*.*"))
    all_resource_files = resource_files + dynamic_resource_files
    for idx, resource_file in enumerate(all_resource_files, start=1):
        is_dynamic = resource_file.name.startswith("dynamic_resource_")
        # Extract resource_id from filename
        # dynamic_resource_1.txt -> resource_1, resource_1.txt -> resource_1
        resource_id = resource_file.stem.replace("dynamic_", "")
        resource = Resource(
            file=resource_file.name,
            resource_id=resource_id,
            content="" if is_dynamic else resource_file.read_text(),
            is_dynamic=is_dynamic,
        )
        resources[str(idx)] = resource

    # Auto-discover workflow steps (instruction_*.txt)
    workflow: dict[str, WorkflowStep] = {}
    instruction_files = sorted(
        kit_path.glob("instruction_*.txt"),
        key=lambda f: _extract_number(f.name) or 0,
    )
    for instruction_file in instruction_files:
        # Extract step number from filename (e.g., instruction_1.txt -> 1)
        step_num = _extract_number(instruction_file.name)
        if step_num is None:
            continue
        step = WorkflowStep(
            file=instruction_file.name,
            output_id=f"workflow_{step_num}",
            prompt=instruction_file.read_text(),
        )
        workflow[str(step_num)] = step

    if not workflow:
        raise FileNotFoundError(f"No instruction files found in {kit_path}")

    return ReasoningKit(
        name=kit_path.name,
        path=str(kit_path),
        resources=resources,
        workflow=workflow,
    )


def _extract_number(filename: str) -> int | None:
    """Extract the number from a filename like instruction_1.txt or resource_2.csv."""
    match = re.search(r"_(\d+)\.", filename)
    if match:
        return int(match.group(1))
    return None


def list_reasoning_kits(base_path: str | Path = "reasoning_kits") -> list[str]:
    """List all available local reasoning kits.

    A valid kit is a directory containing at least one instruction_*.txt file.

    Args:
        base_path: Base path to search for reasoning kits

    Returns:
        List of reasoning kit names
    """
    base_path = Path(base_path)
    if not base_path.exists():
        return []

    kits = []
    for item in base_path.iterdir():
        if item.is_dir():
            # Check for instruction files instead of synopsis.json
            instruction_files = list(item.glob("instruction_*.txt"))
            if instruction_files:
                kits.append(item.name)
    return kits


# =============================================================================
# DATABASE LOADING FUNCTIONS
# =============================================================================


async def load_reasoning_kit_from_db(slug: str, version_id: UUID | None = None) -> LoadedKit:
    """Load a reasoning kit from the database by slug.

    Args:
        slug: The kit's URL-friendly slug
        version_id: Optional specific version ID to load instead of current_version

    Returns:
        A LoadedKit containing the ReasoningKit and database metadata

    Raises:
        FileNotFoundError: If kit not found or has no current version
    """
    async with get_async_session() as session:
        repo = ReasoningKitRepository(session)
        db_kit = await repo.get_by_slug(slug)

        if db_kit is None:
            raise FileNotFoundError(f"Reasoning kit not found: {slug}")

        target_version = None
        if version_id:
            version_repo = KitVersionRepository(session)
            target_version = await version_repo.get_by_id(version_id)
            if not target_version or target_version.kit_id != db_kit.id:
                raise FileNotFoundError(f"Reasoning kit version '{version_id}' not found for kit '{slug}'")
        else:
            target_version = db_kit.current_version
            if target_version is None:
                raise FileNotFoundError(f"Reasoning kit '{slug}' has no published version")

        kit = await _convert_db_kit_to_model(db_kit, target_version)
        return LoadedKit(
            kit=kit,
            version_id=target_version.id,
            kit_id=db_kit.id,
        )


async def _convert_db_kit_to_model(
    db_kit: DBReasoningKit, version: KitVersion
) -> ReasoningKit:
    """Convert database kit and version to Pydantic model.

    Args:
        db_kit: Database reasoning kit
        version: Kit version with resources and steps loaded

    Returns:
        Pydantic ReasoningKit model
    """
    storage = StorageService()

    # Load resources
    resources: dict[str, Resource] = {}
    for db_resource in version.resources:
        is_dynamic = getattr(db_resource, "is_dynamic", False)

        # Dynamic resources have no pre-loaded content
        if is_dynamic:
            content = ""
        else:
            # Download content from storage
            try:
                content = storage.download_resource_text(db_resource.storage_path)
            except Exception:
                # If download fails, use extracted text as fallback
                content = db_resource.extracted_text or ""

        resource = Resource(
            file=db_resource.filename,
            resource_id=db_resource.resource_id,
            content=content,
            is_dynamic=is_dynamic,
            display_name=db_resource.display_name,
        )
        resources[str(db_resource.resource_number)] = resource

    # Load workflow steps
    workflow: dict[str, WorkflowStep] = {}
    for db_step in version.workflow_steps:
        step = WorkflowStep(
            file=f"instruction_{db_step.step_number}.txt",
            output_id=db_step.output_id,
            prompt=db_step.prompt_template,
            display_name=db_step.display_name,
        )
        workflow[str(db_step.step_number)] = step

    # Load tools
    tools: dict[str, Tool] = {}
    for db_tool in version.tools:
        tool = Tool(
            tool_name=db_tool.tool_name,
            tool_id=f"tool_{db_tool.tool_number}",
            display_name=db_tool.display_name,
            configuration=db_tool.configuration,
        )
        tools[str(db_tool.tool_number)] = tool

    return ReasoningKit(
        name=db_kit.name,
        path=f"db://{db_kit.slug}",  # Special path indicating database source
        resources=resources,
        workflow=workflow,
        tools=tools,
    )


async def list_reasoning_kits_from_db() -> list[dict[str, str]]:
    """List all public reasoning kits from database.

    Returns:
        List of dicts with 'slug', 'name', and 'description'
    """
    async with get_async_session() as session:
        repo = ReasoningKitRepository(session)
        kits = await repo.list_public()

        return [
            {
                "slug": kit.slug,
                "name": kit.name,
                "description": kit.description or "",
            }
            for kit in kits
        ]


async def get_kit_info_from_db(slug: str) -> dict | None:
    """Get detailed information about a kit from database.

    Args:
        slug: The kit's URL-friendly slug

    Returns:
        Dict with kit details or None if not found
    """
    async with get_async_session() as session:
        repo = ReasoningKitRepository(session)
        db_kit = await repo.get_by_slug(slug)

        if db_kit is None:
            return None

        version = db_kit.current_version
        version_info = None

        if version:
            version_info = {
                "version_number": version.version_number,
                "commit_message": version.commit_message,
                "created_at": version.created_at.isoformat(),
                "resources": [
                    {
                        "number": r.resource_number,
                        "filename": r.filename,
                        "mime_type": r.mime_type,
                        "file_size_bytes": r.file_size_bytes,
                        "is_dynamic": getattr(r, "is_dynamic", False),
                    }
                    for r in version.resources
                ],
                "workflow_steps": [
                    {
                        "number": s.step_number,
                        "output_id": s.output_id,
                    }
                    for s in version.workflow_steps
                ],
                "tools": [
                    {
                        "number": t.tool_number,
                        "tool_name": t.tool_name,
                        "display_name": t.display_name,
                    }
                    for t in version.tools
                ],
            }

        return {
            "slug": db_kit.slug,
            "name": db_kit.name,
            "description": db_kit.description,
            "is_public": db_kit.is_public,
            "created_at": db_kit.created_at.isoformat(),
            "updated_at": db_kit.updated_at.isoformat(),
            "current_version": version_info,
        }
