# FastAPI Integration Example

This example demonstrates how to embed Clerk into an existing FastAPI application.

## What This Example Shows

- Mounting Clerk's FastAPI app as a sub-application
- Integrating with Clerk's authentication system
- Executing a reasoning kit programmatically
- Retrieving and displaying execution results

## Prerequisites

- Python 3.13+
- OpenAI API key (for LLM reasoning)
- Supabase account (for database, optional)

## Setup

1. Clone this example:
   ```bash
   cd examples/fastapi-integration
   ```

2. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Running

Start the combined application:
```bash
uvicorn main:app --reload --port 8000
```

## Usage

1. Visit http://localhost:8000/ — your main app
2. Visit http://localhost:8000/clerk/ — Clerk UI
3. Visit http://localhost:8000/api/custom/execute — API example

## Project Structure

- `main.py` — Combined FastAPI application
- `requirements.txt` — Python dependencies
- `.env.example` — Environment variable template

## Integration Points

### 1. Mounting Clerk

```python
from openclerk.web.app import create_app as create_clerk_app

clerk_app = create_clerk_app()
app.mount("/clerk", clerk_app)
```

### 2. Authentication

Clerk's session middleware handles authentication. Access user info in your endpoints:

```python
from openclerk.web.dependencies import get_optional_user

@app.get("/api/user")
async def get_user(user: dict | None = Depends(get_optional_user)):
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}
```

### 3. Kit Execution

Execute a kit programmatically via Clerk's API:

```python
# POST to /clerk/api/v1/kits/{slug}/execute
# Then GET /clerk/api/v1/kits/{slug}/execute/{execution_id}/stream
```

See `main.py` for a complete example.

## Troubleshooting

**Import errors?** Make sure the `clerk-framework` package is installed and your virtual environment is activated.

**Database connection issues?** Set `SUPABASE_URL` and `SUPABASE_KEY` in `.env` or run in file-based mode without them.

**OpenAI errors?** Verify your `OPENAI_API_KEY` is set correctly in `.env`.
