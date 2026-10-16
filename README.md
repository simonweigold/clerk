# Reasoning Kits

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)

> A lightweight standard for self-improving LLM reasoning workflows.

A **reasoning kit** is a directory of plain text files that defines a multi-step LLM workflow. Any agent that reads the directory can follow the workflow. The `rk` CLI executes it, evaluates it, and — experimentally — improves it autonomously.

Reasoning kits are agent-skills on steroids: they're file-based, version-controlled, and improve themselves over time.

## Install

```bash
uv tool install reasoning-kits
# or
uv add reasoning-kits
```

## Quickstart

```bash
# Browse the reference kits
rk list

# Inspect a kit
rk info demo

# Validate a kit's structure
rk validate my-kit

# Run it
rk run my-kit

# Run with input piped in
echo "Article 41 OR" | rk run my-kit --stdin resource_1

# Run with evaluation (judge LLM scores each step)
rk run my-kit --evaluate --auto-evaluate
```

## What is a kit?

```
my-kit/
├── instruction_1.txt     # "Summarize {resource_1} in 3 bullets."
├── instruction_2.txt     # "Given this summary:\n{workflow_1}\n\nRate 1-5."
├── resource_1.txt        # Source document
└── resource_2.csv        # Rating criteria
```

Plus, optionally:
- `tool_N.json` to expose LLM-callable tools (built-in or MCP)
- `evaluator_N.{txt,json}` for automatic scoring
- `mcp_servers.json` to attach Model Context Protocol servers
- `dynamic_resource_N.EXT` for runtime-supplied inputs
- `kit.json` for default model/judge settings

See [SPEC.md](SPEC.md) for the full specification.

## Why reasoning kits?

- **Files, not code.** Anyone can read, edit, diff, and version-control a kit. No framework lock-in.
- **Agent-readable.** Claude Code, Codex, Hermes, opencode — any agent that reads files can follow a kit. No SDK required to use one.
- **No platform.** No hosted service, no user accounts, no vendor lock-in. The repo IS the registry.
- **Self-improving.** A kit can fork itself, mutate its instructions/resources/tools/evals, run the eval, and auto-merge winners. The eval IS the gate.

## Documentation

- [SPEC.md](SPEC.md) — canonical format specification
- [kits/](kits/) — reference kits

## Development

```bash
git clone https://github.com/simonweigold/reasoning-kits
cd reasoning-kits
uv sync
uv run pytest
uv run rk list
```

See [AGENTS.md](AGENTS.md) for code conventions.

## License

[MIT](LICENSE)