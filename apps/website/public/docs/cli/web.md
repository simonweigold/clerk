# Web Command

The `web` command starts the CLERK web UI server. The Web UI can be used to [edit](../ui/editing_kits.md) and [run](../ui/running_kits.md) [reasoning kits](../reasoning_kits.md).

## Usage

```bash
uv run clerk web [OPTIONS]
```

## Options

* `--host HOST`: Host to bind to (default: `127.0.0.1`).
* `--port PORT`: Port to listen on (default: `8000`).
* `--reload`: Enable auto-reload on code changes (development mode).

## Example

```bash
uv run clerk web --reload
```
This starts the web server on `http://127.0.0.1:8000` with hot reloading enabled.
