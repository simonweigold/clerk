# OpenClerk Frontend

The main OpenClerk application frontend - built with React, TypeScript, and Vite.

## Overview

This is the primary application interface for OpenClerk, providing:

- Interactive reasoning kit browser and management
- Visual kit editor with step-by-step workflow builder
- Kit execution interface with real-time streaming
- User authentication and settings
- Execution history and evaluations

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
cd apps/frontend
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

## Project Structure

```
apps/frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Route/page components
│   │   ├── HomePage.tsx       # Dashboard/home
│   │   ├── KitDetailPage.tsx  # Kit detail view
│   │   ├── KitEditorPage.tsx  # Kit creation/editing
│   │   ├── KitRunPage.tsx     # Kit execution
│   │   ├── DocsPage.tsx       # Documentation viewer
│   │   └── ...
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utilities and API clients
│   ├── App.tsx        # Main app component with routing
│   └── main.tsx       # Entry point
├── public/            # Static assets
├── index.html         # HTML template
└── vite.config.ts     # Vite configuration
```

## Environment Variables

Create a `.env` file in `apps/frontend/` with:

```
VITE_API_URL=http://localhost:8000
```

## Deployment

The frontend is typically deployed alongside the backend in a Docker container (see `docker-compose.yml`), or can be deployed separately to platforms like Vercel or Netlify.

**Note:** For the standalone marketing website and documentation (hosted on Vercel), see `apps/website/`.

## Links

- [Live Site](https://openclerk.dev)
- [Main Repository](../../README.md)
- [Python Package](../../packages/clerk/README.md)
