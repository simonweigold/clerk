# Info Command

The `info` command shows information about a [reasoning kit](../reasoning_kits.md).

## Usage

```bash
uv run clerk info [OPTIONS] KIT
```

## Arguments

* `KIT`: Name/slug of the reasoning kit to query.

## Options

* `--local`: Load from the local filesystem instead of the database.
* `--base-path PATH`: Base path for local reasoning kits. Defaults to `reasoning_kits`.

## Example

```bash
uv run clerk info demo
```

You can use the info output to see the resources and workflow steps before executing it with the [run command](run.md). To see all available kits, use the [list command](list.md).
