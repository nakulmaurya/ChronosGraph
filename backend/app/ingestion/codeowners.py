"""Bounded, pinned GitHub-style CODEOWNERS evidence; never verified identity.

Parser source is vendored unchanged with its MIT notices. This wrapper rejects
unsupported syntax instead of silently applying GitLab/gitignore semantics.
Read only committed regular-file blobs, not workspace paths or symlink targets.
"""
from __future__ import annotations
import hashlib
import re
import subprocess
from app._vendor.codeowners import CodeOwners
from app.ingestion.git_safety import git_command, git_environment

SOURCE_PATHS = ('.github/CODEOWNERS', 'CODEOWNERS', 'docs/CODEOWNERS')
MAX_BYTES, MAX_LINES = 65536, 2000
OWNER = re.compile(r'(?:@[A-Za-z0-9][A-Za-z0-9-]{0,38}(?:/[A-Za-z0-9_.-]{1,100})?|[^\s@#]+@[^\s@#]+\.[^\s@#]+)\Z')


def parse_rules(text):
    """Return parser plus bounded diagnostics, preserving original line numbers."""
    lines = text.splitlines()
    if len(text.encode('utf-8')) > MAX_BYTES or len(lines) > MAX_LINES:
        raise ValueError('CODEOWNERS exceeds the supported size or line limit')
    accepted, diagnostics = [], []
    invalid_count = 0
    for number, line in enumerate(lines, 1):
        clean = line.strip()
        reason = None
        if not clean or clean.startswith('#'):
            accepted.append('')
            continue
        # Escaped leading #, negation, [] and GitLab sections are not GitHub rules.
        body = clean.split('#', 1)[0].rstrip()
        parts = body.replace('\\ ', '\0').split()
        pattern = parts[0].replace('\0', '\\ ') if parts else ''
        owners = parts[1:]
        if clean.startswith(('!', '\\#', '[', '^[')) or '[' in pattern or ']' in pattern:
            reason = 'UNSUPPORTED_GITHUB_PATTERN'
        elif not pattern.strip('/') or len(pattern) > 256 or pattern.count('*') > 8:
            reason = 'PATTERN_LIMIT_OR_EMPTY'
        elif '\\' in pattern.replace('\\ ', ''):
            reason = 'UNSUPPORTED_ESCAPE'
        elif len(owners) > 20 or any(len(o) > 200 or not OWNER.fullmatch(o) for o in owners):
            reason = 'UNSUPPORTED_OWNER_OR_LIMIT'
        if reason:
            invalid_count += 1
            if len(diagnostics) < 50:
                diagnostics.append({'line': number, 'reason': reason})
            accepted.append('')
        else:
            accepted.append(pattern + (' ' + ' '.join(owners) if owners else ''))
    parser = CodeOwners('\n'.join(accepted))
    return parser, diagnostics, invalid_count


def _git_bytes(root, *args):
    return subprocess.check_output([*git_command(), '-C', str(root), *args], env=git_environment(), timeout=30)


def committed_document(root, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('CODEOWNERS requires a full pinned SHA-1 revision')
    # First existing location wins, including an unsupported-mode location: never
    # silently fall back to a different policy when the chosen file is invalid.
    for path in SOURCE_PATHS:
        record = _git_bytes(root, 'ls-tree', '-z', revision, '--', path)
        if not record:
            continue
        header, actual_path = record.rstrip(b'\0').split(b'\t', 1)
        mode, kind, oid = header.split()
        if actual_path.decode() != path or kind != b'blob' or mode not in (b'100644', b'100755'):
            return {'status': 'UNSUPPORTED_SOURCE_MODE', 'path': path}
        size = int(_git_bytes(root, 'cat-file', '-s', oid.decode()))
        if size > MAX_BYTES:
            return {'status': 'SOURCE_TOO_LARGE', 'path': path}
        data = _git_bytes(root, 'cat-file', 'blob', oid.decode())
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            return {'status': 'SOURCE_NOT_UTF8', 'path': path}
        if '\0' in text:
            return {'status': 'SOURCE_NOT_TEXT', 'path': path}
        return {'status': 'FOUND', 'path': path, 'text': text,
                'sha256': hashlib.sha256(data).hexdigest()}
    return {'status': 'ABSENT_AT_PINNED_REVISION'}


def index_codeowners(graph, root, revision, origin, known_paths):
    document = committed_document(root, revision)
    status = document['status']
    rows, diagnostics, invalid_count = [], [], 0
    if status == 'FOUND':
        try:
            parser, diagnostics, invalid_count = parse_rules(document['text'])
        except ValueError:
            status = 'SOURCE_LIMIT_EXCEEDED'
        else:
            status = 'PARTIAL_INVALID_RULES_SKIPPED' if invalid_count else 'INDEXED'
            for path in sorted(known_paths):
                owners, line, pattern, _ = parser.matching_line(path)
                if line is None:
                    continue
                # An empty owner list is a real last-match clearing rule.
                rule_id = document['sha256']+':'+str(line)
                rows.append({'path': path, 'rule_id': rule_id, 'line': line,
                             'pattern': pattern, 'owners': [{'kind': k, 'name': n} for k, n in owners]})
    source_path = document.get('path', '')
    sha = document.get('sha256', '')
    url = origin+'/blob/'+revision+'/'+source_path if origin and source_path else ''
    graph.query('''MATCH (m:RepoMetadata) SET m.ownership_index_status=$status,
      m.ownership_source_path=$path,m.ownership_source_sha256=$sha,
      m.ownership_source_revision=$revision,m.ownership_source_url=$url,
      m.ownership_invalid_rule_count=$invalid''',
      {'status': status, 'path': source_path, 'sha': sha, 'revision': revision,
       'url': url, 'invalid': invalid_count})
    if rows:
        graph.query('''CREATE (:OwnershipSource {id:$sha,path:$path,sha256:$sha,
          source_revision:$revision,source_url:$url,source_type:'PINNED_CODEOWNERS'})''',
          {'sha': sha, 'path': source_path, 'revision': revision, 'url': url})
        for start in range(0, len(rows), 250):
            graph.query('''UNWIND $rows AS r MATCH (s:OwnershipSource {id:$sha}),(f:File {path:r.path})
              MERGE (rule:OwnershipRule {id:r.rule_id}) SET rule.pattern=r.pattern,rule.source_line=r.line
              MERGE (s)-[:DEFINES_OWNERSHIP_RULE]->(rule)
              MERGE (rule)-[:APPLIES_TO]->(f)''', {'rows': rows[start:start+250], 'sha': sha})
            graph.query('''UNWIND $rows AS r UNWIND r.owners AS o
              MATCH (rule:OwnershipRule {id:r.rule_id})
              MERGE (owner:DeclaredOwner {name:o.name,kind:o.kind})
              MERGE (rule)-[:DECLARES_OWNER]->(owner)''', {'rows': rows[start:start+250]})
    return {'status': status, 'source_path': source_path, 'matched_files': len(rows),
            'invalid_rule_count': invalid_count, 'diagnostics': diagnostics,
            'basis': 'Declared at pinned commit; GitHub identity/access not verified'}
