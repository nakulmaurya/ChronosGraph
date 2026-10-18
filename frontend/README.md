# ChronosGraph frontend

The Next.js interface for exploring code relationships, task context and proposed
changes. Built with TypeScript, Tailwind CSS and React Flow.

For the complete application, use the [root setup guide](../README.md#start-locally).

## Frontend development

With the backend running on port 8000:

```sh
npm ci
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev -- -p 3001
```

`NEXT_PUBLIC_API_BASE_URL` is compiled into the frontend. Set it when building
for a different API endpoint; a runtime-only environment change is insufficient.

## Checks

```sh
npm test
npx tsc --noEmit
npm run build
```

Use Node.js 24 for the repository's test tooling. Next.js requires Node.js 20.9+.

[Architecture](../docs/architecture.md) · [Graph model](../docs/graph-model.md)
