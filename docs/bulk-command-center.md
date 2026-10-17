# Bulk command-center milestone

Status: **in progress**, on `build/bulk-command-center-readiness`. This is not the code running on main or the existing VM preview.

## Implemented in this milestone

- Public import requests store a client-generated ID and exact inputs **before** submission. Retry the same saved request after a lost response; it does not create a second saved version while the seven-day receipt is retained.
- Redis-backed receipts outlive an API process. A separate bounded worker publishes a graph linked to the request ID; receipt reconciliation recognizes a completed publication even after its completion acknowledgement was lost.
- Interrupted deadlines are explicit. Incomplete graphs are retained for operator review, not silently deleted or automatically relaunched. Losing the Redis volume or expiring the seven-day receipt ends this recovery guarantee.
- An independent tracked-file inventory shows regular non-Python files, excluded paths and unsupported local Git entries. **Dependency, call and source analysis remains Python-only.** Public archive import still requires Python source and refuses symlinks/submodules/unsafe or oversized archives; it is not an arbitrary-language importer.
- Folder/file maps and developer search have keyset pagination. Compact agent context is still separately budgeted. Cross-page graph relationships and high-degree dependency/symbol views remain bounded and disclosed.
- New local-Git imports preserve commit-file records even if a file is deleted or non-Python. History/changed-file lists are pageable within the indexed history (default latest 40 commits, not the entire repository history). Public archive imports do not fetch history.
- Saved-version labels include a short commit and tenant suffix. “Copy workspace link” preserves the exact saved version/revision and selected file or view. An unavailable or mismatched link does not silently open another snapshot. This link is navigation, not an agent authorization or live workspace session.

## Import recovery

Close/reopen the import panel after a connection issue. Use **Check import status again** or **Retry same saved import request**, not a new import, to reconcile. “Reload indexed repositories” can reveal a version that finished while disconnected. Dismissing tracking neither cancels the worker nor deletes the snapshot. A fresh request gets its own tenant; existing versions are never overwritten.

Blank browser branch means the repository's declared default branch, not necessarily `main`. The optional branch-head hash confirms the currently resolved branch commit; it is explicitly **not a historical commit picker**. The advanced CLI guide continues to document its explicit branch argument.

## History/source distinction

A changed-file entry describes that indexed commit. File inspection opens the **current saved snapshot**, not that commit's historical source. Deleted entries are labeled and cannot open a nonexistent current file. Older snapshots with only current-Python-file change links are explicitly labeled; reimport local Git history for independent records. Renames use add/delete semantics, not inferred rename identity. No runtime execution or test success is inferred from static impact.

## Verification commands

See `backend/DEPENDENCIES.md` for the hashed Linux/Python 3.13 environment and CI scope.

```bash
# Requires native Docker + the four existing demo graphs on the trusted source instance.
# Writes/tests run only in a disposable database copy.
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/verify-quality-batch1.sh
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/verify-change-planning-ui.sh

# Self-contained owned container/volume; deliberately crashes only that container.
PYTHON_BIN="$PWD/.venv/bin/python" bash scripts/verify-database-persistence.sh
```

The native harness now records a synthetic 5,000-file navigation baseline. It is not an import-throughput, multi-client, 50,000-file or production-capacity claim. Browser import lost-acknowledgement tests inject transport responses; native Redis tests independently check idempotency, concurrent retries, process replacement and publication/deadline reconciliation. Neither is a claim that a real external IDE task was completed.

## Not finished

- Real client task → proposal → human decision → externally reported execution → verification workflow and polished end-to-end demonstration.
- All-language semantics, dynamic Python dispatch, arbitrary historical source checkout and full GitHub commit-history import.
- Cross-process protection for every legacy mutation, automatic interrupted-graph remediation, public multi-user authentication/authorization.
- Full screen-reader/keyboard audit, shared UI-state refactor and representative real-repository import/load/concurrency testing.
- Root project license decision by the owner. Third-party notices must remain intact.

A critique-only acceptance review can still reject the complete product despite passing these regression gates. No report from an agent is relabeled independently observed execution.
