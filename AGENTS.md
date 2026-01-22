# AGENTS.md - Guidelines for AI Coding Agents

This document provides guidelines for AI coding agents working in the CLERK (Community Library of Executable Reasoning Kits) codebase.

## Project Overview

CLERK is a Python framework for defining and executing multi-step LLM reasoning workflows using file-based configuration. It uses LangChain/LangGraph for workflow orchestration and Pydantic for data validation.

**Tech Stack:**
- Python 3.13+
- Package Manager: UV
- LLM Framework: LangChain + LangGraph
- Data Validation: Pydantic
- LLM Provider: OpenAI (gpt-5-mini)

## Project Structure

```
clerk/
├── src/clerk/              # Main package
│   ├── __init__.py         # Package init, version
│   ├── cli.py              # CLI commands (list, run, info)
│   ├── evaluation.py       # Evaluation prompting and persistence
│   ├── graph.py            # LangGraph workflow execution
│   ├── loader.py           # Reasoning kit file loader
│   └── models.py           # Pydantic data models
├── reasoning_kits/         # Reasoning kit storage
│   └── demo/               # Example reasoning kit
│       └── evaluations/    # Evaluation results (JSON files)
├── main.py                 # Direct execution entry point
├── pyproject.toml          # Project configuration
└── uv.lock                 # Dependency lock file
```

## Build/Lint/Test Commands

### Installation
```bash
uv sync                     # Install all dependencies
```

### Running the Application
```bash
uv run clerk list           # List available reasoning kits
uv run clerk info <name>    # Show info about a reasoning kit
uv run clerk run <name>     # Run a reasoning kit
uv run clerk run <name> --evaluate  # Run with step-by-step evaluation
uv run clerk run <name> --evaluate --mode=anonymous  # Evaluation with char counts only
uv run python main.py       # Alternative direct execution
```

### Testing
```bash
# No test suite currently configured
# When tests are added, expected commands:
uv run pytest               # Run all tests
uv run pytest tests/test_loader.py  # Run single test file
uv run pytest tests/test_loader.py::test_function_name  # Run single test
uv run pytest -k "pattern"  # Run tests matching pattern
uv run pytest -x            # Stop on first failure
```

### Linting/Formatting
```bash
# No linting currently configured
# When configured, expected commands:
uv run ruff check .         # Run linter
uv run ruff check --fix .   # Auto-fix linting issues
uv run ruff format .        # Format code
```

### Environment Setup
```bash
cp .env.example .env        # Create env file
# Add OPENAI_API_KEY to .env
```

## Code Style Guidelines

### Python Version
- Python 3.13+ required
- Use modern syntax: `str | None` not `Optional[str]`
- Use built-in generics: `dict[str, str]` not `Dict[str, str]`

### Import Organization

Imports must follow this order with blank lines between groups:

```python
"""Module docstring - always first line."""

# 1. Standard library imports (alphabetized)
import re
import sys
from pathlib import Path
from typing import Annotated, TypedDict

# 2. Third-party imports (alphabetized)
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

# 3. Local/relative imports
from .loader import load_reasoning_kit
from .models import ReasoningKit, Resource
```

**Rules:**
- Use relative imports (`.module`) within the package
- Use `from X import Y` style, not `import X`
- Alphabetize imports within each group

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `loader.py`, `graph.py` |
| Functions | snake_case, verb-first | `load_reasoning_kit()`, `create_state()` |
| Variables | snake_case | `kit_path`, `resource_id` |
| Classes | PascalCase | `ReasoningKit`, `GraphState` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_MODEL` |
| Private | underscore prefix | `_extract_number()` |

### Type Annotations

All functions must have complete type annotations:

```python
def load_reasoning_kit(kit_path: str | Path) -> ReasoningKit:
    """Load a reasoning kit from disk."""
    ...

def resolve_placeholders(
    text: str,
    resources: dict[str, str],
    outputs: dict[str, str]
) -> str:
    """Resolve placeholder references in text."""
    ...
```

### Data Models

Use Pydantic BaseModel for all data classes:

```python
class Resource(BaseModel):
    """A resource in a reasoning kit."""
    file: str
    resource_id: str
    content: str = ""

class GraphState(BaseModel):
    outputs: dict[str, str] = {}
    current_step: int = 1
    error: str | None = None
```

Use TypedDict for LangGraph state:

```python
class State(TypedDict):
    """TypedDict state for LangGraph."""
    kit_name: str
    resources: dict[str, str]
    outputs: Annotated[dict[str, str], lambda x, y: {**x, **y}]
