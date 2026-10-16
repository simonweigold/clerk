"""Loader for reasoning kits from filesystem."""

import json
import re
from pathlib import Path

from .models import KitConfig, ReasoningKit, Resource, Tool, WorkflowStep


def load_reasoning_kit(kit_path: str | Path) -> ReasoningKit:
    """Load a reasoning kit from a local directory by auto-discovering files.

    Discovers:
    - resource_*.* files as static resources
    - dynamic_resource_*.* files as dynamic resources (content loaded at runtime)
    - instruction_*.txt files as workflow steps (ordered by number)
    - tool_*.json files as tool references
    - evaluator_*.json / evaluator_*.txt files as evaluators
    - kit.json as kit-level config (optional)

    Args:
        kit_path: Path to the reasoning kit directory.

    Returns:
        A fully loaded ReasoningKit with all resources and workflow steps.

    Raises:
        FileNotFoundError: If the kit path doesn't exist or has no instructions.
    """
    kit_path = Path(kit_path)
    if not kit_path.exists():
        raise FileNotFoundError(f"Reasoning kit not found: {kit_path}")

    resources: dict[str, Resource] = {}
    resource_files = sorted(kit_path.glob("resource_*.*"))
    dynamic_resource_files = sorted(kit_path.glob("dynamic_resource_*.*"))
    all_resource_files = resource_files + dynamic_resource_files
    for idx, resource_file in enumerate(all_resource_files, start=1):
        is_dynamic = resource_file.name.startswith("dynamic_resource_")
        resource_id = resource_file.stem.replace("dynamic_", "")
        resources[str(idx)] = Resource(
            file=resource_file.name,
            resource_id=resource_id,
            content="" if is_dynamic else resource_file.read_text(),
            is_dynamic=is_dynamic,
        )

    workflow: dict[str, WorkflowStep] = {}
    instruction_files = sorted(
        kit_path.glob("instruction_*.txt"),
        key=lambda f: _extract_number(f.name) or 0,
    )
    for instruction_file in instruction_files:
        step_num = _extract_number(instruction_file.name)
        if step_num is None:
            continue
        workflow[str(step_num)] = WorkflowStep(
            file=instruction_file.name,
            output_id=f"workflow_{step_num}",
            prompt=instruction_file.read_text(),
        )

    if not workflow:
        raise FileNotFoundError(f"No instruction files found in {kit_path}")

    tools: dict[str, Tool] = {}
    tool_files = sorted(
        kit_path.glob("tool_*.json"),
        key=lambda f: _extract_number(f.name) or 0,
    )
    for tool_file in tool_files:
        tool_num = _extract_number(tool_file.name)
        if tool_num is None:
            continue
        try:
            data = json.loads(tool_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        raw_config = data.get("configuration")
        if raw_config is None:
            configuration = None
        elif isinstance(raw_config, str):
            configuration = raw_config
        else:
            configuration = json.dumps(raw_config)
        tools[str(tool_num)] = Tool(
            tool_name=data.get("tool_name", ""),
            tool_id=f"tool_{tool_num}",
            display_name=data.get("display_name"),
            configuration=configuration,
        )

    evaluators: dict[str, list[tuple[str, str]]] = {}
    evaluator_aggregations: dict[str, str] = {}
    seen_steps: set[str] = set()

    for json_file in sorted(
        kit_path.glob("evaluator_*.json"),
        key=lambda f: _extract_number(f.name) or 0,
    ):
        step_num = _extract_number(json_file.name)
        if step_num is None:
            continue
        key = str(step_num)
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        dimensions = data.get("dimensions", {})
        if not isinstance(dimensions, dict):
            continue
        evaluators[key] = list(dimensions.items())
        if "aggregation" in data:
            evaluator_aggregations[key] = data["aggregation"]
        seen_steps.add(key)

    for txt_file in sorted(
        kit_path.glob("evaluator_*.txt"),
        key=lambda f: _extract_number(f.name) or 0,
    ):
        step_num = _extract_number(txt_file.name)
        if step_num is None:
            continue
        key = str(step_num)
        if key in seen_steps:
            continue
        evaluators[key] = [("default", txt_file.read_text())]

    kit_config = KitConfig()
    kit_json_path = kit_path / "kit.json"
    if kit_json_path.exists():
        try:
            kit_json_data = json.loads(kit_json_path.read_text(encoding="utf-8"))
            kit_config = KitConfig(**kit_json_data)
        except Exception:
            pass

    return ReasoningKit(
        name=kit_path.name,
        path=str(kit_path),
        resources=resources,
        workflow=workflow,
        tools=tools,
        evaluators=evaluators,
        evaluator_aggregations=evaluator_aggregations,
        config=kit_config,
    )


def _extract_number(filename: str) -> int | None:
    """Extract the number from a filename like instruction_1.txt or resource_2.csv."""
    match = re.search(r"_(\d+)\.", filename)
    if match:
        return int(match.group(1))
    return None


def list_reasoning_kits(base_path: str | Path = "kits") -> list[str]:
    """List all available local reasoning kits.

    A valid kit is a directory containing at least one instruction_*.txt file.

    Args:
        base_path: Base path to search for reasoning kits.

    Returns:
        List of reasoning kit names.
    """
    base_path = Path(base_path)
    if not base_path.exists():
        return []

    kits = []
    for item in base_path.iterdir():
        if item.is_dir():
            instruction_files = list(item.glob("instruction_*.txt"))
            if instruction_files:
                kits.append(item.name)
    return sorted(kits)