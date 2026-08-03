# Reasoning Kits

A reasoning kit is the core unit of CLERK. It represents a structured set of resources and sequential instructions that define a workflow.

## Structure

A typical kit is a directory with auto-discovered files:

```
reasoning_kits/
└── my_kit/
    ├── kit.json            # Optional: per-kit default settings
    ├── resource_1.txt      # Referenced as {resource_1} in prompts
    ├── resource_2.csv      # Referenced as {resource_2} in prompts
    ├── instruction_1.txt   # First workflow step, output: {workflow_1}
    ├── evaluator_1.txt     # Optional: judge LLM prompt for step 1 (auto-eval)
    ├── instruction_2.txt   # Second workflow step, output: {workflow_2}
    ├── evaluator_2.txt     # Optional: judge LLM prompt for step 2 (auto-eval)
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

### Kit configuration (optional)

`kit.json` sets per-kit default values for run-time settings. All fields are optional. CLI flags always take precedence over `kit.json`.

```json
{
  "judge_model": "deepseek/deepseek-v4-pro",
  "model": "gpt-5.4-nano",
  "evaluator_aggregation": "average",
  "mode": "transparent"
}
```

| Field                  | Type     | Description                                                      |
| ---------------------- | -------- | ---------------------------------------------------------------- |
| `judge_model`          | `string` | Default judge LLM for `--auto-evaluate`. Overrides the global default. |
| `model`                | `string` | Default LLM for the main workflow. Overrides `CLERK_DEFAULT_MODEL`. |
| `evaluator_aggregation`| `string` | Default score aggregation: `average`, `min`, `max`, or `first`. |
| `mode`                 | `string` | Default evaluation mode: `transparent` or `anonymous`.          |

Precedence (highest to lowest): **CLI flag → `kit.json` → environment variable → hardcoded default**.

### Evaluators (optional)

Files matching `evaluator_N.txt` or `evaluator_N.json` define judge LLM prompts for automated scoring.
- N must match the step number of the corresponding `instruction_N.txt`.
- When the kit runs with `--auto-evaluate`, each step's prompt and output are injected into the evaluator template and sent to a judge LLM, which returns a score (0–100).
- Steps without a matching evaluator file fall back to the interactive prompt.

See [Auto-Evaluation](auto_eval.md) for details and examples.

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
