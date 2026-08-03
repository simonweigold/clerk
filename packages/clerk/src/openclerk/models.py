"""Data models for reasoning kits."""

from pydantic import BaseModel, ConfigDict


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


class Tool(BaseModel):
    """A tool in a reasoning kit."""

    tool_name: str  # Global registry name
    tool_id: str  # e.g. "tool_1"
    display_name: str | None = None  # Optional custom display name
    configuration: str | None = None  # Optional JSON config overrides


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
    tools: dict[str, Tool] = {}  # tool_number -> Tool
    # step number (str) -> [(label, prompt), ...]; label "default" for plain .txt evaluators
    evaluators: dict[str, list[tuple[str, str]]] = {}
    # step number (str) -> aggregation strategy; set when evaluator_N.json defines "aggregation"
    evaluator_aggregations: dict[str, str] = {}
    config: KitConfig = KitConfig()


class DimensionScore(BaseModel):
    """Score for one evaluation dimension of a workflow step."""

    label: str  # e.g. "structure", "coverage", "default"
    score: int  # 0-100


class StepEvaluation(BaseModel):
    """Evaluation data for a single workflow step."""

    input: str | int  # Full text (transparent) or char count (anonymous)
    output: str | int  # Full text (transparent) or char count (anonymous)
    dimension_scores: list[DimensionScore] = []  # one entry per evaluator; [] for legacy data
    evaluation: int  # aggregated 0-100 score (average by default)


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

    model_config = ConfigDict(arbitrary_types_allowed=True)
