"""Evaluation logic for reasoning kit workflow steps."""

import json
from pathlib import Path
from uuid import UUID

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


# =============================================================================
# DATABASE EVALUATION FUNCTIONS
# =============================================================================


async def save_evaluation_to_db(
    run_id: UUID,
    step_number: int,
    prompt: str,
    output: str,
    score: int,
    mode: str,
    model_used: str | None = None,
    tokens_used: int | None = None,
    latency_ms: int | None = None,
) -> None:
    """Save a step evaluation to the database.

    Args:
        run_id: The execution run's UUID
        step_number: The workflow step number
        prompt: The input prompt sent to the LLM
        output: The output received from the LLM
        score: The user's evaluation score (0-100)
        mode: Either "transparent" or "anonymous"
        model_used: LLM model used for this step
        tokens_used: Total tokens consumed
        latency_ms: Execution latency in milliseconds
    """
    from .db import ExecutionRepository, get_async_session

    async with get_async_session() as session:
        repo = ExecutionRepository(session)

        if mode == "transparent":
            await repo.add_step_execution(
                run_id=run_id,
                step_number=step_number,
                input_text=prompt,
                output_text=output,
                evaluation_score=score,
                model_used=model_used,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )
        else:  # anonymous
            await repo.add_step_execution(
                run_id=run_id,
                step_number=step_number,
                input_char_count=len(prompt),
                output_char_count=len(output),
                evaluation_score=score,
                model_used=model_used,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )


async def save_step_to_db(
    run_id: UUID,
    step_number: int,
    prompt: str,
    output: str,
    mode: str,
    model_used: str | None = None,
    tokens_used: int | None = None,
    latency_ms: int | None = None,
) -> None:
    """Save a step execution (without evaluation) to the database.

    Args:
        run_id: The execution run's UUID
        step_number: The workflow step number
        prompt: The input prompt sent to the LLM
        output: The output received from the LLM
        mode: Either "transparent" or "anonymous"
        model_used: LLM model used for this step
        tokens_used: Total tokens consumed
        latency_ms: Execution latency in milliseconds
    """
    from .db import ExecutionRepository, get_async_session

    async with get_async_session() as session:
        repo = ExecutionRepository(session)

        if mode == "transparent":
            await repo.add_step_execution(
                run_id=run_id,
                step_number=step_number,
                input_text=prompt,
                output_text=output,
                model_used=model_used,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )
        else:  # anonymous
            await repo.add_step_execution(
                run_id=run_id,
                step_number=step_number,
                input_char_count=len(prompt),
                output_char_count=len(output),
                model_used=model_used,
                tokens_used=tokens_used,
                latency_ms=latency_ms,
            )


async def update_step_evaluation_in_db(
    run_id: UUID,
    step_number: int,
    score: int,
) -> None:
    """Update the evaluation score for a step in the database.

    Args:
        run_id: The execution run's UUID
        step_number: The workflow step number
        score: The user's evaluation score (0-100)
    """
    from .db import ExecutionRepository, get_async_session

    async with get_async_session() as session:
        repo = ExecutionRepository(session)
        await repo.update_step_evaluation(
            run_id=run_id,
            step_number=step_number,
            evaluation_score=score,
        )


async def create_execution_run(
    version_id: UUID,
    storage_mode: str,
    user_id: UUID | None = None,
) -> UUID:
    """Create a new execution run in the database.

    Args:
        version_id: The kit version's UUID
        storage_mode: Either "transparent" or "anonymous"
        user_id: Optional user ID

    Returns:
        The created run's UUID
    """
    from .db import ExecutionRepository, get_async_session

    async with get_async_session() as session:
        repo = ExecutionRepository(session)
        run = await repo.create(
            version_id=version_id,
            storage_mode=storage_mode,
            user_id=user_id,
        )
        return run.id


async def complete_execution_run(
    run_id: UUID,
    error: str | None = None,
) -> None:
    """Mark an execution run as completed or failed.

    Args:
        run_id: The run's UUID
        error: Error message if failed (None for success)
    """
    from .db import ExecutionRepository, get_async_session

    async with get_async_session() as session:
        repo = ExecutionRepository(session)
        await repo.complete_run(run_id=run_id, error=error)


async def pause_execution_run(run_id: UUID) -> None:
    """Mark an execution run as paused.

    Args:
        run_id: The run's UUID
    """
    from .db import ExecutionRepository, get_async_session

    async with get_async_session() as session:
        repo = ExecutionRepository(session)
        await repo.pause_run(run_id=run_id)


async def delete_execution_run(run_id: UUID) -> bool:
    """Delete an execution run from the database.

    Args:
        run_id: The run's UUID

    Returns:
        True if deleted, False if not found
    """
    from .db import ExecutionRepository, get_async_session

    async with get_async_session() as session:
        repo = ExecutionRepository(session)
        return await repo.delete_run(run_id=run_id)
