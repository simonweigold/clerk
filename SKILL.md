## Installation (TestPyPI)

**1. Install the package**

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openclerk
```

**2. Set your OpenAI API key**

```bash
export OPENAI_API_KEY=sk-...
```

Or create a `.env` file:

```
OPENAI_API_KEY=sk-...
```

**3. Verify the installation**

```bash
clerk --help
```

**4. Run a reasoning kit**

```bash
clerk list
clerk run <kit-name>
```

> **Python 3.13+ required.** With `uv`: `uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openclerk`

---

# OpenClerk Package — Agent Skill Reference

This document gives an AI agent the exact knowledge needed to use, create, update, and execute reasoning kits with the `openclerk` Python package.

---

## Package Identity

| Item               | Value                 |
| ------------------ | --------------------- |
| Package name       | `openclerk`           |
| CLI commands       | `clerk` / `openclerk` |
| Entry point        | `openclerk.cli:main`  |
| Python requirement | `>=3.13`              |
| Version            | `0.1.1`               |

Install from source:

```bash
just setup          # preferred
# or
uv sync --all-groups
```

---

## Core Concept: Reasoning Kits

A **reasoning kit** is a directory of plain text files that define a multi-step LLM workflow. No Python code is needed to define a kit — only files with strict naming conventions.

### File naming rules

| File pattern             | Role                         | Notes                                                           |
| ------------------------ | ---------------------------- | --------------------------------------------------------------- |
| `instruction_N.txt`      | Workflow step N              | N starts at 1; steps run in ascending order                     |
| `resource_N.EXT`         | Static resource N            | Read at load time; any extension supported                      |
| `dynamic_resource_N.EXT` | Dynamic resource N           | Content is empty at load time; user provides it at runtime      |
| `tool_N.json`            | Tool reference N             | References a tool from the global registry (built-in or MCP)    |
| `mcp_servers.json`       | MCP server config (optional) | Kit-local override; merges with project-root `mcp_servers.json` |

Directories named `evaluations/` inside a kit are created automatically and hold evaluation JSON files — do not create them manually.

### Placeholder syntax inside instructions

Instructions use `{placeholder}` to reference content:

| Placeholder    | Resolves to                                           |
| -------------- | ----------------------------------------------------- |
| `{resource_1}` | Content of `resource_1.*`                             |
| `{resource_2}` | Content of `resource_2.*`                             |
| `{workflow_1}` | Output of step 1 (available from step 2 onward)       |
| `{workflow_N}` | Output of step N                                      |
| `{tool_1}`     | Result of calling tool 1 (LLM decides when to invoke) |

For resources exceeding 4 000 characters, the loader automatically uses RAG (chunking + embeddings) to retrieve only the most relevant chunks. RAG status is logged at `DEBUG` level only — no console warnings.

### Tool reference file (`tool_N.json`)

A `tool_N.json` file references a tool from the global registry by name. The tool can be built-in or provided by an MCP server.

```json
{
  "tool_name": "read_url",
  "display_name": "Web Fetcher",
  "configuration": null
}
```

Only `tool_name` is required. `display_name` is optional (used in prompts). `configuration` is optional JSON that overrides the tool's default behavior.

The placeholder `{tool_1}` in an instruction resolves to the tool's display name and makes the tool available to the LLM for that step.

### Minimal kit example

```
my-kit/
├── instruction_1.txt     # "Summarize {resource_1} in 3 bullet points."
├── instruction_2.txt     # "Given this summary:\n{workflow_1}\n\nRate it 1-5 using {resource_2}."
├── resource_1.txt        # Source document
└── resource_2.csv        # Rating criteria
```

### Tool-enabled kit example

```
my-kit/
├── instruction_1.txt       # "Use {tool_1} to read https://example.com and summarise."
├── tool_1.json             # {"tool_name": "read_url", "display_name": "Web Fetcher"}
└── mcp_servers.json        # Optional: kit-local MCP server override
```

### Dynamic resource example (user provides input at runtime)

```
my-kit/
├── instruction_1.txt       # "Analyse the following text: {dynamic_resource_1}"
└── dynamic_resource_1.txt  # (empty — filled in by user or CLI prompt)
```

---

## Data Models (Pydantic)

```python
from openclerk.models import Resource, WorkflowStep, Tool, ReasoningKit

