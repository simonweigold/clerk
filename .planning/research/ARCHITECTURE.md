# Architecture Research

**Domain:** Open-source Python/React developer tools with excellent DX
**Researched:** 2025-03-24
**Confidence:** MEDIUM (based on analysis of existing projects and patterns, not primary research)

## Standard Architecture

### System Overview

Based on analysis of successful open-source Python projects (LangChain, Prefect, Reflex), here's the typical architecture for DX-focused developer tools:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Developer Interface Layer                        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │   CLI Tool   │  │ Web UI/API   │  │  SDK/Client  │  │  Config/Env  ││
│  │   (Typer)    │  │  (FastAPI)   │  │   (Import)   │  │  (.env/yaml) ││
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘│
│         │                 │                 │                 │        │
├─────────┴─────────────────┴─────────────────┴─────────────────┴────────┤
│                         Core Framework Layer                             │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      Orchestration Engine                         │  │
│  │              (LangGraph/Workflow Engine/State Machine)            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         │                        │                        │            │
│         ▼                        ▼                        ▼            │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐      │
│  │   Resource   │        │    Plugin    │        │  Validation  │      │
│  │    Loader    │        │   System     │        │    Layer     │      │
│  └──────────────┘        └──────────────┘        └──────────────┘      │
├─────────────────────────────────────────────────────────────────────────┤
│                         Infrastructure Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │   Database   │  │    Cache     │  │   Storage    │  │   External   ││
│  │  (SQL/NoSQL) │  │   (Redis)    │  │   (S3/Local) │  │   Services   ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|----------------------|
| **CLI** | Entry point for local development, kit execution | Typer or Click with rich output |
| **Web UI** | Browser-based workflow management and monitoring | React + FastAPI or standalone |
| **Orchestration** | Workflow execution, state management, retries | LangGraph, Prefect, or custom state machine |
| **Resource Loader** | Parse and validate reasoning kits | Pydantic models + file I/O |
| **Plugin System** | Tool integrations, LLM providers | Entry points or dynamic imports |
| **Database Layer** | Persistence for state, metadata, evaluations | SQLAlchemy async + migrations |
| **Configuration** | Environment management, secrets | python-dotenv, pydantic-settings |

## Current Clerk Structure

### Existing Architecture

```
clerk/
├── packages/clerk/                    # Main package (UV workspace)
│   └── src/openclerk/
│       ├── __init__.py
│       ├── cli.py                     # Entry point: `clerk` command
│       ├── models.py                  # Pydantic: Resource, WorkflowStep, etc.
│       ├── loader.py                  # Reasoning kit loading
│       ├── graph.py                   # LangGraph orchestration
│       ├── evaluation.py              # Step-by-step evaluation
│       ├── embeddings.py              # Vector similarity
│       ├── llm_factory.py             # LLM provider abstraction
│       ├── mcp_client.py              # MCP tool integration
│       ├── tools.py                   # Tool registry
│       ├── db/                        # Database layer
│       │   ├── config.py              # Connection management
│       │   ├── models.py              # SQLAlchemy tables
│       │   ├── repository.py          # Data access patterns
│       │   ├── migrations/            # Alembic migrations
│       │   └── storage.py             # File/blob storage
│       └── web/                       # FastAPI web interface
│           ├── app.py                 # FastAPI application
│           ├── dependencies.py        # Dependency injection
│           └── routes/
│               ├── api.py             # API endpoints
│               └── __init__.py
├── reasoning_kits/                    # Default kit location
├── docs/                              # Documentation
├── apps/                              # Example applications
└── pyproject.toml                     # UV workspace config
```

### Strengths of Current Structure

1. **Workspace-aware**: Uses UV workspace for multi-package support
2. **Clear separation**: CLI, web, and database are distinct modules
3. **Pydantic models**: Type safety from API to database
4. **Async-first**: SQLAlchemy async for non-blocking I/O

### DX Gaps to Address

| Gap | Impact | Solution |
|-----|--------|----------|
| No devcontainer | Contributors need manual setup | Add .devcontainer/ |
| No VS Code settings | Inconsistent editor experience | Add .vscode/ |
| Missing GitHub templates | Poor contribution experience | Add issue/PR templates |
| No CONTRIBUTING.md | Unclear how to contribute | Create contributor guide |
| No examples/ folder | Hard to understand usage patterns | Add usage examples |
| Frontend not integrated | Web UI unclear/undocumented | Add frontend/ to mono-repo |

