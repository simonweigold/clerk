# Reasoning Kits — Specification

A **reasoning kit** is a directory of plain text files that defines a multi-step LLM workflow. Any agent that reads the directory can follow the workflow. The `rk` CLI (and Python SDK) executes it, evaluates it, and — experimentally — improves it autonomously.

Reasoning kits are:
- **Lightweight.** Plain text files. No packaging, no platform.
- **Agent-readable.** Claude Code, Codex, Hermes, opencode — any agent that reads files can follow a kit.
- **Self-improving.** Kits can be evaluated, branched, mutated, and auto-merged by the improver (experimental).

---

## Quick start

```bash
# Install
uv tool install reasoning-kits            # or: uv add reasoning-kits

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
```

---

## File naming

| File pattern             | Role                          | Notes                                                         |
| ------------------------ | ----------------------------- | ------------------------------------------------------------- |
| `instruction_N.txt`      | Workflow step N               | N starts at 1; steps run in ascending order                   |
| `resource_N.EXT`         | Static resource N             | Loaded at startup; any extension supported                    |
| `dynamic_resource_N.EXT` | Dynamic resource N            | Empty file; content provided at runtime via CLI or stdin      |
| `tool_N.json`            | Tool reference N              | References a tool from the global registry or MCP             |
| `evaluator_N.json`       | Multi-dimension evaluator N   | `{dimensions: {label: prompt}, aggregation?: "average"\|"min"\|"max"\|"first"}` |
| `evaluator_N.txt`        | Single-dimension evaluator N  | Plain text fallback; label is `"default"`                     |
| `mcp_servers.json`       | Kit-local MCP server config   | Optional; merged with the project-root config                 |
| `kit.json`               | Kit-level defaults            | Optional; sets default `model`, `judge_model`, `mode`, etc.   |

A valid kit contains **at least one** `instruction_*.txt`.

`evaluations/` subdirectories are created automatically by `rk run --evaluate` and hold eval JSON files.

---

## Placeholders

Instructions use `{placeholder}` to reference content:

| Placeholder    | Resolves to                                                |
| -------------- | ---------------------------------------------------------- |
| `{resource_N}` | Content of `resource_N.*`                                  |
| `{workflow_N}` | Output of step N (available from step N+1 onward)           |
| `{tool_N}`     | Tool description; makes the tool callable by the LLM       |

For resources exceeding ~400,000 characters, the loader uses lightweight RAG (keyword overlap) to select relevant chunks. Embedding-based RAG is planned.

---

## Examples

### Minimal kit (text only)

```
my-kit/
├── instruction_1.txt     # "Summarize {resource_1} in 3 bullets."
├── instruction_2.txt     # "Given this summary:\n{workflow_1}\n\nRate 1-5 using {resource_2}."
├── resource_1.txt        # Source document
└── resource_2.csv        # Rating criteria
```

### Tool-enabled kit

```
my-kit/
├── instruction_1.txt     # "Use {tool_1} to read https://example.com and summarise."
├── tool_1.json           # {"tool_name": "read_url", "display_name": "Web Fetcher"}
└── mcp_servers.json      # Optional kit-local MCP overrides
```

### Dynamic resource kit (input at runtime)

```
my-kit/
├── instruction_1.txt          # "Analyse the following text: {resource_1}"
└── dynamic_resource_1.txt     # (empty — filled in by --dynamic-resource or stdin)
```

---

## Running a kit

The CLI is the canonical entry point. Always prefer it over writing custom Python.

```bash
# Local kit
rk run my-kit

# With inline dynamic resource
rk run my-kit --dynamic-resource resource_1="Article 41 OR"

# From stdin
echo "Article 41 OR" | rk run my-kit --stdin resource_1

# From file
rk run my-kit --dynamic-resource-file resource_1=./input.txt

# With evaluation (judge LLM scores each step)
rk run my-kit --evaluate --auto-evaluate --judge-model gpt-5.4-nano

# Override model
rk run my-kit --model claude-3-5-sonnet-latest

# Skip MCP initialization
rk run my-kit --no-mcp
```

The CLI handles MCP server connection, dynamic resource injection, tool registration, and cleanup.

### Outputs

By default, outputs are written to `outputs/<kit-name>/<timestamp>/` containing:
- `step_N_workflow_N.md` — the LLM response
- `step_N_workflow_N_prompt.md` — the resolved prompt
- `run.json` — metadata

Use `--no-save` to skip, `--output-dir <path>` to redirect.

---

## Validating a kit

```bash
rk validate my-kit
```

Checks:
- Instructions numbered sequentially starting at 1
- All `{resource_N}` placeholders have matching resource files
- All `{tool_N}` placeholders have matching tool files AND resolve in the global registry
- All `{workflow_N}` placeholders refer to earlier steps
- Approximate token-size warnings on resolved prompts

Exit code is 0 on success, 1 on errors.

---

## Evaluation

`rk run --evaluate` activates per-step evaluation. Two modes:

- **Interactive** (`--evaluate` alone): user is prompted for a 0-100 score after each step.
- **Automatic** (`--evaluate --auto-evaluate`): a judge LLM scores each step using `evaluator_N.{json,txt}`.

### Evaluator file format

`evaluator_1.txt` — single-dimension prompt, label `"default"`:

```
Rate the following output for accuracy, completeness, and clarity.
Output a single integer score 0-100 on the last line.

PROMPT:
{prompt}

OUTPUT:
{output}
```

`evaluator_2.json` — multi-dimension with aggregation:

```json
{
  "aggregation": "min",
  "dimensions": {
    "structure": "Does the output have clear sections? ...",
    "depth":     "Is the analysis deep or superficial? ..."
  }
}
```

Aggregation strategies: `average` (default), `min`, `max`, `first`.

### Result storage

