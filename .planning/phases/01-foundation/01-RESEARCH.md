# Phase 01: Foundation - Research

**Researched:** 2025-03-24
**Domain:** Developer Experience (DX) - Documentation, Tooling, Dev Environment
**Confidence:** HIGH

## Summary

Phase 01 establishes the foundational infrastructure for Clerk as a contributor-ready open-source project. This phase focuses on three pillars: **documentation** (LICENSE, README, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG), **developer tooling** (UV, Ruff, pytest, mypy, Just), and **zero-setup development environment** (Dev Container, VS Code settings).

The project already has a solid foundation with UV workspace configuration, Python package structure, and basic README. The work in this phase is primarily additive—creating missing documentation files, configuring tools properly, and setting up the dev container for seamless onboarding.

**Primary recommendation:** Build upon existing UV/Ruff/pytest setup, use Just as the task runner interface (not Make), and create a full-stack dev container with PostgreSQL for true zero-setup contributions.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Documentation Structure (D-01):** `docs/` folder with clear separation:
  - `docs/README.md` - Main entry point
  - `docs/user-guide/` - For self-hosted users
  - `docs/integration/` - For developers embedding Clerk
  - `docs/contributing/` - For contributors
  - Root README stays concise with quickstart only

- **Setup Approach (D-02):** Use Just task runner as the primary interface
  - `just setup` - Full environment setup
  - `just test` - Run all tests
  - `just lint` - Run Ruff + mypy
  - `just format` - Format code
  - `just dev` - Start development servers
  - Rationale: Cross-platform, modern, simpler than Make, works well with UV

- **Dev Container Scope (D-03):** Full-stack dev container including:
  - Python 3.13 with UV pre-installed
  - Node.js 20+ for frontend
  - PostgreSQL 15 for local database
  - Pre-configured VS Code extensions

- **Testing Strategy (D-04):** pytest with coverage reporting
  - Coverage threshold: 80% for new code
  - Python versions: 3.13 (primary), 3.12 (compatibility)
  - Test command: `just test` or `pytest`
  - Async tests via pytest-asyncio

- **Code Quality Gates (D-05):** Ruff for linting and formatting (replaces flake8, black, isort)
  - Line length: 100 characters
  - Python 3.13+ target
  - Import sorting enabled
  - mypy for type checking (strict mode)

- **VS Code Configuration (D-06):** Pre-configured extensions:
  - Python (ms-python.python)
  - Ruff (charliermarsh.ruff)
  - ESLint (dbaeumer.vscode-eslint)
  - Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)
  - Prettier (esbenp.prettier-vscode)

- **Package Naming (D-07):** Keep existing `openclerk` package name on PyPI
  - Already configured in pyproject.toml
  - CLI commands: `clerk` and `openclerk` (both work)

### the agent's Discretion
- License year and copyright holder details (use standard MIT template)
- Specific Ruff rule selection (use sensible defaults)
- Exact CHANGELOG categories (follow Keep a Changelog standard)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within Phase 1 scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOCS-01 | Repository has MIT LICENSE file in root directory | Standard MIT license template from choosealicense.com |
| DOCS-02 | README includes clear value proposition and 5-line example | Existing README has good foundation; needs quickstart simplification per D-01 |
| DOCS-03 | README includes working installation instructions (verified on clean system) | UV-based installation via `uv sync` and `uv pip install -e ".[dev]"` |
| DOCS-04 | CONTRIBUTING.md exists with step-by-step dev environment setup | Use Just commands (D-02) as primary setup path; include dev container option |
| DOCS-05 | CODE_OF_CONDUCT.md uses Contributor Covenant standard | Version 2.1 from contributor-covenant.org |
| DOCS-06 | CHANGELOG.md follows Keep a Changelog format | Version 1.1.0 format; categories: Added, Changed, Deprecated, Removed, Fixed, Security |
| TOOL-01 | UV workspace configured for Python dependency management | Already configured in root pyproject.toml; workspace members = ["packages/*"] |
| TOOL-02 | Ruff configured for linting and formatting in pyproject.toml | Configure in `[tool.ruff]` with line-length=100, target-version="py313" |
| TOOL-03 | pytest configured with coverage reporting | Configure in `[tool.pytest]` with pytest-cov for coverage; 80% threshold |
| TOOL-04 | mypy configured for type checking | Configure in `[tool.mypy]` with strict=true |
| TOOL-06 | Just task runner configured for common commands (test, lint, format) | Justfile with recipes: setup, test, lint, format, dev, dev-backend, dev-frontend |
| TOOL-07 | Dev container configuration enables zero-setup contributions | Docker Compose with PostgreSQL, Python 3.13, Node.js 20+; post-create runs `just setup` |
| TOOL-08 | VS Code settings/extensions configured for the project | .vscode/extensions.json and .vscode/settings.json per D-06 |
</phase_requirements>

