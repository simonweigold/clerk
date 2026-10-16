"""Tests for the reasoning_kits loader."""

from pathlib import Path

from reasoning_kits.loader import list_reasoning_kits, load_reasoning_kit


def test_list_reasoning_kits_empty(tmp_path: Path) -> None:
    assert list_reasoning_kits(tmp_path) == []


def test_list_reasoning_kits_finds_kits(tmp_path: Path) -> None:
    kit_a = tmp_path / "kit_a"
    kit_a.mkdir()
    (kit_a / "instruction_1.txt").write_text("Step 1")

    kit_b = tmp_path / "kit_b"
    kit_b.mkdir()
    (kit_b / "instruction_1.txt").write_text("Step 1")
    (kit_b / "instruction_2.txt").write_text("Step 2")

    not_a_kit = tmp_path / "not_a_kit"
    not_a_kit.mkdir()
    (not_a_kit / "readme.md").write_text("not a kit")

    assert list_reasoning_kits(tmp_path) == ["kit_a", "kit_b"]


def test_load_reasoning_kit_basic(tmp_path: Path) -> None:
    kit_dir = tmp_path / "my_kit"
    kit_dir.mkdir()
    (kit_dir / "instruction_1.txt").write_text("Step 1 prompt")
    (kit_dir / "instruction_2.txt").write_text("Step 2 uses {workflow_1}")
    (kit_dir / "resource_1.txt").write_text("Resource content")

    kit = load_reasoning_kit(kit_dir)

    assert kit.name == "my_kit"
    assert set(kit.workflow.keys()) == {"1", "2"}
    assert kit.workflow["1"].output_id == "workflow_1"
    assert kit.workflow["2"].output_id == "workflow_2"
    assert kit.workflow["2"].prompt == "Step 2 uses {workflow_1}"
    assert "1" in kit.resources
    assert kit.resources["1"].content == "Resource content"


def test_load_reasoning_kit_dynamic_resources(tmp_path: Path) -> None:
    kit_dir = tmp_path / "dyn_kit"
    kit_dir.mkdir()
    (kit_dir / "instruction_1.txt").write_text("Process {resource_1}")
    (kit_dir / "dynamic_resource_1.txt").write_text("placeholder will be replaced")

    kit = load_reasoning_kit(kit_dir)
    assert kit.resources["1"].is_dynamic
    assert kit.resources["1"].content == ""


def test_load_reasoning_kit_tools(tmp_path: Path) -> None:
    kit_dir = tmp_path / "tool_kit"
    kit_dir.mkdir()
    (kit_dir / "instruction_1.txt").write_text("Step with tool")
    (kit_dir / "tool_1.json").write_text('{"tool_name": "read_url"}')

    kit = load_reasoning_kit(kit_dir)
    assert kit.tools["1"].tool_name == "read_url"


def test_load_reasoning_kit_evaluators(tmp_path: Path) -> None:
    kit_dir = tmp_path / "eval_kit"
    kit_dir.mkdir()
    (kit_dir / "instruction_1.txt").write_text("Step")
    (kit_dir / "evaluator_1.txt").write_text("Rate the output")

    kit = load_reasoning_kit(kit_dir)
    assert kit.evaluators["1"] == [("default", "Rate the output")]


def test_load_reasoning_kit_kit_config(tmp_path: Path) -> None:
    kit_dir = tmp_path / "config_kit"
    kit_dir.mkdir()
    (kit_dir / "instruction_1.txt").write_text("Step")
    (kit_dir / "kit.json").write_text('{"model": "gpt-4", "mode": "anonymous"}')

    kit = load_reasoning_kit(kit_dir)
    assert kit.config.model == "gpt-4"
    assert kit.config.mode == "anonymous"


def test_load_reasoning_kit_not_found(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(FileNotFoundError):
        load_reasoning_kit(tmp_path / "nonexistent")


def test_load_reasoning_kit_no_instructions(tmp_path: Path) -> None:
    import pytest

    kit_dir = tmp_path / "empty_kit"
    kit_dir.mkdir()
    (kit_dir / "resource_1.txt").write_text("Resource without instructions")

    with pytest.raises(FileNotFoundError):
        load_reasoning_kit(kit_dir)