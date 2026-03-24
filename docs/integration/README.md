# Integration Guide

This guide helps you embed Clerk into your existing applications. Whether you're building with FastAPI, Django, or Flask, Clerk can integrate seamlessly into your stack.

---

## When to Embed Clerk

### Use Clerk as a standalone tool when:

- You want a ready-to-use web UI
- You're self-hosting and need the full experience
- Your team wants to author and manage reasoning kits

### Embed Clerk when:

- You have an existing application and want to add reasoning capabilities
- You need Clerk's workflow engine without the UI
- You want to expose reasoning kits via your own API endpoints
- You're building a SaaS and want white-labeled reasoning workflows

---

## FastAPI Integration

FastAPI is the recommended way to embed Clerk due to its native ASGI support and shared ecosystem.

### Step 1: Install Clerk

```bash
pip install clerk-framework
```

### Step 2: Import and Mount

```python
from fastapi import FastAPI
from openclerk.web.app import create_app as create_clerk_app

# Your existing FastAPI app
app = FastAPI(title="My Application")

# Create Clerk app
clerk_app = create_clerk_app()

# Mount Clerk at a subpath
app.mount("/clerk", clerk_app)
```

### Step 3: Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required for LLM operations
OPENAI_API_KEY=sk-...

# Optional: Database (Supabase)
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...

# Optional: Session secret for auth
SESSION_SECRET_KEY=your-secret-key
```

### Step 4: Authentication Setup

Clerk uses session-based authentication. If your app already has auth, you can synchronize users:

```python
from openclerk.web.dependencies import get_optional_user

@app.get("/api/my-endpoint")
async def my_endpoint(user: dict | None = Depends(get_optional_user)):
    if not user:
        return {"error": "Authentication required"}
    # Your logic here
```

### Complete Example

```python
# main.py
from fastapi import FastAPI, Depends
from openclerk.web.app import create_app as create_clerk_app
from openclerk.web.dependencies import get_optional_user

app = FastAPI(title="My App with Clerk")

# Mount Clerk
clerk_app = create_clerk_app()
app.mount("/clerk", clerk_app)

# Your custom routes
@app.get("/api/status")
async def status():
    return {"status": "ok"}

@app.get("/api/user-kits")
async def user_kits(user: dict | None = Depends(get_optional_user)):
    if not user:
        return {"error": "Not authenticated"}
    # Return user's kits
    return {"kits": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run it:

```bash
uvicorn main:app --reload
```

Access Clerk at: `http://localhost:8000/clerk`

---

## Accessing Clerk's API

Once mounted, Clerk's full API is available under the mount path:

| Endpoint | Description |
|----------|-------------|
| `GET /clerk/api/kits` | List available kits |
| `POST /clerk/api/kits` | Create a new kit |
| `GET /clerk/api/kits/{slug}` | Get kit details |
| `POST /clerk/api/kits/{slug}/execute` | Execute a kit |
| `GET /clerk/api/openapi.json` | OpenAPI specification |

See the [API Reference](api-reference.md) for complete documentation.

---

## Custom Integration Patterns

### Direct Graph Execution

For programmatic use without the web API:

```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit

# Load a kit
kit = load_reasoning_kit("./reasoning_kits/my-kit")

# Run it
result = run_reasoning_kit(kit)
print(result)
```

### Database-Only Mode

If you only need database operations without the web layer:

```python
from openclerk.db import get_async_session, ReasoningKitRepository

async def get_kits():
    async with get_async_session() as session:
        repo = ReasoningKitRepository(session)
        kits = await repo.list_public()
        return kits
```

---

## Other Frameworks

While FastAPI is recommended, you can integrate Clerk with other frameworks:

### Django

Use Clerk's async database layer and graph execution directly:

```python
# views.py
from django.http import JsonResponse
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit

async def run_kit(request, kit_name):
    kit = load_reasoning_kit(f"./kits/{kit_name}")
    result = await run_reasoning_kit(kit)
    return JsonResponse({"result": result})
```

### Flask

Similar approach using Flask's async support:

```python
from flask import Flask
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit

app = Flask(__name__)

@app.route("/run/<kit_name>")
async def run_kit(kit_name):
    kit = load_reasoning_kit(f"./kits/{kit_name}")
    result = await run_reasoning_kit(kit)
    return {"result": result}
```

---

## Next Steps

- **[API Reference](api-reference.md)** — Complete API documentation
- **[Integration Examples](examples.md)** — Working code examples
- See the FastAPI integration example in `examples/fastapi-integration/`

---

## Reference

See requirement **INTEG-01** for the detailed embedding specification.
