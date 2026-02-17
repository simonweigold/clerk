"""Data models for reasoning kits."""

from pydantic import BaseModel


class Resource(BaseModel):
    """A resource in a reasoning kit."""

    file: str
    resource_id: str
    content: str = ""  # Loaded at runtime
    is_dynamic: bool = False  # Dynamic resources are provided by user at execution time
    display_name: str | None = None  # Optional custom display name


class WorkflowStep(BaseModel):
    """A step in the workflow."""

    file: str
    output_id: str
    prompt: str = ""  # Loaded at runtime
    display_name: str | None = None  # Optional custom display name


class ReasoningKit(BaseModel):
    """A complete reasoning kit with resources and workflow."""

    name: str
    path: str
    resources: dict[str, Resource]
    workflow: dict[str, WorkflowStep]


class StepEvaluation(BaseModel):
    """Evaluation data for a single workflow step."""

    input: str | int  # Full text (transparent) or char count (anonymous)
    output: str | int  # Full text (transparent) or char count (anonymous)
    evaluation: int  # 0-100 score from user


class Evaluation(BaseModel):
    """Complete evaluation for a reasoning kit run."""

    mode: str  # "transparent" or "anonymous"
    steps: dict[str, StepEvaluation]  # step number -> evaluation


class GraphState(BaseModel):
    """State for the LangGraph execution."""

    kit: ReasoningKit
    outputs: dict[str, str] = {}
    current_step: int = 1
    completed: bool = False
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True
