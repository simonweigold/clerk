set dotenv-load

# Default recipe - list all commands
default:
    @just --list

# Setup development environment
setup:
    uv sync --all-groups
    echo "Setup complete! Run 'just test' to verify."

# Run all tests with coverage
test:
    uv run --extra dev pytest --cov=src/reasoning_kits --cov-report=term-missing

# Run linting (Ruff + mypy)
lint:
    uv run --extra dev ruff check src/ tests/
    uv run --extra dev mypy src/

# Format all code
format:
    uv run --extra dev ruff format src/ tests/
    uv run --extra dev ruff check --fix src/ tests/

# Run the CLI against the reference kits
list:
    uv run rk list

# Validate every reference kit
validate:
    uv run rk validate demo --base-path kits
    uv run rk validate oll_employment_contracts --base-path kits
    uv run rk validate test_swiss_legal --base-path kits

# Run a kit (usage: just run <kit-name>)
run KIT:
    uv run rk run {{KIT}} --base-path kits --verbose

# Build package for distribution
build:
    uv build

# Publish to TestPyPI
publish-test: build
    uv publish --index testpypi dist/reasoning-kits-*

# Publish to PyPI (requires credentials)
publish: build
    uv publish dist/reasoning-kits-*

# Bump package version (e.g. just version patch)
version BUMP:
    uvx bump-my-version bump {{BUMP}}

# Clean build artifacts and caches
clean:
    find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .mypy_cache -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .ruff_cache -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
    rm -rf dist build *.egg-info 2>/dev/null || true
    echo "Cleaned build artifacts"