class Resource(BaseModel):
    file: str              # filename, e.g. "resource_1.txt"
    resource_id: str       # e.g. "resource_1"
    content: str           # loaded text (empty for dynamic)
    is_dynamic: bool       # True  → user provides at runtime
    display_name: str | None

class WorkflowStep(BaseModel):
    file: str              # filename, e.g. "instruction_1.txt"
    output_id: str         # e.g. "workflow_1"
    prompt: str            # raw template text
    display_name: str | None

class Tool(BaseModel):
    tool_name: str         # registry key, e.g. "read_url"
    tool_id: str           # e.g. "tool_1"
    display_name: str | None
    configuration: str | None  # optional JSON overrides

class ReasoningKit(BaseModel):
    name: str
    path: str              # filesystem path or "db://<slug>"
    resources: dict[str, Resource]     # "1" -> Resource
    workflow: dict[str, WorkflowStep]  # "1" -> WorkflowStep
    tools: dict[str, Tool]             # "1" -> Tool  (may be empty)
```

---

## Loading a Kit

### From the filesystem (sync)

```python
from openclerk.loader import load_reasoning_kit

kit = load_reasoning_kit("reasoning_kits/demo")
# kit is a ReasoningKit instance
```

### List local kits

```python
from openclerk.loader import list_reasoning_kits

names = list_reasoning_kits("reasoning_kits")   # returns list[str]
```

### From the database (async)

```python
from openclerk.loader import load_reasoning_kit_from_db

loaded = await load_reasoning_kit_from_db("my-kit-slug")
# loaded.kit        → ReasoningKit
# loaded.version_id → UUID
# loaded.kit_id     → UUID

# Load a specific version
loaded = await load_reasoning_kit_from_db("my-kit-slug", version_id=some_uuid)
```

### List database kits

```python
from openclerk.loader import list_reasoning_kits_from_db

kits = await list_reasoning_kits_from_db()
# [{"slug": "...", "name": "...", "description": "..."}, ...]
```

---

## Executing a Kit

### Programmatic API

```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit, run_reasoning_kit_async

kit = load_reasoning_kit("reasoning_kits/demo")

# Sync
outputs = run_reasoning_kit(kit, model="gpt-4o-mini")

# Async (preferred)
outputs = await run_reasoning_kit_async(kit, model="gpt-4o-mini")

# outputs is dict[str, str]:
# {"workflow_1": "...", "workflow_2": "..."}
print(outputs["workflow_1"])
```

### Full parameter reference

```python
outputs = await run_reasoning_kit_async(
    kit=kit,
    evaluate=False,                  # Prompt user to score each step 0-100
    evaluation_mode="transparent",   # "transparent" | "anonymous"
    save_to_db=False,                # Persist run + step results to DB
    db_version_id=None,              # UUID — required when save_to_db=True
    model="gpt-4o-mini",            # LLM model string
    user_id=None,                    # UUID string — loads user's LLM provider config
    verbose=False,                   # Print step prompts and results to stdout
)
```

**Evaluation modes:**

- `transparent` — stores full prompt + output text in DB
- `anonymous` — stores only character counts (privacy-preserving)

---

## LLM Provider (LLM Factory)

```python
from openclerk.llm_factory import get_llm

# Returns a LangChain-compatible chat model
llm = await get_llm(
    user_id="uuid-string",   # looks up user's provider in DB; fallback to env vars
    model="gpt-4o-mini",
    temperature=0.0,
)
```

Supported providers (configured via env vars or DB per-user):

- `OpenAI` (`OPENAI_API_KEY`)
- `Anthropic` (`ANTHROPIC_API_KEY`)
- `Mistral`
- `Google Gemini`
- `Vertex AI`
- `OpenRouter`

---

## Tools

### Built-in tools (always available)

| Tool name     | Description                                                           |
| ------------- | --------------------------------------------------------------------- |
| `read_url`    | Fetches a URL and extracts readable text via BeautifulSoup            |
| `jina_reader` | Fetches a URL via `https://r.jina.ai/{url}` — bypasses bot protection |

