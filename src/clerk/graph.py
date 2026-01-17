"""LangGraph workflow execution for reasoning kits."""

import re
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .models import ReasoningKit


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


def create_initial_state(kit: ReasoningKit) -> State:
    """Create initial state from a reasoning kit."""
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
    )


def resolve_placeholders(text: str, resources: dict[str, str], outputs: dict[str, str]) -> str:
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
    prompt = resolve_placeholders(
        prompt_template, state["resources"], state["outputs"]
    )

    # Execute with LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke(prompt)
    result = response.content

    # Update outputs
    new_outputs = {**state["outputs"], output_id: result}

    print(f"\n{'='*60}")
    print(f"Step {current_step} - Output ID: {output_id}")
    print(f"{'='*60}")
    print(f"Prompt:\n{prompt[:200]}..." if len(prompt) > 200 else f"Prompt:\n{prompt}")
    print(f"\nResult:\n{result}")
    print(f"{'='*60}\n")

    return {
        **state,
        "outputs": new_outputs,
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


def should_continue(state: State) -> str:
    """Determine next node based on state."""
    if state["completed"]:
        return "end"
    if state["error"]:
        return "end"
    return "execute"


def build_graph() -> StateGraph:
    """Build the LangGraph workflow."""
    graph = StateGraph(State)

    # Add nodes
    graph.add_node("execute", execute_step)
    graph.add_node("advance", advance_step)

    # Set entry point
    graph.set_entry_point("execute")

    # Add edges
    graph.add_edge("execute", "advance")
    graph.add_conditional_edges(
        "advance",
        should_continue,
        {
            "execute": "execute",
            "end": END,
        },
    )

    return graph.compile()


def run_reasoning_kit(kit: ReasoningKit) -> dict[str, str]:
    """Run a reasoning kit through the workflow.

    Args:
        kit: The reasoning kit to execute

    Returns:
        Dict of all outputs from the workflow
    """
    graph = build_graph()
    initial_state = create_initial_state(kit)

    print(f"\n{'#'*60}")
    print(f"Running Reasoning Kit: {kit.name}")
    print(f"{'#'*60}")
    print(f"Resources: {list(initial_state['resources'].keys())}")
    print(f"Workflow Steps: {initial_state['total_steps']}")
    print(f"{'#'*60}\n")

    final_state = graph.invoke(initial_state)

    print(f"\n{'#'*60}")
    print("Workflow Completed!")
    print(f"{'#'*60}")
    print("Final Outputs:")
    for output_id, result in final_state["outputs"].items():
        print(f"\n{output_id}:")
        print(result)
    print(f"{'#'*60}\n")

    return final_state["outputs"]
