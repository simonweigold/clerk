"""Loader for reasoning kits."""

import re
from pathlib import Path

from .models import ReasoningKit, Resource, WorkflowStep


def load_reasoning_kit(kit_path: str | Path) -> ReasoningKit:
    """Load a reasoning kit from a directory by auto-discovering files.

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

    # Auto-discover resources (resource_*.*)
    resources: dict[str, Resource] = {}
    resource_files = sorted(kit_path.glob("resource_*.*"))
    for idx, resource_file in enumerate(resource_files, start=1):
        # Extract resource_id from filename (e.g., resource_1.txt -> resource_1)
        resource_id = resource_file.stem
        resource = Resource(
            file=resource_file.name,
            resource_id=resource_id,
            content=resource_file.read_text(),
        )
        resources[str(idx)] = resource

    # Auto-discover workflow steps (instruction_*.txt)
    workflow: dict[str, WorkflowStep] = {}
    instruction_files = sorted(
        kit_path.glob("instruction_*.txt"),
        key=lambda f: _extract_number(f.name),
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
    """List all available reasoning kits.

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
