# Phase 01: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2025-03-24
**Phase:** 01-Foundation
**Areas discussed:** Documentation structure, Setup approach, Dev container scope, Testing strategy, Code quality gates, VS Code configuration, Package naming

---

## Documentation Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Centralized docs/ folder | Clear separation of user/integration/contributor docs | ✓ |
| README-only | Keep everything in root README | |
| Wiki approach | Use GitHub wiki for docs | |

**User's choice:** Centralized docs/ folder with progressive disclosure
**Notes:** Root README should stay concise (quickstart only), detailed docs in docs/ folder

---

## Setup Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Just task runner | Modern, cross-platform, works with UV | ✓ |
| Make | Traditional but macOS/Linux only | |
| npm scripts | JavaScript ecosystem tool | |
| Shell scripts | Platform-specific issues | |

**User's choice:** Just task runner
**Notes:** Primary command is `just setup` for full environment setup

---

## Dev Container Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full stack | Backend + frontend + PostgreSQL | ✓ |
| Backend only | Python environment only | |
| Minimal | Just Python + UV | |

**User's choice:** Full stack with PostgreSQL
**Notes:** Enables zero-setup contributions via GitHub Codespaces

---

## Testing Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| pytest with 80% coverage | Standard Python testing | ✓ |
| unittest | Built-in but less featured | |
| No coverage requirement | Simpler but less quality assurance | |

**User's choice:** pytest with 80% coverage threshold
**Notes:** Python 3.13 primary, 3.12 for compatibility

---

## Code Quality Gates

| Option | Description | Selected |
|--------|-------------|----------|
| Ruff (all-in-one) | Linting + formatting + import sorting | ✓ |
| Black + flake8 + isort | Multiple tools, more config | |
| No enforcement | Manual code review only | |

**User's choice:** Ruff for everything, mypy for type checking
**Notes:** Line length 100, Python 3.13+ target

---

## VS Code Configuration

| Extension | Purpose | Selected |
|-----------|---------|----------|
| Python (ms-python.python) | Core Python support | ✓ |
| Ruff (charliermarsh.ruff) | Linting integration | ✓ |
| ESLint (dbaeumer.vscode-eslint) | Frontend linting | ✓ |
| Tailwind CSS IntelliSense | Frontend styling | ✓ |
| Prettier | Code formatting | ✓ |

**User's choice:** All listed extensions pre-configured
**Notes:** Settings should include format-on-save, Ruff as default formatter

---

## Package Naming

| Option | Description | Selected |
|--------|-------------|----------|
| Keep openclerk | Already configured in pyproject.toml | ✓ |
| Rename to clerk | Shorter but may conflict | |
| ClerkFramework | More descriptive | |

**User's choice:** Keep existing `openclerk` package name
**Notes:** Both `clerk` and `openclerk` CLI commands work

---

## the agent's Discretion

- License year and copyright holder details
- Specific Ruff rule selection  
- Exact CHANGELOG categories

## Deferred Ideas

None — discussion stayed within Phase 1 scope.
