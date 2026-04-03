set dotenv-load

# Default recipe - list all commands
default:
    @just --list

# Setup development environment
setup:
    #!/usr/bin/env bash
    echo "Setting up Clerk development environment..."
    uv sync
    cd packages/clerk && uv pip install -e ".[dev]"
    cd apps/website && npm install
    echo "Setup complete! Run 'just dev' to start development."

# Run all tests with coverage
test:
    cd packages/clerk && uv run --extra dev pytest --cov=src/openclerk --cov-report=term-missing; \
    exit_code=$?; [ $exit_code -eq 5 ] && exit 0 || exit $exit_code

# Run linting (Ruff + mypy)
lint:
    cd packages/clerk && uv run --extra dev ruff check src/ tests/
    cd packages/clerk && uv run --extra dev mypy src/

# Format all code
format:
    cd packages/clerk && uv run --extra dev ruff format src/ tests/

# Start full development environment
dev:
    #!/usr/bin/env bash
    trap "kill %1 %2 2>/dev/null || true" EXIT
    just dev-backend &
    just dev-frontend &
    wait

# Start backend only
dev-backend:
    cd packages/clerk && uv run clerk web --host 0.0.0.0

# Start frontend only
dev-frontend:
    cd apps/website && npm run dev

# Clean build artifacts
clean:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name node_modules -path "*/website/*" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
    echo "Cleaned build artifacts"
