# AGENTS.md - Reasoning Kits Coding Guidelines

Reasoning Kits is a lightweight Python package for self-improving LLM workflows.

## Tech Stack

- **Backend**: Python 3.13+, UV, LiteLLM, Pydantic, MCP
- **Docs**: Markdown (SPEC.md is canonical)

## Commands

### Python (UV)
```bash
# Install dependencies
uv sync

# Run CLI (after `uv sync`, `rk` is on PATH)
rk list                                       # List reasoning kits
rk info <name>                                # Show kit structure
rk validate <name>                            # Validate a kit
rk run <name>                                 # Run a kit
rk run <name> --evaluate --auto-evaluate      # Run with judge-LLM scoring
rk run <name> --dynamic-resource resource_1="text"   # Inline dynamic resource
rk run <name> --stdin resource_1                     # Pipe dynamic resource
rk batch <name> --input-dir <dir> --resource resource_1  # Run over many files

# Testing
uv run pytest                                 # Run all tests
uv run pytest tests/test_loader.py            # Single test file
uv run pytest tests/test_loader.py::test_function  # Single test
uv run pytest -k "pattern"                    # Pattern match
uv run pytest -x                              # Stop on first failure

# Linting
uv run ruff check .                           # Lint
uv run ruff check --fix .                     # Auto-fix
uv run ruff format .                          # Format
uv run mypy src/                              # Type check
```

## Python Code Style

### Imports (ordered, alphabetized within groups)

```python
"""Module docstring."""

# 1. Standard library
import re
from pathlib import Path
from typing import Any

# 2. Third-party
from pydantic import BaseModel

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
- Lazy imports for heavy deps (litellm, mcp) inside functions, to keep module import cheap

## File Organization

```
reasoning-kits/
├── src/reasoning_kits/
│   ├── __init__.py           # Package metadata
│   ├── __main__.py           # python -m reasoning_kits
│   ├── cli.py                # CLI entry point (rk)
│   ├── models.py             # Pydantic data models
│   ├── loader.py             # Filesystem loading
│   ├── runner.py             # Prompt-chaining executor
│   ├── evaluator.py          # Evaluation logic
│   ├── improver.py           # Self-improvement loop (Phase 4)
│   ├── experiments.py        # Branch/merge logic (Phase 3)
│   ├── tools.py              # Global tool registry
│   ├── mcp_client.py         # MCP integration
│   ├── llm.py                # LiteLLM wrapper
│   └── manifest.py           # kit.yaml parsing (optional)
├── kits/                     # Reference kits
│   ├── demo/
│   ├── oll_employment_contracts/
│   └── test_swiss_legal/
├── tests/
├── SPEC.md                   # Canonical format spec
├── pyproject.toml            # Single-package layout
└── README.md
```

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
# Add at minimum: OPENAI_API_KEY (or another provider key)
```

Supported providers via LiteLLM: OpenAI, Anthropic, Mistral, Gemini, OpenRouter. See SPEC.md.