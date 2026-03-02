# List Command

The `list` command displays all available reasoning kits.

## Usage

```bash
uv run clerk list [OPTIONS]
```

## Options

* `--local`: List from the local filesystem instead of the database.
* `--path PATH`: Base path for local reasoning kits. Defaults to `reasoning_kits`.

## Example

```bash
uv run clerk list --local
```

For executing a kit from this list, use the [run command](run.md). To view detailed info, use the [info command](info.md).
