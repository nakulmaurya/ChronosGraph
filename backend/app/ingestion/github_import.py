"""Opt-in CLI public GitHub intake. No clone/checkout, credentials or model calls.

A complete bounded API tree and SHA-1 verified selected archive blobs feed the
existing FalkorDB AST index. This is not an arbitrary URL importer or a sandbox.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
import zipfile
from app.ingestion.codeowners import SOURCE_PATHS, MAX_BYTES
from app.ingestion.ingest_repo import EXCLUDED, _ingest_repo, writer_locks
from app.services.common import TENANT_PATTERN
from app.db.client import db_manager

SHA = re.compile(r'[0-9a-f]{40}\Z')
PART = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z')
MAX_ENTRIES = 10000
MAX_ARCHIVE = 16_000_000
MAX_EXPANDED = 64_000_000
SUPPORT = {'README.md', 'pyproject.toml', 'AGENTS.md', 'CLAUDE.md', *SOURCE_PATHS}


def repository_url(value):
    """Exactly github.com/owner/repo, not SSH, tree URLs, ports or userinfo."""
    parsed = urlsplit(value)
    parts = parsed.path.strip('/').split('/')
    if (parsed.scheme != 'https' or parsed.netloc != 'github.com' or
        parsed.query or parsed.fragment or len(parts) != 2 or '//' in parsed.path or
        value != value.strip() or any(ord(c) < 33 or ord(c) > 126 for c in value)):
        raise ValueError('Use a credential-free https://github.com/owner/repo URL only')
    owner, repo = parts
    repo = repo.removesuffix('.git')
    if not PART.fullmatch(owner) or not PART.fullmatch(repo) or repo in ('.','..'):
        raise ValueError('Unsupported GitHub owner/repository name')
    return owner, repo, f'https://github.com/{owner}/{repo}'


def branch_name(branch):
    if (not branch or len(branch) > 200 or not re.fullmatch(r'[A-Za-z0-9_./-]+', branch) or
        branch.startswith(('-', '.', '/')) or branch.endswith(('.', '/')) or
        '..' in branch or '//' in branch or
        any(p.startswith('.') or p.endswith('.lock') for p in branch.split('/'))):
        raise ValueError('Use an explicit supported branch name, not a ref expression')
    return branch


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PublicGitHub:
    """Fixed hosts; ignore proxy env and never send tokens/cookies or follow redirects."""
    def __init__(self):
        self.deadline = time.monotonic()+180
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def get(self, url, limit):
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc not in ('api.github.com','codeload.github.com'):
            raise ValueError('Network destination is not an allowed GitHub host')
        request = Request(url, headers={'User-Agent':'ChronosGraph-public-intake',
            'Accept':'application/vnd.github+json' if parsed.netloc=='api.github.com' else 'application/zip'})
        try:
            remaining = self.deadline-time.monotonic()
            if remaining <= 0: raise ValueError('Public import download deadline exceeded')
            with self.opener.open(request, timeout=min(20,remaining)) as response:
                length = response.headers.get('Content-Length')
                if length and int(length) > limit: raise ValueError('GitHub response exceeds byte limit')
                chunks, size = [], 0
                while True:
                    if time.monotonic() > self.deadline: raise ValueError('Public import download deadline exceeded')
                    chunk = response.read(min(65536,limit+1-size))
                    if not chunk: break
                    size += len(chunk)
                    if size > limit: raise ValueError('GitHub response exceeds byte limit')
                    chunks.append(chunk)
                return b''.join(chunks)
        except HTTPError as exc:
            raise ValueError(f'GitHub request refused (HTTP {exc.code}); no redirects/private authentication supported') from None
        except (URLError, TimeoutError, OSError) as exc:
            raise ValueError('GitHub network request failed or timed out') from exc

    def json(self,url):
        return json.loads(self.get(url, 4_000_000))


def inspect_remote(url, branch, *, client=None):
    owner, repo, canonical = repository_url(url)
    branch = branch_name(branch)
    client = client or PublicGitHub()
    base = f'https://api.github.com/repos/{owner}/{repo}'
    info = client.json(base)
    # Explicit public status, no ambient credentials and no renamed-repository redirect.
    if info.get('private') is not False or info.get('visibility') != 'public':
        raise ValueError('Only explicitly public GitHub repositories are supported')
    commit = client.json(base+'/commits/'+quote('refs/heads/'+branch,safe=''))
    revision = commit.get('sha','')
    tree_sha = commit.get('commit',{}).get('tree',{}).get('sha','')
    if not SHA.fullmatch(revision) or not SHA.fullmatch(tree_sha):
        raise ValueError('GitHub returned an invalid pinned commit/tree revision')
    return {'repository':owner+'/'+repo,'url':canonical,'selected_branch':branch,
            'source_revision':revision,'tree_sha':tree_sha}


def safe_path(path):
    parts = PurePosixPath(path).parts
    if (not path or len(path)>1024 or path.startswith('/') or '\\' in path or ':' in path or
        any(p in ('', '.', '..') or p.casefold()=='.git' for p in path.split('/')) or
        any(ord(c)<32 or ord(c)==127 for c in path)):
        raise ValueError('Unsafe or unsupported repository/archive path')
    return parts


def validate_tree(data, expected_tree):
    if data.get('truncated') is not False or data.get('sha') != expected_tree:
        raise ValueError('Require a complete tree matching the pinned commit')
    entries = data.get('tree')
    if not isinstance(entries,list) or not 1 <= len(entries) <= MAX_ENTRIES:
        raise ValueError('GitHub tree exceeds entry limits or is empty')
    files, seen, folded, total, python_bytes = {}, set(), set(), 0, 0
    for entry in entries:
        path = entry.get('path','')
        parts = safe_path(path)
        if path in seen or path.casefold() in folded:
            raise ValueError('Duplicate or case-colliding repository paths')
        seen.add(path); folded.add(path.casefold())
        mode, kind = entry.get('mode'),entry.get('type')
        if mode=='040000' and kind=='tree': continue
        if mode not in ('100644','100755') or kind!='blob':
            raise ValueError('Symlinks/submodules/non-regular Git entries are not supported')
        size = entry.get('size')
        if not isinstance(size,int) or size<0 or not SHA.fullmatch(entry.get('sha','')):
            raise ValueError('Invalid Git blob size or hash')
        total += size
        if total>MAX_EXPANDED: raise ValueError('Repository exceeds expanded byte limit')
        selected = not any(p in EXCLUDED for p in parts) and (path.endswith('.py') or path in SUPPORT)
        if selected:
            limit = MAX_BYTES if path in SOURCE_PATHS else (1_000_000 if path.endswith('.py') else 512000)
            if size>limit: raise ValueError('Selected source file exceeds byte limit')
            if path.endswith('.py'): python_bytes+=size
        files[path]={**entry,'selected':selected}
    if python_bytes>16_000_000 or not any(p.endswith('.py') and e['selected'] for p,e in files.items()):
        raise ValueError('Require Python source within the 16 MB snapshot limit')
    # Fail on file/parent conflicts before touching the filesystem.
    for path in seen:
        for parent in PurePosixPath(path).parents:
            if str(parent) in files: raise ValueError('Repository file/directory collision')
    return files


def unpack_verified(archive, files, root):
    """Never extractall. Bound metadata/inflation and verify selected Git blob hashes."""
    if len(archive)>MAX_ARCHIVE: raise ValueError('Archive exceeds compressed byte limit')
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        members = bundle.infolist()
        if not members or len(members)>MAX_ENTRIES+1: raise ValueError('Archive entry limit exceeded')
        prefix = members[0].filename.split('/')[0]
        safe_path(prefix)
        seen, found, expanded, casefolded = set(), set(), 0, set()
        for member in members:
            name = member.filename
            if member.orig_filename != name:
                raise ValueError('Ambiguous NUL-containing archive name')
            if not name.startswith(prefix+'/'): raise ValueError('Archive root mismatch')
            relative = name[len(prefix)+1:].removesuffix('/')
            if not relative:
                if not member.is_dir(): raise ValueError('Invalid archive root')
                continue
            safe_path(relative)
            if relative in seen or relative.casefold() in casefolded: raise ValueError('Duplicate archive path')
            seen.add(relative);casefolded.add(relative.casefold())
            mode = member.external_attr>>16
            if member.flag_bits&1 or (stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR)):
                raise ValueError('Encrypted or non-regular archive entry')
            expanded+=member.file_size
            if expanded>MAX_EXPANDED: raise ValueError('Archive expanded byte limit exceeded')
            if member.is_dir():
                if relative in files: raise ValueError('Archive directory/file mismatch')
                continue
            entry = files.get(relative)
            if entry is None or member.file_size!=entry['size']: raise ValueError('Archive/tree file mismatch')
            found.add(relative)
            if not entry['selected']: continue
            with bundle.open(member) as stream:
                content = stream.read(entry['size']+1)
            if len(content)!=entry['size'] or hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()!=entry['sha']:
                raise ValueError('Archive source does not match pinned Git blob')
            if b'\0' in content: raise ValueError('Selected source contains NUL bytes')
            target = root/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(content)
        if found!=set(files): raise ValueError('Archive is missing pinned tree files')


def archive_ownership(root):
    for path in SOURCE_PATHS:
        source = root/path
        if source.is_file():
            data = source.read_bytes()
            try: text = data.decode('utf-8')
            except UnicodeDecodeError: return {'status':'SOURCE_NOT_UTF8','path':path}
            return {'status':'FOUND','path':path,'text':text,'sha256':hashlib.sha256(data).hexdigest()}
    return {'status':'ABSENT_AT_PINNED_REVISION'}


def import_public(url, branch, tenant, expected_head):
    if os.environ.get('CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT')!='1':
        raise ValueError('Public import disabled: operator must set CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT=1')
    if not TENANT_PATTERN.fullmatch(tenant) or not SHA.fullmatch(expected_head):
        raise ValueError('Require a new repo_ tenant and full expected SHA-1 commit')
    owner, repo, canonical = repository_url(url)
    branch_name(branch)
    with writer_locks(canonical,tenant):
        if tenant in db_manager.list_tenant_graphs(): raise ValueError('Tenant already exists; no overwrite')
        client = PublicGitHub()
        pinned = inspect_remote(canonical,branch,client=client)
        if pinned['source_revision']!=expected_head: raise ValueError('Branch moved or expected commit differs; inspect and confirm again')
        tree = client.json(f'https://api.github.com/repos/{owner}/{repo}/git/trees/{pinned["tree_sha"]}?recursive=1')
        files = validate_tree(tree,pinned['tree_sha'])
        archive = client.get(f'https://codeload.github.com/{owner}/{repo}/zip/{expected_head}',MAX_ARCHIVE)
        with tempfile.TemporaryDirectory(prefix='chronosgraph-public-') as temp:
            root=Path(temp)
            unpack_verified(archive,files,root)
            paths=sorted(p for p,e in files.items() if e['selected'] and p.endswith('.py'))
            now=int(time.time())
            return _ingest_repo(canonical,tenant,expected_head,False,
                snapshot_metadata={'connection_kind':'PUBLIC_GITHUB_ARCHIVE','selected_branch':branch,
                    'workspace_check_status':'PINNED_AT_IMPORT','workspace_checked_at':now,
                    'workspace_observed_revision':expected_head,'import_tree_sha':pinned['tree_sha'],
                    'import_file_count':len(files),'import_archive_sha256':hashlib.sha256(archive).hexdigest(),
                    'import_selected_blob_verification':'GIT_SHA1','import_model_calls':0},
                prepared_snapshot={'source':(root,expected_head,canonical,owner+'/'+repo),
                    'paths':paths,'ownership_document':archive_ownership(root)})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['inspect','import'])
    parser.add_argument('--url',required=True)
    parser.add_argument('--branch',required=True)
    parser.add_argument('--tenant')
    parser.add_argument('--expected-head')
    args=parser.parse_args()
    try:
        if args.operation=='inspect':
            if args.tenant or args.expected_head: raise ValueError('inspect does not write a graph or accept import arguments')
            result=inspect_remote(args.url,args.branch)
        else:
            if not args.tenant or not args.expected_head: raise ValueError('import requires --tenant and --expected-head')
            result=import_public(args.url,args.branch,args.tenant,args.expected_head)
    except (ValueError,OSError,zipfile.BadZipFile,RuntimeError) as exc:
        parser.exit(2,'Public GitHub intake refused: '+(str(exc) if isinstance(exc,ValueError) else 'operation failed; no source code executed')+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
