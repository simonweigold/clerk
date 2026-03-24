---
phase: 02
plan: 02
plan_name: Pre-commit Hooks
phase_name: contributor-experience
status: completed
completed_at: "2026-03-24"
duration_minutes: 5
tasks_completed: 2
tasks_total: 2
files_created:
  - .pre-commit-config.yaml
files_modified:
  - CONTRIBUTING.md
commits:
  - hash: ad5881b
    message: "chore(02-02): add pre-commit configuration with Ruff and mypy"
    files:
      - .pre-commit-config.yaml
  - hash: bbf2215
    message: "docs(02-02): add pre-commit setup instructions to CONTRIBUTING.md"
    files:
      - CONTRIBUTING.md
tech_stack:
  added:
    - pre-commit
  patterns:
    - Git hooks for automated quality checks
    - UV-based tool installation
key_links:
  - from: .pre-commit-config.yaml
    to: packages/clerk/pyproject.toml
    via: Shared Ruff (v0.6.0) and mypy (v1.10.0) versions
requirements:
  - TOOL-05
---

# Phase 02 Plan 02: Pre-commit Hooks Summary

**One-liner:** Configured pre-commit hooks with Ruff linting/formatting and mypy type checking to ensure code quality before every commit.

## What Was Built

### Pre-commit Configuration (`.pre-commit-config.yaml`)

A pre-commit configuration file that runs automatically on every git commit:

- **Ruff hooks** (v0.6.0):
  - `ruff` with `--fix` argument for auto-fixing lint issues
  - `ruff-format` for consistent code formatting
- **mypy hook** (v1.10.0) for static type checking

Versions are pinned to match the project's `pyproject.toml` dev dependencies for consistency.

### Documentation Updates (`CONTRIBUTING.md`)

Added a "Pre-commit Hooks" section to the contributor documentation that covers:

1. Installation via `uv pip install pre-commit` (project-standard tooling)
2. Hook installation with `pre-commit install`
3. Optional one-time run on all files
4. What checks run automatically (Ruff and mypy)

## Key Decisions

1. **Version pinning:** Used exact versions from pyproject.toml (ruff v0.6.0, mypy v1.10.0) to ensure CI and local pre-commit use identical tool versions
2. **UV for installation:** Used `uv pip install pre-commit` instead of `pip install pre-commit` to stay consistent with project's UV-first approach
3. **Section placement:** Inserted pre-commit documentation after dev container setup but before development workflow for logical flow

## Verification

- ✅ `.pre-commit-config.yaml` exists with correct Ruff and mypy hooks
- ✅ Hook versions match pyproject.toml dev dependencies
- ✅ CONTRIBUTING.md has Pre-commit Hooks section with installation instructions
- ✅ Instructions use `uv pip install pre-commit` (project-standard tooling)

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- [x] `.pre-commit-config.yaml` exists and is valid YAML
- [x] CONTRIBUTING.md contains pre-commit documentation
- [x] Commits recorded and verified
