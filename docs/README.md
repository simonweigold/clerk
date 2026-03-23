# CLERK Documentation

Welcome to the documentation for CLERK (Community Library of Executable Reasoning Kits).

## What is CLERK?

CLERK (Community Library of Executable Reasoning Kits), commonly referred to as OpenClerk, is a powerful Python framework designed for creating, managing, and executing multi-step LLM reasoning workflows. It includes a modern React frontend for interacting with and visualizing these workflows.

### Scope and Capabilities
- **Reasoning Kits**: Define complex, multi-step LLM operations using structured instructions, dynamic resources, and evaluation criteria.
- **Agentic Workflows**: Powered by LangChain and LangGraph to manage stateful, multi-agent reasoning chains.
- **Web Interface**: A modern React 19 UI to build, edit, test, and monitor reasoning kits in real-time.
- **CLI Utilities**: Comprehensive command-line tools (`uv run clerk ...`) for running workflows locally, managing tasks, syncing data, and maintaining the database.
- **Extensibility**: Designed to be easily integrated into other applications and augmented with external integrations like MCP (Model Context Protocol).

### How to Use CLERK

**For Human Developers:**
- **Integration**: Embed CLERK as an orchestration engine in your Python backend to manage complex LLM operations.
- **UI Prototyping**: Use the provided React frontend to give end-users a visual way to construct workflows, tweak parameters, and track reasoning steps.
- **Production-Ready**: With Pydantic for data validation and SQLAlchemy/Supabase for asynchronous persistence, the framework is built to be robust for production environments.

**For AI Coding Agents:**
- **Clear Architecture**: CLERK has strict architectural boundaries (`models.py`, `loader.py`, `graph.py`), making it straightforward for an AI to scaffold new reasoning logic, adjust database models, or create new API routes.
- **Standardized Tooling**: Uses predictable and fast tooling conventions (`uv` for Python dependency management, `pytest` for testing, and `Vite` for the frontend). Agents can quickly build, run, and verify changes reliably.
- **Structured Development Guidelines**: The framework utilizes clear typed Pydantic models and explicit naming conventions (detailed in the `AGENTS.md` guidelines) allowing agents to deterministically parse, create, and update workflows or features.

## Directory

- **General**
  - [Reasoning Kits](reasoning_kits.md)
  - [MCP](mcp.md)
  - [Integration Guide](integration.md)

- **CLI Commands**
  - [List Commands](cli/list.md)
  - [Run Commands](cli/run.md)
  - [Info Command](cli/info.md)
  - [Kit Management](cli/kit.md)
  - [Sync Commands](cli/sync.md)
  - [Database Commands](cli/db.md)
  - [Web Command](cli/web.md)

- **UI Features**
  - [Overview](ui/overview.md)
  - [Editing Kits](ui/editing_kits.md)
  - [Running Kits](ui/running_kits.md)
