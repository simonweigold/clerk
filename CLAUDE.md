<!-- GSD:project-start source:PROJECT.md -->
## Project

**Clerk — Developer Experience Enhancement**

Clerk is a Python framework for multi-step LLM reasoning workflows with a React frontend. This project aims to transform Clerk from a solo-developed tool into an open-source project with excellent developer experience, comprehensive onboarding, and flexible deployment options (self-hosted or embedded in existing applications).

**Core Value:** Developers can set up Clerk in under 5 minutes and contribute meaningfully in under 1 hour, regardless of whether they're self-hosting, embedding, or contributing to the core framework.

### Constraints

- **Tech Stack**: Python 3.13+, UV, LangChain/LangGraph, React 19, TypeScript, Tailwind
- **Timeline**: Aggressive — open source launch target
- **Dependencies**: Must remain compatible with existing LangChain ecosystem
- **Compatibility**: Existing reasoning kits must continue to work
- **Documentation**: Must be excellent from day one (no "docs coming soon")
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Executive Summary
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
## Installation
### One-Time Setup (Project Initialization)
# Install UV (if not already installed)
# Install global development tools
# Install pre-commit hooks manager
### Project Dependencies (pyproject.toml)
### Quick Install Commands
# Install all dependencies including dev group
# Install only production dependencies
# Run linting
# Run type checking
# Run tests
# Run all quality checks
## Configuration Files
### pyproject.toml (Centralized Config)
### .pre-commit-config.yaml
### justfile
# Default recipe - show available commands
# Install development environment
# Run all quality checks
# Run linting
# Fix auto-fixable linting issues
# Run type checking
# Run tests
# Run tests with coverage
# Serve documentation locally
# Build documentation
# Deploy documentation (maintainers only)
# Clean build artifacts
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
## Version Compatibility Matrix
| Tool | Python 3.13 | Python 3.14 (dev) | Notes |
|------|-------------|-------------------|-------|
| UV 0.6.x | ✅ | ✅ | Full support |
| Ruff 0.11.x | ✅ | ✅ | Target py313 works |
| pytest 8.3.x | ✅ | ✅ | asyncio support confirmed |
| mypy 1.15.x | ✅ | ⚠️ | Check for 3.14 support |
| pre-commit 4.x | ✅ | ✅ | No issues |
| commitizen 4.x | ✅ | ✅ | Python 3.10+ required |
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
## Roadmap Implications
- UV is already partially in use — expand to full project management
- Ruff replaces any existing linting (Flake8, Black)
- Just provides contributor-friendly task commands
- MkDocs Material provides professional documentation site
- Semantic-release automates versioning based on conventional commits
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
