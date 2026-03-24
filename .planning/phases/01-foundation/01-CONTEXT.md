# Phase 01: Foundation - Context

**Gathered:** 2025-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the foundational repository structure, documentation, and developer tooling required for contributors to set up Clerk in under 5 minutes. This includes: LICENSE, README with quickstart, CONTRIBUTING.md with dev setup instructions, CODE_OF_CONDUCT.md, CHANGELOG.md, UV workspace configuration, Ruff/pytest/mypy tooling, Just task runner, dev container, and VS Code settings.

</domain>

<decisions>
## Implementation Decisions

### Documentation Structure
- **D-01:** Documentation lives in `docs/` folder with clear separation:
  - `docs/README.md` - Main entry point
  - `docs/user-guide/` - For self-hosted users
  - `docs/integration/` - For developers embedding Clerk
  - `docs/contributing/` - For contributors
  - Root README stays concise with quickstart only

### Setup Approach
- **D-02:** Use Just task runner as the primary interface
  - `just setup` - Full environment setup (dependencies, DB, config)
  - `just test` - Run all tests
  - `just lint` - Run Ruff + mypy
  - `just format` - Format code
  - `just dev` - Start development servers
- **Rationale:** Cross-platform, modern, simpler than Make, works well with UV

### Dev Container Scope
- **D-03:** Full-stack dev container including:
  - Python 3.13 with UV pre-installed
  - Node.js 20+ for frontend
  - PostgreSQL 15 for local database
  - Pre-configured VS Code extensions
- **Rationale:** Enables true zero-setup contributions; contributors can start immediately via GitHub Codespaces

### Testing Strategy
- **D-04:** pytest with coverage reporting
  - Coverage threshold: 80% for new code
  - Python versions: 3.13 (primary), 3.12 (compatibility)
  - Test command: `just test` or `pytest`
  - Async tests via pytest-asyncio

### Code Quality Gates
- **D-05:** Ruff for linting and formatting (replaces flake8, black, isort)
  - Line length: 100 characters
  - Python 3.13+ target
  - Import sorting enabled
  - mypy for type checking (strict mode)

### VS Code Configuration
- **D-06:** Pre-configured extensions:
  - Python (ms-python.python)
  - Ruff (charliermarsh.ruff)
  - ESLint (dbaeumer.vscode-eslint)
  - Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)
  - Prettier (esbenp.prettier-vscode)

### Package Naming
- **D-07:** Keep existing `openclerk` package name on PyPI
  - Already configured in pyproject.toml
  - CLI commands: `clerk` and `openclerk` (both work)

### the agent's Discretion
- License year and copyright holder details (use standard MIT template)
- Specific Ruff rule selection (use sensible defaults)
- Exact CHANGELOG categories (follow Keep a Changelog standard)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Documentation
- `.planning/PROJECT.md` — Project vision, core value, and constraints
- `.planning/REQUIREMENTS.md` — Detailed requirements with REQ-IDs
- `.planning/ROADMAP.md` — Phase boundaries and success criteria

### Research Findings
- `.planning/research/FEATURES.md` — Table stakes vs differentiators for DX
- `.planning/research/STACK.md` — Recommended tooling stack
- `.planning/research/ARCHITECTURE.md` — Architecture patterns
- `.planning/research/PITFALLS.md` — Common mistakes to avoid

### Existing Codebase
- `packages/clerk/pyproject.toml` — Existing package configuration
- `pyproject.toml` — UV workspace configuration
- `README.md` — Current documentation (to be improved)

### External Standards
- https://choosealicense.com/licenses/mit/ — MIT License text
- https://contributor-covenant.org/version/2/1/code_of_conduct/ — Code of Conduct
- https://keepachangelog.com/en/1.1.0/ — Changelog format
- https://opensource.guide/ — Open source best practices

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `packages/clerk/pyproject.toml` — Already has MIT license, dev dependencies (pytest, ruff, mypy)
- `pyproject.toml` — UV workspace already configured
- Root `README.md` — Good foundation but needs quickstart simplification
- `AGENTS.md` — Existing agent guidance (keep and enhance)

### Established Patterns
- UV for Python package management (modern replacement for pip/poetry)
- Hatchling as build backend
- Monorepo structure with packages/ and apps/
- CLI entry points via `clerk` and `openclerk` commands

### Integration Points
- CLI is in `packages/clerk/src/openclerk/cli.py`
- Frontend is in `apps/website/`
- Reasoning kits are in `reasoning_kits/` at root
- Database models likely in `packages/clerk/src/openclerk/db/`

</code_context>

<specifics>
## Specific Ideas

### README Quickstart Example
```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit

kit = load_reasoning_kit("reasoning_kits/demo")
outputs = run_reasoning_kit(kit)
print(outputs)
```

### Justfile Structure
```just
# List available commands
list:
    @just --list

# Setup development environment
setup:
    uv sync
    cd packages/clerk && uv pip install -e ".[dev]"
    cd apps/website && npm install

# Run tests
test:
    cd packages/clerk && pytest

# Run linting and type checking
lint:
    cd packages/clerk && ruff check .
    cd packages/clerk && mypy src/

# Format code
format:
    cd packages/clerk && ruff format .

# Start development servers
dev:
    just dev-backend & just dev-frontend

dev-backend:
    cd packages/clerk && uv run clerk web

dev-frontend:
    cd apps/website && npm run dev
```

### Dev Container Requirements
- Docker Compose with PostgreSQL
- Post-create command runs `just setup`
- Ports forwarded: 3000 (frontend), 8000 (backend), 5432 (database)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 1 scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2025-03-24*
