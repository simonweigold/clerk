# OpenClerk Marketing Website

The public-facing marketing website for OpenClerk - built with React, TypeScript, and Vite.

## Overview

This is the landing page and documentation site hosted on Vercel at openclerk.dev, providing:

- **Landing page** - Product overview and features
- **Documentation** - User guides and API reference (static, no backend required)
- **Sign up/Login** - User authentication flows (redirects to main app)
- **Early access** - Waitlist and registration

**Note:** This is distinct from `apps/frontend/`, which is the main OpenClerk application where users create and execute reasoning kits.

## Tech Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Routing**: React Router
- **UI Components**: Custom components with Tailwind

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Setup

```bash
cd apps/website
npm install
```

### Development Server

```bash
npm run dev
```

This starts the development server at `http://localhost:5173`.

### Build

```bash
npm run build
```

This creates a production build in the `dist/` directory.

### Preview Build

```bash
npm run preview
```

Preview the production build locally.

### Linting

```bash
npm run lint
```

## Documentation System

Documentation is sourced from the main `docs/` directory at the project root and served as static files (no backend API required).

### How it works

1. Documentation files in `docs/` are Markdown files organized by category
2. The `scripts/sync-docs.sh` script copies docs to `public/docs/`
3. A `manifest.json` and `timestamp.json` are generated for the frontend
4. The `DocsPage` component fetches and renders Markdown files client-side

### Syncing Documentation

To update the docs in the website:

```bash
# From project root
just sync-docs

# Or directly
./scripts/sync-docs.sh
```

This copies all `.md` files from `docs/` to `apps/website/public/docs/` and generates metadata files.

### Documentation Display

- **URL**: `/docs` or `/docs/path/to/file.md`
- **Navigation**: Sidebar with sections based on directory structure
- **Features**: 
  - Syntax-highlighted code blocks
  - Tables and GitHub-flavored Markdown
  - Responsive design with mobile sidebar
  - "Last updated" timestamp footer

## Project Structure

```
apps/website/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Route/page components
│   ├── hooks/         # Custom React hooks
│   │   └── useDocs.ts # Documentation data fetching
│   ├── lib/           # Utilities and API clients
│   ├── App.tsx        # Main app component with routing
│   └── main.tsx       # Entry point
├── public/            # Static assets
│   └── docs/          # Synced documentation (generated)
├── index.html         # HTML template
└── vite.config.ts     # Vite configuration
```

## Environment Variables

Create a `.env` file in `apps/website/` with:

```
VITE_API_URL=http://localhost:8000
```

## Deployment

The website is deployed to openclerk.dev via **Vercel**.

See `vercel.json` for deployment configuration.

## Links

- [Live Site](https://openclerk.dev)
- [Main Repository](../../README.md)
- [Python Package](../../packages/clerk/README.md)
- [Main Application](../frontend/README.md) - The full OpenClerk app
