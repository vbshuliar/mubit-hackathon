# Fixi frontend

React 19, TypeScript, TanStack Start/Router (SPA), TanStack Query and Tailwind CSS 4. The product preview at `/` works without the backend. Operational pages use the existing API on port 8000 during development.

```sh
npm ci
npm run dev
```

Open http://localhost:5174. Main routes: `/` (product preview), `/overview`, `/maintenance`, and `/maintenance/tickets/:ticketId`. See [backend setup](../SETUP.md) to load operational data.

```sh
npm test
npm run typecheck
npm run lint
npm run test:browser
npm run build
```

Browser tests use synthetic intercepted API responses and Chrome; they never send mutations to a backend.

The roof/scaffolding Three.js illustration loads lazily, has direct HTML stage controls, supports reduced motion and a static fallback, and never changes real case state.
