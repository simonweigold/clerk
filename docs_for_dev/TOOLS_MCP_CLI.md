# OpenClerk Tool & MCP Integration Roadmap

**Date:** 2026-04-24
**Scope:** `openclerk` Python package (`packages/clerk/`) and CLI
**Goal:** Make tool usage (built-in, custom, MCP) a first-class, zero-code experience for reasoning kit authors and users.

---

## 1. Problem Statement

Today, tool and MCP integration in OpenClerk works, but requires significant manual setup. The friction points are:

| #   | Pain Point                                                                                                                                                                                                                      | Impact                                                                                                       |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 1   | **Filesystem loader does not auto-discover tools.** Only DB-loaded kits get `kit.tools` populated. Local kits must attach tools programmatically after `load_reasoning_kit()`.                                                  | Tool-enabled kits cannot be shared as plain text file directories.                                           |
| 2   | **MCP client only supports `stdio` transport.** The `init_mcp_servers()` function spawns subprocesses via `StdioServerParameters`. Remote MCP servers (SSE, HTTP, Streamable HTTP) cannot be configured via `mcp_servers.json`. | Servers like OpenCaseLaw (`https://mcp.opencaselaw.ch`) require a custom wrapper script.                     |
| 3   | **No convention for declaring tools in a local kit.** There is no `tool_N.json` or `tools.json` file that the filesystem loader recognizes.                                                                                     | Kit authors must write Python code to attach tools, defeating the "plain text files only" design philosophy. |
| 4   | **CLI prompts for dynamic resources via file path only.** It does not support pasting text directly, piping from stdin, or accepting text via `--dynamic-resource` CLI flags.                                                   | Iterative testing is slow; users must create temporary files for every run.                                  |
| 5   | **No MCP tool caching or offline mode.** Every `clerk run` re-initializes MCP servers and re-discovers tools.                                                                                                                   | Slow startup, unnecessary network calls, no offline capability.                                              |
| 6   | **RAG fallback is noisy and confusing.** When `SUPABASE_URL` is missing, the engine prints warnings about RAG failure even though it gracefully falls back to full text.                                                        | Users think something is broken when it is not.                                                              |
| 7   | **No per-step tool visibility.** Users cannot see which tools were invoked, how many rounds occurred, or what results were returned without reading raw LLM output.                                                             | Debugging tool-enabled kits is difficult.                                                                    |

---

## 2. Vision

> A reasoning kit author should be able to create a fully tool-enabled kit using **only plain text files** — no Python code, no database, no custom runner scripts. A user should be able to run it with a single `clerk run` command.

---

## 3. Proposed Improvements

### 3.1 Auto-discover tools from the filesystem

**What:** Extend `load_reasoning_kit()` to recognize tool definition files inside the kit directory.

**File conventions:**

```
my-kit/
├── instruction_1.txt
├── instruction_2.txt
├── resource_1.txt
├── tool_1.json          # NEW: Tool declaration
├── tool_2.json          # NEW: Tool declaration
└── mcp_servers.json     # NEW: MCP server config (local override)
```

**`tool_1.json` schema:**

```json
{
  "tool_name": "read_url",
  "display_name": "Web Fetcher",
  "configuration": null
}
```

**`mcp_servers.json` (kit-local override):**

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

**Implementation notes:**

- The loader already scans for `resource_*.*` and `instruction_*.txt`. Add a scan for `tool_*.json`.
- Populate `kit.tools` from these files using the existing `Tool` Pydantic model.
- If an `mcp_servers.json` exists in the kit directory, merge it with (or override) the project-root `mcp_servers.json`.
- Support three transport types in `mcp_servers.json`: `stdio` (default), `sse`, `http`.

**Effort:** Low. The loader and models already support this; only the scan logic is missing.

---

### 3.2 Support SSE and HTTP MCP transports

**What:** Refactor `openclerk/mcp_client.py` to support multiple transport types.

**Current state:**

```python
server_params = StdioServerParameters(command=command, args=args, env=server_env)
stdio_transport = await _exit_stack.enter_async_context(stdio_client(server_params))
```

**Desired state:**

```python
transport = server_cfg.get("transport", "stdio")

if transport == "stdio":
    # existing logic
elif transport == "sse":
    from mcp.client.sse import sse_client
    sse_transport = await _exit_stack.enter_async_context(
        sse_client(server_cfg["url"])
    )
    read, write = sse_transport
elif transport == "http":
    from mcp.client.streamable_http import streamable_http_client
    # ...
```

**Implementation notes:**

- `mcp` Python SDK already provides `mcp.client.sse` and `mcp.client.streamable_http`.
- The `AsyncExitStack` pattern works for all three transports.
- Environment variable substitution (`${VAR}`) should work for all transport configs.
- Add validation: `url` is required for `sse`/`http`; `command` is required for `stdio`.

**Effort:** Low-Medium. Transport abstractions are available in the MCP SDK; mainly refactoring.

---

### 3.3 CLI improvements for dynamic resources

**What:** Make it easier to provide dynamic resource content without creating temporary files.

**New CLI flags:**

```bash
# Provide dynamic resource as inline text
clerk run my-kit --local \
  --dynamic-resource resource_1="What are my rights as a tenant in Zurich?"

# Provide dynamic resource from stdin
echo "What are my rights as a tenant in Zurich?" | clerk run my-kit --local --stdin resource_1

# Provide from a file (existing behavior, but add a flag for consistency)
clerk run my-kit --local --dynamic-resource-file resource_1=./my-question.txt
```

**Implementation notes:**