---

## Standard Stack

### Core Developer Tools
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| UV | 0.9.5+ | Python package management | Modern replacement for pip/poetry; fast; lockfile support; workspace-native |
| Just | 1.x | Task runner | Cross-platform; modern syntax; simpler than Make; works well with UV |
| Ruff | 0.6.0+ | Linting & formatting | Replaces flake8, black, isort; extremely fast; unified toolchain |
| pytest | 8.0.0+ | Testing | Standard Python testing framework; async support via pytest-asyncio |
| mypy | 1.10.0+ | Type checking | Standard Python static type checker; strict mode for quality |
| pytest-cov | 5.x | Coverage reporting | pytest plugin for coverage; 80% threshold enforcement |

### Dev Container Stack
| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.13 | Primary runtime |
| Node.js | 20+ | Frontend development |
| PostgreSQL | 15 | Local database |
| UV | 0.9.5+ | Python package management |

### VS Code Extensions (Pre-configured)
| Extension | ID | Purpose |
|-----------|-----|---------|
| Python | ms-python.python | Python language support |
| Ruff | charliermarsh.ruff | Linting and formatting |
| ESLint | dbaeumer.vscode-eslint | JavaScript/TypeScript linting |
| Tailwind CSS IntelliSense | bradlc.vscode-tailwindcss | Tailwind autocomplete |
| Prettier | esbenp.prettier-vscode | Code formatting |

### Installation Commands
```bash
# Install Just (macOS)
brew install just

# Install Just (Linux)
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash

# All Python tools installed via UV
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy
```

---

## Architecture Patterns

### Documentation Structure Pattern
```
docs/
├── README.md                 # Main documentation entry
├── user-guide/              # Self-hosted users
│   ├── getting-started.md
│   └── configuration.md
├── integration/             # Developers embedding Clerk
│   ├── fastapi.md
│   └── embedding.md
└── contributing/            # Contributors
    ├── setup.md
    └── guidelines.md
```

### Root README Pattern (Concise)
```markdown
# OpenClerk

[![PyPI](https://img.shields.io/pypi/v/openclerk.svg)](https://pypi.org/project/openclerk/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> Community Library of Executable Reasoning Kits

## Quickstart

```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit

kit = load_reasoning_kit("reasoning_kits/demo")
outputs = run_reasoning_kit(kit)
```

## Installation

```bash
pip install openclerk
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.
```

### Justfile Pattern
```justfile
# List available commands
list:
    @just --list

# Setup development environment
setup:
    uv sync
    cd packages/clerk && uv pip install -e ".[dev]"
    cd apps/website && npm install

# Run tests with coverage
test:
    cd packages/clerk && pytest --cov=src/openclerk --cov-report=term-missing

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

### Dev Container Pattern (Docker Compose)
```yaml
# .devcontainer/docker-compose.yml
version: '3.8'
services:
  app:
    build:
      context: ..
      dockerfile: .devcontainer/Dockerfile
    volumes:
      - ..:/workspace:cached
    command: sleep infinity
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: clerk
      POSTGRES_PASSWORD: clerk
      POSTGRES_DB: clerk
    ports:
      - "5432:5432"
```

### Ruff Configuration Pattern
```toml
[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # Pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### pytest Configuration Pattern
```toml
[tool.pytest]
minversion = "8.0"
addopts = "-ra -q --strict-markers --cov=openclerk --cov-report=term-missing"
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src/openclerk"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### mypy Configuration Pattern
```toml
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
```

