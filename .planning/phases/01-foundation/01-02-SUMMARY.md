---
phase: 01-foundation
plan: 02
name: Python Development Tooling
subsystem: tooling
tags: [ruff, pytest, mypy, just, tooling, python]
requires: []
provides: [TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-06]
affects: []
tech-stack:
  added: [ruff, pytest, mypy, pytest-cov, just]
  patterns: [pyproject.toml tool configuration, justfile task runner]
key-files:
  created:
    - Justfile
  modified:
    - packages/clerk/pyproject.toml
metrics:
  duration: 79
  completed-date: "2026-03-24"
  tasks: 3
  files-created: 1
  files-modified: 1
---

# Phase 01 Plan 02: Python Development Tooling — Summary

**One-liner:** Configured Ruff linting/formatting, pytest with 80% coverage threshold, mypy strict type checking, and Just task runner for streamlined development workflows.

## What Was Built

### Ruff Configuration (Task 1)
Added comprehensive Ruff configuration to `packages/clerk/pyproject.toml`:
- Target Python 3.13 with 100-character line length
- Enabled rules: E (pycodestyle errors), F (Pyflakes), I (isort), N (pep8-naming), W (pycodestyle warnings)
- Configured Google-style docstring convention
- Set double quotes and spaces for formatting

### pytest and mypy Configuration (Task 2)
Added testing and type checking configuration to `packages/clerk/pyproject.toml`:
- pytest with async mode, strict markers, and coverage reporting
- Coverage threshold set to 80% with branch coverage
- mypy in strict mode for Python 3.13
- Configured warnings for return types and unused configs

### Justfile Task Runner (Task 3)
Created `Justfile` in repository root with development commands:
- `just setup` — Full environment setup (uv sync, pip install, npm install)
- `just test` — Run tests with coverage reporting
- `just lint` — Run Ruff and mypy checks
- `just format` — Format code with Ruff
- `just dev` — Start both backend and frontend simultaneously
- `just dev-backend` — Start backend server only
- `just dev-frontend` — Start frontend dev server only
- `just clean` — Remove build artifacts and caches

## Deviations from Plan

None — plan executed exactly as written.

## Decisions Made

No new decisions required — configuration followed established patterns from 01-RESEARCH.md.

## Verification Results

All success criteria verified:
- ✅ `[tool.ruff]` section present in pyproject.toml
- ✅ `line-length = 100` configured
- ✅ `[tool.pytest.ini_options]` section present
- ✅ `fail_under = 80` coverage threshold set
- ✅ `[tool.mypy]` section present with `strict = true`
- ✅ Justfile created with all required commands

## Auth Gates

None encountered.

## Commits

| Commit | Description |
|--------|-------------|
| 61c66bf | chore(01-02): configure Ruff linting and formatting |
| 221495e | chore(01-02): configure pytest and mypy |
| c35acae | chore(01-02): add Justfile with development commands |

## Self-Check: PASSED

- ✅ packages/clerk/pyproject.toml exists and contains [tool.ruff]
- ✅ packages/clerk/pyproject.toml contains [tool.pytest.ini_options]
- ✅ packages/clerk/pyproject.toml contains [tool.mypy]
- ✅ Justfile exists in repository root
- ✅ All commits recorded and verified
