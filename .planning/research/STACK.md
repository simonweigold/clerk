# Technology Stack: Developer Experience Tooling

**Project:** Clerk — Developer Experience Enhancement
**Domain:** Open-source Python LLM workflow framework
**Researched:** 2025-03-24
**Confidence:** HIGH (based on official docs, current versions verified)

## Executive Summary

The 2025 standard for Python developer experience tooling is dominated by **Astral** (the creators of Ruff and UV) and established tools like pytest and mypy. For Clerk's transformation into an open-source project, the stack should prioritize:

1. **Speed** — Tools that run fast enough to be used in pre-commit hooks and CI
2. **Unified Configuration** — Single `pyproject.toml` for all tools
3. **Contributor Accessibility** — Low-friction onboarding for new contributors
4. **Modern Python Standards** — PEP-compliant, actively maintained tools

---

## Recommended Stack

### Core Tooling (Required)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **UV** | 0.6.x | Package manager, virtual env, Python version management | Replaces pip/pip-tools/poetry/pipx with 10-100x faster resolution; universal lockfile support; Astral-backed with rapid development | HIGH |
| **Ruff** | 0.11.x | Linter and formatter | Replaces Flake8, Black, isort, pydocstyle with 10-100x speed; 800+ built-in rules; used by FastAPI, Pandas, Airflow | HIGH |
| **pytest** | 8.3.x | Testing framework | Industry standard; 1300+ plugins; superior failure reporting; native asyncio support via pytest-asyncio | HIGH |
| **mypy** | 1.15.x+ | Static type checking | De facto standard for Python type checking; gradual typing support; strong ecosystem compatibility | HIGH |

### Development Workflow (Required)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **pre-commit** | 4.x | Git hooks framework | Multi-language hook management; auto-installs dependencies; CI integration; prevents bad commits | HIGH |
| **commitizen** | 4.x | Conventional commits, changelog, versioning | Python-native; generates changelogs; enforces commit standards; integrates with pre-commit | HIGH |
| **Just** | 1.x | Task runner | Modern Make alternative; cross-platform; shell-agnostic; `.env` support; self-documenting | HIGH |
| **coverage.py** | 7.6.x+ | Code coverage measurement | Standard coverage tool; pytest integration; HTML/XML/LCOV reports; branch coverage | HIGH |

### Documentation (Required)

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **MkDocs** | 1.6.x+ | Static site generator for docs | Markdown-based; Material theme available; plugin ecosystem; GitHub Pages deployment | HIGH |
| **MkDocs Material** | 9.x | Documentation theme | Beautiful, responsive design; search; dark mode; versioning support | HIGH |
| **mike** | 2.x | Versioned documentation | Deploy multiple doc versions; essential for library projects | MEDIUM |

### CI/CD (Required)

| Technology | Version/Config | Purpose | Why Recommended | Confidence |
|------------|----------------|---------|-----------------|------------|
| **GitHub Actions** | Latest | CI/CD automation | Native GitHub integration; free for open source; matrix builds; OIDC for PyPI | HIGH |
| **semantic-release** | 24.x | Automated versioning/releases | Conventional commit-based; automatic changelog; GitHub releases; PyPI publishing | HIGH |

### Supporting Libraries (Recommended)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest-asyncio** | 0.25.x+ | Async test support | Required for testing async SQLAlchemy, LangGraph workflows |
| **pytest-cov** | 6.x | Coverage integration | Convenient coverage with pytest; may use coverage.py directly instead |
| **httpx** | 0.28.x+ | HTTP client for tests | Modern requests alternative; async support; type hints |
| **respx** | 0.22.x+ | HTTPX mocking | Mock HTTP calls in tests; essential for external API testing |
| **factory-boy** | 3.3.x+ | Test data factories | Create test fixtures; SQLAlchemy integration available |
| **freezegun** | 1.5.x+ | Time mocking | Freeze time in tests; useful for timestamp-dependent workflows |

---

## Installation

### One-Time Setup (Project Initialization)

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install global development tools
uv tool install commitizen
uv tool install rust-just  # via PyPI wrapper

# Install pre-commit hooks manager
uv tool install pre-commit
```

### Project Dependencies (pyproject.toml)

```toml
[project]
name = "clerk"
version = "0.1.0"
description = "Multi-step LLM reasoning workflows"
requires-python = ">=3.13"
dependencies = [
    "langchain>=0.3.0",
    "langgraph>=0.2.0",
    "pydantic>=2.0",
    "sqlalchemy[asyncio]>=2.0",
    # ... other runtime deps
]

[dependency-groups]
dev = [
    # Core tooling
    "ruff>=0.11.0",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
    "mypy>=1.15.0",
    "coverage>=7.6.0",
    "pre-commit>=4.0",
    
    # Testing utilities
    "httpx>=0.28.0",
    "respx>=0.22.0",
    "factory-boy>=3.3.0",
    "freezegun>=1.5.0",
    
    # Documentation
    "mkdocs>=1.6.0",
    "mkdocs-material>=9.0",
    "mike>=2.0",
]
```

### Quick Install Commands

```bash
# Install all dependencies including dev group
uv sync

# Install only production dependencies
uv sync --no-dev

# Run linting
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .

# Run type checking
uv run mypy src/

# Run tests
uv run pytest
uv run pytest --cov=src --cov-report=html

# Run all quality checks
just check  # via justfile
```

---

## Configuration Files

### pyproject.toml (Centralized Config)

```toml
[tool.ruff]
target-version = "py313"
line-length = 100
select = [
    "E",   # pycodestyle errors
    "F",   # Pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
    "TCH", # flake8-type-checking
    "TID", # flake8-tidy-imports
    "RUF", # Ruff-specific rules
]
ignore = ["E501"]  # Line length handled by formatter

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
show_error_codes = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict]

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.0.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

