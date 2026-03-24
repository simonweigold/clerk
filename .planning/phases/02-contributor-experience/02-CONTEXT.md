# Phase 02: Contributor Experience - Context

**Gathered:** 2025-03-24
**Status:** Ready for planning
**Approach:** Standard open-source patterns (user deferred detailed discussion)

<domain>
## Phase Boundary

Phase 2 delivers the quality gates and contribution workflow required to accept external contributions safely. This includes: GitHub issue/PR templates, GitHub Actions CI for testing and linting, pre-commit hooks, branch protection rules, and initial "good first issue" labels.

</domain>

<decisions>
## Implementation Decisions

### Issue Templates
- **D-01:** Two templates: Bug Report and Feature Request
- Standard GitHub forms (YAML-based) for structured input
- Include: Description, reproduction steps (bugs), expected behavior, environment info

### Pull Request Template
- **D-02:** Simple markdown checklist:
  - [ ] Tests pass (`just test`)
  - [ ] Code follows style (`just lint`)
  - [ ] Documentation updated (if needed)
  - [ ] Related issue linked

### CI Strategy
- **D-03:** GitHub Actions workflow:
  - Trigger: PRs to main, pushes to main
  - Python versions: 3.13 (primary), 3.12 (compatibility)
  - Jobs: lint (Ruff), type-check (mypy), test (pytest with coverage)
  - Use UV for fast dependency installation
  - Matrix: ubuntu-latest, macos-latest (Windows optional for v2)

### Pre-commit Hooks
- **D-04:** Standard hooks only:
  - Ruff (lint + format)
  - mypy (type check)
  - commitizen or conventional commit check (optional for v1)
  - No secret scanning (defer to v2)

### Branch Protection
- **D-05:** Basic protection:
  - Require PR reviews (1 approval)
  - Require CI checks to pass
  - No direct pushes to main
  - Allow force push with lease (maintainers only)

### Good First Issues
- **D-06:** Create 3 initial issues:
  1. Documentation improvements
  2. Add test coverage for existing code
  3. Fix minor lint/type issues

### the agent's Discretion
- Specific issue template wording
- Exact CI job names and ordering
- Pre-commit hook versions
- Branch protection admin overrides

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Documentation
- `.planning/PROJECT.md` — Project vision and core value
- `.planning/REQUIREMENTS.md` — GHUB-01 through GHUB-06, TOOL-05
- `.planning/ROADMAP.md` — Phase 2 goal and success criteria

### Prior Phase Context
- `.planning/phases/01-foundation/01-CONTEXT.md` — Decisions from Phase 1
- `Justfile` — Commands to use in CI (test, lint, format)
- `packages/clerk/pyproject.toml` — Ruff, pytest, mypy configuration

### External Standards
- https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests — GitHub templates
- https://docs.github.com/en/actions — GitHub Actions docs
- https://pre-commit.com/ — Pre-commit framework

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Justfile` — Commands already defined: test, lint, format, dev
- `packages/clerk/pyproject.toml` — Dev dependencies include pytest, ruff, mypy
- `.planning/` structure — GSD workflow already established

### Established Patterns
- UV for dependency management
- Ruff for linting/formatting (configured in pyproject.toml)
- pytest for testing (async mode via pytest-asyncio)
- mypy in strict mode

### Integration Points
- GitHub Actions will call `just test`, `just lint` commands
- Pre-commit hooks will run same tools as CI
- Branch protection will require CI status checks

</code_context>

<specifics>
## Specific Ideas

### CI Workflow Structure
```yaml
name: CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: just lint
  test:
    strategy:
      matrix:
        python: ['3.12', '3.13']
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: just test
```

### Pre-commit Config
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
```

### Issue Labels to Create
- `good first issue` — Entry-level contributions
- `bug` — Something isn't working
- `enhancement` — New feature or request
- `documentation` — Docs improvement

</specifics>

<deferred>
## Deferred Ideas

**Advanced CI (v2):**
- Windows testing in matrix
- Performance regression testing
- Code coverage reports with Codecov
- Dependabot for dependency updates
- Release automation with semantic-release

**Advanced Governance (v2):**
- CODEOWNERS file for automatic review assignment
- Issue triage automation
- Stale bot for old issues
- Security policy and reporting process

</deferred>

---

*Phase: 02-contributor-experience*
*Context gathered: 2025-03-24 (user deferred detailed discussion)*
