# Website Launch Plan

> **Status:** Active
> **Branch:** `feature/website-launch`
> **Goal:** Ship a marketing landing page on Vercel with working sign-up, early access gate, and no backend deployment.

---

## Scope

This plan covers the minimum required to launch `openclerk.ch` as a public website. It is intentionally narrow:

| In scope                                | Out of scope                            |
| --------------------------------------- | --------------------------------------- |
| Marketing landing page at `/`           | Next.js migration (see ARCHITECTURE.md) |
| Working sign-up / login via Supabase JS | Backend (FastAPI) deployment            |
| Early access screen for signed-in users | Full app access for users               |
| Vercel deployment config                | Railway / Fly.io backend deployment     |
| Public repo security audit              | Pricing page, docs site                 |

The full architecture vision (Next.js, Railway, etc.) is documented in `ARCHITECTURE.md`. This plan delivers the first deployable milestone only.

---

## Architecture for this milestone

```
Browser
  │
  ▼
Vercel (static Vite build)
  ├── /                    → LandingPage (public, SEO)
  ├── /auth/login          → LoginPage (public)
  ├── /auth/signup         → SignupPage (public)
  ├── /auth/logout         → LogoutPage
  └── /app                 → EarlyAccessPage (requires login)
       └── (all /kit/* and /settings routes are not linked / unreachable)
  │
  ▼
Supabase (auth + DB, already provisioned)
  └── Auth calls go directly from the browser via @supabase/supabase-js
      No FastAPI backend involved for this milestone.
```

The FastAPI backend is not deployed. App routes (`/kit/*`, `/settings`) remain in the codebase but are not reachable via any UI link. The Vite build is deployed as a static SPA on Vercel.

---

## Required changes

### 1. Auth migration: FastAPI sessions → Supabase JS

**Problem:** `useAuth.tsx` and `api.ts` currently call `/api/auth/me`, `/api/auth/login`, etc. — all FastAPI endpoints. With no backend deployed, these requests would fail for every visitor.

**Solution:** Replace the auth layer with `@supabase/supabase-js`, which authenticates directly against Supabase from the browser. No backend involved.

**What changes:**

| File                                    | Change                                                                                                                      |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `apps/website/package.json`             | Add `@supabase/supabase-js` dependency                                                                                      |
| `apps/website/src/lib/supabase.ts`      | New file — Supabase client singleton, reads `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`                                  |
| `apps/website/src/hooks/useAuth.tsx`    | Rewrite to use `supabase.auth.getSession()` and `onAuthStateChange()` instead of polling `/api/auth/me`                     |
| `apps/website/src/pages/LoginPage.tsx`  | Replace `login()` API call with `supabase.auth.signInWithPassword()`                                                        |
| `apps/website/src/pages/SignupPage.tsx` | Replace `signup()` API call with `supabase.auth.signUp()`                                                                   |
| `apps/website/src/pages/LogoutPage.tsx` | Replace `logout()` API call with `supabase.auth.signOut()`                                                                  |
| `apps/website/src/lib/api.ts`           | No change needed — auth functions stay as dead code; kit/execution functions remain for future use when backend is deployed |

**New env vars required on Vercel (safe to expose — these are public Supabase keys):**

```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

The `SUPABASE_ANON_KEY` is designed to be public — it is rate-limited and row-level-security enforced. It is safe to commit to Vercel env vars and safe in a `VITE_*` prefixed variable (which Vite inlines into the JS bundle at build time).

**What stays the same:**

- FastAPI auth endpoints remain in the backend codebase — they will be used again when the backend is deployed
- The `User` type shape in `api.ts` can be reused or mirrored from the Supabase session

---

### 2. Routing split

**Problem:** `/` currently renders `HomePage` (the kit browser — the full app). There is no marketing landing page.

**Solution:** Introduce a route hierarchy separating public marketing routes from the app shell.

**New route map:**

```
/                        → LandingPage (new, public)
/auth/login              → LoginPage (existing, public)
/auth/signup             → SignupPage (existing, public)
/auth/logout             → LogoutPage (existing)
/app                     → EarlyAccessPage (new, requires auth)

