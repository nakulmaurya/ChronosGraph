# Current managed preview access

The current managed preview runs application **`44bb68b459f83dbdc091ceecf4cd60ded72b379b`**.
Both frontend and API were rebuilt/reconfigured for that exact application commit.
The prepared example’s source revision `fabe543f…` is a different identity: it is
the code being inspected, not the ChronosGraph application build.

## Connect privately

The VM preview is a **trusted loopback deployment**, not a public authenticated
SaaS. An authorized operator forwards the existing ports:

```sh
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 127.0.0.1:3000:127.0.0.1:3004 \
  -L 127.0.0.1:8004:127.0.0.1:8004 USER@VM
```

Open **http://127.0.0.1:3000**. Click **Open prepared example** to inspect the
persisted synthetic timeout-contract task. Its recorded worker/reviewer evidence
is retained, not a new live agent run. Application/API build declarations are
available under **Build & snapshot identity**. Source commit declarations are not
cryptographic execution attestations.

No VM credentials are required to review the public source, release video or
[complete local setup](../README.md#start-locally). A fresh local database does not
recreate historical sessions; linked public evidence preserves their provenance.
This local setup is the submission’s deployment alternative.

## Operator state and rollback

Only the existing `chronosgraph-preview-api.service` and
`chronosgraph-preview-web.service` were updated, still on loopback **8004/3004**.
The API uses the existing prepared FalkorDB instance at **6381** with
`--lifespan off`, avoiding startup seeding. Public/browser import and worktree
execution flags are **disabled** in this prepared preview. A separate local
launcher can opt into imports; those flags are not silently enabled here.
The pre-existing API8015 and review services8007/3007 remain separate and untouched.

The previous service definitions and the immediately prior working override were
preserved before replacement. Operator receipts/rollback are in the VM’s owned
`publication-20261018/deployment-<application-commit>/` directory, outside public
source. Rollback changes service configuration, not graph data. Do not run an old
historical rollback script blindly: the much older API expected absent DB6379.

```sh
systemctl --user status chronosgraph-preview-api.service chronosgraph-preview-web.service
curl -fsS http://127.0.0.1:8004/health
curl -fsS http://127.0.0.1:8004/api/v1/release/identity
```

Local/origin checks are not multi-user authentication. Disabling candidate
execution does not make every endpoint read-only. Do not expose mutation endpoints
publicly without additional access controls. No approval or candidate execution
was performed by this release. [Historical preview](preview-access-historical-46d1508.md).
