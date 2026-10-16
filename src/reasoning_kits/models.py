"""Data models for reasoning kits."""

from pydantic import BaseModel


class Resource(BaseModel):
    """A resource in a reasoning kit.

    Resources are files (text, PDF, etc.) that can be referenced in workflow
    steps using {resource_N} placeholders.
    """

    file: str
    resource_id: str
    content: str = ""
    is_dynamic: bool = False
    display_name: str | None = None


class WorkflowStep(BaseModel):
    """A step in the workflow.

    Workflow steps execute sequentially. Each step's prompt can reference
    resources ({resource_N}) and earlier outputs ({workflow_N}).
    """

    file: str
    output_id: str
    prompt: str = ""
    display_name: str | None = None


class Tool(BaseModel):
    """A tool reference in a reasoning kit.

    References a tool from the global registry by name. When referenced via
    {tool_N} in a step, the tool is exposed to the LLM.
    """

    tool_name: str
    tool_id: str
    display_name: str | None = None
    configuration: str | None = None


class KitConfig(BaseModel):
    """Per-kit default settings loaded from kit.json."""

    model: str | None = None
    judge_model: str | None = None
    evaluator_aggregation: str | None = None
    mode: str | None = None


class ReasoningKit(BaseModel):
    """A complete reasoning kit with resources and workflow."""

    name: str
    path: str
    resources: dict[str, Resource]
    workflow: dict[str, WorkflowStep]
    tools: dict[str, Tool] = {}
    evaluators: dict[str, list[tuple[str, str]]] = {}
    evaluator_aggregations: dict[str, str] = {}
    config: KitConfig = KitConfig()


class DimensionScore(BaseModel):
    """Score for one evaluation dimension of a workflow step."""

    label: str
    score: int


class StepEvaluation(BaseModel):
    """Evaluation data for a single workflow step."""

    input: str | int
    output: str | int
    dimension_scores: list[DimensionScore] = []
    evaluation: int


class Evaluation(BaseModel):
    """Complete evaluation for a reasoning kit run."""

    mode: str
    steps: dict[str, StepEvaluation]