— Hidden, not linked —
/kit/*                   → existing pages (stay in codebase, no nav links)
/settings                → existing page (stays in codebase, no nav links)
/docs/*                  → existing page (stays in codebase, no nav links)
```

**Changes to `App.tsx`:**

- Add `/` route pointing to `LandingPage`
- Add `/app` route pointing to `EarlyAccessPage` wrapped in an auth guard
- The existing app routes (`/kit/*`, `/settings`) remain declared but have no nav links — they are unreachable from the UI without direct URL entry
- The `Layout` component should conditionally render different nav (landing nav vs app nav)

**Auth guard pattern:**

```tsx
// Redirect to /auth/login if not authenticated
// Render EarlyAccessPage if authenticated
// In the future: render app content when access is granted
```

---

### 3. New pages to create

#### `LandingPage.tsx`

Marketing-focused, statically rendered, SEO-optimized (meta tags, semantic HTML).

Suggested sections:

1. **Hero** — headline, sub-headline, primary CTA ("Sign up for early access"), secondary CTA ("View on GitHub")
2. **Features / value props** — 3–4 key capabilities (e.g., multi-step reasoning workflows, LangGraph-powered, self-hostable, kit marketplace)
3. **How it works** — short 3-step visual (Install → Define a kit → Execute)
4. **Sign-up CTA** — repeated CTA block
5. **Footer** — GitHub link, docs link, copyright

Content and design are decided separately from this plan. The component structure above is the technical scaffold.

#### `EarlyAccessPage.tsx`

Shown to any authenticated user in place of the app.

Content:

- "You're on the list" / early access confirmation message
- Brief description of what's coming
- Logout link
- Optional: link to GitHub or docs

This page requires no API calls — it reads user email from the Supabase auth session only.

---

### 4. Vercel deployment config

The Vite build produces a static SPA. Vercel needs two things:

**`apps/website/vercel.json`** — SPA routing (all paths serve `index.html`) and build config:

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

**Root `vercel.json`** (or Vercel project settings) — point Vercel at the correct subdirectory:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "apps/website/dist",
  "installCommand": "npm install",
  "framework": null
}
```

Alternatively, set `Root Directory` to `apps/website` in the Vercel project settings UI — this is simpler and avoids a root-level `vercel.json`.

**Build command** (from `apps/website/`):

```
tsc -b && vite build
```

This is already the `build` script in `apps/website/package.json`.

---

### 5. Security audit for public repo

#### What must never be in the repo

| Secret                                 | Location    | Risk                          |
| -------------------------------------- | ----------- | ----------------------------- |
| `SUPABASE_SERVICE_KEY`                 | `.env` only | Full DB access — backend-only |
| `SECRET_KEY` / `CLERK_SESSION_SECRET`  | `.env` only | Session forgery               |
| `OPENAI_API_KEY` (and other LLM keys)  | `.env` only | API billing                   |
| `DATABASE_URL` / `DATABASE_URL_DIRECT` | `.env` only | Direct DB access              |

#### Verify before going public

- [ ] `.env` is in `.gitignore` — confirm with `git check-ignore -v .env`
- [ ] `git log --all -- .env` returns nothing (`.env` was never committed)
- [ ] No hardcoded credentials in any source file — run `grep -r "sk-" apps/ packages/` and similar
- [ ] `.env.example` contains only placeholder values (it does — already reviewed)
- [ ] `SUPABASE_SERVICE_KEY` is never referenced in `apps/website/src/` — it must only appear in backend code
- [ ] Vercel env vars: only `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set (both are public-safe)

#### What is safe to expose in the Vite bundle

`VITE_*` prefixed variables are inlined into the JS bundle at build time — they are visible to anyone who inspects the site's JS. This is intentional and acceptable for:

- `VITE_SUPABASE_URL` — public project URL
- `VITE_SUPABASE_ANON_KEY` — public key, protected by RLS policies

Everything else (`SUPABASE_SERVICE_KEY`, `OPENAI_API_KEY`, `SECRET_KEY`) must **never** be prefixed with `VITE_` and must never appear in `apps/website/src/`.

---

## Implementation phases

### Phase 1 — Auth migration

1. Add `@supabase/supabase-js` to `apps/website/package.json`
2. Create `apps/website/src/lib/supabase.ts` — Supabase client using `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`
3. Rewrite `useAuth.tsx` — use `supabase.auth.getSession()` + `onAuthStateChange()` listener
4. Update `LoginPage.tsx` — use `supabase.auth.signInWithPassword()`
5. Update `SignupPage.tsx` — use `supabase.auth.signUp()`
6. Update `LogoutPage.tsx` — use `supabase.auth.signOut()`
7. Test locally: sign up, log in, log out, page refresh preserves session

### Phase 2 — Routing and new pages

1. Create `apps/website/src/pages/LandingPage.tsx` (scaffold, content TBD)
2. Create `apps/website/src/pages/EarlyAccessPage.tsx`
3. Update `App.tsx` — add `/` → `LandingPage`, add `/app` → `EarlyAccessPage` behind auth guard
4. Update `Layout.tsx` — render different nav for landing vs app routes
5. Post-signup redirect: after successful sign-up, redirect to `/app`
6. Post-login redirect: after successful login, redirect to `/app`
7. Test: unauthenticated visit to `/app` redirects to `/auth/login`; authenticated visit shows early access page

### Phase 3 — Vercel config

1. Add `vercel.json` to `apps/website/` (SPA rewrite rule)
2. Create Vercel project, set root directory to `apps/website`
3. Add env vars in Vercel dashboard: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`
4. Trigger a preview deploy and verify build passes
5. Verify SPA routing works (direct URL to `/app` loads correctly)

### Phase 4 — Security audit

1. Run through the checklist in section 5 above
2. Confirm `.env` has never been committed (`git log --all -- .env`)
3. Grep source files for any hardcoded secrets
4. Review Vercel env var list — remove anything not needed

### Phase 5 — Domain and go-live

1. Add custom domain (`openclerk.ch`) in Vercel project settings
2. Update DNS records (Vercel provides the required A/CNAME values)
3. Verify SSL certificate is provisioned
4. Smoke test: landing page, sign-up, early access screen, mobile layout

---

## Open decisions

| Decision                     | Options                           | Recommendation                                      |
| ---------------------------- | --------------------------------- | --------------------------------------------------- |
| Landing page copy and design | TBD                               | Separate task — scaffold component first            |
| Early access page copy       | TBD                               | Keep simple: "You're in. App coming soon." + logout |
| Supabase email confirmation  | Enabled (default) or disabled     | Enable — confirms real emails for launch list       |
| Analytics                    | Vercel Analytics, Plausible, none | Add Vercel Analytics (zero config, free tier)       |
| Custom domain registrar      | Already owned?                    | Confirm DNS access before Phase 5                   |

---

## Relationship to ARCHITECTURE.md

This plan is a subset of the larger architecture. Decisions made here are compatible with the long-term plan:

- Direct Supabase auth (this plan) is the same auth provider as the target Next.js architecture — no throwaway work
- The Vite SPA on Vercel is a stepping stone; the root directory structure already anticipates `apps/website/` as the deployable frontend
- FastAPI auth routes are left intact in the backend — they will be wired back in when the backend is deployed to Railway
- App routes (`/kit/*`) stay in the codebase, just ungated from the UI, so no migration work is lost

---

_Last updated: 2026-04-03_