## Recommended Project Structure

For excellent DX as an open-source project:

```
clerk/
├── .devcontainer/                     # GitHub Codespaces support
│   ├── devcontainer.json
│   └── docker-compose.yml
├── .github/
│   ├── workflows/                     # CI/CD
│   │   ├── test.yml
│   │   ├── release.yml
│   │   └── docs.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── .vscode/                           # Editor settings
│   ├── extensions.json
│   ├── settings.json
│   └── launch.json
├── docs/                              # Documentation site
│   ├── getting-started/
│   ├── api/
│   ├── contributing/
│   └── examples/
├── examples/                          # Usage examples
│   ├── simple-reasoning/
│   ├── multi-step-evaluation/
│   └── custom-tools/
├── packages/
│   ├── clerk/                         # Core framework
│   │   └── src/openclerk/
│   │       ├── cli/                   # CLI commands (split from single file)
│   │       │   ├── __init__.py
│   │       │   ├── main.py
│   │       │   ├── kit_commands.py
│   │       │   └── db_commands.py
│   │       ├── core/                  # Core framework
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── loader.py
│   │       │   ├── graph.py
│   │       │   └── evaluation.py
│   │       ├── integrations/          # External integrations
│   │       │   ├── __init__.py
│   │       │   ├── llm/
│   │       │   ├── mcp/
│   │       │   └── embeddings/
│   │       ├── db/                    # Database (unchanged)
│   │       └── web/                   # API layer
│   └── clerk-frontend/                # React frontend (if separate)
│       ├── src/
│       └── package.json
├── reasoning_kits/                    # Example kits
├── tests/                             # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/                           # Automation scripts
│   ├── setup.sh
│   └── release.sh
├── docker/                            # Deployment configs
│   ├── Dockerfile
│   └── docker-compose.yml
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
├── README.md
├── pyproject.toml
└── uv.lock
```

### Structure Rationale

- **`.devcontainer/`**: One-click development environment via GitHub Codespaces
- **`.vscode/`**: Consistent editor settings, recommended extensions
- **`docs/`**: Documentation as code, versioned with releases
- **`examples/`**: Runnable examples demonstrate patterns
- **`packages/clerk/src/openclerk/cli/`**: Split CLI into modules as it grows
- **`packages/clerk/src/openclerk/core/`**: Framework-agnostic core logic
- **`packages/clerk/src/openclerk/integrations/`**: Pluggable external services
- **`tests/`**: Separated from source for clarity
- **`scripts/`**: Automation that doesn't belong in CLI

## Architectural Patterns

### Pattern 1: Plugin System via Entry Points

**What:** Use Python entry points for tool/LLM provider registration
**When to use:** When users need to extend functionality without modifying core
**Trade-offs:** 
- Pros: Clean extension mechanism, no core code changes needed
- Cons: Slightly more complex discovery, requires packaging

**Example:**
```python
# pyproject.toml
[project.entry-points."clerk.tools"]
my_tool = "my_package.tools:MyTool"

# Core loader
from importlib.metadata import entry_points

def load_tools():
    eps = entry_points(group="clerk.tools")
    return {ep.name: ep.load() for ep in eps}
```

### Pattern 2: Repository Pattern for Data Access

**What:** Abstract database operations behind repository classes
**When to use:** When you need to support multiple storage backends
**Trade-offs:**
- Pros: Swappable implementations, testable with mocks
- Cons: Additional abstraction layer

**Example:**
```python
# Abstract interface
class KitRepository(ABC):
    async def get_kit(self, kit_id: str) -> ReasoningKit: ...
    async def save_kit(self, kit: ReasoningKit) -> None: ...

# Concrete implementations
class SQLKitRepository(KitRepository): ...
class FileKitRepository(KitRepository): ...
```

### Pattern 3: Strategy Pattern for LLM Providers

**What:** Abstract LLM creation behind factory/strategy
**When to use:** Supporting multiple providers with unified interface
**Trade-offs:**
- Pros: Consistent interface, easy to add providers
- Cons: May lose provider-specific features