### Register a custom tool

```python
from openclerk.tools import register_tool, ToolDefinition
import asyncio

async def my_tool(query: str) -> str:
    return f"Result for: {query}"

register_tool(ToolDefinition(
    name="my_tool",
    description="Does something useful",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"}
        },
        "required": ["query"],
    },
    execute=my_tool,
    source="builtin",          # or MCP server name
))
```

### Get OpenAI-format schema for LLM

```python
from openclerk.tools import get_openai_tool_schema

schema = get_openai_tool_schema("read_url")
```

### Reference a tool inside a kit instruction

Add the tool to the kit's `tools` dict with key `"1"` and placeholder `{tool_1}`:

```
instruction_1.txt:
  Research this topic using {tool_1}: LangGraph architecture
```

```python
from openclerk.models import Tool
kit.tools["1"] = Tool(tool_name="read_url", tool_id="tool_1")
```

The LLM decides when to invoke the tool; results flow back automatically.

### Tool execution logging

When tools are invoked, structured logs are emitted at `INFO` level:

```
Step 1 - Tools enabled: read_url
Tool call: read_url(url='https://example.com')
Tool result: Example Domain...
```

These appear in the terminal during `clerk run` and in the server logs during web execution. Set `LOGLEVEL=DEBUG` to see RAG chunking details as well.

---

## MCP Integration

MCP servers can be configured at the project root or inside a kit directory. Kit-local configs override global configs by server name.

### Supported transports

| Transport         | Required fields            | Notes                        |
| ----------------- | -------------------------- | ---------------------------- |
| `stdio` (default) | `command`, `args?`, `env?` | Spawns a subprocess          |
| `sse`             | `url`                      | Server-Sent Events over HTTP |
| `http`            | `url`                      | Streamable HTTP              |

### Project-root `mcp_servers.json`

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["-m", "my_mcp_module"],
      "env": {
        "API_KEY": "${MY_API_KEY}"
      }
    }
  }
}
```

### Kit-local `mcp_servers.json`

Place an `mcp_servers.json` inside a kit directory to add or override servers for that kit only. It merges with the project-root config (kit-local wins by server name).

```json
{
  "mcpServers": {
    "opencaselaw": {
      "transport": "sse",
      "url": "https://mcp.opencaselaw.ch"
    }
  }
}
```

MCP tools are auto-registered into the global tool registry when the kit runs (CLI or web) and can be referenced in kits as `{tool_N}` exactly like built-in tools.

### Using MCP tools programmatically

MCP client sessions are bound to the event loop they are created in. When calling kits with MCP tools from Python code, **initialize MCP, run the kit, and clean up all within the same event loop**:

```python
import asyncio
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit_async
from openclerk.mcp_client import init_mcp_servers, close_mcp_servers
from openclerk.tools import clear_mcp_tools

kit = load_reasoning_kit("reasoning_kits/my-kit")

clear_mcp_tools()

async def run():
    await init_mcp_servers(
        config_path="mcp_servers.json",
        kit_config_path=f"{kit.path}/mcp_servers.json",
    )
    try:
        outputs = await run_reasoning_kit_async(kit, verbose=True)
        print(outputs["workflow_1"])
    finally:
        await close_mcp_servers()

asyncio.run(run())
```

**Do not** call `run_reasoning_kit()` (the sync LangGraph path) after initializing MCP in a different `asyncio.run()` — the tool sessions will fail with `ClosedResourceError`. Use `run_reasoning_kit_async()` instead, or manage a single persistent event loop manually.

---

## CLI Reference

### Kit discovery

```bash
clerk list                          # List kits from database
clerk list --local --path reasoning_kits   # List local kits
clerk info <slug>                   # Show kit details
```

### Running a kit

```bash
clerk run demo                      # From database
clerk run demo --local              # From filesystem (looks in reasoning_kits/)
clerk run demo --evaluate           # Enable step-by-step evaluation
clerk run demo --mode anonymous     # Privacy-preserving evaluation
clerk run demo --model gpt-4o       # Override model