### Anti-Patterns to Avoid
- **Don't use Make:** Just is modern, cross-platform, and simpler
- **Don't split Ruff config:** Keep in pyproject.toml `[tool.ruff]` section
- **Don't commit .venv:** Already in .gitignore; use UV's workspace isolation
- **Don't hardcode ports in dev:** Use environment variables with defaults
- **Don't require global tool installation:** All tools via UV or Just

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Task runner | Make/Shell scripts | Just | Cross-platform, modern syntax, no .PHONY needed |
| Python linting | flake8 + black + isort | Ruff | Unified toolchain, 10-100x faster, compatible |
| CHANGELOG format | Git log dumps | Keep a Changelog | Human-readable, categorized, versioned |
| Code of Conduct | Custom text | Contributor Covenant v2.1 | Community standard, legally reviewed |
| Dev environment | Manual setup docs | Dev Container | Zero setup, reproducible, GitHub Codespaces ready |
| Type checking | Runtime checks only | mypy strict | Catch errors early, IDE support, documentation |

---

## Common Pitfalls

### Pitfall 1: Line Length Conflicts
**What goes wrong:** Ruff linter (E501) and formatter disagree on line length
**Why it happens:** Formatter wraps at 88, linter complains at 88
**How to avoid:** Set `line-length = 100` in `[tool.ruff]` and ignore E501 in lint rules
**Warning signs:** CI fails with "line too long" after formatting

### Pitfall 2: Missing pytest-cov
**What goes wrong:** Coverage reporting doesn't work despite pytest config
**Why it happens:** pytest-cov not installed as dev dependency
**How to avoid:** Add `pytest-cov>=5.0.0` to dev dependencies in pyproject.toml
**Warning signs:** `--cov` flag unrecognized by pytest

### Pitfall 3: Dev Container Port Binding
**What goes wrong:** Services inside container not accessible from host
**Why it happens:** Binding to 127.0.0.1 instead of 0.0.0.0 inside container
**How to avoid:** Configure FastAPI/frontend to bind to 0.0.0.0 in dev mode
**Warning signs:** "Connection refused" when accessing forwarded ports

### Pitfall 4: UV Workspace Path Issues
**What goes wrong:** `uv sync` fails or installs wrong package versions
**Why it happens:** Running from subdirectory instead of workspace root
**How to avoid:** Always run `uv sync` from repo root; use `cd packages/clerk && uv pip install` for editable installs
**Warning signs:** Import errors, wrong package versions installed

### Pitfall 5: Async Test Failures
**What goes wrong:** pytest-asyncio tests fail with event loop errors
**Why it happens:** Missing `asyncio_mode = "auto"` in pytest config
**How to avoid:** Add explicit asyncio_mode configuration
**Warning signs:** "Event loop is closed" errors in test output

### Pitfall 6: mypy Strict Mode Shock
**What goes wrong:** mypy reports hundreds of errors on existing codebase
**Why it happens:** Strict mode enabled on untyped legacy code
**How to avoid:** Add `# type: ignore` comments for legacy, require types for new code
**Warning signs:** CI fails immediately after adding mypy

---

## Code Examples

### Justfile Complete Example
```just
set dotenv-load

# Default recipe - list all commands
default:
    @just --list

# Setup development environment
setup:
    #!/usr/bin/env bash
    echo "Setting up Clerk development environment..."
    uv sync
    cd packages/clerk && uv pip install -e ".[dev]"
    cd apps/website && npm install
    echo "Setup complete! Run 'just dev' to start development."

# Run all tests with coverage
test:
    cd packages/clerk && pytest --cov=src/openclerk --cov-report=term-missing

# Run linting
lint:
    cd packages/clerk && ruff check src/ tests/
    cd packages/clerk && mypy src/
    cd apps/website && npm run lint

# Format all code
format:
    cd packages/clerk && ruff format .
    cd apps/website && npx prettier --write .

# Start full development environment
dev:
    #!/usr/bin/env bash
    trap "kill %1 %2 2>/dev/null || true" EXIT
    just dev-backend &
    just dev-frontend &
    wait

# Start backend only
dev-backend:
    cd packages/clerk && uv run clerk web --host 0.0.0.0

# Start frontend only
dev-frontend:
    cd apps/website && npm run dev

# Clean build artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name .pytest_cache -exec rm -rf {} +
    find . -type d -name .mypy_cache -exec rm -rf {} +
    find . -type d -name .ruff_cache -exec rm -rf {} +
    find . -type d -name node_modules -path "*/website/*" -exec rm -rf {} +
    find . -type d -name dist -exec rm -rf {} +
```

