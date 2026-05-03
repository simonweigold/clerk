# Sync Command

The `sync` command is used to synchronize [reasoning kits](../reasoning_kits.md) between the local filesystem and the database.

## Push

```bash
uv run clerk sync push [OPTIONS] KIT
```
Pushes a local kit to the database.
* `KIT`: Name of the local kit to push.
* `--base-path PATH`: Base path for local reasoning kits.
* `--message -m`: Commit message for this version.

## Pull

```bash
uv run clerk sync pull [OPTIONS] KIT
```
Pulls a kit from the database to the local filesystem.
* `KIT`: Slug of the kit to pull.
* `--base-path PATH`: Base path for local reasoning kits.

## List

```bash
uv run clerk sync list
```
Compares local and database kits.
