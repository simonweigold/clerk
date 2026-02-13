# AGENTS.md - Guidelines for AI Coding Agents

This document provides guidelines for AI coding agents working in the CLERK (Community Library of Executable Reasoning Kits) codebase.

## Project Overview

CLERK is a Python framework for defining and executing multi-step LLM reasoning workflows using file-based configuration. It uses LangChain/LangGraph for workflow orchestration and Pydantic for data validation.

**Tech Stack:**
- Python 3.13+
- Package Manager: UV
- LLM Framework: LangChain + LangGraph
- Data Validation: Pydantic
- Database: Supabase (PostgreSQL) with SQLAlchemy async
- File Storage: Supabase Storage
- LLM Provider: OpenAI (gpt-5-mini)

## Project Structure

```
clerk/
├── src/clerk/                    # Main package
│   ├── __init__.py               # Package init, version
│   ├── cli.py                    # CLI commands (list, run, info, db, sync)
│   ├── evaluation.py             # Evaluation prompting and persistence
│   ├── graph.py                  # LangGraph workflow execution
│   ├── loader.py                 # Reasoning kit loader (local + database)
│   ├── models.py                 # Pydantic data models
│   │
│   └── db/                       # Database layer
│       ├── __init__.py           # DB module exports
│       ├── config.py             # Supabase connection configuration
│       ├── models.py             # SQLAlchemy ORM models
│       ├── repository.py         # Data access layer (CRUD operations)
│       ├── storage.py            # Supabase Storage integration
│       ├── text_extraction.py    # PDF/XLSX text extraction
│       └── migrations/           # Alembic migrations
│           ├── alembic.ini
│           ├── env.py
│           ├── script.py.mako
│           └── versions/
│               └── 001_initial_schema.py
│
├── reasoning_kits/               # Local reasoning kit storage
│   └── demo/                     # Example reasoning kit
│       └── evaluations/          # Evaluation results (JSON files)
├── main.py                       # Direct execution entry point
├── pyproject.toml                # Project configuration
└── uv.lock                       # Dependency lock file
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

## Database System

CLERK uses Supabase (PostgreSQL) for centralized storage of reasoning kits, with async SQLAlchemy for database operations.

### Database Setup

```bash
# Configure environment variables (see .env.example)
cp .env.example .env
# Edit .env with your Supabase credentials

# Run full database setup (migrations + storage bucket)
uv run clerk db setup

# Or run individual commands:
uv run clerk db migrate          # Apply database migrations
uv run clerk db status           # Check migration status
```

### Environment Variables

```bash
# Required for database functionality
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...                    # Public anon key
SUPABASE_SERVICE_ROLE_KEY=eyJ...            # Service role key (for admin ops)

# Database connections
DATABASE_URL=postgresql+asyncpg://user:pass@db.xxx.supabase.co:6543/postgres
DATABASE_URL_DIRECT=postgresql+asyncpg://user:pass@db.xxx.supabase.co:5432/postgres

# OpenAI (required)
OPENAI_API_KEY=sk-...
```

### CLI Commands

#### Database Commands
```bash
uv run clerk db setup              # Full setup: migrations + storage bucket
uv run clerk db migrate            # Apply pending migrations
uv run clerk db migrate --revision head   # Migrate to specific revision
uv run clerk db status             # Show current migration status
```

#### Sync Commands
```bash
uv run clerk sync list             # Compare local vs database kits
uv run clerk sync push <kit>       # Push local kit to database
uv run clerk sync push <kit> -m "Initial version"  # With commit message
uv run clerk sync pull <kit>       # Pull kit from database to local
```

#### Default Behavior
- `clerk list` - Lists from database (falls back to local if DB not configured)
- `clerk run <kit>` - Loads from database first, then tries local
- `clerk info <kit>` - Shows database info first, then tries local
- Use `--local` flag to force local filesystem operations

### Database Schema

#### Tables

| Table | Description |
|-------|-------------|
| `user_profiles` | User profiles linked to Supabase Auth |
| `reasoning_kits` | Main reasoning kit entities |
| `kit_versions` | Versioned snapshots of kits |
| `resources` | Resource files with extracted text |
| `workflow_steps` | Instruction prompts |
| `execution_runs` | Execution tracking |
| `step_executions` | Per-step results and evaluations |

#### Entity Relationships

```
user_profiles
    └── reasoning_kits (owner_id)
            └── kit_versions (kit_id)
                    ├── resources (version_id)
                    ├── workflow_steps (version_id)
                    └── execution_runs (version_id)
                            └── step_executions (run_id)
```

#### SQLAlchemy ORM Models

```python
# src/clerk/db/models.py

