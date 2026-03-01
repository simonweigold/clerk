# Reasoning Kits

A reasoning kit is the core unit of CLERK. It represents a structured set of resources and sequential instructions that define a workflow.

## Structure

A typical kit is a directory with auto-discovered files:

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

Resources provide the context or data for the kit.
- Files matching `resource_*.txt` or `resource_*.csv` are loaded automatically.
- The resource ID is derived from the filename (e.g., `resource_1.txt` becomes `{resource_1}`).

### Workflow Steps

Workflow steps define the sequence of prompts to execute.
- Files matching `instruction_*.txt` define workflow steps.
- Steps are executed in numerical order (1, 2, 3, ...).
- Each step's output is stored as `{workflow_N}` for use in later steps.

### Placeholders

In instruction files, use placeholders to reference data:
- Resources: `{resource_1}`, `{resource_2}`, etc.
- Previous outputs: `{workflow_1}`, `{workflow_2}`, etc.

**Example `instruction_2.txt`**:
```
Here is some context: {resource_1}
Based on the previous analysis: {workflow_1}
Please provide a summary.
```

## Creating Kits

You can create and manage kits via the [CLI Commands](cli/kit.md) or via the [Web UI](ui/editing_kits.md).

## Executing Kits

You can run kits using the [CLI `run` command](cli/run.md) or via the [Web UI](ui/running_kits.md).
