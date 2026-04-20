# Development Setup

This guide will help you set up a development environment for contributing to Clerk.

## Prerequisites

- Python 3.13+
- Node.js 20+
- UV (Python package manager)
- Just (task runner)

## Quick Setup (Recommended)

Run the automated setup:

```bash
just setup
```

This will:
1. Install Python dependencies via UV
2. Install the package in editable mode
3. Install frontend dependencies

## Platform-Specific Instructions

### macOS

1. Install Homebrew (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install required tools:
   ```bash
   brew install uv just node
   ```

3. Clone and setup:
   ```bash
   git clone https://github.com/simonweigold/clerk.git
   cd clerk
   just setup
   ```

### Linux

1. Install UV:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install Just:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash
   ```

3. Install Node.js 20+ (via your package manager or nvm)

4. Clone and setup:
   ```bash
   git clone https://github.com/simonweigold/clerk.git
   cd clerk
   just setup
   ```

## Dev Container (Zero Setup)

For a completely automated setup, use the dev container:

1. Install VS Code with the Dev Containers extension
2. Clone the repository
3. Open in VS Code and click "Reopen in Container"
4. The container will automatically run `just setup`

Alternatively, use GitHub Codespaces for a browser-based development environment.

## Verification

After setup, verify everything works:

```bash
# Run tests
just test

# Run linting
just lint

# Start development servers
just dev
```

## Common Issues

### UV not found
Make sure UV is installed and in your PATH. On macOS with Homebrew, run:
```bash
brew install uv
```

### Node modules not found
If frontend dependencies fail to install, try:
```bash
cd apps/website && npm install
```

### Port conflicts
The dev servers use ports 3000 (frontend) and 8000 (backend). Make sure these are available or modify the Justfile to use different ports.
