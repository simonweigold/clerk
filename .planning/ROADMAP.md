# Clerk Roadmap

**Project:** Clerk — Multi-step LLM Reasoning Framework  
**Core Value:** Developers can set up Clerk in under 5 minutes and contribute meaningfully in under 1 hour  
**Granularity:** Coarse  
**Created:** 2025-03-24

---

## Phases

- [ ] **Phase 1: Foundation** — Project structure, documentation, and developer tooling configured
- [ ] **Phase 2: Contributor Experience** — GitHub workflows, CI/CD, and quality gates operational
- [ ] **Phase 3: Frontend & Integration** — API documentation and integration examples published
- [ ] **Phase 4: Distribution** — PyPI publishing, Docker packaging, and deployment guides complete

---

## Phase Details

### Phase 1: Foundation
**Goal:** Repository is contributor-ready with complete documentation and automated development environment

**Depends on:** Nothing (first phase)

**Requirements:**
- DOCS-01: Repository has MIT LICENSE file in root directory
- DOCS-02: README includes clear value proposition and 5-line example
- DOCS-03: README includes working installation instructions (verified on clean system)
- DOCS-04: CONTRIBUTING.md exists with step-by-step dev environment setup
- DOCS-05: CODE_OF_CONDUCT.md uses Contributor Covenant standard
- DOCS-06: CHANGELOG.md follows Keep a Changelog format
- TOOL-01: UV workspace configured for Python dependency management
- TOOL-02: Ruff configured for linting and formatting in pyproject.toml
- TOOL-03: pytest configured with coverage reporting
- TOOL-04: mypy configured for type checking
- TOOL-06: Just task runner configured for common commands (test, lint, format)
- TOOL-07: Dev container configuration enables zero-setup contributions
- TOOL-08: VS Code settings/extensions configured for the project

**Success Criteria** (what must be TRUE):
1. New contributor can clone repo, run single command (e.g., `just setup`), and have working dev environment within 5 minutes
2. README displays clear value proposition with runnable 5-line code example
3. CONTRIBUTING.md includes step-by-step setup instructions that work on macOS, Linux, and via devcontainer
4. Code follows consistent style automatically (Ruff, mypy configured and passing)
5. Devcontainer configuration allows zero-local-setup contributions via VS Code or GitHub Codespaces

**Plans:** 2/3 plans executed

Plans:
- [x] 01-01-PLAN.md — Documentation (LICENSE, README, CONTRIBUTING, CODE_OF_CONDUCT, CHANGELOG)
- [x] 01-02-PLAN.md — Python Tooling (Ruff, pytest, mypy, Justfile)
- [x] 01-03-PLAN.md — Dev Environment (dev container, VS Code settings)

---

### Phase 2: Contributor Experience
**Goal:** Quality gates and contribution workflow operational, ready to accept external contributions

**Depends on:** Phase 1

**Requirements:**
- GHUB-01: Issue templates exist for bug reports and feature requests
- GHUB-02: Pull request template includes checklist (tests, docs, linked issue)
- GHUB-03: GitHub Actions CI runs tests on PRs
- GHUB-04: GitHub Actions CI runs linting (Ruff) on PRs
- GHUB-05: Branch protection requires CI to pass before merge
- GHUB-06: "Good first issue" labels applied to beginner-friendly issues
- TOOL-05: pre-commit hooks configured (Ruff, mypy, commit message check)

**Success Criteria** (what must be TRUE):
1. Contributor can open an issue using structured templates (bug report or feature request)
2. Pull request automatically triggers test and lint CI checks; failures block merge
3. Pre-commit hooks prevent commits with style violations or failing type checks
4. Repository has at least 3 issues labeled "good first issue" with clear acceptance criteria
5. Branch protection enforces CI pass requirement; no direct pushes to main allowed

**Plans:** 2/3 plans executed