### Dev Container Configuration
```json
// .devcontainer/devcontainer.json
{
  "name": "Clerk Development",
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace",
  "features": {
    "ghcr.io/devcontainers/features/common-utils:2": {
      "installZsh": true,
      "configureZshAsDefaultShell": true
    },
    "ghcr.io/devcontainers/features/node:1": {
      "version": "20"
    }
  },
  "postCreateCommand": "just setup",
  "forwardPorts": [3000, 8000, 5432],
  "portsAttributes": {
    "3000": { "label": "Frontend" },
    "8000": { "label": "Backend API" },
    "5432": { "label": "PostgreSQL" }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "charliermarsh.ruff",
        "dbaeumer.vscode-eslint",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode"
      ]
    }
  }
}
```

### VS Code Settings
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.typeCheckingMode": "strict",
  "ruff.organizeImports": true,
  "ruff.fixAll": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.ruff": "explicit",
    "source.organizeImports.ruff": "explicit"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### MIT License Template
```
MIT License

Copyright (c) 2025 OpenClerk Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Make | Just | 2020+ | Simpler syntax, cross-platform, no .PHONY |
| flake8 + black + isort | Ruff | 2022+ | 10-100x faster, unified config |
| pip / poetry | UV | 2024+ | 10-100x faster, built-in workspace support |
| setup.py | pyproject.toml | PEP 621 | Standardized, simpler |
| Manual setup | Dev Containers | 2022+ | Zero setup, reproducible environments |

**Deprecated/outdated:**
- setup.py: Use pyproject.toml with hatchling/flit
- requirements.txt: Use UV lockfile (uv.lock)
- Tox: Use Just + UV for task running
- pip-tools: Use UV (better lockfile, faster)

---

## Open Questions

1. **License copyright holder**
   - What we know: MIT license requires copyright notice
   - What's unclear: Is "OpenClerk Contributors" sufficient, or should it be specific individuals/organizations?
   - Recommendation: Use "OpenClerk Contributors" for community-driven project

2. **Ruff rule selection**
   - What we know: Ruff has 500+ rules available
   - What's unclear: Which specific rules beyond defaults should be enabled?
   - Recommendation: Start with E, F, I, N, W; add others as team identifies needs

3. **Test directory structure**
   - What we know: No tests/ directory exists yet in packages/clerk
   - What's unclear: Should tests be in `tests/` or `src/openclerk/tests/`?
   - Recommendation: Use `packages/clerk/tests/` (separate from source)

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| UV | Python deps | ✓ | 0.9.5 | pip (slower) |
| Python | Runtime | ✓ | 3.13 | — |
| Node.js | Frontend | ✓ | 25.6.1 | — |
| npm | Frontend | ✓ | 11.9.0 | — |
| Docker | Dev container | ✓ | 28.3.3 | manual setup |
| Just | Task runner | ✗ | — | Use `make` temporarily |
| PostgreSQL | Database | ✗ | — | Use SQLite or Supabase |

**Missing dependencies with no fallback:**
- None (Just can be installed via brew/curl; PostgreSQL optional for Phase 1)

**Missing dependencies with fallback:**
- Just: Can use Make temporarily, but should install Just
- PostgreSQL: Can use SQLite for local dev, Supabase for cloud

---

## Validation Architecture

> Validation is **DISABLED** in config (`nyquist_validation: false`). This section is skipped per configuration.

---

## Sources

### Primary (HIGH confidence)
- [Just Manual](https://just.systems/man/en/) - Task runner syntax and features
- [Ruff Configuration](https://docs.astral.sh/ruff/configuration/) - Ruff config options
- [mypy Configuration](https://mypy.readthedocs.io/en/stable/config_file.html) - mypy strict mode settings
- [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) - CHANGELOG format standard
- [Dev Container Spec](https://containers.dev/implementors/json_reference/) - devcontainer.json reference
- [pytest Configuration](https://docs.pytest.org/en/stable/reference/customize.html) - pytest config file formats

### Secondary (MEDIUM confidence)
- [MIT License Template](https://choosealicense.com/licenses/mit/) - License text
- [Contributor Covenant v2.1](https://contributor-covenant.org/version/2/1/code_of_conduct/) - Code of Conduct template

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official docs and current versions verified
- Architecture: HIGH - Based on existing project structure
- Pitfalls: MEDIUM-HIGH - Based on common patterns, some from experience

**Research date:** 2025-03-24
**Valid until:** 2025-06-24 (90 days for stable tooling)

---

*Phase: 01-foundation*
*Research completed: 2025-03-24*
