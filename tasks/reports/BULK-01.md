# Bulk command-center implementation report

Branch: `build/bulk-command-center-readiness`. Base: `ca46b8c`.

## Delivered scope

1. Redis-backed seven-day import receipts, same-request idempotency, independently bounded worker, publication/deadline reconciliation and client pre-submit request persistence.
2. Independent tracked-file inventory, truthful unsupported-language/excluded-entry states, paged map/search, exact saved-version labels/links and storage-tolerant browsing.
3. Independent local-Git commit-file records including deleted/non-Python files, paged history and changed-file navigation, explicit current-vs-historical source distinction.
4. Native regression additions, desktop/mobile lost-response/navigation checks, hashed Linux/Python 3.13 runtime lock, clean-install CI definition, pinned loopback AOF deployment and crash-recovery script.
5. Synthetic navigation baseline, operator documentation and critique-only review. See `tasks/reviews/BULK-01-readiness.md` for the **NOT READY** complete-product decision.

## Verification

Final verification results are recorded below after completion. VM evidence is under `~/t09-evidence/bulk-01/`; logs are not committed as proof of independent execution by a coding agent.

- Backend: **268 tests passed in 43.52 seconds**, using the fresh locked Python environment and a disposable native copy of the four demo graphs (`final-native-corrected/backend-full.log`). The subsequent synthetic navigation gate passed.
- Frontend: fresh separate `npm ci`, 32 unit tests, TypeScript and production build passed. npm install reported zero known vulnerabilities at that run; this is not a security audit.
- Browser: 50 desktop/mobile checks passed across change planning (18), read/import recovery (18), agent setup (4), and new bulk inventory/link/lost-ack checks (10). Production build passed. Real impact previews are isolated; the lost-import acknowledgement responses are explicitly injected, not real external import results.
- Persistence: pinned image with AOF restored native graph plus durable import receipt after deliberately killing/restarting an owned container and persistent volume. No production database accessed.
- CI-native equivalent: **17 tests passed in 3.18 seconds** against an entirely empty disposable native DB, without the four demo graphs. This validates the selected CI test subset locally, not a remote Actions run.
- Release hygiene: 392 tracked files / 621 reachable historical text blobs scanned; no credential-pattern findings or forbidden tracked artifacts; no orphan sandbox/test graphs or fixture nodes in the four source graphs. Heuristic scan, not security certification.
- Dependency install: fresh locked Python 3.13 environment installed and dependency compatibility check passed. Build-backend toolchain is not fully locked. Remote GitHub Actions status is not asserted here.
- Synthetic scale: 5,000 tracked files / 1,000 Python files / 1,000 functions / 1,000 imports, 12 samples per operation, local p95 budget 2,000 ms. First clean-run p95 root map 139.47 ms, folder map 46.57 ms, tail exact-path search 42.61 ms, symbol search page 39.15 ms, inspector 18.86 ms. Not a production/import-throughput guarantee.

## Known failure history

The first importer run found three failures, including a real same-request coordination race and decoded-string assumptions in tests. These were fixed and rerun. The first persistence assertion assumed a Redis return representation incorrectly; corrected, then real crash recovery passed. An added archive test incorrectly assumed README was not extracted; corrected because README is intentionally bounded evidence. Failed runs are retained in the evidence directory, not described as passes.

## Deployment and remaining work

Main and the existing VM preview are not automatically merged or restarted. This report is not a deployment claim. B06 real agent lifecycle/demo, broader B07 accessibility/shared UI-state work, legacy cross-process mutation safety/orphan remediation, representative scale testing and the owner license decision remain open. Tests do not justify a final-product quality claim.
