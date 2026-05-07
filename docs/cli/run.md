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
- `--mode MODE`: Evaluation mode: `transparent` stores full text, `anonymous` stores character counts. Defaults to `transparent`.
- `--auto-evaluate`: Score each step automatically using `evaluator_N.txt` files instead of prompting the user. Implicitly enables evaluation.
- `--judge-model MODEL`: Model to use for auto-evaluation scoring. Defaults to the same model as the main run.
- `--model MODEL`: LLM model for the main workflow (e.g. `gpt-5.4-nano`). Overrides the `CLERK_DEFAULT_MODEL` environment variable.
- `--dynamic-resource resource_N="text"`: Provide a dynamic resource inline.
- `--dynamic-resource-file resource_N=./file.txt`: Read a dynamic resource from a file.
- `--stdin resource_N`: Read a dynamic resource from standard input.
- `--verbose`, `-v`: Enable verbose output (tool calls, LLM responses, etc.).
- `--output-dir PATH`: Base directory for saved run outputs. Defaults to `outputs/`.
- `--no-save`: Do not save run outputs to disk.

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