# Dynamic resources (skip interactive prompts)
clerk run demo --dynamic-resource resource_1="inline text"
clerk run demo --dynamic-resource-file resource_1=./my-input.txt
echo "piped text" | clerk run demo --stdin resource_1
```

**Dynamic resource flags:**

- `--dynamic-resource resource_N="text"` — Provide content inline
- `--dynamic-resource-file resource_N=./file.txt` — Read content from a file
- `--stdin resource_N` — Read content from standard input (useful for piping)

If all dynamic resources are satisfied via flags, the interactive prompt is skipped entirely.

### Validating a kit

```bash
clerk validate my-kit --local
```

Checks for:

- Sequential instruction numbering
- All `{resource_N}` placeholders have matching resource files
- All `{tool_N}` placeholders have matching tool definitions (from `tool_*.json`, DB, or global registry)
- All `{workflow_N}` placeholders refer to earlier steps
- Dynamic resources are present but empty
- Approximate prompt size per step is within model context limits

### Creating and managing kits

```bash
clerk kit create <name> --description "What this kit does"
clerk kit delete <slug> --force
```

### Syncing local ↔ database

```bash
clerk sync push <name> -m "Commit message"   # Upload local kit to DB
clerk sync pull <slug>                        # Download DB kit to filesystem
clerk sync list                               # Compare local vs. DB
```

### Database management

```bash
clerk db setup      # Initialize database and storage bucket
clerk db migrate    # Run pending Alembic migrations
clerk db status     # Check migration status
```

### Web server

```bash
clerk web                    # Start API + React UI on port 8000
clerk web --port 3001        # Custom port
```

---

## REST API (FastAPI)

Base URL: `http://localhost:8000/api/v1`

### Kits

```
POST   /kits                              Body: {slug, name, description, is_public}
GET    /kits/{slug}                       → Kit details
PUT    /kits/{slug}                       Body: {name?, description?}
DELETE /kits/{slug}
GET    /kits/{slug}/info                  → Kit + current version details
```

### Resources

```
POST   /kits/{slug}/resources             Multipart file upload
DELETE /kits/{slug}/resources/{res_num}
```

### Workflow steps

```
POST   /kits/{slug}/steps                 Body: {prompt_template, display_name?}
PUT    /kits/{slug}/steps/{step_num}      Body: {prompt_template?, display_name?}
DELETE /kits/{slug}/steps/{step_num}
```

### Tools

```
GET    /tools/available                   → List all registered tool names
POST   /kits/{slug}/tools                 Body: {tool_name, display_name?, configuration?}
DELETE /kits/{slug}/tools/{tool_num}
```

### Execution

```
POST   /kits/{slug}/execute               Body: {model?, evaluation_mode?} → {run_id}
GET    /kits/{slug}/execute/{run_id}      → Run status + outputs
GET    /kits/{slug}/execute/{run_id}/stream  → SSE stream of step results
```

### Auth

```
POST   /auth/signup      Body: {email, password}
POST   /auth/login       Body: {email, password}
POST   /auth/logout
```

---

## Embedding in an Existing FastAPI App

```python
from fastapi import FastAPI
from openclerk.web.app import create_app as create_clerk_app

app = FastAPI()
app.mount("/clerk", create_clerk_app())

# Clerk routes now at /clerk/api/...
# Clerk React UI now at /clerk/
```

---

## Environment Variables

```env
# LLM (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Database — Supabase (recommended)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...

# Database — raw PostgreSQL (alternative)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/clerk_db

# Storage
SUPABASE_STORAGE_BUCKET=reasoning-kit-resources

# Web security
SESSION_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000,https://example.com
```

---

## Database Schema Quick Reference

