# Contributing to OpenClerk

Thank you for your interest in contributing to OpenClerk! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Development Setup

### Quick Start (5 minutes)

1. **Prerequisites**: Python 3.13+, Node.js 20+, UV, Just
2. **Clone**: `git clone https://github.com/simonweigold/clerk.git`
3. **Setup**: `just setup`
4. **Verify**: `just test`

See [detailed setup instructions](docs/contributing/setup.md) for platform-specific guidance and troubleshooting.

### Dev Container Option

For zero local setup, use the dev container:
- VS Code: "Reopen in Container"
- GitHub: Click "Code" → "Codespaces" → "Create codespace"

### Pre-commit Hooks

We use pre-commit to run linting and type checks before each commit.

1. Install pre-commit:
   ```bash
   uv pip install pre-commit
   ```

2. Install the hooks:
   ```bash
   pre-commit install
   ```

3. (Optional) Run on all files once:
   ```bash
   pre-commit run --all-files
   ```

The hooks will now run automatically on every commit, checking:
- Ruff linting and formatting
- mypy type checking

## Development Workflow

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Make changes**: Edit code following our style guidelines
3. **Run tests**: `just test`
4. **Run linting**: `just lint`
5. **Commit**: Use clear, descriptive commit messages
6. **Push**: `git push origin feature/your-feature-name`
7. **Pull Request**: Submit PR with description of changes

## Code Style

We use automated tools to maintain code quality:

- **Python**: Ruff for linting/formatting, mypy for type checking
- **TypeScript/JavaScript**: ESLint and Prettier
- **Line length**: 100 characters
- **Import style**: Sorted by Ruff

Run `just format` to auto-format code before committing.

## Testing

All contributions should include tests:

```bash
# Run all tests
just test

# Run specific test file
pytest test_specific.py

# Run with coverage
pytest --cov=src/openclerk
```

## Pull Request Process

1. Update documentation if your changes affect usage
2. Add tests for new functionality
3. Ensure all tests pass (`just test`)
4. Ensure linting passes (`just lint`)
5. Update CHANGELOG.md with your changes under [Unreleased]
6. Link any related issues in your PR description

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues and discussions before creating new ones
- Join our community discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
