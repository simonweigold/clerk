# Clerk — Developer Experience Enhancement

## What This Is

Clerk is a Python framework for multi-step LLM reasoning workflows with a React frontend. This project aims to transform Clerk from a solo-developed tool into an open-source project with excellent developer experience, comprehensive onboarding, and flexible deployment options (self-hosted or embedded in existing applications).

## Core Value

Developers can set up Clerk in under 5 minutes and contribute meaningfully in under 1 hour, regardless of whether they're self-hosting, embedding, or contributing to the core framework.

## Requirements

### Validated

- ✓ Multi-step LLM reasoning workflows — existing
- ✓ Reasoning kit system with resources and instructions — existing
- ✓ LangChain/LangGraph integration — existing
- ✓ React frontend with Tailwind CSS — existing
- ✓ CLI for running kits — existing
- ✓ Evaluation system — existing

### Active

- [ ] Clear, structured contributor onboarding
- [ ] Self-hosted deployment documentation and tooling
- [ ] Integration guide for existing applications
- [ ] Improved documentation structure
- [ ] Development environment setup automation
- [ ] Contributing guidelines and templates
- [ ] License and legal framework for open source

### Out of Scope

- Multi-tenancy SaaS platform — out of scope for v1, focus on self-hosted
- Advanced user management (RBAC, teams) — defer to v2
- Cloud-hosted managed service — business model decision needed
- Mobile native SDKs — web-first, mobile responsive is sufficient

## Context

**Current State:**
- Solo-developed project with limited documentation
- No clear onboarding path for contributors
- Docker setup exists but not documented
- No clear path for self-hosting vs integration
- AGENTS.md provides some context but not comprehensive

**Target Audience:**
- Developers wanting to add LLM reasoning workflows to their apps
- Contributors wanting to improve the framework
- Teams evaluating workflow orchestration tools

**Competitive Landscape:**
- LangGraph (lower-level, more complex)
- CrewAI (agent-focused, different paradigm)
- AutoGen (Microsoft, more research-oriented)
- n8n (no-code, different audience)

## Constraints

- **Tech Stack**: Python 3.13+, UV, LangChain/LangGraph, React 19, TypeScript, Tailwind
- **Timeline**: Aggressive — open source launch target
- **Dependencies**: Must remain compatible with existing LangChain ecosystem
- **Compatibility**: Existing reasoning kits must continue to work
- **Documentation**: Must be excellent from day one (no "docs coming soon")

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Self-hosted first | Easier to contribute, clearer value prop | — Pending |
| UV for Python tooling | Modern, fast, lockfile support | — Pending |
| Mono-repo structure | Backend + frontend in one repo | — Pending |
| MIT License | Permissive, contributor-friendly | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2025-03-24 after initialization*
