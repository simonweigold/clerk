---
phase: 03-frontend-integration
plan: "01"
subsystem: documentation
tags: [docs, openapi, integration]
dependencies:
  requires: []
  provides: [DOCS-07, INTEG-03]
  affects: []
tech-stack:
  added: []
  patterns: [audience-based-docs]
key-files:
  created:
    - docs/user-guide/README.md
    - docs/user-guide/concepts.md
    - docs/user-guide/faq.md
    - docs/integration/README.md
    - docs/integration/api-reference.md
    - docs/integration/examples.md
    - docs/contributing/README.md
    - docs/contributing/architecture.md
  modified:
    - packages/clerk/src/openclerk/cli.py
    - packages/clerk/src/openclerk/web/routes/api.py
    - apps/website/src/pages/DocsPage.tsx
decisions:
  - Adapted CLI command location to existing single-file cli.py structure
  - Added OpenAPI endpoint directly to api.py rather than separate docs.py
metrics:
  duration_minutes: 25
  completed_at: "2026-03-24T17:55:00Z"
  files_created: 8
  files_modified: 3
  commits: 5
---

# Phase 03 Plan 01: Documentation Structure & OpenAPI Summary

**One-liner:** Created audience-separated documentation (user, integration, contributor) with auto-generated OpenAPI specification served at /api/openapi.json.

## Completed Work

### Documentation Structure (8 files)

**User Guide** (`docs/user-guide/`):
- README.md — Quickstart guide with installation and first workflow
- concepts.md — Core Clerk concepts (Reasoning Kits, Resources, Instructions, Workflows)
- faq.md — Frequently asked questions covering installation, kit format, LLM requirements

**Integration Guide** (`docs/integration/`):
- README.md — FastAPI integration guide with step-by-step mounting instructions
- api-reference.md — Complete API reference with OpenAPI spec access instructions
- examples.md — Links to integration examples (FastAPI, with Django/Flask coming soon)

**Contributing Guide** (`docs/contributing/`):
- README.md — Contributor quick start with setup and workflow
- architecture.md — System architecture documentation with diagrams and data flow

### OpenAPI Specification (INTEG-03)

**CLI Command** (`packages/clerk/src/openclerk/cli.py`):
- Added `clerk docs generate-openapi` command
- Accepts `--output` option (default: openapi.json)
- Uses FastAPI's `get_openapi()` utility

**HTTP Endpoint** (`packages/clerk/src/openclerk/web/routes/api.py`):
- Added `GET /api/openapi.json` endpoint
- Returns complete OpenAPI 3.0 specification
- Includes all API routes from api.py

### Updated Sidebar (DOCS-07)

**DocsPage.tsx** (`apps/website/src/pages/DocsPage.tsx`):
- Added DIR_NAMES mappings: user-guide, integration, contributing
- Custom order: User Guide → Integration → Contributing → General → CLI Commands → UI Features
- Groups documentation by audience as specified in D-04

## Deviations from Plan

### Auto-fixed Issues

**None** — Plan executed exactly as written with one adaptation:

**[Rule 3 - Adaptation] CLI structure adaptation**
- **Found during:** Task 4
- **Issue:** Plan assumed `packages/clerk/src/openclerk/cli/commands/docs.py` structure, but actual project has single-file `cli.py`
- **Fix:** Added docs subcommand directly to existing `cli.py` instead of creating separate module
- **Files modified:** `packages/clerk/src/openclerk/cli.py`
- **Commit:** a3bd4a1

## Verification

All verification checks passed:
- ✅ docs/user-guide/ exists with README.md, concepts.md, faq.md
- ✅ docs/integration/ exists with README.md, api-reference.md, examples.md
- ✅ docs/contributing/ exists with README.md, architecture.md
- ✅ CLI command `clerk docs generate-openapi` implemented
- ✅ HTTP endpoint `/api/openapi.json` returns valid spec
- ✅ Sidebar updated with audience-based sections

## Self-Check: PASSED

- [x] All 8 created files exist and are accessible
- [x] All 3 modified files committed with proper messages
- [x] Commit hashes verified in git log
- [x] No stubs or placeholder content in documentation

## Commits

1. ed98fab — docs(03-01): add user guide documentation
2. 141a62b — docs(03-01): add integration documentation
3. 193cfa4 — docs(03-01): add contributor documentation
4. a3bd4a1 — feat(03-01): add CLI command for OpenAPI spec generation
5. 1e664d6 — feat(03-01): add OpenAPI endpoint and update docs sidebar

## Requirements Satisfied

- ✅ DOCS-07: Documentation paths clearly separate user, integration, contributor audiences
- ✅ INTEG-03: OpenAPI spec auto-generated and accessible at /api/openapi.json
