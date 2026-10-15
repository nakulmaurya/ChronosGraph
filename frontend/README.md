# ChronosGraph Flight Recorder

T-03 local engineering console: Next.js App Router, TypeScript, Tailwind CSS,
React Flow (`@xyflow/react`) and Lucide. It consumes the existing FastAPI contract;
it does not serve fake API fixtures, call external models, or change backend schemas.

## Run locally

Use Node.js 24 (the test runner strips TypeScript directly) and the existing Python
backend environment. Next.js itself requires Node >=20.9.

From the repository root, start the database and backend as described in `AGENTS.md`:

```sh
docker compose up -d
cd backend
pip install -e .
python -m app.ingestion.seed_repos
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:3001`. For a production-mode **local** check:

```sh
npm run build
npm start
```

The browser calls `http://localhost:8000/api/v1` by default. Copy `.env.example` to
`.env.local` to change `NEXT_PUBLIC_API_BASE_URL`, then restart/rebuild. Keep the
frontend on port 3000/3001 to match the backend's localhost CORS allowlist. Both
services must be reachable from the browser; a remotely hosted UI cannot reach
your computer's localhost backend. Do not expose these unauthenticated mutation
routes publicly. No production deployment is included.

## Checks

```sh
npm test
npm run typecheck
npm run build
npm audit --omit=dev
```

For live Chromium integration with both servers already running:

```sh
CHROMIUM_PATH=/path/to/chromium \
BACKEND_PYTHON=/absolute/path/to/backend/venv/bin/python \
EVIDENCE_DIR=/absolute/path/to/ui-evidence \
npm run test:e2e
```

The test uses real HTTP/FalkorDB responses. It deliberately aborts one browser
request to verify the network-error state (not to substitute a fake response).
It temporarily overrides a local demo policy and restores only its changed
fields/created decision nodes in `finally`. Use a disposable local database and
run it without concurrent writers. The test leaves real investigation/playbook
records behind, so node counts grow. Defaults: Chromium at
`/usr/local/bin/chromium`, `BACKEND_PYTHON=python3` with `app` installed, and
`EVIDENCE_DIR=../../ui-evidence`. No paid credentials are needed.

## Workflows

- **Track 1:** Choose a real snapshot PR and/or preset files. Explicit files take
  priority; clear them to use the PR's ingested Python files. Audit a disposable
  graph clone, view static potential impact and verify cleanup. Synthetic
  dependencies are labeled; this does not execute a source diff or predict outages.
- **Track 2:** Include a policy-governed file in the scenario; cold triage executes
  5 deterministic graph-tool actions across 6 states. Native shortestPath retains
  3 verified actions, removing both dead ends. Replay requires the exact scenario
  and current graph fingerprint. UI displays actual route latency, including a
  factor below 1 if replay is slower; it never forces a speedup. Zero tokens and
  zero token-savings percentage are model-free sentinels, not LLM benchmarks.
- **Track 3:** Read active/superseded policies, scope and both validity/recorded
  times. The explicit override form requires confirmation and preserves history.
  The backend's HTTP 409 mixed-scope guard is retained. `lead-maintainer` is the
  backend's demo actor, not verified GitHub identity. Read current policy before
  retrying a write after network failure: it may already have completed.
- **Graph:** Focused files/rules are shown first, with an explicit visible/total
  count. Show all payload nodes to inspect functions and the complete returned
  subgraph. Positions are presentation only; all nodes and relationships are
  sourced from the API. Drag, zoom, pan, fit and select nodes for metadata. The
  backend itself bounds its subgraph; the UI never claims to show the whole repo.
- **MCP config:** Copy a local stdio template and set the absolute backend cwd and
  Python executable for your environment. Lists all five backend tools. This is
  not an installed IDE connection.

## Evidence and known limits

See `../tasks/reports/T-03.md`. The frontend branch is intentionally unmerged for
Principal Architect review. T-02 is merged through PR #2 at `6e70cac`.

Latency varies with machine load and graph size; action reduction is deterministic,
not a promised wall-clock speedup. Owners are based only on ingested public PR-file
links; empty coverage is explained rather than fabricated. Policies retain demo
provenance, vectors are lexical hashes, and policy triage is not autonomous bug
repair. Native `<dialog>` gives keyboard focus containment, Escape and restoration;
reduced-motion CSS suppresses animated paths. Desktop panes scroll internally and
mobile stacks controls, graph and results. Chromium desktop and 390px emulation
were checked; Safari, Firefox, physical-device and screen-reader audits are NOT RUN.
