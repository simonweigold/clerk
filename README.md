# OpenClerk

Community Library of Executable Reasoning Kits

[![PyPI](https://img.shields.io/pypi/v/openclerk.svg)](https://pypi.org/project/openclerk/)
[![Docs](https://img.shields.io/badge/docs-openclerk.dev-blue.svg)](https://openclerk.dev/docs)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

Clerk is a Python framework for multi-step LLM reasoning workflows with a React frontend. It provides a declarative way to define and execute modular, reusable reasoning workflows using Large Language Models (LLMs).

## Installation

```bash
# Install from PyPI (when published)
pip install openclerk

# Or install from source
git clone https://github.com/simonweigold/clerk.git
cd clerk
uv sync
cd packages/clerk
uv pip install -e .
```

## Usage

### CLI Commands

List available reasoning kits:
```bash
clerk list
```

Show info about a reasoning kit:
```bash
clerk info demo
```

Run a reasoning kit:
```bash
clerk run demo
```

Run web app:
```bash
clerk web
```

Or using UV directly:
```bash
uv run python -m openclerk list
uv run python -m openclerk run demo
uv run python -m openclerk web
```

### Programmatic Usage

```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit

kit = load_reasoning_kit("reasoning_kits/demo")
outputs = run_reasoning_kit(kit)
```

## Repository Structure

This is a monorepo containing:

- `packages/clerk/` - Python package (`pip install openclerk`)
- `apps/website/` - Next.js website (openclerk.ch)
- `docs/` - Documentation
- `reasoning_kits/` - Example reasoning kits

## Development

### Python Package
```bash
cd packages/clerk
uv pip install -e ".[dev]"
pytest
```

### Website
```bash
cd apps/website
npm install
npm run dev
```

## Creating New Reasoning Kits

1. Create a new directory under `reasoning_kits/`
2. Add resource files named `resource_1.txt`, `resource_2.csv`, etc.
3. Add instruction files named `instruction_1.txt`, `instruction_2.txt`, etc.

## Reasoning Kit Structure

A reasoning kit is a directory with auto-discovered files:

```
reasoning_kits/
└── my_kit/
    ├── resource_1.txt      # Referenced as {resource_1} in prompts
    ├── resource_2.csv      # Referenced as {resource_2} in prompts
    ├── instruction_1.txt   # First workflow step, output: {workflow_1}
    ├── instruction_2.txt   # Second workflow step, output: {workflow_2}
    └── instruction_3.txt   # Third workflow step, output: {workflow_3}
```

### Resources
- Files matching `resource_*.txt` or `resource_*.csv` are loaded as resources
- The resource ID is derived from the filename (e.g., `resource_1.txt` → `{resource_1}`)

### Workflow Steps
- Files matching `instruction_*.txt` define workflow steps
- Steps are executed in numerical order (1, 2, 3, ...)
- Each step's output is stored as `{workflow_N}` for use in later steps

### Placeholders
In instruction files, use placeholders to reference:
- Resources: `{resource_1}`, `{resource_2}`, etc.
- Previous outputs: `{workflow_1}`, `{workflow_2}`, etc.

Example `instruction_2.txt`:
```
Here is some context: {resource_1}
Based on the previous analysis: {workflow_1}
Please provide a summary.
```

The abstract overview of a reasoning kit:

```json
{
    "resources": {
        "1": {
            "content": "Full text",
            "link": "",
            "resource_id": "resource_1"
        },
        "2": {
            "content": "",
            "link": "https://blob-storage.cloud-provider.com/file.pdf",
            "resource_id": "resource_2"
        }
    },
    "workflow": {
        "1": {
            "type": "instruction",
            "prompt": "Look at this document:\n{resource_1}\nand classify it",
            "evaluation": "",
            "output_id": "workflow_1"
        },
        "2": {
            "type": "instruction",
            "prompt": "Look up a definition for this classification:\n{workflow_1}\nfrom this resource:\n{resource_2}",
            "evaluation": "",
            "output_id": "workflow_2"
        },
        "3": {
            "type": "instruction",
            "prompt": "Generate the final answer with this context information:\n{resource_1}\n{workflow_1}\n{workflow_2}",
            "evaluation": "",
            "output_id": "workflow_3"
        }
    }
}
```

## Workflow
The workflow runs chronologically. Steps are executed in order (1, 2, 3, ...) with each step's output available to subsequent steps via placeholders.

## MCP
Clerk can be connected to other LLMs via MCP. The LLM can create new Reasoning Kits, edit and execute them. In order to be able to do this, it needs to be instructed via prompts.

## Roadmap

### Completed
- [x] LangChain logic for executing workflow steps
- [x] Present all results back to user after final event
- [x] Evaluation steps with user feedback interruption
- [x] Database layer for kit storage
- [x] Reasoning Kit definition layer (via terminal)
- [x] Web UI (`clerk web`)
- [x] Monorepo structure with package/website separation

### In Progress
- [ ] Spin up local db for storage (as alternative to Supabase) → launch with `clerk web --local`
- [ ] MCP logic with Supabase login
- [ ] New type: resources, workflows, tools!
- [ ] Batch execution mode
- [ ] Docker implementation

### Future Ideas
- [ ] PDF support for resources
- [ ] More practical use cases for showcasing
- [ ] Allow resources to be websites
- [ ] Password reset and user management improvements
- [ ] Resizable text input fields when editing workflow steps
- [ ] Allow editing outputs during execution
- [ ] View entire prompt option during execution
- [ ] Save workflow executions to db for later access
- [ ] Download results option

## Links

- [Documentation](https://openclerk.ch/docs)
- [Website](https://openclerk.ch)
- [PyPI](https://pypi.org/project/openclerk/)
- [Issues](https://github.com/simonweigold/clerk/issues)

## License

MIT License
