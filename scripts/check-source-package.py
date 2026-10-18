#!/usr/bin/env python3
"""Offline audit of an exact committed source tree; never contacts a database.

Reports paths/kinds, never matching credential values. No archive is produced.
This heuristic is not a security certification or a scan of Git history.
"""
import argparse
import hashlib
import json
from pathlib import PurePosixPath, Path
import re
import subprocess

FORBIDDEN_PARTS = {'.git', '.venv', 'venv', 'node_modules', '.next', '.source-cache',
                   '__pycache__', 'private-recovery', 'private-vm', '.ssh'}
PATTERNS = {
    'aws_access_key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'google_api_key': rb'\bAIza[0-9A-Za-z_-]{35}\b',
    'github_token': rb'\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'openai_like_key': rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b',
    'private_key': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'long_literal_credential': rb'''(?i)(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*["']([A-Za-z0-9_./+=-]{20,})["']''',
}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def forbidden(path):
    p = PurePosixPath(path)
    name = p.name.lower()
    return (bool(FORBIDDEN_PARTS.intersection(p.parts))
            or (name.startswith('.env') and name not in {'.env.example', '.env.sample'})
            or name in {'id_rsa', 'id_ed25519', 'dump.rdb', 'appendonly.aof', 'auth.json'}
            or name.endswith(('.rdb', '.pem', '.key'))
            or name.startswith(('private-export', 'session-export', 'raw-export')))


def audit(repo, ref):
    commit = git(repo, 'rev-parse', '--verify', ref + '^{commit}').decode().strip()
    tree = git(repo, 'ls-tree', '-rz', '--full-tree', commit)
    entries = []
    for entry in tree.split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            entries.append((path.decode('utf-8'), mode, kind, oid))
    blobs = [e for e in entries if e[2] == 'blob']
    # One local Git subprocess, bounded to this committed tree, no history/export reads.
    data = b'' if not blobs else subprocess.check_output(
        ['git', '-C', str(repo), 'cat-file', '--batch'],
        input=('\n'.join(e[3] for e in blobs) + '\n').encode())
    contents, offset = {}, 0
    for path, _, _, oid in blobs:
        header_end = data.index(b'\n', offset)
        got_oid, kind, size = data[offset:header_end].decode().split()
        if got_oid != oid or kind != 'blob':
            raise ValueError('Unexpected Git object response')
        offset = header_end + 1
        contents[path] = data[offset:offset + int(size)]
        offset += int(size) + 1
    findings, inventory = [], []
    for path, mode, kind, _ in entries:
        if forbidden(path):
            findings.append({'path': path, 'kind': 'forbidden_package_path'})
        if mode not in {'100644', '100755'} or kind != 'blob':
            findings.append({'path': path, 'kind': 'unsupported_symlink_or_submodule'})
        body = contents.get(path, b'')
        inventory.append({'path': path, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()})
        for label, pattern in PATTERNS.items():
            if re.search(pattern, body):
                findings.append({'path': path, 'kind': label})
    checked = 0
    for path, body in contents.items():
        if not path.endswith('/sha256-manifest.json'):
            continue
        try:
            manifest = json.loads(body)
            if not isinstance(manifest, dict):
                raise ValueError('Expected a path-to-hash mapping')
            for relative, digest in manifest.items():
                p = PurePosixPath(relative)
                if p.is_absolute() or '..' in p.parts or not re.fullmatch(r'[0-9a-f]{64}', str(digest)):
                    raise ValueError('Unsafe or unsupported manifest entry')
                target = str(PurePosixPath(path).parent / p)
                checked += 1
                if target not in contents or hashlib.sha256(contents[target]).hexdigest() != digest:
                    findings.append({'path': path, 'target': target, 'kind': 'evidence_hash_mismatch_or_missing'})
        except (ValueError, TypeError):
            findings.append({'path': path, 'kind': 'invalid_evidence_manifest'})
    dirty = bool(git(repo, 'status', '--porcelain', '--untracked-files=normal'))
    return {'status': 'FINDINGS' if findings else 'PASS_SCOPED_TREE_AUDIT',
            'commit': commit, 'working_tree_dirty': dirty,
            'tracked_entries': len(entries), 'total_bytes': sum(x['bytes'] for x in inventory),
            'evidence_hashes_checked': checked, 'findings': findings, 'inventory': inventory,
            'scope': 'Exact committed tree only; all blob bytes pattern-scanned. No Git history, ignored/untracked files, databases, dependency audit, archive generation or final release approval. Dirty state is reported, not included. Passing heuristics do not prove absence of secrets. Final ZIP must use the audited commit, exclude .git, and be independently inspected.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.repo, args.ref)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in {'inventory', 'scope'}}, indent=2))
    return int(bool(result['findings']))


if __name__ == '__main__':
    raise SystemExit(main())
