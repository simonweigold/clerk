# Phase 04: Distribution - Context

**Gathered:** 2025-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers PyPI publishing, Docker packaging, and deployment documentation. This enables users to install Clerk via pip, deploy with Docker Compose, and follow production-ready setup guides. The phase addresses requirements SETUP-01 through SETUP-03 and DEPLOY-01 through DEPLOY-03.

</domain>

<decisions>
## Implementation Decisions

### PyPI Package Name
- **D-01:** Keep package name as "openclerk"
  - Current pyproject.toml already uses this name
  - Matches GitHub organization naming
  - Import statements remain `from openclerk import ...`
  - pip install openclerk
  - Rationale: Consistent with existing setup, no refactoring needed

### Docker Compose Architecture
- **D-02:** Multi-container (services) architecture
  - Separate containers for: backend (Python/FastAPI), frontend (React/static), database (PostgreSQL)
  - Allows independent scaling of services
  - Follows production best practices
  - Better resource isolation
  - Rationale: Production-ready, scalable, aligns with microservices pattern

### Setup Script Scope
- **D-03:** Database setup only via `clerk setup`
  - Create database tables and run migrations
  - Verify database connection
  - Seed initial data if needed
  - Does NOT install system dependencies or build frontend
  - Rationale: Focused, composable with other setup steps, stays under 5-minute target when combined with other setup

### Production Environment Strategy
- **D-04:** .env file mounting for environment variables
  - Mount .env file into containers at runtime
  - Document all required variables with descriptions and defaults
  - Provide .env.example as template
  - File permissions must be protected on host (documented in security section)
  - Rationale: Simple, familiar pattern for self-hosted users

### Deployment Guide Location
- **D-05:** Deployment documentation lives in `docs/deployment/` folder
  - `docs/deployment/docker.md` — Docker Compose setup
  - `docs/deployment/environment.md` — Environment variables reference
  - `docs/deployment/production.md` — Production considerations (HTTPS, scaling, security)
  - Integrated with existing React docs viewer
  - Rationale: Consistent with Phase 3 docs structure, searchable, versioned with code

### the agent's Discretion
- Specific Docker image base (python:3.13-slim recommended)
- PostgreSQL version for compose file
- Volume mounting strategy for persistent data
- Health check implementation details
- Exact CLI output formatting for setup command
- Nginx vs direct static file serving for frontend

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Core value, deployment philosophy (self-hosted focus)
- `.planning/REQUIREMENTS.md` — SETUP-01 through SETUP-03, DEPLOY-01 through DEPLOY-03
- `.planning/ROADMAP.md` — Phase 4 goal and success criteria

### Prior Phase Decisions
- `.planning/phases/03-frontend-integration/03-CONTEXT.md` — Documentation structure (D-04)

### Existing Codebase
- `packages/clerk/pyproject.toml` — Package metadata, dependencies
- `Dockerfile` — Current multi-stage build
- `.devcontainer/docker-compose.yml` — Existing compose patterns
- `packages/clerk/src/openclerk/cli.py` — CLI structure, existing db commands
- `docs/contributing/setup.md` — Current setup documentation

### External Standards
- https://packaging.python.org/en/latest/ — Python packaging best practices
- https://docs.docker.com/compose/ — Docker Compose file format
- https://setuptools.pypa.io/ — Build system configuration

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Dockerfile` — Multi-stage build pattern already established (frontend + Python)
- `packages/clerk/src/openclerk/cli.py` — CLI framework with db subcommands
- `.devcontainer/docker-compose.yml` — Compose file pattern for reference
- `docs/contributing/setup.md` — Setup instructions to reference from deployment guide

### Established Patterns
- UV for Python dependency management
- Node 20+ for frontend builds
- Just task runner for common commands
- Hatchling for package building
- GitHub Actions for CI/CD

### Integration Points
- CLI commands integrate with SQLAlchemy/Alembic for database operations
- Docker Compose integrates with existing Dockerfile
- Deployment docs integrate with React DocsPage viewer
- PyPI publishing integrates with existing pyproject.toml metadata

</code_context>

<specifics>
## Specific Ideas

### Docker Compose Structure
```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  backend:
    build: ./packages/clerk
    depends_on:
      - db
    env_file: .env
  
  frontend:
    build: ./apps/website
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Environment Variables to Document
- `DATABASE_URL` — PostgreSQL connection string
- `OPENAI_API_KEY` — LLM provider API key
- `SUPABASE_URL`, `SUPABASE_KEY` — Optional Supabase backend
- `SECRET_KEY` — Session signing key
- `LOG_LEVEL` — Application logging level

### Setup Command Flow
1. Check database connectivity
2. Run Alembic migrations (if using migrations)
3. Create initial tables (if not using migrations)
4. Verify setup with test query
5. Output success message with next steps

</specifics>

<deferred>
## Deferred Ideas

- Kubernetes deployment manifests — future phase for enterprise users
- Terraform modules for cloud deployment — out of scope for v1
- Automated SSL/TLS certificate provisioning — document manual steps first
- Multi-region deployment guide — advanced topic for v2
- Managed cloud hosting service — business model decision needed

</deferred>

---

*Phase: 04-distribution*
*Context gathered: 2025-03-25*
