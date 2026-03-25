# Phase 04: Distribution - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2025-03-25
**Phase:** 04-distribution
**Areas discussed:** PyPI Package Name, Docker Compose Architecture, Setup Script Scope, Production Environment Strategy, Deployment Guide Hosting

---

## PyPI Package Name

| Option | Description | Selected |
|--------|-------------|----------|
| openclerk | Keep current name. Matches GitHub org, imports as 'openclerk' | ✓ |
| clerk-framework | Change to match requirement. More descriptive | |
| clerk | Simplest, most memorable. Risk of name collision | |

**User's choice:** openclerk
**Notes:** Keep current name for consistency with existing setup and GitHub organization.

---

## Docker Compose Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Single container (monolith) | Frontend + backend in one container. Simpler deployment | |
| Multi-container (services) | Separate containers for frontend, backend, database | ✓ |
| Both: simple + production compose | Provide both options | |

**User's choice:** Multi-container (services)
**Notes:** Better for production, allows independent scaling, follows best practices.

---

## Setup Script Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Database setup only | Create tables, run migrations, verify connection | ✓ |
| Database + dependencies check | Verify Python/Node installed, check env vars, setup DB | |
| Full environment setup | Install Python deps, Node deps, build frontend, setup DB | |

**User's choice:** Database setup only
**Notes:** Focused and composable. User handles dependencies via Justfile or dev container.

---

## Production Environment Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| .env file mounting | Mount .env file into container. Simple, familiar pattern | ✓ |
| Docker secrets / external vault | Use Docker secrets or external vault | |
| CLI interactive configuration | clerk setup prompts for values, writes config | |

**User's choice:** .env file mounting
**Notes:** Simple for self-hosted users, document file permissions for security.

---

## Deployment Guide Hosting

| Option | Description | Selected |
|--------|-------------|----------|
| docs/deployment/ folder | Create new docs/deployment/ directory. Consistent with existing structure | ✓ |
| Top-level DEPLOY.md | Single file in repo root. Easy to find | |
| README.md section | Add deployment section to existing README | |

**User's choice:** docs/deployment/ folder
**Notes:** Matches Phase 3 docs structure, integrated with React docs viewer.

---

## the agent's Discretion

Areas where the agent has flexibility:
- Specific Docker image base (python:3.13-slim recommended)
- PostgreSQL version for compose file
- Volume mounting strategy for persistent data
- Health check implementation details
- Exact CLI output formatting for setup command
- Nginx vs direct static file serving for frontend

## Deferred Ideas

None discussed — all scope items addressed.

---

*Discussion completed: 2025-03-25*