Plans:
- [x] 02-01-PLAN.md — GitHub Templates (issue templates, PR template)
- [x] 02-02-PLAN.md — Pre-commit Hooks (Ruff, mypy configuration)
- [x] 02-03-PLAN.md — CI and Quality Gates (GitHub Actions, branch protection docs)

---

### Phase 3: Frontend & Integration
**Goal:** Developers can integrate Clerk into existing applications with documented API and working examples

**Depends on:** Phase 2

**Requirements:**
- DOCS-07: Documentation structure separates user, integration, and contributor paths
- INTEG-01: FastAPI integration example with working code
- INTEG-02: Integration guide explains embedding Clerk in existing apps
- INTEG-03: API documentation generated from FastAPI OpenAPI

**Success Criteria** (what must be TRUE):
1. Developer can follow integration guide to embed Clerk in existing FastAPI app within 30 minutes
2. API documentation (OpenAPI/Swagger UI) auto-generated and publicly accessible
3. Working FastAPI integration example demonstrates authentication, reasoning kit execution, and results retrieval
4. Documentation site has clear separation: users see quickstart, integrators see embedding guide, contributors see development setup

**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Documentation Structure & API Spec (user guide, integration guide, OpenAPI generation)
- [ ] 03-02-PLAN.md — FastAPI Integration Example (embedding example with auth, execution, results)

**UI hint**: yes

---

### Phase 4: Distribution
**Goal:** Project is distributable via PyPI with production-ready Docker packaging and deployment documentation

**Depends on:** Phase 3

**Requirements:**
- SETUP-01: One-command setup script installs all dependencies
- SETUP-02: Database setup is automated via CLI command
- SETUP-03: Dev environment starts with single command (backend + frontend)
- DEPLOY-01: Self-hosted deployment guide with Docker Compose
- DEPLOY-02: Environment variables fully documented
- DEPLOY-03: Production considerations documented (security, scaling)

**Success Criteria** (what must be TRUE):
1. User can install Clerk via `pip install clerk-framework` and run basic workflow within 5 minutes
2. Docker Compose configuration enables single-command production deployment
3. All environment variables documented with descriptions, defaults, and security implications
4. Production guide covers HTTPS setup, database migrations, log management, and scaling considerations
5. CLI provides `clerk setup` command for automated database initialization and configuration

**Plans:** TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Completed| 2026-03-24 |
| 2. Contributor Experience | 2/3 | In Progress|  |
| 3. Frontend & Integration | 0/2 | Planned | - |
| 4. Distribution | 0/3 | Not started | - |

---

## Requirements Coverage

**v1 Requirements:** 26 total  
**Mapped to phases:** 26  
**Unmapped:** 0 ✓

| Category | Requirements | Phase |
|----------|--------------|-------|
| Documentation Foundation | DOCS-01, DOCS-02, DOCS-03, DOCS-04, DOCS-05, DOCS-06 | 1 |
| Documentation Structure | DOCS-07 | 3 |
| GitHub Setup | GHUB-01, GHUB-02, GHUB-03, GHUB-04, GHUB-05, GHUB-06 | 2 |
| Developer Tooling | TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-06, TOOL-07, TOOL-08 | 1 |
| Quality Gates | TOOL-05 | 2 |
| Setup Automation | SETUP-01, SETUP-02, SETUP-03 | 4 |
| Deployment Documentation | DEPLOY-01, DEPLOY-02, DEPLOY-03 | 4 |
| Integration Support | INTEG-01, INTEG-02, INTEG-03 | 3 |

---

## Dependencies Between Phases

```
Phase 1 (Foundation)
    ↓
Phase 2 (Contributor Experience) — requires working dev environment from Phase 1
    ↓
Phase 3 (Frontend & Integration) — requires stable codebase and CI from Phase 2
    ↓
Phase 4 (Distribution) — requires complete documentation and examples from Phase 3
```

---

## Revision History

| Date | Change | Rationale |
|------|--------|-----------|
| 2025-03-24 | Initial roadmap created | Based on research recommendations and 26 v1 requirements |

---
*Last updated: 2025-03-24*
