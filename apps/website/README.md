# OpenClerk Website

The official website for OpenClerk - built with React, TypeScript, and Vite.

## Overview

This is the website application for openclerk.dev, providing:

- Documentation and guides
- Interactive reasoning kit browser
- Kit execution interface
- User authentication and settings

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

## Project Structure

```
apps/website/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Route/page components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utilities and API clients
│   ├── App.tsx        # Main app component with routing
│   └── main.tsx       # Entry point
├── public/            # Static assets
├── index.html         # HTML template
└── vite.config.ts     # Vite configuration
```

## Environment Variables

Create a `.env` file in `apps/website/` with:

```
VITE_API_URL=http://localhost:8000
```

## Deployment

The website is deployed to openclerk.dev via [deployment platform].

## Links

- [Live Site](https://openclerk.dev)
- [Main Repository](../../README.md)
- [Python Package](../../packages/clerk/README.md)
