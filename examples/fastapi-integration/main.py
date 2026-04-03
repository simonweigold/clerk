"""
FastAPI Integration Example

Demonstrates embedding Clerk into an existing FastAPI application.
Shows mounting, authentication, kit execution, and results retrieval.
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

# Load environment variables
load_dotenv()

# Import Clerk's FastAPI app factory
from openclerk.web.app import create_app as create_clerk_app  # noqa: E402


# ============================================================================
# Your Existing FastAPI App
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    print("🚀 Starting combined application...")
    yield
    print("🛑 Shutting down...")


# Create your main FastAPI application
app = FastAPI(
    title="My Application",
    description="Example app with Clerk embedded",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Your main application homepage."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>My App with Clerk</title></head>
    <body>
        <h1>Welcome to My Application</h1>
        <p>This is your existing FastAPI app.</p>
        <p>Clerk is mounted at <a href="/clerk/">/clerk/</a></p>
        <p>Try the <a href="/api/custom/execute">custom execution endpoint</a></p>
    </body>
    </html>
    """


@app.get("/api/health")
async def health_check():
    """Health check endpoint for your app."""
    return {"status": "healthy", "service": "my-app"}


# ============================================================================
# Mount Clerk Application
# ============================================================================

# Create Clerk's FastAPI app
clerk_app = create_clerk_app()

# Mount Clerk at /clerk path
# This makes Clerk available at /clerk/ and /clerk/api/
app.mount("/clerk", clerk_app)

print("✅ Clerk mounted at /clerk/")


# ============================================================================
# Custom Integration Endpoints
# ============================================================================
# These demonstrate how your app can interact with Clerk programmatically


@app.get("/api/custom/kits")
async def list_kits():
    """
    Example: List available reasoning kits.

    In production, you'd call Clerk's internal APIs or database directly.
    This shows the pattern for integration.
    """
    # For demo, return static list
    # In real use: query Clerk's database or API
    return {
        "kits": [{"slug": "example-kit", "name": "Example Reasoning Kit"}],
        "note": "This endpoint shows integration pattern",
    }


@app.post("/api/custom/execute")
async def execute_example():
    """
    Example: Execute a reasoning kit programmatically.

    Demonstrates how your app can trigger Clerk workflows
    and handle results.
    """
    # This is a simplified example
    # In production, you'd:
    # 1. Validate user has permission
    # 2. Call Clerk's execution engine
    # 3. Return execution ID for polling

    return {
        "message": "Execution triggered",
        "execution_id": "demo-123",
        "status": "pending",
        "note": "See main.py comments for full implementation",
    }


@app.get("/api/custom/results/{execution_id}")
async def get_results(execution_id: str):
    """
    Example: Retrieve execution results.

    Shows how your app can fetch and process Clerk execution results
    for display in your own UI.
    """
    # In production, query Clerk's database or cache
    return {
        "execution_id": execution_id,
        "status": "completed",
        "results": {"output": "Example reasoning result", "steps_completed": 5},
        "note": "Connect to Clerk's execution storage for real data",
    }


# ============================================================================
# Authentication Integration Example
# ============================================================================


@app.get("/api/custom/user")
async def get_current_user(request: Request):
    """
    Example: Access Clerk's authentication in your app.

    This shows how to check if user is authenticated via Clerk's session
    and access user info in your own endpoints.
    """
    # In a real implementation, you'd:
    # 1. Extract session token from request
    # 2. Validate with Clerk's auth system
    # 3. Return user info or 401

    # For demo, return example structure
    return {
        "authenticated": False,
        "note": "Integrate with Clerk's get_optional_user dependency",
        "documentation": "See openclerk.web.dependencies module",
    }


# ============================================================================
# Error Handling
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler for the combined application."""
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
