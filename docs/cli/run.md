# Run Command

The `run` command executes a [reasoning kit](../reasoning_kits.md).

## Usage

```bash
uv run clerk run [OPTIONS] KIT
```

## Arguments

* `KIT`: Name/slug of the reasoning kit to run.

## Options

* `--local`: Load from the local filesystem instead of the database.
* `--base-path PATH`: Base path for local reasoning kits. Defaults to `reasoning_kits`.
* `--evaluate`: Enable step-by-step evaluation prompts.
* `--mode MODE`: Evaluation mode: 'transparent' stores full text, 'anonymous' stores character counts. Defaults to 'transparent'.

## Example

```bash
uv run clerk run demo --evaluate
```

This will run the kit and prompt for feedback after each evaluation step. To see all available kits, use the [list command](list.md).