### justfile

```makefile
# Default recipe - show available commands
default:
    @just --list

# Install development environment
install:
    uv sync
    pre-commit install
    pre-commit install --hook-type commit-msg

# Run all quality checks
check: lint type test

# Run linting
lint:
    uv run ruff check .
    uv run ruff format --check .

# Fix auto-fixable linting issues
lint-fix:
    uv run ruff check --fix .
    uv run ruff format .

# Run type checking
type:
    uv run mypy src/

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=html
    @echo "Coverage report: htmlcov/index.html"

# Serve documentation locally
docs:
    uv run mkdocs serve

# Build documentation
docs-build:
    uv run mkdocs build

# Deploy documentation (maintainers only)
docs-deploy:
    uv run mike deploy --push --update-aliases $(git describe --tags --abbrev=0) latest

# Clean build artifacts
clean:
    rm -rf .venv
    rm -rf .pytest_cache
    rm -rf .ruff_cache
    rm -rf htmlcov
    rm -rf .mypy_cache
    rm -rf site
    rm -rf dist
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
```

---

## Alternatives Considered

| Category | Recommended | Alternative | When Alternative Makes Sense |
|----------|-------------|-------------|------------------------------|
| Package Manager | **UV** | Poetry | Poetry has wider ecosystem support; use if team already familiar |
| Linter/Formatter | **Ruff** | Black + Flake8 | If you need plugins not yet in Ruff (rare) |
| Type Checker | **mypy** | pyright | Pyright is faster; use for very large codebases |
| Task Runner | **Just** | Make | Make is ubiquitous; use if avoiding new dependencies |
| Task Runner | **Just** | Invoke (Python) | Use Invoke for complex Python-based task logic |
| Commit Standards | **commitizen** | commitlint (JS) | commitlint has more rules; use if already in JS ecosystem |
| Docs | **MkDocs** | Sphinx | Sphinx is better for API docs; use for complex reference docs |
| CI/CD | **GitHub Actions** | GitLab CI | Use GitLab CI if self-hosting on GitLab |

---

## What NOT to Use

| Avoid | Why Not | Use Instead |
|-------|---------|-------------|
| **pip + requirements.txt** | No lockfile, slow resolution, no workspace support | UV with uv.lock |
| **setup.py** | Deprecated; use pyproject.toml | pyproject.toml with hatchling/uv build |
| **Black** (standalone) | Ruff's formatter is Black-compatible and 10x faster | Ruff format |
| **Flake8** | Ruff replaces all plugins with native rules | Ruff lint |
| **isort** | Ruff handles import sorting natively | Ruff organize imports |
| **pylint** | Slower, more false positives; Ruff covers most rules | Ruff + mypy |
| **tox** | UV environments are faster and simpler | UV workspaces + GitHub Actions matrix |
| **Makefile** | Windows compatibility issues, tab sensitivity | Just |
| **setuptools** | Complex, legacy baggage | hatchling (PEP 517) or uv build |

---

## Version Compatibility Matrix

| Tool | Python 3.13 | Python 3.14 (dev) | Notes |
|------|-------------|-------------------|-------|
| UV 0.6.x | ✅ | ✅ | Full support |
| Ruff 0.11.x | ✅ | ✅ | Target py313 works |
| pytest 8.3.x | ✅ | ✅ | asyncio support confirmed |
| mypy 1.15.x | ✅ | ⚠️ | Check for 3.14 support |
| pre-commit 4.x | ✅ | ✅ | No issues |
| commitizen 4.x | ✅ | ✅ | Python 3.10+ required |

---

## Sources

| Source | URL | Confidence | Notes |
|--------|-----|------------|-------|
| Ruff Docs | https://docs.astral.sh/ruff/ | HIGH | Official; v0.11.x current |
| UV Docs | https://docs.astral.sh/uv/ | HIGH | Official; v0.6.x current |
| pytest Docs | https://docs.pytest.org/ | HIGH | Official; v8.3.x current |
| mypy Docs | https://mypy.readthedocs.io/ | HIGH | Official; v1.15.x current |
| pre-commit Docs | https://pre-commit.com/ | HIGH | Official; v4.x current |
| commitizen Docs | https://commitizen-tools.github.io/commitizen/ | HIGH | Official; v4.x current |
| Just GitHub | https://github.com/casey/just | HIGH | Official; v1.x stable |
| Coverage.py Docs | https://coverage.readthedocs.io/ | HIGH | Official; v7.6.x current |
| MkDocs | https://www.mkdocs.org/ | HIGH | Official; v1.6.x current |
| Hatch PyPI | https://pypi.org/project/hatch/ | MEDIUM | Verified versions |

---

## Roadmap Implications

For Clerk's DX enhancement phases:

1. **Phase 1 (Foundation)**: Implement UV + Ruff + pytest + mypy configuration
2. **Phase 2 (Workflow)**: Add pre-commit, commitizen, Just task runner
3. **Phase 3 (Documentation)**: Setup MkDocs Material with versioning
4. **Phase 4 (CI/CD)**: GitHub Actions workflows with semantic-release

**Key Decisions for Implementation:**
- UV is already partially in use — expand to full project management
- Ruff replaces any existing linting (Flake8, Black)
- Just provides contributor-friendly task commands
- MkDocs Material provides professional documentation site
- Semantic-release automates versioning based on conventional commits

---

*Research completed: 2025-03-24*
*Next review: After UV 0.7 or Ruff 0.12 major releases*
