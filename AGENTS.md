# AGENTS.md - CLERK Coding Guidelines

CLERK is a Python framework for multi-step LLM reasoning workflows with a React frontend.

## Tech Stack

- **Backend**: Python 3.13+, UV, LangChain/LangGraph, Pydantic, SQLAlchemy async, Supabase
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, React Router

## Commands

### Python (UV)
```bash
# Install dependencies
uv sync

# Run CLI
uv run clerk list                    # List reasoning kits
uv run clerk run <name>              # Run a kit
uv run clerk run <name> --evaluate   # Run with evaluation
uv run clerk run <name> --dynamic-resource resource_1="text"  # Inline dynamic resource
uv run clerk run <name> --stdin resource_1                     # Pipe dynamic resource
uv run clerk validate <name>         # Validate kit structure

# Testing
uv run pytest                        # Run all tests
uv run pytest test_tools_api.py      # Single test file
uv run pytest test_tools_api.py::test_function  # Single test
uv run pytest -k "pattern"           # Pattern match
uv run pytest -x                     # Stop on first failure

# Database
uv run clerk db setup                # Full DB setup
uv run clerk db migrate              # Run migrations
uv run clerk db status               # Migration status

# Linting (configure ruff in pyproject.toml when ready)
uv run ruff check .                  # Lint
uv run ruff check --fix .            # Auto-fix
uv run ruff format .                 # Format
```

### Frontend
```bash
cd frontend

# Development
npm install                          # Install deps
npm run dev                          # Start dev server (Vite)

# Build & Lint
npm run build                        # Production build
npm run lint                         # ESLint check
npm run preview                      # Preview build
```

## Python Code Style

### Imports (ordered, alphabetized within groups)
```python
"""Module docstring."""

# 1. Standard library
import re
from pathlib import Path
from typing import Annotated, TypedDict

# 2. Third-party
from pydantic import BaseModel
from langgraph.graph import StateGraph

# 3. Local (relative)
from .loader import load_reasoning_kit
from .models import ReasoningKit
```

### Naming
- Files/functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

### Type Annotations
- Use modern syntax: `str | None` not `Optional[str]`
- Use built-in generics: `dict[str, str]` not `Dict[str, str]`
- All functions must have complete type annotations

### Pydantic Models
```python
class Resource(BaseModel):
    """A resource in a reasoning kit."""
    file: str
    resource_id: str
    content: str = ""
    is_dynamic: bool = False
```

### Documentation
- Module docstring at top of every file
- Function docstrings: Google-style with Args/Returns
- Class docstrings: brief single-line

### Error Handling
```python
def load_reasoning_kit(kit_path: str | Path) -> ReasoningKit:
    kit_path = Path(kit_path)
    if not kit_path.exists():
        raise FileNotFoundError(f"Reasoning kit not found: {kit_path}")
    # ... rest of function
```

### Patterns
- Use f-strings for formatting
- Use `pathlib.Path` not string manipulation
- Immutable updates: `{**state, "key": value}`
- Guard clauses with early returns

## Frontend Code Style

### Project Structure
```
frontend/src/
├── pages/           # Route components
├── components/      # Reusable UI
├── hooks/           # Custom React hooks
├── lib/             # Utilities
└── App.tsx          # Router setup
```

### Styling (Tailwind + STYLE_GUIDE.md)
- Colors: Primary `#130DDD`, Background `#ffffff`, Muted `#f4f6f9`
- Border radius: `rounded-md` (10px), `rounded-lg` (12px)
- Typography: Inter (body), Bodoni Moda SC (logo)
- Follow glassmorphism pattern: `bg-white/80 backdrop-blur-md`

### React Patterns
- Functional components with hooks
- Use React Router for navigation
- Custom hooks in `hooks/` directory (useAuth, useToast)

## File Organization

- **`models.py`**: Pydantic data models
- **`loader.py`**: File I/O and data loading
- **`cli.py`**: CLI commands and argument parsing
- **`graph.py`**: LangGraph workflow execution
- **`evaluation.py`**: Evaluation prompting and persistence
- **`web/`**: FastAPI web interface
- **`db/`**: Database models, migrations, repository pattern

## Reasoning Kit Conventions

- Resources: `resource_*.txt` or `resource_*.csv`
- Dynamic resources: `dynamic_resource_*.txt` (provided at runtime)
- Instructions: `instruction_*.txt` (numbered: 1, 2, 3...)
- Tools: `tool_*.json` referencing the global registry (e.g., `{"tool_name": "read_url"}`)
- MCP servers: `mcp_servers.json` (kit-local override, merges with project-root config)
- Placeholders: `{resource_N}`, `{workflow_N}`, and `{tool_N}`
- Evaluations: stored in `evaluations/*.json`

### MCP Server Config (`mcp_servers.json`)

Supported transports: `stdio` (default), `sse`, `http`.

```json
{
  "mcpServers": {
    "opencaselaw": {
      "transport": "sse",
      "url": "https://mcp.opencaselaw.ch"
    }
  }
}
```

## Environment Setup

```bash
cp .env.example .env
# Add OPENAI_API_KEY and Supabase credentials to .env
```