class ReasoningKit(Base):
    """A reasoning kit (main entity)."""
    id: UUID
    slug: str              # URL-friendly unique identifier
    name: str              # Display name
    description: str | None
    owner_id: UUID | None  # Links to UserProfile
    is_public: bool        # Default True
    current_version_id: UUID | None
    created_at: datetime
    updated_at: datetime

class KitVersion(Base):
    """A version of a reasoning kit."""
    id: UUID
    kit_id: UUID
    version_number: int
    commit_message: str | None
    created_by: UUID | None
    created_at: datetime
    is_draft: bool

class Resource(Base):
    """A resource file in a kit version."""
    id: UUID
    version_id: UUID
    resource_number: int
    filename: str
    mime_type: str | None
    storage_path: str      # Path in Supabase Storage
    extracted_text: str | None  # For full-text search
    file_size_bytes: int | None

class WorkflowStep(Base):
    """An instruction step in a kit version."""
    id: UUID
    version_id: UUID
    step_number: int
    prompt_template: str

class ExecutionRun(Base):
    """A single execution run of a reasoning kit."""
    id: UUID
    version_id: UUID
    user_id: UUID | None
    storage_mode: str      # "transparent" or "anonymous"
    status: str            # "running", "completed", "failed"
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None

class StepExecution(Base):
    """Execution result for a single workflow step."""
    id: UUID
    run_id: UUID
    step_number: int
    input_text: str | None        # Transparent mode
    input_char_count: int | None  # Anonymous mode
    output_text: str | None       # Transparent mode
    output_char_count: int | None # Anonymous mode
    evaluation_score: int | None  # 0-100
    model_used: str | None
    tokens_used: int | None
    latency_ms: int | None
```

### Repository Pattern

Database operations use the repository pattern for clean separation:

```python
from clerk.db import (
    ReasoningKitRepository,
    KitVersionRepository,
    ExecutionRepository,
    get_async_session,
)

async with get_async_session() as session:
    kit_repo = ReasoningKitRepository(session)
    
    # List public kits
    kits = await kit_repo.list_public()
    
    # Get kit by slug (with version, resources, steps loaded)
    kit = await kit_repo.get_by_slug("my-kit")
    
    # Create new kit
    kit = await kit_repo.create(
        slug="new-kit",
        name="New Kit",
        description="A new reasoning kit",
    )
    
    # Search kits
    results = await kit_repo.search("keyword")
```

### Storage Service

File storage uses Supabase Storage:

```python
from clerk.db import StorageService

storage = StorageService()

# Upload a resource file
storage_path = storage.upload_resource(
    kit_id=kit_id,
    version_id=version_id,
    filename="resource_1.txt",
    file_path=Path("local/path/resource_1.txt"),
)

# Download a resource
content = storage.download_resource(storage_path)  # bytes
text = storage.download_resource_text(storage_path)  # str
```

### Text Extraction

Resources are processed for full-text search:

```python
from clerk.db import extract_text, detect_mime_type

mime_type = detect_mime_type(Path("document.pdf"))
extracted_text = extract_text(Path("document.pdf"), mime_type)
```

Supported formats:
- **Text**: `.txt`, `.md`, `.csv` (read directly)
- **PDF**: `.pdf` (extracted with pypdf)
- **Excel**: `.xlsx`, `.xls` (extracted with openpyxl)

### Execution Tracking

When running kits from the database, executions are automatically tracked:

```python
from clerk.graph import run_reasoning_kit
from clerk.loader import load_reasoning_kit_from_db

# Load and run (automatically tracks in DB)
loaded = await load_reasoning_kit_from_db("my-kit")
outputs = run_reasoning_kit(
    loaded.kit,
    evaluate=True,
    evaluation_mode="transparent",
    save_to_db=True,
    db_version_id=loaded.version_id,
)
```

### Key Database Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `get_async_session()` | `db/config.py` | Get async database session context manager |
| `get_config()` | `db/config.py` | Get Supabase configuration |
| `ReasoningKitRepository` | `db/repository.py` | CRUD for reasoning kits |
| `KitVersionRepository` | `db/repository.py` | CRUD for kit versions |
| `ExecutionRepository` | `db/repository.py` | CRUD for execution runs |
| `StorageService` | `db/storage.py` | Supabase Storage operations |
| `extract_text()` | `db/text_extraction.py` | Extract text from files |
| `create_execution_run()` | `evaluation.py` | Create DB execution run |
| `save_step_to_db()` | `evaluation.py` | Save step execution to DB |
| `complete_execution_run()` | `evaluation.py` | Mark run as completed/failed |

### Migrations

Migrations are managed with Alembic:

```bash
# Create a new migration
cd src/clerk/db/migrations
alembic revision --autogenerate -m "description"

# Apply migrations
uv run clerk db migrate

# Check current status
uv run clerk db status
```

Migration files are in `src/clerk/db/migrations/versions/`.
