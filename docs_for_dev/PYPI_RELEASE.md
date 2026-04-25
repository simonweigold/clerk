# PyPI Release Plan for `openclerk`

## Pre-Release Todo List

Use this checklist to track progress toward the first PyPI release.

- [x] **P0**: Verify URLs in pyproject.toml (`packages/clerk/pyproject.toml`)
- [x] **P0**: Create release workflow (`.github/workflows/release.yml`)
- [x] **P0**: Ensure LICENSE is packaged (copied to `packages/clerk/LICENSE`)
- [x] **P1**: Add release commands to Justfile (`Justfile`)
- [x] **P1**: Test build locally (`uv build` succeeds, LICENSE verified in wheel/sdist)
- [x] **P2**: Set up TestPyPI upload (index configured, `just publish-test` ready)
- [ ] **P2**: Configure trusted publishing (PyPI + GitHub settings)

---

## Current State Summary

| Component      | Status               |
| -------------- | -------------------- |
| Package name   | `openclerk`          |
| Version        | `0.1.0`              |
| Location       | `packages/clerk/`    |
| Build system   | Hatchling (via UV)   |
| Source layout  | `src/openclerk/`     |
| Python support | 3.13+                |
| CI/CD          | Basic (lint, test)   |
| Entry points   | `clerk`, `openclerk` |

---

## Pre-Release Checklist

### 1. Package Metadata Verification

- [ ] **Verify classifiers** are accurate (currently "Development Status :: 3 - Alpha")
- [x] **Update project URLs** in `pyproject.toml` (currently placeholder GitHub URLs)
- [x] **Confirm license file** is included in package distribution (verified in wheel + sdist)
- [ ] **Review keywords** for PyPI searchability
- [ ] **Add CHANGELOG.md** reference to pyproject.toml if desired

### 2. Build Verification

```bash
# Test the build locally
cd packages/clerk
uv build
# Verify wheel and sdist are created in dist/
```

### 3. TestPyPI Testing

- [x] Configure TestPyPI index in workspace `pyproject.toml`
- [ ] Create TestPyPI account and API token (manual step)
- [ ] Upload to TestPyPI: `just publish-test` (or `uv publish --index testpypi --username __token__ --password $TESTPYPI_TOKEN dist/openclerk-*`)
- [ ] Verify installation: `pip install --index-url https://test.pypi.org/simple/ openclerk`
- [ ] Test CLI: `clerk --version`

### 4. Long Description Verification

- [ ] Ensure `README.md` renders correctly on PyPI
- [ ] Check relative links work (or use absolute URLs)

---

## Required Additions

### 1. Release GitHub Workflow

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  release:
    runs-on: ubuntu-latest
    environment: release
    permissions:
      id-token: write # For trusted publishing

    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          version: "0.4.x"

      - name: Build package
        run: uv build packages/clerk

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist/
```

### 2. Justfile Release Commands

Add to `Justfile`:

```just
# Build package for distribution
build:
    uv build packages/clerk

# Publish to TestPyPI
publish-test: build
    uv publish --index testpypi dist/openclerk-*

# Publish to PyPI (requires credentials)
publish: build
    uv publish dist/openclerk-*

# Create a new version tag
version BUMP:
    cd packages/clerk && uvx bump-my-version bump {{BUMP}}
```

### 3. Version Management

Options:

- **Option A**: Manual version bumping in `pyproject.toml` and `__init__.py`
- **Option B**: Use `bump-my-version` or `hatch-vcs` for automated versioning
- **Option C**: Use git tags with `hatch-vcs` (recommended)

---

## Release Process

### Phase 1: Preparation (Pre-Release)

1. **Update version** in both:
   - `packages/clerk/pyproject.toml`
   - `packages/clerk/src/openclerk/__init__.py`

2. **Update CHANGELOG.md** with release notes

3. **Run full test suite**:

   ```bash
   just test
   just lint
   ```

4. **Build and verify**:

   ```bash
   just build
   ```

5. **TestPyPI upload**:
   ```bash
   just publish-test
   ```

### Phase 2: Release

1. **Create git tag**:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **GitHub Release** (auto-triggers workflow):
   - Navigate to Releases → Create release
   - Select tag `v0.1.0`
   - Add release notes from CHANGELOG
   - Publish

3. **Verify PyPI**:
   - Check package appears at https://pypi.org/project/openclerk/
   - Test: `pip install openclerk`

### Phase 3: Post-Release

1. **Update documentation** with installation instructions
2. **Announce** on relevant channels
3. **Bump to dev version** (e.g., `0.2.0-dev`) for next cycle

---

## Open Questions

Before proceeding, clarify the following:

1. **PyPI Account**: Do you have a PyPI account set up for `openclerk`? Is the package name reserved?

2. **Versioning Strategy**:
   - Option A: Manual version bumps (simple, explicit)
   - Option B: Automated via git tags with `hatch-vcs` (recommended for CI/CD)
3. **Trusted Publishing**: Would you like to set up PyPI trusted publishing (OIDC) for the GitHub workflow, or use API tokens?

4. ~~**TestPyPI**: Should we automate TestPyPI uploads on every merge to main, or only on demand?~~ **Configured**: Index added to workspace `pyproject.toml`; use `just publish-test` on demand.

5. **Homepage URL**: The README shows `openclerk.dev` - is this the correct domain for `project.urls.Homepage`?

6. ~~**License**: The LICENSE file is at root level. Should it be copied to `packages/clerk/` or is hatchling configured to find it at workspace root?~~ **Resolved**: Copied to `packages/clerk/LICENSE` and verified in wheel/sdist.

---

## Reference Commands

### Local Build & Test

```bash
# Build package (outputs to workspace root dist/)
uv build packages/clerk

# Check what's in the wheel
unzip -l dist/openclerk-*.whl

# Check what's in the sdist
tar -tzf dist/openclerk-*.tar.gz
```

### Manual PyPI Upload (if not using GitHub Actions)

```bash
# Publish to TestPyPI (requires --index testpypi!)
uv publish --index testpypi --username __token__ --password $TESTPYPI_TOKEN dist/openclerk-*
# Or use the Justfile command (includes --index testpypi automatically)
just publish-test

# Publish to PyPI (production)
uv publish --username __token__ --password $PYPI_TOKEN dist/openclerk-*
# Or use the Justfile command
just publish
```

---

_Last updated: 2026-04-20_