```

### Documentation

**Module docstrings** - required at the top of every file:
```python
"""Loader for reasoning kits."""
```

**Function docstrings** - Google-style with Args/Returns:
```python
def resolve_placeholders(text: str, resources: dict[str, str], outputs: dict[str, str]) -> str:
    """Resolve {placeholder} references in text.

    Args:
        text: Text with placeholders like {resource_1} or {workflow_1}
        resources: Dict of resource_id -> content
        outputs: Dict of output_id -> result

    Returns:
        Text with all placeholders resolved
    """
```

**Class docstrings** - brief single-line for data classes:
```python
class Resource(BaseModel):
    """A resource in a reasoning kit."""
```

### Error Handling

Use guard clauses with early returns and descriptive error messages:

```python
def load_reasoning_kit(kit_path: str | Path) -> ReasoningKit:
    kit_path = Path(kit_path)
    
    if not kit_path.exists():
        raise FileNotFoundError(f"Reasoning kit not found: {kit_path}")
    
    # ... rest of function
```

Use built-in exception types. Catch specific exceptions:

```python
try:
    kit = load_reasoning_kit(kit_path)
    outputs = run_reasoning_kit(kit)
except FileNotFoundError as e:
    print(f"Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error running reasoning kit: {e}")
    sys.exit(1)
```

### File Organization

- **`models.py`**: Pure data structures (Pydantic models only)
- **`loader.py`**: File I/O and data loading functions
- **`cli.py`**: User interface, argument parsing, command dispatch
- **`graph.py`**: Business logic, workflow orchestration
- **`evaluation.py`**: User evaluation prompting and JSON persistence

### Common Patterns

**String formatting** - always use f-strings:
```python
print(f"Running Reasoning Kit: {kit.name}")
raise FileNotFoundError(f"Reasoning kit not found: {kit_path}")
```

**Path handling** - use pathlib.Path, not string manipulation:
```python
from pathlib import Path
kit_path = Path(kit_path)
resource_files = sorted(kit_path.glob("resource_*.*"))
```

**Immutable state updates** - use spread operator:
```python
new_outputs = {**state["outputs"], output_id: result}
return {**state, "outputs": new_outputs}
```

**Entry points** - use main() function pattern:
```python
def main():
    """Main entry point for the CLI."""
    load_dotenv()
    # ... logic

if __name__ == "__main__":
    main()
```

## Reasoning Kit File Conventions

When working with reasoning kits:
- Resources: `resource_*.txt` or `resource_*.csv`
- Instructions: `instruction_*.txt` (numbered sequentially: 1, 2, 3...)
- Placeholders in instructions: `{resource_N}` and `{workflow_N}`
- Evaluation outputs: stored in `evaluations/` subdirectory as JSON

## Evaluation System

The evaluation system allows users to rate each workflow step during execution.

### CLI Flags

| Flag | Description |
|------|-------------|
| `--evaluate` | Enable step-by-step evaluation prompts |
| `--mode` | `transparent` (default) or `anonymous` |

### Evaluation Modes

**Transparent mode** - stores full prompt/output text:
```json
{
    "mode": "transparent",
    "steps": {
        "1": {
            "input": "<full prompt text>",
            "output": "<full LLM response>",
            "evaluation": 85
        }
    }
}
```

**Anonymous mode** - stores character counts only:
```json
{
    "mode": "anonymous",
    "steps": {
        "1": {
            "input": 1234,
            "output": 567,
            "evaluation": 85
        }
    }
}
```

### Evaluation Storage

- Evaluations are saved to `reasoning_kits/<kit>/evaluations/<N>.json`
- Files use incrementing numbers (1.json, 2.json, 3.json...)
- The `evaluations/` directory is created automatically if it doesn't exist

### Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `prompt_for_evaluation()` | `evaluation.py` | Prompt user for 0-100 score with validation |
| `save_evaluation()` | `evaluation.py` | Save evaluation to JSON file |
| `create_step_evaluation()` | `evaluation.py` | Create step data based on mode |
| `evaluate_step()` | `graph.py` | LangGraph node that handles evaluation |

### Data Models

```python
class StepEvaluation(BaseModel):
    """Evaluation data for a single workflow step."""
    input: str | int   # Full text or char count
    output: str | int  # Full text or char count
    evaluation: int    # 0-100 score

class Evaluation(BaseModel):
    """Complete evaluation for a reasoning kit run."""
    mode: str                          # "transparent" or "anonymous"
    steps: dict[str, StepEvaluation]   # step number -> evaluation
```