- The CLI already iterates `dynamic_resources` and prompts for file paths (see `cli.py` line 473-495).
- Add argument parsing for `--dynamic-resource` and `--dynamic-resource-file` before the prompt loop.
- If all dynamic resources are satisfied via flags, skip the interactive prompt entirely.
- Support multiple `--dynamic-resource` flags for kits with multiple dynamic resources.

**Effort:** Low. CLI arg parsing only; no core engine changes.

---

### 3.4 MCP tool caching and offline mode

**What:** Cache MCP tool schemas and optionally cache tool results for faster, repeatable runs.

**Cache location:**

```
~/.cache/openclerk/mcp/
├── opencaselaw/
│   ├── tools.json          # Cached tool schemas from tools/list
│   └── timestamp
```

**Behavior:**

- On `init_mcp_servers()`, first check the cache. If `tools.json` exists and is younger than a configurable TTL (e.g., 1 hour), use the cached schemas instead of calling `list_tools()`.
- Add `--refresh-mcp` CLI flag to force re-discovery.
- For `sse`/`http` transports, a cached schema is sufficient; the server does not need to be reachable if the user only needs the schema (though execution will still require connectivity).

**Effort:** Low. Simple file-based caching with JSON serialization.

---

### 3.5 Per-step tool execution logging

**What:** Make tool invocations visible and debuggable.

**New behavior:**

- When `openai_tools` is non-empty, print a clear header:
  ```
  Step 2 - Tools enabled: search_decisions, get_law, find_leading_cases
  ```
- After each tool call round, print:
  ```
  Tool call: search_decisions(query="Mietrecht Kündigung", canton="ZH", limit=5)
  Tool result: 3 decisions found
  ```
- Save structured tool execution logs to `evaluations/tool_calls.json` (or a new `logs/` directory).

**Effort:** Low. The tool-call loop already exists in `graph.py`; just add logging.

---

### 3.6 Suppress misleading RAG warnings

**What:** When RAG is unavailable (missing `SUPABASE_URL` or embeddings), the engine should silently fall back to full text or log at `DEBUG` level only.

**Current behavior:**

```
Warning: async RAG failed for resource_2, falling back to full text. Error: SUPABASE_URL environment variable required
```

**Desired behavior:**

- If the resource is below the threshold (default 4000 chars), no RAG is attempted → no message.
- If the resource is above the threshold but RAG fails, log at `DEBUG` level instead of `print()`.
- Optionally add `--verbose` flag to show these diagnostics.

**Effort:** Minimal. Change `print()` to `logging.debug()` or remove entirely.

---

### 3.7 Kit validation command

**What:** Add a `clerk validate` command that checks a kit for structural correctness before running.

```bash
clerk validate my-kit --local
```

**Checks:**

- All `instruction_N.txt` files are present and numbered sequentially.
- All `{resource_N}` placeholders in instructions have a matching resource file.
- All `{tool_N}` placeholders have a matching tool definition (from `tool_*.json`, DB, or global registry).
- All `{workflow_N}` placeholders refer to earlier steps.
- Dynamic resources are present but empty (or contain placeholder text).
- Total prompt size per step is within model context limits (approximate).

**Effort:** Medium. Requires building a placeholder parser and dependency graph checker.

---

## 4. Acceptance Criteria

A user should be able to:

1. Create a new kit directory with `instruction_*.txt`, `resource_*.txt`, and `tool_*.json` files.
2. Add an `mcp_servers.json` with an `sse` transport pointing to a remote server.
3. Run `clerk validate my-kit --local` and see zero errors.
4. Run `clerk run my-kit --local --dynamic-resource resource_1="..."` and see the LLM invoke MCP tools automatically.
5. See clear per-step tool execution logs in the terminal.
6. Run the same kit a second time and benefit from MCP tool schema caching.
7. Never see a `SUPABASE_URL` warning when running a local kit without a database.

---

## 5. Prioritization

| Priority | Feature                            | Effort  | User Impact                                    |
| -------- | ---------------------------------- | ------- | ---------------------------------------------- |
| **P0**   | 3.2 SSE/HTTP MCP transport         | Low-Med | Unlocks remote MCP servers (OpenCaseLaw, etc.) |
| **P0**   | 3.1 Filesystem tool auto-discovery | Low     | Enables tool kits without code                 |
| **P1**   | 3.3 CLI dynamic resource flags     | Low     | Dramatically improves iteration speed          |
| **P1**   | 3.6 Suppress RAG warnings          | Minimal | Removes false alarm noise                      |
| **P1**   | 3.5 Tool execution logging         | Low     | Essential for debugging tool kits              |
| **P2**   | 3.4 MCP tool caching               | Low     | Nice-to-have performance boost                 |
| **P2**   | 3.7 Kit validation command         | Medium  | Improves authoring experience                  |

---

## 6. Files to Modify

| File                       | Change                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------- |
| `openclerk/loader.py`      | Add `tool_*.json` scan; add `mcp_servers.json` kit-local override                     |
| `openclerk/mcp_client.py`  | Add `sse` and `http` transport branches                                               |
| `openclerk/graph.py`       | Add tool execution logging; suppress RAG warnings                                     |
| `openclerk/cli.py`         | Add `--dynamic-resource`, `--dynamic-resource-file`, `--stdin`, `--refresh-mcp` flags |
| `openclerk/tools.py`       | (Optional) Add MCP tool caching utilities                                             |
| `AGENTS.md` or `README.md` | Document new conventions and CLI flags                                                |

---

## 7. Non-Goals

- **Custom tool authoring in JSON/YAML.** This roadmap focuses on _referencing_ existing tools (built-in, MCP). Defining new Python tools still requires code.
- **MCP server hosting.** OpenClerk remains a client, not a server.
- **GUI tool configuration.** The web UI can be updated later to match; this plan targets the Python package and CLI first.