| Table             | Key columns                                                                                                               |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `user_profiles`   | `id`, `display_name`, `is_premium`                                                                                        |
| `reasoning_kits`  | `id`, `slug` (unique), `name`, `owner_id`, `is_public`, `current_version_id`                                              |
| `kit_versions`    | `id`, `kit_id`, `version_number`, `commit_message`, `is_draft`                                                            |
| `resources`       | `id`, `version_id`, `resource_number`, `resource_id`, `filename`, `storage_path`, `extracted_text`, `is_dynamic`          |
| `workflow_steps`  | `id`, `version_id`, `step_number`, `output_id`, `prompt_template`                                                         |
| `tools`           | `id`, `version_id`, `tool_number`, `tool_name`, `configuration`                                                           |
| `execution_runs`  | `id`, `version_id`, `user_id`, `status`, `storage_mode`, `started_at`, `completed_at`                                     |
| `step_executions` | `id`, `run_id`, `step_number`, `input_text`, `output_text`, `evaluation_score`, `model_used`, `tokens_used`, `latency_ms` |

`resource_id` on the `resources` table matches the placeholder used in prompts (e.g., `resource_1`).

---

## Common Patterns

### Create a kit programmatically and run it

```python
from openclerk.models import ReasoningKit, Resource, WorkflowStep
from openclerk.graph import run_reasoning_kit

kit = ReasoningKit(
    name="my-kit",
    path="reasoning_kits/my-kit",   # can be any string when constructing manually
    resources={
        "1": Resource(
            file="resource_1.txt",
            resource_id="resource_1",
            content="The sun is a star at the center of the Solar System.",
        )
    },
    workflow={
        "1": WorkflowStep(
            file="instruction_1.txt",
            output_id="workflow_1",
            prompt="Summarise in one sentence: {resource_1}",
        ),
        "2": WorkflowStep(
            file="instruction_2.txt",
            output_id="workflow_2",
            prompt="Expand this summary into a paragraph: {workflow_1}",
        ),
    },
)

outputs = run_reasoning_kit(kit, model="gpt-4o-mini")
print(outputs["workflow_2"])
```

### Add a tool to a kit via filesystem

Create `tool_1.json` inside the kit directory:

```json
{
  "tool_name": "read_url",
  "display_name": "Web Fetcher"
}
```

Then reference it in `instruction_1.txt`:

```
Fetch {tool_1} and summarise the content.
```

No Python code required — the loader auto-discovers `tool_*.json` files.

### Add a tool to a kit programmatically

```python
from openclerk.models import Tool

kit.tools["1"] = Tool(tool_name="read_url", tool_id="tool_1")
# Then in instruction_1.txt:  "Fetch {tool_1} and summarise the content."
```

### Evaluate a run

```python
outputs = await run_reasoning_kit_async(
    kit=kit,
    evaluate=True,
    evaluation_mode="transparent",
    save_to_db=True,
    db_version_id=loaded.version_id,
)
# After each step the CLI prompts: "Rate step N (0-100):"
# Scores are stored in evaluations/{N}.json and in the DB step_executions table
```

---

## Key Source Files

| File                                             | Purpose                              |
| ------------------------------------------------ | ------------------------------------ |
| `packages/clerk/src/openclerk/models.py`         | Pydantic data models                 |
| `packages/clerk/src/openclerk/loader.py`         | Kit loading (filesystem + DB)        |
| `packages/clerk/src/openclerk/graph.py`          | LangGraph execution engine           |
| `packages/clerk/src/openclerk/tools.py`          | Tool registry + built-in tools       |
| `packages/clerk/src/openclerk/llm_factory.py`    | Multi-provider LLM factory           |
| `packages/clerk/src/openclerk/cli.py`            | CLI commands                         |
| `packages/clerk/src/openclerk/web/routes/api.py` | REST API endpoints                   |
| `packages/clerk/src/openclerk/db/models.py`      | SQLAlchemy ORM models                |
| `packages/clerk/src/openclerk/db/repository.py`  | Database access layer                |
| `packages/clerk/src/openclerk/mcp_client.py`     | MCP server integration               |
| `packages/clerk/src/openclerk/evaluation.py`     | Evaluation scoring                   |
| `reasoning_kits/demo/`                           | Reference kit (2 steps, 2 resources) |
