# Run Command

The `run` command executes a [reasoning kit](../reasoning_kits.md).

## Usage

```bash
uv run clerk run [OPTIONS] KIT
```

## Arguments

- `KIT`: Name/slug of the reasoning kit to run.

## Options

- `--local`: Load from the local filesystem instead of the database.
- `--base-path PATH`: Base path for local reasoning kits. Defaults to `reasoning_kits`.
- `--evaluate`: Enable step-by-step evaluation prompts.
- `--mode MODE`: Evaluation mode: `transparent` stores full text, `anonymous` stores character counts. Defaults to `transparent` (or the kit's `kit.json` value).
- `--auto-evaluate`: Score each step automatically using `evaluator_N.txt` / `evaluator_N.json` files instead of prompting the user. Implicitly enables evaluation.
- `--judge-model MODEL`: Model to use for auto-evaluation scoring. Overrides `kit.json` → defaults to the same model as the main run.
- `--evaluator-aggregation STRATEGY`: How to combine scores for multi-dimension evaluators: `average` (default), `min`, `max`, or `first`. Overrides `kit.json`.
- `--model MODEL`: LLM model for the main workflow (e.g. `gpt-5.4-nano`). Overrides `kit.json` → overrides `CLERK_DEFAULT_MODEL`.
- `--dynamic-resource resource_N="text"`: Provide a dynamic resource inline.
- `--dynamic-resource-file resource_N=./file.txt`: Read a dynamic resource from a file.
- `--stdin resource_N`: Read a dynamic resource from standard input.
- `--verbose`, `-v`: Enable verbose output (tool calls, LLM responses, etc.).
- `--output-dir PATH`: Base directory for saved run outputs. Defaults to `outputs/`.
- `--no-save`: Do not save run outputs to disk.

## Settings precedence

For `--model`, `--judge-model`, `--mode`, and `--evaluator-aggregation`, settings are resolved in this order (highest wins):

```
CLI flag  →  kit.json  →  CLERK_DEFAULT_MODEL env var  →  hardcoded default
```

A kit can set its own defaults in `kit.json` — see [Reasoning Kits](../reasoning_kits.md#kit-configuration-optional).

## Examples

```bash
# Run a local kit
uv run clerk run demo --local

# Run with interactive evaluation after each step
uv run clerk run demo --evaluate

# Run with fully automated scoring (requires evaluator_N.txt files in the kit)
uv run clerk run demo --auto-evaluate

# Use a different model as judge
uv run clerk run demo --auto-evaluate --judge-model gpt-5.4-nano

# Auto-eval where evaluator files exist; interactive prompt for remaining steps
uv run clerk run demo --evaluate --auto-evaluate

# Provide a dynamic resource inline
uv run clerk run demo --local --dynamic-resource resource_1="my contract text"

# Pipe content into a dynamic resource
cat document.txt | uv run clerk run demo --local --stdin resource_1
```

To see all available kits, use the [list command](list.md). For details on adding evaluator files to a kit, see [Auto-Evaluation](../auto_eval.md).
