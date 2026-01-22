"""LangGraph workflow execution for reasoning kits."""

import re
from pathlib import Path
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .evaluation import (
    create_step_evaluation,
    prompt_for_evaluation,
    save_evaluation,
)
from .models import Evaluation, ReasoningKit


class State(TypedDict):
    """TypedDict state for LangGraph."""

    kit_name: str
    kit_path: str
    resources: dict[str, str]  # resource_id -> content
    workflow_prompts: dict[str, str]  # step number -> prompt template
    workflow_output_ids: dict[str, str]  # step number -> output_id
    outputs: Annotated[dict[str, str], lambda x, y: {**x, **y}]  # output_id -> result
    current_step: int
    total_steps: int
    completed: bool
    error: str | None
    # Evaluation fields
    evaluate: bool  # Whether evaluation is enabled
    evaluation_mode: str  # "transparent" or "anonymous"
    evaluations: dict[str, dict]  # step number -> {input, output, evaluation}
    last_prompt: str  # Store the last prompt for evaluation
    last_output: str  # Store the last output for evaluation


def create_initial_state(
    kit: ReasoningKit,
    evaluate: bool = False,
    evaluation_mode: str = "transparent",
) -> State:
    """Create initial state from a reasoning kit.

    Args:
        kit: The reasoning kit to execute
        evaluate: Whether to enable step-by-step evaluation
        evaluation_mode: Either "transparent" or "anonymous"

    Returns:
        Initial state for the workflow
    """
    resources = {r.resource_id: r.content for r in kit.resources.values()}
    workflow_prompts = {k: v.prompt for k, v in kit.workflow.items()}
    workflow_output_ids = {k: v.output_id for k, v in kit.workflow.items()}

    return State(
        kit_name=kit.name,
        kit_path=kit.path,
        resources=resources,
        workflow_prompts=workflow_prompts,
        workflow_output_ids=workflow_output_ids,
        outputs={},
        current_step=1,
        total_steps=len(kit.workflow),
        completed=False,
        error=None,
        evaluate=evaluate,
        evaluation_mode=evaluation_mode,
        evaluations={},
        last_prompt="",
        last_output="",
    )


def resolve_placeholders(
    text: str, resources: dict[str, str], outputs: dict[str, str]
) -> str:
    """Resolve {placeholder} references in text.

    Args:
        text: Text with placeholders like {resource_1} or {workflow_1}
        resources: Dict of resource_id -> content
        outputs: Dict of output_id -> result

    Returns:
        Text with all placeholders resolved
    """
    # Find all placeholders
    placeholders = re.findall(r"\{(\w+)\}", text)

    for placeholder in placeholders:
        if placeholder in resources:
            text = text.replace(f"{{{placeholder}}}", resources[placeholder])
        elif placeholder in outputs:
            text = text.replace(f"{{{placeholder}}}", outputs[placeholder])

    return text


def execute_step(state: State) -> State:
    """Execute the current workflow step."""
    current_step = str(state["current_step"])

    if current_step not in state["workflow_prompts"]:
        return {
            **state,
            "completed": True,
            "error": f"Step {current_step} not found in workflow",
        }

    prompt_template = state["workflow_prompts"][current_step]
    output_id = state["workflow_output_ids"][current_step]

    # Resolve placeholders in prompt
    prompt = resolve_placeholders(prompt_template, state["resources"], state["outputs"])

    # Execute with LLM
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    response = llm.invoke(prompt)
    result = response.content

    # Update outputs
    new_outputs = {**state["outputs"], output_id: result}

    print(f"\n{'=' * 60}")
    print(f"Step {current_step} - Output ID: {output_id}")
    print(f"{'=' * 60}")
    print(f"Prompt:\n{prompt[:200]}..." if len(prompt) > 200 else f"Prompt:\n{prompt}")
    print(f"\nResult:\n{result}")
    print(f"{'=' * 60}\n")

    return {
        **state,
        "outputs": new_outputs,
        "last_prompt": prompt,
        "last_output": result,
    }


def advance_step(state: State) -> State:
    """Advance to the next step or mark as completed."""
    next_step = state["current_step"] + 1

    if next_step > state["total_steps"]:
        return {
            **state,
            "completed": True,
            "current_step": next_step,
        }

    return {
        **state,
        "current_step": next_step,
    }


def evaluate_step(state: State) -> State:
    """Prompt user for evaluation of the current step if evaluation is enabled."""
    if not state["evaluate"]:
        return state

    current_step = str(state["current_step"])
    output_id = state["workflow_output_ids"][current_step]

    # Prompt user for evaluation score
    score = prompt_for_evaluation(state["current_step"], output_id)

    # Create step evaluation based on mode
    step_eval = create_step_evaluation(
        prompt=state["last_prompt"],
        output=state["last_output"],
        score=score,
        mode=state["evaluation_mode"],
    )

    # Update evaluations dict
    new_evaluations = {
        **state["evaluations"],
        current_step: step_eval.model_dump(),
    }

    return {
        **state,
        "evaluations": new_evaluations,
    }


def should_continue(state: State) -> str:
    """Determine next node based on state."""
    if state["completed"]:
        return "end"
    if state["error"]:
        return "end"
    return "execute"


def build_graph():
    """Build the LangGraph workflow."""
    graph = StateGraph(State)

    # Add nodes
    graph.add_node("execute", execute_step)
    graph.add_node("evaluate", evaluate_step)
    graph.add_node("advance", advance_step)

    # Set entry point
    graph.set_entry_point("execute")

    # Add edges: execute -> evaluate -> advance -> (loop or end)
    graph.add_edge("execute", "evaluate")
    graph.add_edge("evaluate", "advance")
    graph.add_conditional_edges(
        "advance",
        should_continue,
        {
            "execute": "execute",
            "end": END,
        },
    )

    return graph.compile()


def run_reasoning_kit(
    kit: ReasoningKit,
    evaluate: bool = False,
    evaluation_mode: str = "transparent",
) -> dict[str, str]:
    """Run a reasoning kit through the workflow.

    Args:
        kit: The reasoning kit to execute
        evaluate: Whether to enable step-by-step evaluation
        evaluation_mode: Either "transparent" or "anonymous"

    Returns:
        Dict of all outputs from the workflow
    """
    graph = build_graph()
    initial_state = create_initial_state(kit, evaluate, evaluation_mode)

    print(f"\n{'#' * 60}")
    print(f"Running Reasoning Kit: {kit.name}")
    print(f"{'#' * 60}")
    print(f"Resources: {list(initial_state['resources'].keys())}")
    print(f"Workflow Steps: {initial_state['total_steps']}")
    if evaluate:
        print(f"Evaluation: enabled ({evaluation_mode} mode)")
    print(f"{'#' * 60}\n")

    final_state = graph.invoke(initial_state)

    print(f"\n{'#' * 60}")
    print("Workflow Completed!")
    print(f"{'#' * 60}")
    print("Final Outputs:")
    for output_id, result in final_state["outputs"].items():
        print(f"\n{output_id}:")
        print(result)
    print(f"{'#' * 60}\n")

    # Save evaluation if enabled
    if evaluate and final_state["evaluations"]:
        evaluation = Evaluation(
            mode=evaluation_mode,
            steps={
                k: final_state["evaluations"][k] for k in final_state["evaluations"]
            },
        )
        eval_file = save_evaluation(Path(kit.path), evaluation)
        print(f"Evaluation saved to: {eval_file}\n")

    return final_state["outputs"]