**Example (already partially implemented):**
```python
class LLMFactory:
    def create(self, provider: str, model: str, **kwargs) -> BaseChatModel:
        match provider:
            case "openai": return ChatOpenAI(model=model, **kwargs)
            case "anthropic": return ChatAnthropic(model=model, **kwargs)
            # ...
```

### Pattern 4: Dependency Injection for Web Layer

**What:** Inject dependencies via FastAPI's Depends()
**When to use:** Testing, swapping implementations
**Trade-offs:**
- Pros: Testable, flexible
- Cons: Slightly more verbose

**Example:**
```python
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

@app.get("/kits")
async def list_kits(db: AsyncSession = Depends(get_db)):
    ...
```

## Data Flow

### CLI Execution Flow

```
User Input (cli.py)
    ↓
Parse Arguments (argparse)
    ↓
Load Kit (loader.py) → Database OR Filesystem
    ↓
Initialize Graph (graph.py) → LangGraph StateGraph
    ↓
Execute Steps (graph.py) → LLMFactory → LLM API
    ↓
Store Results (db/repository.py)
    ↓
Output (rich/print)
```

### Web API Request Flow

```
HTTP Request (FastAPI)
    ↓
Middleware (auth, logging)
    ↓
Route Handler (routes/api.py)
    ↓
Dependency Injection (dependencies.py)
    ↓
Repository Layer (db/repository.py)
    ↓
Database (SQLAlchemy → asyncpg → PostgreSQL)
    ↓
Response Serialization (Pydantic)
    ↓
HTTP Response (JSON)
```

### Kit Loading Flow

```
Kit Path/ID
    ↓
Loader (loader.py)
    ↓
Parse kit.yaml → Pydantic Validation
    ↓
Load Resources (.txt, .csv) → Resource Objects
    ↓
Load Workflow Steps (.txt) → WorkflowStep Objects
    ↓
Assemble ReasoningKit Model
    ↓
Return or Cache
```

### State Management in Workflow