Eval results are saved to `<kit-path>/evaluations/N.json` as the kit is run. Each evaluation is a self-contained record you can diff, version-control, or feed back into the improver.

`--mode anonymous` stores character counts instead of full text (privacy-preserving).

---

## Tools

Tools are LLM-callable functions exposed via the OpenAI function-calling format. The LLM decides when to call them.

### Built-in tools (always available)

| Name          | Description                                                  |
| ------------- | ------------------------------------------------------------ |
| `read_url`    | Fetch a URL, extract readable text via BeautifulSoup         |
| `jina_reader` | Fetch via `https://r.jina.ai/{url}` — bypasses bot protection |

### Custom tools

```python
from reasoning_kits.tools import register_tool, ToolDefinition

async def my_tool(args: dict) -> str:
    return f"Result for: {args['query']}"

register_tool(ToolDefinition(
    name="my_tool",
    description="Does something useful",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
    execute=my_tool,
))
```

### Reference in an instruction

Add `tool_1.json` pointing at the tool, then use `{tool_1}` in an instruction. The tool is exposed to the LLM for that step; results flow back automatically.

---

## MCP integration

[Model Context Protocol](https://modelcontextprotocol.io) servers can be declared in:
- `<project-root>/mcp_servers.json` (global)
- `<kit-dir>/mcp_servers.json` (kit-local override; merges by server name, later wins)

Supported transports: `stdio` (default), `sse`, `http`.

```json
{
  "mcpServers": {
    "opencaselaw": {
      "transport": "sse",
      "url": "https://mcp.opencaselaw.ch"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

`${VAR}` placeholders in env values are resolved from the current environment at connect time.

`rk run` initializes MCP automatically (skip with `--no-mcp`).

---

## Programmatic API

When embedding reasoning kits inside another Python application:

```python
from reasoning_kits.loader import load_reasoning_kit
from reasoning_kits.runner import run_kit_async
from reasoning_kits.mcp_client import init_mcp_servers, close_mcp_servers

kit = load_reasoning_kit("./my-kit")

await init_mcp_servers(config_path="mcp_servers.json")
try:
    outputs = await run_kit_async(
        kit,
        evaluate=True,
        auto_evaluate=True,
        model="gpt-5.4-nano",
        judge_model="gpt-5.4-nano",
    )
finally:
    await close_mcp_servers()
```

`run_kit_async` keyword arguments:

| Argument            | Type    | Default     | Description                                                    |
| ------------------- | ------- | ----------- | -------------------------------------------------------------- |
| `evaluate`          | bool    | False       | Enable per-step evaluation                                     |
| `evaluation_mode`   | str     | transparent | "transparent" or "anonymous"                                   |
| `auto_evaluate`     | bool    | False       | Use judge LLM instead of interactive prompts                   |
| `judge_model`       | str?    | None        | Model for judge; None → use the main model                     |
| `model`             | str     | env default | LLM model for the main workflow                                |
| `evaluator_aggregation` | str | "average"   | "average" \| "min" \| "max" \| "first"                        |
| `verbose`           | bool    | False       | Print step details to stdout                                   |
| `collected_prompts` | dict?   | None        | If set, resolved prompts are written into this dict            |

---

## LLM providers

LLM calls go through [LiteLLM](https://github.com/BerriAI/litellm). Set the corresponding env var and any LiteLLM-supported model name works:

| Provider   | Env var                  | Example model                          |
| ---------- | ------------------------ | -------------------------------------- |
| OpenAI     | `OPENAI_API_KEY`         | `gpt-5.4-nano`                         |
| Anthropic  | `ANTHROPIC_API_KEY`      | `claude-3-5-sonnet-latest`             |
| Mistral    | `MISTRAL_API_KEY`        | `mistral-large-latest`                 |
| Gemini     | `GEMINI_API_KEY`         | `gemini/gemini-1.5-pro`                |
| OpenRouter | `OPENROUTER_API_KEY`     | `openrouter/anthropic/claude-3.5-sonnet` |

Default model: `gpt-5.4-nano` (override with `RK_DEFAULT_MODEL` env var or `kit.json`).

---

## Self-improvement (experimental)

The killer feature. A reasoning kit can fork itself, mutate its instructions / resources / tools / eval criteria / model selection, run the eval, and auto-merge winners. The agent decides when and what to change.

```
                  ┌──────────────┐
       main ─────►│   branch     │─► mutate
                  │   eval       │─► score
                  │   compare    │
       main ◄─────│   merge      │  winner > main
                  └──────────────┘
```

### Versioning

Linear `main` branch. Each improvement attempt lives on its own branch until eval decides. Branches are never deleted automatically — revert by `git checkout` and `git revert`.

### Safety net

There is **no human-in-the-loop merge approval**. The eval IS the gate. The rollback is `git revert`.

This is intentional. Reasoning kits improve when the agent has wide latitude. If you want human gating, run the improver manually and review each branch before merging.

### Triggers

The improver runs continuously when activated. After every kit execution, the agent decides whether to invest cycles in improvement based on:
- Eval scores trending down or stagnating
- New external information becoming available (web search, doc updates)
- Cost/quality tradeoffs surfaced by model experimentation

---

## Design philosophy

- **Files, not code.** A kit is text. Anyone can read it, edit it, version-control it, diff it.
- **Agent-first.** A kit is as much an artifact for human readers as for LLM agents. Both should be able to follow it.
- **No platform.** No hosted service, no user accounts, no vendor lock-in. The repo IS the registry.
- **Self-improvement is core.** A kit that doesn't get better over time is dead. Improvement is the loop that keeps it alive.
- **Reversibility over approval.** Eval gates replace human review. Git history replaces backups. Make rollback cheap.

---

## License

MIT. Use it, fork it, ship it.