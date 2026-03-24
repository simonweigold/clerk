# Architecture

This document describes Clerk's system architecture and design decisions.

---

## Overview

Clerk is a mono-repo containing:

- **Backend:** Python FastAPI application with LangGraph workflows
- **Frontend:** React SPA with TypeScript and Tailwind CSS
- **Package:** Installable Python package (`clerk-framework`)

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Clients                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Web UI     │  │     CLI      │  │   External   │       │
│  │   (React)    │  │   (Python)   │  │    Apps      │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼────────────────┼────────────────┼────────────────┘
          │                │                │
          └────────────────┴────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │      OpenClerk API (FastAPI)     │
          │  ┌────────────────────────────┐  │
          │  │    Authentication Layer    │  │
          │  │  (Session + OAuth)         │  │
          │  └────────────────────────────┘  │
          │  ┌────────────────────────────┐  │
          │  │      API Routes            │  │
          │  │  /kits, /execute, /docs    │  │
          │  └────────────────────────────┘  │
          └────────────────┬────────────────┘
                           │
          ┌────────────────┴────────────────┐
          │        Core Services             │
          │  ┌──────────┐    ┌──────────┐   │
          │  │  Graph   │    │  Loader  │   │
          │  │  Engine  │    │          │   │
          │  │(LangGraph│    │(Kit I/O) │   │
          │  └────┬─────┘    └────┬─────┘   │
          │       │               │         │
          │       └───────┬───────┘         │
          │               │                 │
          │          ┌────┴────┐            │
          │          │  Models │            │
          │          │(Pydantic│            │
          │          └────┬────┘            │
          └───────────────┼─────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │      Data Layer (Optional)    │
          │  ┌─────────────────────────┐  │
          │  │  Supabase (PostgreSQL)  │  │
          │  │  - Kit storage          │  │
          │  │  - Version control      │  │
          │  │  - User data            │  │
          │  └─────────────────────────┘  │
          │  ┌─────────────────────────┐  │
          │  │  Object Storage         │  │
          │  │  - Resource files       │  │
          │  │  - Kit assets           │  │
          │  └─────────────────────────┘  │
          └───────────────────────────────┘
```

---

## Backend

### FastAPI Application

Location: `packages/clerk/src/openclerk/web/`

Key components:

| Component | Purpose |
|-----------|---------|
| `app.py` | Application factory, middleware setup |
| `routes/api.py` | API endpoints (kits, execution, auth) |
| `routes/docs.py` | Documentation serving |
| `dependencies.py` | FastAPI dependencies (auth, DB) |

### Database Layer

Location: `packages/clerk/src/openclerk/db/`

Uses SQLAlchemy async with Supabase PostgreSQL:

- **Models:** SQLAlchemy ORM models (kits, versions, resources, users)
- **Repositories:** Data access pattern (`ReasoningKitRepository`, etc.)
- **Migrations:** Alembic for schema migrations

Key models:

```python
# Simplified view
ReasoningKit (id, slug, name, owner_id)
  └── KitVersion (id, kit_id, version_number, commit_message)
        ├── Resource (version_id, number, filename, storage_path)
        └── WorkflowStep (version_id, number, prompt_template)
```

### Reasoning Engine

Location: `packages/clerk/src/openclerk/graph.py`

Uses LangGraph for workflow execution:

1. **Parse:** Load kit resources and instructions
2. **Compile:** Build LangGraph state machine
3. **Execute:** Run step-by-step with LLM
4. **Stream:** Yield tokens and progress events

State flow:

```
Input → Resource Loading → Step 1 → Step 2 → ... → Final Output
              │              │         │
              └──────────────┴─────────┴────→ Token Stream
```

---

## Frontend

Location: `apps/website/`

### Tech Stack

- **Framework:** React 19 + TypeScript
- **Build:** Vite
- **Styling:** Tailwind CSS
- **Routing:** React Router
- **UI Components:** Custom + shadcn/ui patterns

### Project Structure

```
apps/website/src/
├── pages/              # Route components
│   ├── HomePage.tsx    # Landing page
│   ├── DocsPage.tsx    # Documentation viewer
│   ├── KitsPage.tsx    # Kit browser
│   └── KitEditorPage.tsx  # Kit creation/editing
├── components/         # Reusable UI
│   ├── ui/            # Base components
│   └── kit-editor/    # Kit-specific components
├── hooks/             # Custom React hooks
│   ├── useAuth.ts     # Authentication state
│   └── useToast.ts    # Notifications
├── lib/               # Utilities
│   ├── api.ts         # API client
│   └── utils.ts       # Helpers
└── App.tsx            # Router setup
```

### Key Pages

| Page | Route | Purpose |
|------|-------|---------|
| Home | `/` | Landing, feature overview |
| Docs | `/docs/*` | Documentation viewer (markdown) |
| Kits | `/kits` | Browse public kits |
| Kit Editor | `/kits/:slug/edit` | Create/edit kits |

---

## Package Structure

### Mono-repo Layout

```
clerk/
├── apps/
│   └── website/           # Deployable web app
│       ├── package.json   # npm dependencies
│       └── src/           # React source
├── packages/
│   └── clerk/             # Installable package
│       ├── pyproject.toml # Python dependencies
│       └── src/openclerk/ # Python source
└── docs/                  # Documentation (shared)
```

### Build Process

1. **Python Package:**
   ```bash
   cd packages/clerk
   uv build
   ```
   Creates: `dist/clerk_framework-*.whl`

2. **Frontend:**
   ```bash
   cd apps/website
   npm run build
   ```
   Creates: `dist/` with static assets

---

## Data Flow

### Reasoning Kit Flow

```
1. Authoring Phase
   User → Web UI/CLI → API → Database → Storage

2. Execution Phase
   User Request → API → Load Kit → Graph Engine
                                          ↓
   Token Stream ←─ Stream Response ←── LLM Calls

3. Retrieval Phase
   User → API → Database → Storage → Response
```

### File vs Database Kits

| Aspect | File-based | Database |
|--------|------------|----------|
| Storage | Local filesystem | PostgreSQL + Storage |
| Versioning | Git | Built-in versioning |
| Sharing | Git/Export | Web UI/Permissions |
| Use case | Development | Production/Teams |

---

## Design Decisions

### 1. File-First Design

Kits start as files (easy to version, edit, share) and can be promoted to database for web features.

### 2. LangGraph for Workflows

LangGraph provides:
- Stateful execution
- Streaming support
- Branching/conditional logic (future)
- Ecosystem compatibility

### 3. FastAPI + React

- FastAPI: Modern Python, automatic OpenAPI, async support
- React: Component model, TypeScript, large ecosystem

### 4. Mono-repo

Single repository for:
- Backend/frontend in sync
- Shared documentation
- Atomic changes across stack
- Simplified CI/CD

---

## Extension Points

### Adding New CLI Commands

Add to `packages/clerk/src/openclerk/cli.py`:

```python
# Add subparser
my_parser = subparsers.add_parser("my-command", help="Description")
my_parser.add_argument("--flag", help="A flag")

# Add handler
def _cmd_my_command(args: argparse.Namespace) -> None:
    # Implementation
    pass
```

### Adding API Endpoints

Add to `packages/clerk/src/openclerk/web/routes/api.py`:

```python
@router.post("/my-endpoint")
async def my_endpoint(request: Request):
    return {"ok": True, "data": ...}
```

### Adding Frontend Pages

1. Create page in `apps/website/src/pages/`
2. Add route in `apps/website/src/App.tsx`
3. Add link in navigation if needed

---

## Learn More

- **[Contributing Guide](./README.md)** — How to contribute
- **[Backend Code](../../packages/clerk/src/openclerk/)** — Explore the source
- **[Frontend Code](../../apps/website/src/)** — Explore the UI
