# Fictional World web client

Minimal Stage 1 Vue client for the Caldris runtime. The client reads canonical
projections from the API, replays durable stream events, and submits player
actions as attempts.

```bash
pnpm generate:api
pnpm test
pnpm build
pnpm dev
```

Vite proxies `/worlds`, `/api`, and `/ws` to `127.0.0.1:8000`. Set
`VITE_WORLD_SLUG` to load a world other than the default `caldris` seed slug.
