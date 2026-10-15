# ChronosGraph — Google Cloud VM Docker verification

## Outcome
PASS: the accepted repository was installed, tested against actual Docker, and left
running privately on the user-provided Google Cloud test VM. No GitHub login was
required; no code changes were pushed and no production deployment is claimed.

## Revision and environment
- Repository: https://github.com/nakulmaurya/ChronosGraph
- Commit: `36baf3059036878f7c9582f458dc72ce5de703f4`
- VM: instance-falkordb-hackathon, Debian 13 x86-64, 4 vCPU, 16 GB RAM, ~60 GB SSD.
- Docker Engine: 29.9.1; Compose plugin: 5.6.0.
- Node: v24.22.0; npm: 11.19.1; Python 3.13.5.
- Container Redis: 8.10.2; FalkorDB graph module ver 42201 (4.22.1).
- Image: `falkordb/falkordb@sha256:b0bdcac2cbaff989e77cb0610439b7a9289e86de033ccbbd4368b66fb680ae7a`.
- SSH host-key fingerprint matched the value supplied from the VM console.
- Docker installed from its official Debian repository. Node archive checksum
  matched the official HTTPS-served manifest; independent GPG verification NOT RUN.

## Observed verification
| Check | Result |
| --- | --- |
| `bash scripts/start-local.sh --verify-only` | PASS with real Docker; full dependency setup, graph seed, tests and build |
| Backend | 40/40 passed in 6.23 s |
| Frontend regression | 7/7 passed |
| TypeScript | PASS |
| Optimized production build | PASS |
| Exact default `bash scripts/start-local.sh` | PASS; started Docker FalkorDB, FastAPI and Next.js |
| API `/health` | HTTP success, `{"status":"ok"}` |
| Frontend | HTTP 200 |
| Live Chromium smoke | 15/15 PASS; no uncaught browser errors |
| Production dependency audit | 0 reported vulnerabilities |
| Scoped history/tracked-file hygiene | 0 matched credential/artifact findings |
| Test cleanup | No test fixture nodes or orphan sandbox/test graphs |
| Git checkout | Clean, unchanged accepted revision |
| Verification-container cleanup | No launcher container remained after verify-only exit |

The 15 UI checks ran against the default launcher's Next.js development server.
The production build passed separately; production-mode UI smoke was NOT RUN on
this VM. The suite exercised both tenants, all three tracks, policy overrides and
restoration, stale-playbook guards, five-tool MCP modal, node interaction, failure
recovery and mobile viewport layouts. This was Chromium automation, not physical
phone, Firefox, Safari or a full accessibility/security audit.

Next.js dev startup regenerated exactly two tracked declaration import paths from
`.next/types/` to `.next/dev/types/`. The diff and initial one-entry hygiene result
were retained, then only that generated change was restored after exact comparison
to the committed file. Final hygiene and git status were clean. Dev startup can
regenerate those paths again; this is not a product-source patch.

This Docker runtime differs from the original native FalkorDB 4.18.3 environment.
These are fresh VM test results, not replacements for the historical T-01/T-02 data.
Latency observations in the raw smoke JSON are single-run timings, not a benchmark
or a token-savings measurement. Hygiene is heuristic, not proof no secret exists.

## Running state and access
- Persistent terminal session: `chronosgraph` (tmux).
- Database: 127.0.0.1:6379, container chronosgraph-local-6142.
- FastAPI: 127.0.0.1:8000.
- Next.js: 127.0.0.1:3001.
- App/database ports are not publicly bound. No cloud firewall was opened for them.

On the user's laptop, with Google Cloud CLI authenticated, run:

```bash
gcloud compute ssh nakulmaurya13579@instance-falkordb-hackathon \
  --project=amazon-ml-509907 \
  --zone=us-central1-a \
  -- -N -L 3001:127.0.0.1:3001 -L 8000:127.0.0.1:8000
```

Then open http://localhost:3001 on that laptop and keep the tunnel terminal open.
This uses the user's own Google Cloud access, not the agent's private SSH key.

To stop the demo, open the VM console SSH terminal, run `tmux attach -t chronosgraph`
and press Ctrl-C. The launcher stops its owned services/container; the database is
ephemeral. The app is not configured to restart after VM reboot. Stop the VM when
finished to avoid ongoing compute charges. Remove the temporary agent public SSH
key when no further agent access is wanted; no private key is included in evidence.

## Remaining boundaries
No installed IDE MCP connection, public deployment, external blog/video publication,
hackathon submission or eligibility verification was performed. The legacy Compose
file was not executed; this verifies the safer loopback-only launcher Docker path.
No repository write/push was needed. The repository's earlier NOT RUN statements
remain historical; this separate report records the subsequent VM verification.

Raw logs, image digest, actual telemetry, audit, cleanup and generated-file diff are
included in the accompanying evidence ZIP. Logs are also retained on the VM under
`~/chronosgraph-evidence/`.
