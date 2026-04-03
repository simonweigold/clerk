# Branch Protection Setup

This document describes the branch protection rules for the `main` branch.

## Required Settings

In GitHub Repository Settings → Branches → Branch protection rules:

### Branch name pattern
```
main
```

### Protect matching branches

- [x] **Require a pull request before merging**
  - Require approvals: 1
  - Dismiss stale PR approvals when new commits are pushed
  - Require review from CODEOWNERS (if CODEOWNERS file exists)

- [x] **Require status checks to pass before merging**
  - Require branches to be up to date before merging
  - Status checks that are required:
    - `lint` (from CI workflow)
    - `test` (from CI workflow)

- [x] **Require conversation resolution before merging**

- [x] **Do not allow bypassing the above settings**

### Optional Settings

- [ ] **Allow force pushes**
  - Enable "Specify who can force push" → "Repository admins"

- [ ] **Allow deletions**
  - Leave unchecked

## Enabling Protection

1. Go to https://github.com/openclerk/clerk/settings/branches
2. Click "Add rule"
3. Enter "main" in Branch name pattern
4. Check the settings above
5. Click "Create"

## Verification

After enabling:
1. Create a test PR
2. Verify that:
   - PR requires at least 1 approval
   - CI checks (lint, test) run automatically
   - Merge is blocked until checks pass
