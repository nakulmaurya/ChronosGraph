# Release checklist — v1.2 accepted local demonstration

Contract v1.2; builder + integrator verification. T-03 is accepted and merged via
PR #3 at `a36ae2fbc8e148068333fc7ca7b3e4b6ecc193a7`. The Principal Architect accepted
T-04/M4 at `d47c035` through the user bridge and authorized final integration.
This is not a production release, article publication or hackathon submission.

## Phase 6 gate
| Check | Result / evidence |
| --- | --- |
| Scope and authority | T-04 assignment; docs and minimal local startup/hygiene helpers only. No product API/schema/query changes. |
| Backend integration | Fresh real FalkorDB run: **40/40 PASS**, 5.07 s. `tasks/reports/T-04-evidence/backend-pytest.txt`. |
| Frontend regression | **7/7 PASS**, zero failures. `frontend-checks.txt`. |
| TypeScript / production build | `npm run typecheck` and `npm run build`: **PASS**. No build/type errors. Parent workspace lockfile warning is environmental, retained in evidence. |
| Production dependencies | `npm audit --omit=dev`: **0 reported vulnerabilities**. `production-audit.json`. Not a full dependency/security review. |
| Live UI | **15/15 PASS** against restarted production server; see `ui-smoke-results.json` and retry history. Earlier T-03 acceptance remains separately documented. |
| Helper syntax | `bash -n scripts/start-local.sh`; Python compile checks: **PASS**. |
| Native helper | Real FalkorDB on isolated port 6381; `GRAPH.LIST`, Cypher `RETURN 1`, own-graph cleanup and signal shutdown: **PASS**, with workspace compatibility loader. |
| Existing-DB verification command | `VENV_DIR=/data/venv bash scripts/start-local.sh --db existing --no-install --verify-only`: **PASS**, seeding + 40/7 checks/typecheck/build. |
| Credentials/artifacts | **PASS**, 129 tracked files / 142 historical text blobs at published pack commit; zero matched findings. See `post-publication-hygiene.json`. Heuristic, not an absence guarantee. |
| Test cleanup | No `__e2e__/` / `E2E_TEST_FIXTURE` nodes in either tenant; no sandbox/test graph leaks. |
| Provenance and article | Actual canonical query excerpts; 1,200–1,800-word article; no measured token-savings claim. `article-validation.json`. |
| Publication integrity | **PASS** at `a165abc`: all 21 published changed files byte-identical after fetch, checkout fast-forwarded, empty `git status --porcelain`. This follow-up records that observed gate; latest head/clean scan in final handoff. |

## Explicitly NOT RUN / out of scope
- Docker execution: Docker is unavailable in the agent environment. The default
  loopback-only Docker launcher is supplied but **not empirically validated here**.
- Entire clean-machine native installation/startup: only the isolated native helper
  and installed existing-DB verification path were exercised. Native wheels and
  module/glibc support vary by platform; no host libraries were replaced.
- Physical phone, Safari/Firefox, screen-reader audit and formal accessibility certification.
  Automated Chromium desktop/mobile checks are not substitutes for these.
- Installed IDE MCP connection. The modal exports a config template; a connection
  must be installed by the user in their own local agent environment.
- Production load, authentication, isolation for untrusted tenants, cloud deployment,
  rollback under production traffic, external LLM/token benchmark or broad RAG comparison.
- Actual 2:45 recording, blog/social publication, prize eligibility and submission.

## Security and trust boundaries
Localhost trusted-user, single-process demonstration only. The backend lacks
production authentication. Read-only discovery uses `GRAPH.RO_QUERY`; controlled
writes are allowed for state recording and confirmed local policy overrides.
The demo actor is not a verified GitHub identity. Keep `DEMO_POLICY_SCENARIO`,
`SIMULATED_PR_DEPENDENCY`, `DETERMINISTIC_POLICY_TRIAGE` and
`CONTROLLED_ONE_HOP_BASELINE` visible. Ownership is limited PR-file evidence.

`.env.example` is a public template, not a credential file. `.venv`, `node_modules`,
source caches, `.next` and Python caches may exist locally but must remain ignored,
not committed. The scan covers common credential patterns in tracked working-tree
text and unique reachable historical text blobs; it skips binary blobs, ignored
local files and remote/platform secrets. Audit and scan results are point-in-time.

## Local operation and recovery
- `bash scripts/start-local.sh` owns an ephemeral database/container and web children.
  Ctrl-C stops only those owned processes; logs are printed under a temporary directory.
- `--db existing` reuses a trusted local database and **does not delete it** on exit.
  Seeding and demo operations can persist state. Do not use an unrelated database.
- A failed request retains previous UI evidence with a warning; it is not a new success.
- After a policy override, run fresh cold triage before replay. Never bypass HTTP 409.
- Local reset: stop the owned ephemeral database and start a new one. Do not blindly
  delete an existing user's tenant. Reseeding is not a supported undo for overrides.
- Source rollback: inspect/revert a reviewed commit as appropriate; do not force-push
  or rewrite accepted history.

## Sign-off boundary
T-04/M4 acceptance and merge authorization are supplied by the Principal Architect
through the user bridge; see `tasks/reviews/T-04.md`. External publication, submission
and deployment remain separate human actions, not implied by code acceptance.
