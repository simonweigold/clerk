"""Tests for the reasoning_kits evaluator."""

from pathlib import Path

from reasoning_kits.evaluator import (
    aggregate_scores,
    create_step_evaluation,
    get_next_evaluation_number,
    save_evaluation,
)
from reasoning_kits.models import DimensionScore, Evaluation, StepEvaluation


def test_aggregate_scores_average() -> None:
    assert aggregate_scores([80, 90, 100], "average") == 90


def test_aggregate_scores_min() -> None:
    assert aggregate_scores([80, 90, 100], "min") == 80


def test_aggregate_scores_max() -> None:
    assert aggregate_scores([80, 90, 100], "max") == 100


def test_aggregate_scores_first() -> None:
    assert aggregate_scores([80, 90, 100], "first") == 80


def test_aggregate_scores_empty() -> None:
    assert aggregate_scores([], "average") == 0


def test_create_step_evaluation_transparent() -> None:
    eval = create_step_evaluation("prompt text", "output text", 85, "transparent")
    assert eval.input == "prompt text"
    assert eval.output == "output text"
    assert eval.evaluation == 85
    assert eval.dimension_scores == [DimensionScore(label="default", score=85)]


def test_create_step_evaluation_anonymous() -> None:
    eval = create_step_evaluation("prompt", "output", 70, "anonymous")
    assert eval.input == 6
    assert eval.output == 6
    assert eval.evaluation == 70


def test_create_step_evaluation_with_dimensions() -> None:
    eval = create_step_evaluation(
        "p", "o", 80, "transparent", [{"label": "structure", "score": 90}, {"label": "depth", "score": 70}]
    )
    assert len(eval.dimension_scores) == 2
    assert eval.dimension_scores[0].label == "structure"


def test_get_next_evaluation_number_empty(tmp_path: Path) -> None:
    assert get_next_evaluation_number(tmp_path) == 1


def test_get_next_evaluation_number_increments(tmp_path: Path) -> None:
    eval_dir = tmp_path / "evaluations"
    eval_dir.mkdir()
    (eval_dir / "1.json").write_text("{}")
    (eval_dir / "2.json").write_text("{}")
    assert get_next_evaluation_number(tmp_path) == 3


def test_save_evaluation(tmp_path: Path) -> None:
    kit_path = tmp_path / "kit"
    kit_path.mkdir()
    evaluation = Evaluation(
        mode="transparent",
        steps={"1": StepEvaluation(input="p", output="o", evaluation=80)},
    )
    saved = save_evaluation(kit_path, evaluation)
    assert saved.exists()
    assert saved.name == "1.json"
    assert saved.parent.name == "evaluations"

    saved2 = save_evaluation(kit_path, evaluation)
    assert saved2.name == "2.json"