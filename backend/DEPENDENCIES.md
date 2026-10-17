# Backend dependency gate

`requirements-linux-py313.lock` freezes runtime/test dependencies with package hashes for the tested Linux/Python 3.13 environment. It does **not** claim compatibility for every Python supported by the broad package manifest.

```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r backend/requirements-linux-py313.lock
.venv/bin/python -m pip install --no-deps -e backend
.venv/bin/python -m pip check
```

The editable project build still uses the `pyproject.toml` build backend in an isolated build environment. This runtime lock is not a bit-for-bit toolchain/container reproducibility guarantee. Frontend dependencies use `npm ci` and `frontend/package-lock.json`.

The command-center GitHub Actions workflow runs fresh installs, frontend tests/build, and native inventory/history/import regressions against disposable FalkorDB. It does not seed the four legacy demo repositories or claim to run the entire demo compatibility suite. The full suite and browser fault checks are separately run with `scripts/verify-quality-batch1.sh` and `scripts/verify-change-planning-ui.sh` against isolated copies of known demo graphs.

The committed image digest and `REDIS_ARGS=--appendonly yes` Compose configuration support graph/receipt recovery from a container crash with a persistent volume. Redis's default every-second fsync is **not zero-loss** on sudden host failure; back up the volume and do not use `docker compose down -v` if data must be retained. Import receipt retention is seven days. This is a trusted loopback workspace, not authenticated multi-user hosting.
