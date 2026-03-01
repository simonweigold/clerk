# Database Command

The `db` command manages the database for [reasoning kits](../reasoning_kits.md).

## Usage

```bash
uv run clerk db [COMMAND]
```

## Commands

### Setup

```bash
uv run clerk db setup
```
Setups the database, runs migrations, and creates the storage bucket.

### Migrate

```bash
uv run clerk db migrate [OPTIONS]
```
Applies pending database migrations.
* `--revision REVISION`: Target revision (default: head).

### Status

```bash
uv run clerk db status
```
Shows the migration status.
