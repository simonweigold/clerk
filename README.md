# CLERK
Community Library of Executable Reasoning Kits

## Setup

1. Install dependencies with UV:
```bash
uv sync
```

2. Create a `.env` file with your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### CLI Commands

List available reasoning kits:
```bash
uv run clerk list
```

Show info about a reasoning kit:
```bash
uv run clerk info demo
```

Run a reasoning kit:
```bash
uv run clerk run demo
```

### Programmatic Usage

```python
from clerk.loader import load_reasoning_kit
from clerk.graph import run_reasoning_kit

kit = load_reasoning_kit("reasoning_kits/demo")
outputs = run_reasoning_kit(kit)
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

```
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
    }
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
            "evalaution": "",
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
CLERK can be connected to other LLMs via MCP. The LLM can create new Reasoning Kits, edit and execute them. In order to be able to do this, it needs to be instructed via prompts.

## General Tasks
- [x] Langchain logic, which executes all steps from the workflow
- [x] After final event, present all results back to user
- [x] For evaluation steps, interrupt logic and ask for user feedback
- [x] Database layer, which centralizes the storage for reasoning kits
- [x] Reasoning Kit definition layer (via terminal)
- [x] UI, which can be launched via `clerk web`
    - [x] wraps the Reasoning Kit definition layer in an intuitive way
    - [x] allows execution of Kits (including evaluation if desired)
- [ ] Spin up local db for storage (as alternative to Supabase) --> launch with `clerk web --local`
- [ ] MCP logic
    - [ ] Log in to Supabase if desired
    - [ ] If not: use local db instance
- [ ] New type: resources, workflows, tools!
- [ ] Batch execution mode
- [ ] Docker implementation

## Tasks (to be implemented another time)
- [ ] change reasoning_kits/demo/resource_1.txt to pdf and add pdf support for resources.
- [ ] collect some more practical use cases for showcasing




- I3 allow resources to be a website

- add option to reset password for supabase when signing in
- when user with mail address already exists in supabase tell the user

- allow resizing of text input fields when editing workflow steps

- when executing a kit, allow user to edit an output (important in case it is referenced in future steps)
- when executing a kit, add option to view entire prompt

- save workflow executions to db and allow user to access them again even after quitting
- add download results option