```
GraphState (Pydantic Model)
    ↓
LangGraph Node Execution
    ↓
Update State (immutable copy)
    ↓
Persist to Database (if configured)
    ↓
Stream Updates (SSE to frontend)
    ↓
Next Node or Completion
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **Solo dev** | Current structure is fine; SQLite optional |
| **Small team** | Add devcontainer, better docs, CI/CD |
| **Active contributors** | Split CLI into modules, add integration tests |
| **Production deployments** | Add caching layer, separate worker processes |
| **High throughput** | Queue-based execution, horizontal scaling |

### Scaling Priorities for Clerk

1. **First bottleneck:** CLI monolith (cli.py is 1400+ lines)
   - Solution: Split into subcommands in separate modules

2. **Second bottleneck:** Synchronous LLM calls in workflow
   - Solution: Ensure all LLM calls use async/await

3. **Third bottleneck:** Database connection pool
   - Solution: Configure SQLAlchemy pool size for expected load

## Build Order Implications

For the roadmap, components should be built in this order:

### Phase 1: Foundation
1. **Project structure** → Organize into recommended structure
2. **Dev environment** → devcontainer, .vscode, scripts/
3. **Documentation skeleton** → docs/ with getting started

### Phase 2: DX Improvements
4. **GitHub templates** → Issue/PR templates, workflows
5. **CLI modularization** → Split cli.py into package
6. **Contributing guide** → CONTRIBUTING.md with clear steps

### Phase 3: Frontend Integration
7. **Frontend setup** → React app in packages/clerk-frontend/
8. **API documentation** → OpenAPI/Swagger integration
9. **Example applications** → examples/ with real use cases

### Phase 4: Distribution
10. **PyPI publishing** → Automated release workflow
11. **Docker packaging** → Production-ready containers
12. **Self-hosting guide** → Complete deployment docs

## Anti-Patterns

### Anti-Pattern 1: CLI Monolith

**What people do:** Keep all CLI commands in one massive file (current state: cli.py is 1400+ lines)
**Why it's wrong:** Hard to test, navigate, and maintain; merge conflicts
**Do this instead:** Split into `cli/commands/*.py` with each command in its own module

### Anti-Pattern 2: Frontend as Afterthought

**What people do:** Build CLI first, add web UI later as separate repo
**Why it's wrong:** API drift, version mismatch, harder to keep in sync
**Do this instead:** Mono-repo with frontend as a package; shared types

### Anti-Pattern 3: Database in Core Models

**What people do:** Mix SQLAlchemy models with business logic
**Why it's wrong:** Tight coupling, hard to test, can't swap storage
**Do this instead:** Pydantic models for domain, SQLAlchemy for persistence; repository pattern

### Anti-Pattern 4: No Abstraction for External Services

**What people do:** Direct LLM client calls throughout codebase
**Why it's wrong:** Can't swap providers, hard to mock for tests
**Do this instead:** Factory pattern (already partially implemented in llm_factory.py)

### Anti-Pattern 5: Synchronous I/O in Async Codebase

**What people do:** Mix sync and async calls carelessly
**Why it's wrong:** Blocks event loop, kills performance
**Do this instead:** Use `asyncpg`, `httpx.AsyncClient`, pure async throughout

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI/Anthropic/etc | Factory + async client | API key from env; rate limiting |
| Supabase | Connection pool | Use service role key server-side |
| MCP Servers | Stdio/HTTP transport | Sandboxed execution |
| Vector DB | Async client | pgvector via SQLAlchemy |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI ↔ Core | Direct import | Same package, synchronous |
| Web ↔ Core | HTTP/FastAPI | API layer abstracts core |
| Core ↔ DB | Repository pattern | Async sessions |
| Core ↔ LLM | Factory pattern | Provider-agnostic |

## Component Boundaries for Clerk

### What Talks to What

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │    CLI      │  │   Web UI    │  │    Python SDK           │ │
│  │  (local)    │  │  (browser)  │  │   (embedded)            │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INTERFACE LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Commands (CLI) │  FastAPI Routes  │  Direct Import     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │                │                     │
          └────────────────┴─────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CORE LAYER                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  Models  │  │  Loader  │  │  Graph   │  │  Evaluation    │  │
│  │(Pydantic)│  │          │  │(LangGraph│  │                │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
│       │             │             │                │           │
│       └─────────────┴─────────────┴────────────────┘           │
│                          │                                     │
│                          ▼                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ LLM Fac. │  │  Tools   │  │   MCP    │  │ Embeddings│       │
│  │          │  │ Registry │  │ Client   │  │           │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘       │
└───────┼─────────────┼─────────────┼──────────────┼─────────────┘
        │             │             │              │
        └─────────────┴─────────────┴──────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Database │  │  Cache   │  │  Vector  │  │ External │         │
│  │(Postgres)│  │ (Redis)  │  │ (pgvector)│  │   APIs   │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Core knows nothing about CLI or Web**: Interface layers depend on core, not vice versa
2. **Models are at the center**: Pydantic models shared across all layers
3. **Dependencies point inward**: Outer layers depend on inner layers (clean architecture)
4. **Async at boundaries**: All I/O operations are async
5. **Configuration injected**: No hardcoded values; env/config passed in

## Suggested Build Order for DX Milestone

Based on this research, here's the recommended component build order:

### Dependency Graph

```
Phase 1 (Foundation)
├── Project structure reorganization
├── Devcontainer configuration
├── VS Code settings
└── Documentation skeleton
    ↓
Phase 2 (Contributor Experience)
├── GitHub issue/PR templates
├── CI/CD workflows
├── CLI modularization
└── CONTRIBUTING.md
    ↓
Phase 3 (Frontend Integration)
├── Frontend package setup
├── API documentation
├── Shared types (if needed)
└── Example applications
    ↓
Phase 4 (Distribution)
├── PyPI publishing workflow
├── Docker optimization
└── Self-hosting documentation
```

### Critical Path

The critical path for "5-minute setup, 1-hour contribution" is:

1. **Devcontainer** → Eliminates "works on my machine"
2. **CONTRIBUTING.md** → Clear contribution steps
3. **CI/CD** → Validates PRs automatically
4. **Examples** → Shows how to use the framework

## Sources

- LangChain GitHub repository structure analysis
- Prefect GitHub repository (mono-repo patterns, uv.lock usage)
- Reflex GitHub repository (CLI patterns, devcontainer)
- Clerk current codebase analysis
- UV workspace documentation patterns
- Python packaging best practices

---
*Architecture research for: Clerk open-source DX enhancement*
*Researched: 2025-03-24*
