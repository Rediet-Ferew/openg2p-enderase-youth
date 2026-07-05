# Enderase Dashboard Web

Next.js UI for the Enderase Youth Association dashboard. It renders the
registry story and proxies `/api/*` requests to the dashboard FastAPI service
in Docker Compose.

## Getting Started

Install dependencies and run the development server:

```bash
npm run dev
```

Open http://localhost:3000 with your browser.

In the full Compose stack, the app is exposed at http://localhost:8080 and
rewrites `/api/*` to the `dashboard-api` service.

## Layout

- `app/` - Next routes and global CSS
- `src/` - dashboard components, hooks, data, and UI primitives
- `public/` - static assets served by Next.js

## Scripts

- `npm run dev` - local Next dev server
- `npm run build` - production build
- `npm run start` - serve the production build
- `npm run lint` - lint the app
