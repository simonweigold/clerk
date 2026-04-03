# Good First Issues

Templates for initial "good first issue" labels. Create these in GitHub Issues.

## Issue 1: Documentation Improvements

**Title:** Improve README with better installation examples

**Labels:** `good first issue`, `documentation`

**Description:**

```
The current README installation section could be clearer for new contributors.

### Task
- Review the README.md installation instructions
- Add more explicit examples for common setups
- Ensure the 5-minute setup claim is accurate

### Acceptance Criteria
- [ ] Installation instructions tested on clean system
- [ ] Examples cover macOS and Linux
- [ ] Troubleshooting section added for common issues
- [ ] Instructions work with the devcontainer setup
```

## Issue 2: Add Test Coverage

**Title:** Add tests for reasoning kit loader

**Labels:** `good first issue`, `testing`

**Description:**

```
The reasoning kit loader (`packages/clerk/src/openclerk/loader.py`) needs better test coverage.

### Task
- Add unit tests for `load_reasoning_kit()` function
- Test edge cases: missing files, invalid JSON, malformed kits
- Aim for >80% coverage on loader module

### Acceptance Criteria
- [ ] Tests exist in `packages/clerk/tests/test_loader.py`
- [ ] All happy paths tested
- [ ] Edge cases (FileNotFoundError, JSONDecodeError) tested
- [ ] Coverage report shows >80% for loader.py
```

## Creating These Issues

1. Go to https://github.com/openclerk/clerk/issues/new
2. Copy title and description from above
3. Add labels: `good first issue` plus relevant category label
4. Repeat for all 3 issues
