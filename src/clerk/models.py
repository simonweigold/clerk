"""Data models for reasoning kits."""

from typing import Any
from pydantic import BaseModel


class Resource(BaseModel):
    """A resource in a reasoning kit."""

    file: str
    resource_id: str
    content: str = ""  # Loaded at runtime


class WorkflowStep(BaseModel):
    """A step in the workflow."""

    file: str
    output_id: str
    prompt: str = ""  # Loaded at runtime


class ReasoningKit(BaseModel):
    """A complete reasoning kit with resources and workflow."""

    name: str
    path: str
    resources: dict[str, Resource]
    workflow: dict[str, WorkflowStep]


class GraphState(BaseModel):
    """State for the LangGraph execution."""

    kit: ReasoningKit
    outputs: dict[str, str] = {}
    current_step: int = 1
    completed: bool = False
    error: str | None = None

    class Config:
        arbitrary_types_allowed = True

