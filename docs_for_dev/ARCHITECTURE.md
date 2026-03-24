# CLERK/OpenClerk Dual-Purpose Architecture Plan

> **Status:** Draft  
> **Last Updated:** March 23, 2026  
> **Goal:** Transform the CLERK repository into both a PyPI-distributable Python package and a unified website (landing page + documentation + live application instance).

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Target Architecture](#target-architecture)
4. [Repository Structure](#repository-structure)
5. [Python Package Design](#python-package-design)
6. [Website Architecture](#website-architecture)
7. [Deployment Strategy](#deployment-strategy)
8. [Implementation Phases](#implementation-phases)
9. [Technical Decisions](#technical-decisions)
10. [Migration Path](#migration-path)
11. [Open Questions](#open-questions)

---

## Executive Summary

This document outlines the plan to restructure the CLERK repository to serve two primary purposes:

1. **Python Package Distribution**: A pip-installable package (`openclerk`) available on PyPI
2. **Unified Web Presence**: A website at `openclerk.ch` that combines:
   - Marketing/landing pages
   - Comprehensive documentation
   - Live CLERK application instance with Supabase integration

### Key Benefits

- **Single source of truth**: Code and documentation live in one repository
- **Developer experience**: Users can install via pip OR use the web interface
- **Community growth**: Lower barrier to entry with multiple access points
- **SaaS potential**: Hosted version generates value while open-source package builds community

---

## Current State Analysis

### Repository Structure (Current)

```
clerk/                          # Repository root
├── src/clerk/                  # Python package source
│   ├── __init__.py
│   ├── cli.py                  # CLI entry point
│   ├── graph.py                # LangGraph workflows
│   ├── loader.py               # Kit loading logic
│   ├── models.py               # Pydantic models
│   ├── web/                    # FastAPI web interface
│   │   ├── app.py
│   │   └── routes/api.py
│   └── db/                     # Database layer
├── frontend/                   # React SPA (Vite + React 19)
│   ├── src/
│   ├── package.json
│   └── dist/                   # Build output
├── docs/                       # Markdown documentation
│   ├── cli/
│   ├── ui/
│   └── *.md
├── reasoning_kits/             # Example kits
├── pyproject.toml              # Package config (hatchling)
└── README.md
```

### Current Capabilities

| Component | Status | Notes |
|-----------|--------|-------|
| CLI | ✅ Working | `clerk list`, `clerk run`, `clerk web` |
| Web UI | ✅ Working | FastAPI + React SPA served from `/` |
| Database | ✅ Working | Supabase (PostgreSQL) + SQLAlchemy |
| Auth | ✅ Working | Supabase Auth via session cookies |
| MCP | 🔄 Partial | Client implemented, server WIP |
| Documentation | ✅ Basic | Markdown files in `/docs` |

### Current Limitations

1. **Package naming**: `clerk` name likely unavailable on PyPI
2. **Bundled frontend**: Web app expects local `frontend/dist/` directory
3. **No separation**: Can't deploy web UI separately from Python package
4. **Documentation**: Static markdown not integrated with web UI
5. **Distribution**: No automated PyPI publishing

---

## Target Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     openclerk.ch                               │
│                    (Next.js on Vercel)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Landing    │  │Documentation │  │   CLERK Web App      │  │
│  │   Pages      │  │    (MDX)     │  │   (Embedded SPA)     │  │
│  │              │  │              │  │                      │  │
│  │  - Features  │  │  - Guides    │  │  - Kit Browser       │  │
│  │  - Pricing   │  │  - API Ref   │  │  - Kit Editor        │  │
│  │  - About     │  │  - Examples  │  │  - Execute Flows     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
        ┌─────▼──────┐          ┌──────▼──────┐
        │  Supabase  │          │  CLERK API  │
        │  (Auth/DB) │          │  (Railway)  │
        └────────────┘          └─────────────┘
                                         │
                              ┌──────────┴──────────┐
                              │                     │
                        ┌─────▼─────┐         ┌────▼────┐
                        │  PyPI     │         │ Docker  │
                        │  Package  │         │  Hub    │
                        └───────────┘         └─────────┘
```

### Dual Access Model

**As a Python Package:**
```bash
pip install openclerk
clerk list                    # List kits
clerk run my-kit             # Execute locally
clerk web --local            # Self-hosted web UI
```

**As a Web Application:**
```
https://openclerk.ch
├── /              → Landing page
├── /features      → Product features
├── /docs          → Documentation
├── /app           → Live CLERK instance (requires login)
└── /pricing       → SaaS pricing (future)
```

---

## Repository Structure

### Proposed Monorepo Layout

```
openclerk/                      # Repository root (renamed)
│
├── .github/
│   └── workflows/
│       ├── release.yml         # PyPI release automation
│       └── deploy.yml          # Website deployment
│
├── packages/                   # Published packages
│   └── clerk/                  # Python package (PyPI)
│       ├── pyproject.toml
│       ├── README.md
│       ├── LICENSE
│       ├── src/
│       │   └── openclerk/      # Renamed from 'clerk'
│       │       ├── __init__.py
│       │       ├── cli.py
│       │       ├── graph.py
│       │       ├── loader.py
│       │       ├── models.py
│       │       ├── web/        # API-only (no bundled SPA)
│       │       │   ├── app.py
│       │       │   └── routes/
│       │       └── db/
│       └── tests/
│
├── apps/                       # Deployable applications
│   └── website/                # Next.js website
│       ├── package.json
│       ├── next.config.js
│       ├── tsconfig.json
│       ├── tailwind.config.ts
│       ├── src/
│       │   ├── app/
│       │   │   ├── (marketing)/
│       │   │   │   ├── page.tsx           # Homepage
│       │   │   │   ├── features/
│       │   │   │   ├── pricing/
│       │   │   │   └── about/
│       │   │   ├── docs/
│       │   │   │   ├── [[...slug]]/
│       │   │   │   │   └── page.tsx       # Docs catch-all
│       │   │   │   └── layout.tsx
│       │   │   ├── app/                   # CLERK web UI
│       │   │   │   ├── page.tsx
│       │   │   │   ├── dashboard/
│       │   │   │   ├── kits/
│       │   │   │   └── settings/
│       │   │   ├── api/                   # Next.js API routes
│       │   │   │   ├── auth/
│       │   │   │   └── proxy/
│       │   │   └── layout.tsx
│       │   ├── components/
│       │   │   ├── ui/                    # shadcn/ui
│       │   │   ├── marketing/             # Landing sections
│       │   │   └── docs/                  # Doc components
│       │   ├── lib/
│       │   │   ├── supabase.ts
│       │   │   └── utils.ts
│       │   └── styles/
│       │       └── globals.css
│       ├── content/              # MDX documentation source
│       │   ├── getting-started.mdx
│       │   ├── reasoning-kits.mdx
│       │   ├── cli-reference.mdx
│       │   ├── api-reference/
│       │   └── examples/
│       └── public/
│           ├── images/
│           └── fonts/
│
├── docs/                       # Architecture docs (this file, etc.)
│   ├── ARCHITECTURE.md         # This document
│   ├── DECISIONS.md            # ADRs (Architecture Decision Records)
│   └── DEPLOYMENT.md           # Deployment runbooks
│
├── reasoning_kits/             # Example/community kits
│   ├── demo/
│   └── README.md
│
├── docker/
│   ├── Dockerfile.package      # For package builds
│   └── Dockerfile.website      # For website deployment
│
├── scripts/
│   ├── bootstrap.sh            # Setup script
│   └── release.sh              # Manual release helper
│
├── pyproject.toml              # Root workspace config (optional)
├── package.json                # Root package.json (optional)
├── README.md                   # Root readme
├── LICENSE                     # MIT License
└── CONTRIBUTING.md             # Contribution guidelines
```

---

## Python Package Design

### Package Configuration

**File:** `packages/clerk/pyproject.toml`

```toml
[project]
name = "openclerk"
version = "0.1.0"
description = "Community Library of Executable Reasoning Kits"
readme = "README.md"
requires-python = ">=3.13"
license = "MIT"
authors = [
    {name = "Your Name", email = "you@example.com"}
]
keywords = ["llm", "ai", "workflow", "reasoning", "langchain", "langgraph"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
dependencies = [
    # LLM Framework
    "langchain>=1.2.4",
    "langchain-openai>=1.1.7",
    "langgraph>=1.0.6",
    # Database
    "sqlalchemy[asyncio]>=2.0.36",
    "alembic>=1.14.0",
    "asyncpg>=0.30.0",
    "supabase>=2.11.0",
    # Web UI (API only)
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "python-multipart>=0.0.12",
    "itsdangerous>=2.2.0",
    "sse-starlette>=2.1.0",
    "pgvector>=0.3.6",
    "langchain-postgres>=0.0.17",
    # Utilities
    "python-dotenv>=1.2.1",
    "pypdf>=5.1.0",
    "openpyxl>=3.1.5",
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    # LLM Providers
    "langchain-anthropic>=1.3.5",
    "langchain-mistralai>=1.1.2",
    "langchain-google-genai>=4.2.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.6.0",
    "mypy>=1.10.0",
]
mcp = [
    "mcp>=1.26.0",
]

[project.scripts]
clerk = "openclerk.cli:main"
openclerk = "openclerk.cli:main"

[project.urls]
Homepage = "https://openclerk.ch"
Documentation = "https://openclerk.ch/docs"
Repository = "https://github.com/yourorg/openclerk"
Issues = "https://github.com/yourorg/openclerk/issues"
Changelog = "https://openclerk.ch/docs/changelog"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/openclerk"]

# Exclude SPA build from wheel (served separately)
[tool.hatch.build.targets.wheel.exclude]
paths = [
    "src/openclerk/web/static/spa/",
    "**/tests/",
    "**/test_*.py",
]

[tool.uv]
package = true

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
```

### Namespace Change

The package namespace changes from `clerk` to `openclerk`:

```python
# Before (current)
from clerk.loader import load_reasoning_kit
from clerk.graph import run_reasoning_kit

# After (target)
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit
```

### Web Module Changes

The web module becomes API-only. It no longer serves the React SPA:

```python
# packages/clerk/src/openclerk/web/app.py

from fastapi import FastAPI

# BEFORE: Serves SPA from frontend/dist/
SPA_DIR = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
app.mount("/assets", StaticFiles(directory=SPA_DIR / "assets"))

# AFTER: API only
# SPA is served by the website app (Next.js)
# API endpoints only

app = FastAPI(
    title="OpenClerk API",
    description="API for Community Library of Executable Reasoning Kits",
    version="0.1.0",
    docs_url="/docs" if os.getenv("ENV") == "development" else None,
)

# Only API routes - no static file serving
app.include_router(api_router, prefix="/api/v1")
```

### CLI Commands

The CLI remains largely unchanged but gains environment detection:

```bash
# Local filesystem mode (default)
clerk list --local
clerk run my-kit --local

# Database mode (connects to Supabase)
clerk list
clerk run my-kit

# Self-hosted web UI (API only)
clerk web --port 8000

# With local database (for self-hosting)
clerk web --local-db
```

---

## Website Architecture

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Framework | Next.js 14+ (App Router) | SEO, SSR, static generation |
| Language | TypeScript | Type safety |
| Styling | Tailwind CSS | Utility-first, consistent design |
| UI Components | shadcn/ui | Accessible, customizable |
| Content | MDX | Markdown + React components |
| Auth | Supabase Auth | Already used in backend |
| Search | Algolia / Pagefind | Doc search (future) |
| Analytics | Vercel / Plausible | Privacy-friendly |

### Route Structure

```
openclerk.ch/
│
├── / (GET)                    # Landing page
│   └── Features, CTA, testimonials
│
├── /features (GET)            # Detailed feature list
├── /pricing (GET)             # Pricing tiers (future SaaS)
├── /about (GET)               # About page, team
│
├── /docs (GET)                # Documentation homepage
├── /docs/getting-started      # Installation & quickstart
├── /docs/reasoning-kits       # Kit creation guide
├── /docs/cli-reference        # CLI commands
├── /docs/api-reference        # API endpoints
├── /docs/examples             # Example kits
├── /docs/changelog            # Version history
│
├── /app (GET)                 # CLERK Web Application
│   ├── /app/dashboard         # User dashboard
│   ├── /app/kits              # Browse kits
│   ├── /app/kits/[id]         # Kit detail/editor
│   ├── /app/kits/[id]/execute # Run kit
│   └── /app/settings          # User settings
│
├── /api (POST/GET)            # Next.js API routes
│   ├── /api/auth/*            # Supabase auth callbacks
│   └── /api/proxy/*           # Proxy to CLERK backend
│
└── /login, /signup (GET)      # Auth pages (or use Supabase)
```

### Application Integration

#### Option A: Embedded SPA (Quick Migration)

Reuse the existing React frontend as an embedded application:

```tsx
// apps/website/src/app/app/page.tsx
export default function ClerkAppPage() {
  return (
    <div className="h-screen w-full">
      <iframe
        src="https://clerk-api.openclerk.ch/app"
        className="w-full h-full border-0"
        title="CLERK Application"
      />
    </div>
  );
}
```

**Pros:**
- Fast migration
- Minimal code changes
- Works immediately

**Cons:**
- Iframe limitations
- No SEO for app pages
- Double auth handling

#### Option B: Rebuilt with Next.js (Recommended Long-term)

Port the React components to Next.js App Router:

```tsx
// apps/website/src/app/app/kits/page.tsx
import { KitBrowser } from "@/components/clerk/kit-browser";
import { getKits } from "@/lib/clerk-api";

export default async function KitsPage() {
  const kits = await getKits();
  
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Reasoning Kits</h1>
      <KitBrowser kits={kits} />
    </div>
  );
}
```

**Pros:**
- Full SSR/SSG capabilities
- Better SEO
- Unified auth flow
- Progressive enhancement

**Cons:**
- More migration work
- Need to adapt components

### Documentation System

**MDX-Based Docs:**

```mdx
---
title: Getting Started with OpenClerk
description: Learn how to install and use OpenClerk
---

# Getting Started

## Installation

```bash
pip install openclerk
```

## Quick Start

<Callout type="info">
  Make sure you have Python 3.13+ installed.
</Callout>

...rest of content...
```

**Components:**
- `Callout` - Info/warning boxes
- `CodeBlock` - Syntax-highlighted code
- `Steps` - Numbered step lists
- `Tabs` - Language/framework tabs

---

## Deployment Strategy

### Python Package (PyPI)

**GitHub Actions Workflow:**

```yaml
# .github/workflows/release.yml
name: Release to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv build packages/clerk/
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: packages/clerk/dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
```

### Website (Vercel)

**Configuration:**

```javascript
// apps/website/next.config.js
const { withContentlayer } = require('next-contentlayer');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // Static export for Vercel
  distDir: 'dist',
  images: {
    unoptimized: true,
  },
  // Proxy API routes to CLERK backend
  async rewrites() {
    return [
      {
        source: '/api/clerk/:path*',
        destination: `${process.env.CLERK_API_URL}/api/:path*`,
      },
    ];
  },
};

module.exports = withContentlayer(nextConfig);
```

**Environment Variables:**

```bash
# Production
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
CLERK_API_URL=https://api.openclerk.ch

# Development
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
CLERK_API_URL=http://localhost:8000
```

### API Backend (Railway/Fly.io)

The FastAPI backend can be deployed separately:

```dockerfile
# docker/Dockerfile.api
FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy package
COPY packages/clerk/ .

# Install dependencies
RUN uv pip install --system -e "."

# Run
CMD ["uvicorn", "openclerk.web.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Implementation Phases

### Phase 1: Repository Restructure (Week 1)

**Tasks:**
1. Create new monorepo structure
2. Move Python code to `packages/clerk/`
3. Rename `clerk` → `openclerk` namespace
4. Update all imports
5. Move frontend to `apps/website/`
6. Set up workspace configuration

**Deliverables:**
- Working monorepo structure
- All tests passing
- Local development works

### Phase 2: Package Preparation (Week 2)

**Tasks:**
1. Configure `pyproject.toml` for PyPI
2. Update web module to be API-only
3. Add package metadata
4. Create package README
5. Set up release automation
6. Test package build

**Deliverables:**
- `pip install -e packages/clerk/` works
- Package builds without errors
- Release workflow ready

### Phase 3: Website Foundation (Week 3-4)

**Tasks:**
1. Initialize Next.js project
2. Set up Tailwind + shadcn/ui
3. Create marketing page layouts
4. Set up MDX documentation
5. Configure Supabase auth
6. Create API proxy routes

**Deliverables:**
- Landing page deployed
- Documentation rendering
- Auth flow working

### Phase 4: Application Integration (Week 5-6)

**Tasks:**
1. Port React components OR embed SPA
2. Integrate kit browser
3. Integrate kit editor
4. Integrate execution flow
5. Test end-to-end workflows

**Deliverables:**
- Full CLERK app accessible at `/app`
- All CRUD operations working
- Execution flows functional

### Phase 5: Documentation & Polish (Week 7)

**Tasks:**
1. Write comprehensive docs
2. Create examples
3. Add search functionality
4. SEO optimization
5. Performance tuning
6. Accessibility audit

**Deliverables:**
- Complete documentation site
- Search working
- Lighthouse score >90

### Phase 6: Launch (Week 8)

**Tasks:**
1. Final testing
2. Domain configuration
3. SSL certificates
4. Analytics setup
5. Initial PyPI release
6. Announcement

**Deliverables:**
- openclerk.ch live
- Package on PyPI
- Documentation complete

---

## Technical Decisions

### Decision Log

| Date | Decision | Context | Status |
|------|----------|---------|--------|
| 2026-03-23 | Monorepo structure | Simplifies coordination between package and website | Proposed |
| 2026-03-23 | Package name: `openclerk` | `clerk` unavailable on PyPI | Proposed |
| 2026-03-23 | Next.js for website | SEO + modern React features | Proposed |
| 2026-03-23 | MDX for docs | Flexibility + React integration | Proposed |
| 2026-03-23 | Separate API deployment | Scalability + separation of concerns | Proposed |

### Package Name Options

1. **openclerk** (recommended)
   - Clear association with CLERK
   - Likely available
   - Follows convention (openai, opentelemetry)

2. **clerk-ai**
   - Distinguishes from Clerky (legal service)
   - AI focus clear

3. **clerk-reasoning**
   - Descriptive
   - Longer to type

### Web Architecture Options

1. **Option A: Next.js + Embedded SPA**
   - Quicker to implement
   - Good enough for MVP
   - Can migrate to full Next.js later

2. **Option B: Full Next.js Rebuild**
   - Better long-term
   - More upfront work
   - Better performance

**Recommendation:** Start with Option A, migrate to B post-launch.

---

## Migration Path

### Current → Target Mapping

```
current                          target
─────────────────────────────────────────────────────────
src/clerk/               →     packages/clerk/src/openclerk/
frontend/src/            →     apps/website/src/app/app/ (or embed)
frontend/dist/           →     apps/website/public/app/ (build output)
docs/*.md                →     apps/website/content/*.mdx
pyproject.toml           →     packages/clerk/pyproject.toml
reasoning_kits/          →     reasoning_kits/ (keep at root)
```

### Import Updates

```python
# Update all internal imports
sed -i 's/from clerk\./from openclerk./g' **/*.py
sed -i 's/import clerk/import openclerk/g' **/*.py
```

### Git History

Use `git mv` to preserve history:

```bash
git mv src/clerk packages/clerk/src/openclerk
git mv frontend apps/website
git commit -m "Restructure for monorepo"
```

---

## Open Questions

### Technical

1. **Should we keep the current React frontend or rebuild in Next.js?**
   - Rebuild: Better integration, SSR
   - Keep: Faster delivery

2. **Should the API backend be deployed per-user or shared?**
   - Shared: Simpler, cost-effective
   - Per-user: Better isolation

3. **How do we handle kit storage for web users vs. package users?**
   - Web: Supabase only
   - Package: Local filesystem OR Supabase

### Business

1. **What is the pricing model for the hosted version?**
   - Free tier limits?
   - Paid features?

2. **Do we need a team/organization feature?**
   - Multi-user kits
   - Sharing permissions

3. **Should we offer a managed Supabase option?**
   - One-click setup
   - Or bring-your-own?

### Documentation

1. **Should we version the documentation?**
   - Per package version?
   - Or single latest version?

2. **What examples should be included?**
   - Basic: demo kit
   - Advanced: real-world use cases

---

## Appendix

### Related Documents

- [CLERK README](../README.md) - Current project readme
- [AGENTS.md](../AGENTS.md) - Coding guidelines
- [STYLE_GUIDE.md](../STYLE_GUIDE.md) - Design guidelines

### Resources

- [PyPI Package Publishing Guide](https://packaging.python.org/)
- [Next.js Documentation](https://nextjs.org/docs)
- [MDX Documentation](https://mdxjs.com/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Supabase Auth](https://supabase.com/docs/guides/auth)

### Glossary

- **CLERK**: Community Library of Executable Reasoning Kits
- **Reasoning Kit**: A directory containing resources and workflow instructions for LLM execution
- **MCP**: Model Context Protocol (for LLM tool integration)
- **SSR**: Server-Side Rendering
- **SSG**: Static Site Generation
- **MDX**: Markdown + JSX (React components in Markdown)

---

*Document maintained by the CLERK core team. Last updated: March 23, 2026*
