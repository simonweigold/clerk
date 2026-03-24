# Phase 03: Frontend & Integration - Context

**Gathered:** 2025-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers the API documentation and integration examples required for developers to embed Clerk into existing applications. This includes: OpenAPI specification generation, documentation site structure separating user/integration/contributor paths, and working FastAPI integration examples.

</domain>

<decisions>
## Implementation Decisions

### API Documentation Strategy
- **D-01:** Export static OpenAPI specification only (no interactive Swagger UI in production)
  - Generate `openapi.json` during build process
  - Serve statically at `/api/openapi.json`
  - Integrators can import into Postman, Swagger UI, or other tools
  - Rationale: Clean, secure, tool-agnostic

### Documentation Format
- **D-02:** Continue using markdown files in `docs/` folder served by React app
  - DocsPage component fetches markdown via `/api/docs/{slug}` API
  - No separate build step required
  - Keeps docs close to the application
  - Rationale: Simple, consistent with existing architecture

### Integration Example Scope
- **D-03:** Full working example with authentication, kit execution, and results retrieval
  - Complete FastAPI app demonstrating: mounting Clerk router, auth middleware integration, executing a reasoning kit, retrieving and displaying results
  - ~200 lines of well-commented code
  - Addresses all aspects of INTEG-01 and INTEG-02
  - Rationale: Provides complete picture, meets 30-minute integration target

### Documentation Organization
- **D-04:** Path-based separation matching folder structure
  - `/docs/user-guide/` — Quickstart, core concepts, FAQ
  - `/docs/integration/` — Embedding guide, API reference, examples
  - `/docs/contributing/` — Dev setup, architecture, contribution process
  - Each section has its own README and clear navigation
  - Rationale: Matches existing structure, clear audience targeting

### Integration Example Delivery
- **D-05:** Example code lives in `examples/fastapi-integration/` directory
  - Standalone folder with its own README
  - Can be copied and adapted by integrators
  - Referenced from integration documentation
  - Rationale: Easy to find, self-contained, can be extended for Django/Flask later

### the agent's Discretion
- Specific OpenAPI generation tooling (can use FastAPI's built-in or CLI tool)
- Exact navigation UI for docs sections
- Code highlighting style in documentation
- Integration example styling (keep it simple)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Core value, constraints
- `.planning/REQUIREMENTS.md` — DOCS-07, INTEG-01, INTEG-02, INTEG-03
- `.planning/ROADMAP.md` — Phase 3 goal and success criteria

### Prior Phase Decisions
- `.planning/phases/01-foundation/01-CONTEXT.md` — Documentation structure (D-01)

### Existing Codebase
- `packages/clerk/src/openclerk/web/app.py` — FastAPI app factory
- `packages/clerk/src/openclerk/web/routes/api.py` — API routes (comprehensive reference)
- `apps/website/src/App.tsx` — React routing
- `apps/website/src/pages/DocsPage.tsx` — Existing docs viewer
- `docs/` — Current documentation structure

### External Standards
- https://spec.openapis.org/oas/latest.html — OpenAPI specification format
- https://www.mkdocs.org/ — Reference for docs structure (even though keeping React-based)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DocsPage.tsx` — Existing markdown viewer component, fetch docs via API
- `/api/docs` endpoints — Already serve markdown content
- FastAPI app factory — Can generate OpenAPI spec programmatically
- `packages/clerk/src/openclerk/web/routes/api.py` — 3000+ lines of API routes, comprehensive reference

### Established Patterns
- Markdown documentation in `docs/` folder
- React Query for data fetching
- React Router for navigation
- API routes return JSON with `{"ok": bool, ...}` pattern

### Integration Points
- Docs are served via `/api/docs/{slug}` and displayed in DocsPage
- Can add `/api/openapi.json` endpoint or generate at build time
- Example code should import from `openclerk` package
- Frontend docs navigation can be enhanced with section grouping

</code_context>

<specifics>
## Specific Ideas

### OpenAPI Generation Options
1. Runtime: Add `/api/openapi.json` endpoint to FastAPI app (already supported)
2. Build-time: Use `fastapi.openapi.utils.get_openapi()` in a CLI command
3. CI: Generate and commit openapi.json during release process

### Docs Structure Target
```
docs/
├── README.md              # Entry point with audience selector
├── user-guide/
│   ├── README.md          # Quickstart
│   ├── concepts.md        # Core Clerk concepts
│   └── faq.md
├── integration/
│   ├── README.md          # Embedding guide
│   ├── api-reference.md   # Link to openapi.json
│   └── examples.md        # Link to example code
└── contributing/
    ├── README.md          # Dev setup (reference CONTRIBUTING.md)
    └── architecture.md    # System design
```

### Integration Example Structure
```
examples/fastapi-integration/
├── README.md              # Setup and running instructions
├── main.py                # Full example code
├── requirements.txt       # Dependencies
└── .env.example           # Required environment variables
```

</specifics>

<deferred>
## Deferred Ideas

- Interactive API playground (Swagger UI) — not needed with static spec
- MkDocs/Docusaurus migration — reconsider if docs grow significantly
- Django/Flask integration examples — Phase 4+ or community contributions
- API versioning documentation — only when API v2 is planned
- Multi-language SDKs — out of scope for v1

</deferred>

---

*Phase: 03-frontend-integration*
*Context gathered: 2025-03-24*
