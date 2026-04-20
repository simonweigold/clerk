# Contributing to Clerk

Thank you for your interest in contributing to Clerk! This guide will get you started quickly.

---

## Quick Setup

The fastest way to get started:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/clerk.git
cd clerk

# 2. Run setup (installs dependencies, sets up git hooks)
just setup

# 3. Start development server
just dev
```

That's it! Clerk will be running at:

- Web UI: `http://localhost:8000`
- API: `http://localhost:8000/api`

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

Edit code, add tests, update documentation as needed.

### 3. Run Quality Checks

```bash
# Run all checks (tests, lint, type-check)
just check

# Or individually:
just test      # Run tests
just lint      # Run ruff linter
just type      # Run mypy type checker
```

### 4. Commit

We use conventional commits:

```bash
git commit -m "feat: add new feature"
git commit -m "fix: correct bug in parser"
git commit -m "docs: update readme"
```

### 5. Push and Create PR

```bash
git push origin feature/my-feature
```

Then open a pull request on GitHub. The CI will run all checks automatically.

---

## What to Contribute

### Good First Issues

Look for issues labeled `good first issue` on GitHub. These are:

- Well-defined and scoped
- Have clear acceptance criteria
- Don't require deep codebase knowledge

### Areas Needing Help

- **Documentation:** User guides, API docs, examples
- **Testing:** More test coverage, edge cases
- **Integrations:** Django, Flask examples
- **UI/UX:** Frontend improvements
- **Reasoning Kits:** Example kits for common use cases

---

## Project Structure

```
clerk/
├── apps/
│   ├── frontend/       # Main OpenClerk application (React)
│   └── website/        # Marketing website (React, Vercel-hosted)
├── packages/
│   └── clerk/          # Python package
│       └── src/openclerk/
│           ├── cli.py          # CLI commands
│           ├── graph.py        # Workflow execution
│           ├── loader.py       # Kit loading
│           ├── models.py       # Data models
│           └── web/            # FastAPI app
├── docs/               # Documentation
├── reasoning_kits/     # Example kits
└── tests/              # Test suite
```

**Note:** `apps/frontend/` is the main application for creating and executing reasoning kits. `apps/website/` is the public-facing marketing site with documentation and landing pages.

---

## Getting Help

- **GitHub Issues:** Bug reports, feature requests
- **GitHub Discussions:** Questions, ideas, general discussion
- **Documentation:** See [Architecture](architecture.md) for system design

---

## Full Contributing Guide

For detailed guidelines on code style, testing, and the review process, see the root [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
