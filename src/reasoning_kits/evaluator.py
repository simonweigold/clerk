"""Evaluation logic for reasoning kit workflow steps."""

import json
from pathlib import Path

from .models import DimensionScore, StepEvaluation


def prompt_for_evaluation(step: int, output_id: str) -> int:
    """Prompt user for an evaluation score (0-100) for a workflow step.

    Args:
        step: The step number being evaluated.
        output_id: The output ID of the step.

    Returns:
        Integer score from 0 to 100.
    """
    while True:
        try:
            user_input = input(f"\nRate step {step} ({output_id}) from 0-100: ")
            score = int(user_input)
            if 0 <= score <= 100:
                return score
            print("Please enter a number between 0 and 100.")
        except ValueError:
            print("Invalid input. Please enter an integer between 0 and 100.")


def get_next_evaluation_number(kit_path: Path) -> int:
    """Find the next available evaluation number for a reasoning kit.

    Args:
        kit_path: Path to the reasoning kit directory.

    Returns:
        Next available evaluation number (1 if none exist).
    """
    evaluations_dir = kit_path / "evaluations"
    if not evaluations_dir.exists():
        return 1

    existing_files = list(evaluations_dir.glob("*.json"))
    if not existing_files:
        return 1

    numbers = []
    for f in existing_files:
        try:
            numbers.append(int(f.stem))
        except ValueError:
            continue

    return max(numbers) + 1 if numbers else 1


def save_evaluation(kit_path: Path, evaluation) -> Path:
    """Save an evaluation to the evaluations/ subdirectory.

    Args:
        kit_path: Path to the reasoning kit directory.
        evaluation: The evaluation data (Evaluation model).

    Returns:
        Path to the saved evaluation file.
    """
    evaluations_dir = kit_path / "evaluations"
    evaluations_dir.mkdir(exist_ok=True)

    eval_number = get_next_evaluation_number(kit_path)
    eval_file = evaluations_dir / f"{eval_number}.json"

    with open(eval_file, "w") as f:
        json.dump(evaluation.model_dump(), f, indent=4)

    return eval_file


def create_step_evaluation(
    prompt: str,
    output: str,
    score: int,
    mode: str,
    dimension_scores: list[dict] | None = None,
) -> StepEvaluation:
    """Create a StepEvaluation with the appropriate data based on mode.

    Args:
        prompt: The input prompt sent to the LLM.
        output: The output received from the LLM.
        score: The aggregated evaluation score (0-100).
        mode: Either "transparent" (store full text) or "anonymous" (char counts).
        dimension_scores: Optional list of per-dimension scores.

    Returns:
        StepEvaluation with data appropriate for the mode.
    """
    if dimension_scores is None:
        dims = [DimensionScore(label="default", score=score)]
    else:
        dims = [DimensionScore(label=d["label"], score=d["score"]) for d in dimension_scores]

    if mode == "transparent":
        return StepEvaluation(input=prompt, output=output, dimension_scores=dims, evaluation=score)

    return StepEvaluation(
        input=len(prompt),
        output=len(output),
        dimension_scores=dims,
        evaluation=score,
    )


def aggregate_scores(scores: list[int], strategy: str) -> int:
    """Aggregate multiple dimension scores into a single score.

    Args:
        scores: List of integer scores (0-100).
        strategy: Aggregation strategy: "average", "min", "max", or "first".

    Returns:
        Aggregated score as integer.
    """
    if not scores:
        return 0
    if strategy == "min":
        return min(scores)
    if strategy == "max":
        return max(scores)
    if strategy == "first":
        return scores[0]
    return round(sum(scores) / len(scores))


def _parse_score(response_text: str) -> int:
    """Extract and validate integer score from judge LLM response."""
    for line in reversed(response_text.strip().splitlines()):
        line = line.strip()
        if line.isdigit():
            score = int(line)
            if 0 <= score <= 100:
                return score
    raise ValueError(f"Could not parse valid score (0-100) from judge response: {response_text!r}")


async def run_judge(
    template: str,
    prompt: str,
    output: str,
    judge_model: str,
) -> int:
    """Call judge LLM and return an integer score 0-100.

    Args:
        template: Evaluator prompt template with {prompt} and {output} placeholders.
        prompt: The prompt that was sent to the main LLM.
        output: The output produced by the main LLM.
        judge_model: Model name to use as judge.

    Returns:
        Integer score from 0 to 100.
    """
    from .llm import acompletion

    eval_prompt = template.replace("{prompt}", prompt).replace("{output}", output)
    response = await acompletion(
        model=judge_model,
        messages=[{"role": "user", "content": eval_prompt}],
        temperature=0.0,
    )
    return _parse_score(response.choices[0].message.content or "")