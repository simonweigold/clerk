# Integrating CLERK into Your Project

CLERK (OpenClerk) is designed to be modular and easily integrated into existing Python applications. If you already have a FastAPI backend, or any other asynchronous Python service, you can bring CLERK's advanced agentic workflows into your existing ecosystem.

## Prerequisites

Ensure your existing project is running a compatible Python version (3.13+) and that you use modern dependency management tooling (like `uv`), as CLERK integrates best with standard modern environments.

## 1. Adding the Dependency

The easiest way to integrate CLERK is by adding it to your project. Since it's built with `uv`, you can install it into your virtual environment:

```bash
uv add path/to/clerk/source
# or via Git if hosted:
# uv add git+https://github.com/simonweigold/clerk.git
```

## 2. Environment Configuration

CLERK requires configuration for LLM providers and state persistence. Depending on your database choice (Supabase vs. Local Postgres), your `.env` configuration will differ.

**If using Supabase:**
```env
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

**If using a Custom/Local Database (e.g., standard PostgreSQL):**
```env
OPENAI_API_KEY=your_openai_key
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/clerk_db
```

## 3. Database Setup Options

CLERK uses asynchronous SQLAlchemy for state persistence. By default, it integrates seamlessly with Supabase, but it can securely run on any standard PostgreSQL-compatible database.

### Option A: Using Supabase (Recommended)

Supabase provides powerful tools and edge functions that CLERK may leverage. You can configure this in two ways:

1. **Supabase Cloud (Managed):**
   - Create a new project on [Supabase](https://supabase.com/).
   - Go to your Project Settings -> API to find your `Project URL` (`SUPABASE_URL`) and `anon` `public` key (`SUPABASE_KEY`).
   - Run CLERK's setup command to initialize its required schemas: `uv run clerk db setup`.

2. **Supabase Local (Self-hosted via CLI):**
   - If you prefer local development within the Supabase ecosystem, install the Supabase CLI.
   - Run `supabase init` and `supabase start` inside your project directory.
   - Use the provided local API URL and anon key displayed in your terminal as your `.env` secrets.

### Option B: Using a Local/Custom Database (Without Supabase)

If you prefer to avoid Supabase entirely, you can run CLERK on a standard database.

1. **Spin up a local Postgres instance** (e.g., via Docker):
   ```bash
   docker run --name clerk-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=clerk_db -p 5432:5432 -d postgres
   ```
2. **Configure your Database connection**: Make sure your `.env` file has the `DATABASE_URL` set to point to this new instance (e.g., `postgresql+asyncpg://postgres:password@localhost:5432/clerk_db`).
3. **Initialize the Schema**: Run `uv run clerk db setup`. CLERK's database module will automatically detect the standard `DATABASE_URL` and migrate the tables into your custom PostgreSQL instance instead of looking for Supabase endpoints.

### Option C: Shared Database Engine

If your existing Python backend already maintains an async SQLAlchemy connection pool, you can inject it directly into CLERK, preventing redundant connections:

```python
from clerk.db import setup_clerk_db

# Inside your startup event, pass your active AsyncEngine
await setup_clerk_db(engine=my_existing_async_engine)
```

## 4. Hooking up to FastAPI

If your application uses FastAPI, you can mount CLERK's API routes directly onto your existing app. This allows your custom frontend, or the CLERK React frontend, to communicate directly with the embedded instance.

```python
from fastapi import FastAPI
from clerk.web.routes.api import router as clerk_api_router

app = FastAPI()

# Mount your existing business logic
# ...

# Mount CLERK's specific API endpoints under a chosen prefix
app.include_router(clerk_api_router, prefix="/api/clerk", tags=["clerk"])
```

## 5. Running Reasoning Kits Programmatically

If you only want CLERK's underlying multi-agent reasoning capabilities within your own services, you can invoke the execution engine directly using the Python API.

```python
import asyncio
from clerk.loader import load_reasoning_kit
from clerk.graph import run_workflow

async def execute_custom_workflow():
    # Load your configured kit
    kit = load_reasoning_kit("path/to/my_kit")
    
    # Run the workflow graph with specific inputs
    result = await run_workflow(
        kit=kit, 
        inputs={"query": "Perform advanced reasoning task"}
    )
    
    return result

if __name__ == "__main__":
    asyncio.run(execute_custom_workflow())
```

## 6. Utilizing the React UI (Optional)

If you would like to run CLERK's workflow builder and monitoring UI within your platform, you can compile the React frontend (`npm run build` inside `frontend/`) and serve the resulting static assets using FastAPI:

```python
from fastapi.staticfiles import StaticFiles

# Serve the static UI files under /clerk-frontend
app.mount("/clerk", StaticFiles(directory="path/to/clerk/frontend/dist", html=True), name="clerk_ui")
```

Alternatively, you can deploy the React app externally on services like Vercel or Netlify, configured to point to your new FastAPI backend integration.
