"""Evaluation logic for reasoning kit workflow steps."""

import json
from pathlib import Path

from .models import Evaluation, StepEvaluation


def prompt_for_evaluation(step: int, output_id: str) -> int:
    """Prompt user for an evaluation score (0-100) for a workflow step.

    Args:
        step: The step number being evaluated
        output_id: The output ID of the step

    Returns:
        Integer score from 0 to 100
    """
    while True:
        try:
            user_input = input(f"\nRate step {step} ({output_id}) from 0-100: ")
            score = int(user_input)
            if 0 <= score <= 100:
                return score
            print("Please enter a number between 0 and 100.")
        except ValueError:
            print("Invalid input. Please enter a number between 0 and 100.")


def get_next_evaluation_number(kit_path: Path) -> int:
    """Find the next available evaluation number for a reasoning kit.

    Args:
        kit_path: Path to the reasoning kit directory

    Returns:
        Next available evaluation number (1 if none exist)
    """
    evaluations_dir = kit_path / "evaluations"
    if not evaluations_dir.exists():
        return 1

    existing_files = list(evaluations_dir.glob("*.json"))
    if not existing_files:
        return 1

    # Extract numbers from existing filenames
    numbers = []
    for f in existing_files:
        try:
            numbers.append(int(f.stem))
        except ValueError:
            continue

    return max(numbers) + 1 if numbers else 1


def save_evaluation(kit_path: Path, evaluation: Evaluation) -> Path:
    """Save an evaluation to the evaluations subdirectory.

    Creates the evaluations/ directory if it doesn't exist.

    Args:
        kit_path: Path to the reasoning kit directory
        evaluation: The evaluation data to save

    Returns:
        Path to the saved evaluation file
    """
    evaluations_dir = kit_path / "evaluations"
    evaluations_dir.mkdir(exist_ok=True)

    eval_number = get_next_evaluation_number(kit_path)
    eval_file = evaluations_dir / f"{eval_number}.json"

    # Convert to dict and write with nice formatting
    eval_dict = evaluation.model_dump()
    with open(eval_file, "w") as f:
        json.dump(eval_dict, f, indent=4)

    return eval_file


def create_step_evaluation(
    prompt: str,
    output: str,
    score: int,
    mode: str,
) -> StepEvaluation:
    """Create a StepEvaluation with the appropriate data based on mode.

    Args:
        prompt: The input prompt sent to the LLM
        output: The output received from the LLM
        score: The user's evaluation score (0-100)
        mode: Either "transparent" (store full text) or "anonymous" (store char counts)

    Returns:
        StepEvaluation with data appropriate for the mode
    """
    if mode == "transparent":
        return StepEvaluation(
            input=prompt,
            output=output,
            evaluation=score,
        )
    else:  # anonymous
        return StepEvaluation(
            input=len(prompt),
            output=len(output),
            evaluation=score,
        )
