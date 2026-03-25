# Production Dockerfile for Clerk Backend
# Multi-stage build with security hardening

FROM python:3.13-slim

# Install UV for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash clerk

# Set working directory
WORKDIR /app

# Copy workspace configuration and lock file from root
COPY pyproject.toml uv.lock ./

# Copy package-specific files
COPY packages/clerk/pyproject.toml packages/clerk/
COPY packages/clerk/src/ packages/clerk/src/

# Install production dependencies
# Using --frozen to ensure lock file is up to date
# Using --no-dev to exclude development dependencies
RUN uv sync --frozen --no-dev

# Change ownership to non-root user
RUN chown -R clerk:clerk /app

# Switch to non-root user
USER clerk

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "clerk", "web", "--host", "0.0.0.0", "--port", "8000"]
