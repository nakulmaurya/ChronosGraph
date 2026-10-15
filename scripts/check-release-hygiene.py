"""Read-only scoped credential/artifact/history and local graph fixture checks.

Heuristics are not a proof that no secret exists. Report paths, never candidate values.
Run from a configured backend environment with native FalkorDB reachable.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    tracked = git("ls-files", "-z").decode().strip("\0").split("\0")
    forbidden = []
    for path in tracked:
        parts = Path(path).parts
        if any(p in {".venv", "venv", "node_modules", ".next", ".source-cache", "__pycache__"} for p in parts):
            forbidden.append(path)
        if Path(path).name in {".env", ".env.local", ".env.production", ".env.development"}:
            forbidden.append(path)
    patterns = {
        "aws_access_key": rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        "google_api_key": rb"\bAIza[0-9A-Za-z_-]{35}\b",
        "github_token": rb"\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b",
        "openai_like_key": rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b",
        "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "long_literal_credential": rb"(?i)(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*[\"']([A-Za-z0-9_./+=-]{20,})[\"']",
    }
    objects = {}
    for line in git("rev-list", "--objects", "--all").decode().splitlines():
        oid, _, path = line.partition(" ")
        if path:
            objects.setdefault(oid, path)
    found = []
    scanned = 0
    for oid, path in objects.items():
        if git("cat-file", "-t", oid).strip() != b"blob":
            continue
        data = git("cat-file", "blob", oid)
        if b"\0" in data:  # Known binary artifacts, not source/config text.
            continue
        scanned += 1
        for kind, pattern in patterns.items():
            if re.search(pattern, data):
                found.append({"blob": oid, "path": path, "kind": kind})
    # Also scan current tracked working-tree content, including staged new files.
    for path in tracked:
        p = ROOT / path
        if not p.is_file():
            continue
        data = p.read_bytes()
        if b"\0" in data:
            continue
        for kind, pattern in patterns.items():
            if re.search(pattern, data):
                found.append({"path": path, "kind": kind, "scope": "working_tree"})
    sys.path.insert(0, str(ROOT / "backend"))
    from app.db.client import db_manager
    graphs = db_manager.list_tenant_graphs()
    orphans = [g for g in graphs if g.startswith(("sandbox_pr_", "test_chronos_"))]
    fixtures = {}
    for graph in ["repo_falkordb_py", "repo_graphrag_sdk"]:
        rows = db_manager.get_graph(graph).ro_query("""MATCH (n)
        WHERE n.source_type='E2E_TEST_FIXTURE' OR n.path STARTS WITH '__e2e__/'
        RETURN count(n)""").result_set
        fixtures[graph] = rows[0][0]
    status = git("status", "--porcelain").decode().splitlines()
    result = {"tracked_files": len(tracked), "history_text_blobs_scanned": scanned,
              "forbidden_tracked_artifacts": forbidden, "credential_pattern_findings": found,
              "orphan_test_or_sandbox_graphs": orphans, "test_fixture_node_counts": fixtures,
              "git_status_entry_count": len(status),
              "scope_note": "Pattern scan of tracked working-tree text and unique reachable historical text blobs; not a guarantee, dependency audit or production security review."}
    print(json.dumps(result, indent=2))
    return int(bool(forbidden or found or orphans or any(fixtures.values())))


if __name__ == "__main__":
    sys.exit(main())
