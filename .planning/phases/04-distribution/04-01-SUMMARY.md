---
phase: 04-distribution
plan: "01"
subsystem: setup
requires: []
provides:
  - one-command-setup
  - single-command-dev-start
  - pypi-ready-metadata
affects:
  - new-contributor-onboarding
  - developer-workflow
tech-stack:
  added:
    - bash (setup script)
    - concurrently (npm package)
  patterns:
    - cross-platform-shell-script
    - npm-workspace-scripts
    - modern-pyproject-toml
key-files:
  created:
    - scripts/setup.sh
    - package.json
  modified:
    - packages/clerk/pyproject.toml
    - .env.example
decisions: []
metrics:
  tasks_completed: 4
  files_created: 2
  files_modified: 2
  setup_time_target: "< 5 minutes"
---

# Phase 04 Plan 01: Setup Automation & PyPI Configuration Summary

**One-liner:** One-command setup script with cross-platform support, root dev command using concurrently, and PyPI-ready package metadata.

## What Was Built

### 1. Cross-Platform Setup Script (`scripts/setup.sh`)

A comprehensive bash script that enables "under 5 minutes" setup:

- **Prerequisites check:** Validates Python 3.13+, Node 20+, UV installation
- **Auto-install UV:** Attempts to install UV if missing
- **Dependency installation:**
  - Python: `uv sync` in packages/clerk/
  - Frontend: `npm install` in apps/website/
- **Environment setup:** Copies `.env.example` to `.env` if missing
- **Database initialization:** Runs `clerk db setup` automatically
- **Help system:** `--help` flag with usage documentation
- **Error handling:** Clear error messages, exits on failures
- **Options:** `--skip-db` and `--skip-env` flags for flexibility

### 2. Root Package.json with Dev Command

Single-command development environment startup:

```json
{
  "scripts": {
    "dev": "concurrently \"npm:dev:backend\" \"npm:dev:frontend\" --names \"API,UI\" --prefix-colors \"blue,green\"",
    "dev:backend": "cd packages/clerk && uv run clerk web --port 8000",
    "dev:frontend": "cd apps/website && npm run dev"
  }
}
```

- Backend and frontend run in parallel with colored prefixes
- Blue for API (backend), Green for UI (frontend)
- Additional convenience scripts: `setup`, `build`, `lint`

### 3. PyPI-Ready Package Metadata

Updated `packages/clerk/pyproject.toml`:

- **Package name:** `openclerk` per D-01
- **License:** MIT with license-files reference (PEP 639)
- **Classifiers:**
  - Development Status :: 3 - Alpha
  - Intended Audience :: Developers
  - License :: OSI Approved :: MIT License
  - Programming Language :: Python :: 3.13
  - Topic :: Scientific/Engineering :: Artificial Intelligence
- **Project URLs:** Homepage, Documentation, Repository, Issues
- **Build system:** Hatchling configured

### 4. Environment Template

Reorganized `.env.example` with:

- **Required variables:** OPENAI_API_KEY, SECRET_KEY
- **Database:** DATABASE_URL with clear format examples
- **Supabase:** Optional cloud database configuration
- **Frontend:** VITE_API_URL for build-time variables
- **Application:** LOG_LEVEL, CLERK_SESSION_SECRET
- **Categories:** Clear REQUIRED vs OPTIONAL sections
- **Quick start:** Step-by-step getting started guide

## Artifacts Delivered

| Artifact | Path | Purpose |
|----------|------|---------|
| Setup script | `scripts/setup.sh` | One-command dependency installation |
| Root package.json | `package.json` | Single command dev environment start |
| PyPI metadata | `packages/clerk/pyproject.toml` | Package publishing readiness |
| Environment template | `.env.example` | Environment variable documentation |

## Requirements Satisfied

- ✓ **SETUP-01:** New user can run `./scripts/setup.sh` to install all dependencies
- ✓ **SETUP-03:** Developer can run `npm run dev` to start full environment
- ✓ Package is PyPI-ready with proper metadata and classifiers
- ✓ .env.example provides clear template for environment configuration

## Deviation Log

None — plan executed exactly as written.

## Commits

| Hash | Message |
|------|---------|
| `911523d` | feat(04-01): add setup script for one-command dependency installation |
| `98150e0` | feat(04-01): add root package.json with dev command |
| `26dab54` | chore(04-01): update pyproject.toml for PyPI readiness |
| `a13cf4e` | docs(04-01): update .env.example template per plan requirements |

## Verification Results

All automated verification checks passed:

- ✓ scripts/setup.sh exists and is executable
- ✓ package.json exists with concurrently
- ✓ pyproject.toml has openclerk package name
- ✓ pyproject.toml has Development Status classifiers
- ✓ .env.example exists with DATABASE_URL, OPENAI_API_KEY, SECRET_KEY

## Next Steps for Users

1. Run setup: `./scripts/setup.sh`
2. Edit `.env` with API keys
3. Start development: `npm run dev`
4. Visit http://localhost:5173 (frontend) and http://localhost:8000 (API)

## Self-Check: PASSED

All expected files and commits verified:

- FOUND: scripts/setup.sh
- FOUND: package.json
- FOUND: .env.example
- FOUND: commit 911523d (setup script)
- FOUND: commit 98150e0 (package.json)
- FOUND: commit 26dab54 (pyproject.toml)
- FOUND: commit a13cf4e (.env.example)
