# Verified loopback preview access

> Current source: `main`. See the [documentation index](README.md) and
> [release status](current-release.md); dated checkpoint details below retain their original scope.

The current VM application release is `46d1508`. Later review receipts and test-only
commits do not silently replace that runtime. The latest hackathon source is now
in `main`; updating GitHub does not update these deployed services.

## Connect

The frontend listens on VM loopback **3004**. Its compiled API address is browser
loopback **8004**. Forward both ports over your authorized SSH connection:

```sh
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 127.0.0.1:3000:127.0.0.1:3004 \
  -L 127.0.0.1:8004:127.0.0.1:8004 USER@VM
```

Open `http://127.0.0.1:3000`. API health is `http://127.0.0.1:8004/health`.
With `gcloud compute ssh`, use your existing instance/project/zone arguments and
pass the forwarding options after `--`. Do not reuse the old API-local-port 8001
tunnel: this production frontend was compiled for 8004.

## Operate on the VM

```sh
systemctl --user status chronosgraph-preview-api.service chronosgraph-preview-web.service
journalctl --user -u chronosgraph-preview-api.service -n 50 --no-pager
curl -fsS http://127.0.0.1:8004/health
curl -fsS http://127.0.0.1:8004/api/v1/imports/capabilities
```

User services are enabled and user linger was verified, so disconnecting SSH does
not intentionally stop the preview. No cold-boot availability claim was tested.
The prior checkout is preserved; the operator's explicit rollback script is recorded
in the deployment receipt. Inspect it before running: rollback stops/disables the
new managed preview and restarts the preserved old preview on the same ports.

Public imports create separate saved versions. The real Click smoke import is an
intentional saved repository, not a leaked test graph. Import tracking is durable;
recover an existing receipt instead of submitting duplicate jobs after a lost read.
Host worktree execution is disabled on this preview. A disposable worktree is not
a hostile-code sandbox, and loopback/origin checks are not multi-user authentication.
