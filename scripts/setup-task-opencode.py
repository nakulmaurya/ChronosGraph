"""Create-only project OpenCode bridge install/doctor. No global or provider edits.

The API is local trusted-user only. This is not authentication or a code sandbox.
The generated config leaves all native permissions at ask; no model call is made.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def bridge_api(origin, path):
    url = urlsplit(origin)
    if url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost') or url.username or url.password or url.path not in ('','/') or url.query or url.fragment:
        raise ValueError('API must be a loopback HTTP origin')
    with urlopen(Request(origin.rstrip('/') + '/api/v1/tasks/' + path), timeout=10) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['install','doctor'])
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--backend', type=Path)
    parser.add_argument('--python', type=Path)
    parser.add_argument('--api', default='http://127.0.0.1:8011')
    parser.add_argument('--tenant')
    parser.add_argument('--revision')
    parser.add_argument('--task')
    parser.add_argument('--plan')
    parser.add_argument('--pack')
    parser.add_argument('--db-port', type=int, default=6381)
    parser.add_argument('--opencode', type=Path)
    args = parser.parse_args()
    project = args.project.resolve(strict=True)
    local = project / '.chronosgraph-local'
    plugin_dir = project / '.opencode/plugins'
    for path in (local, project / '.opencode', plugin_dir, project / '.opencode/chronosgraph'):
        if path.is_symlink():
            raise ValueError('Refuse symlinked integration directories')
    if args.mode == 'install':
        if not all([args.backend,args.python,args.tenant,args.revision,args.task,args.plan,args.pack]):
            parser.error('install requires backend, python, tenant, revision, task, plan and pack')
        backend = args.backend.resolve(strict=True)
        # Preserve venv symlink path: resolving it selects the system interpreter.
        python = Path(os.path.abspath(args.python.expanduser()))
        if not (backend / 'app/mcp_server/server.py').is_file() or not python.is_file():
            raise ValueError('Require installed backend and Python executable')
        if not 1024 <= args.db_port <= 65535:
            raise ValueError('Invalid DB port')
        binding = dict(api_url=args.api,tenant_graph=args.tenant,expected_revision=args.revision,
                       task_id=args.task,plan_id=args.plan,pack_id=args.pack)
        scope = urlencode(dict(tenant_graph=args.tenant,expected_revision=args.revision))
        pack = bridge_api(args.api, f'{args.task}/context-packs/{args.pack}?{scope}')
        if pack['plan_id'] != args.plan:
            raise ValueError('Pack does not match selected current plan')
        plugin = (ROOT/'integrations/opencode/src/bridge.ts').read_bytes()
        entry = b"export { ChronosGraph } from '../chronosgraph/bridge.ts';\n"
        config = {'$schema':'https://opencode.ai/config.json','model':'opencode/deepseek-v4.1-flash-free',
                  'share':'disabled','permission':{'*':'ask','bash':'ask'},
                  'mcp':{'chronosgraph':{'type':'local','command':[str(python),'-m','app.mcp_server.server'],
                    'environment':{'PYTHONPATH':str(backend),'FALKORDB_HOST':'127.0.0.1',
                      'FALKORDB_PORT':str(args.db_port),'CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD':'1'},
                    'enabled':True,'timeout':30000}}}
        files = {local/'binding.json':json.dumps(binding,indent=2).encode(),
                 local/'opencode.json':json.dumps(config,indent=2).encode(),
                 plugin_dir/'chronosgraph.ts':entry,
                 project/'.opencode/chronosgraph/bridge.ts':plugin,
                 project/'.opencode/package.json':json.dumps({'private':True,'dependencies':{'@opencode-ai/plugin':'1.19.3'}}).encode()}
        if any(p.exists() or p.is_symlink() for p in files):
            raise ValueError('Create-only install: target already exists. Preserve and review existing configuration; no overwrite performed.')
        made=[]
        try:
            for path,content in files.items():
                path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
                fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                made.append(path)
                with os.fdopen(fd,'wb') as f:f.write(content);f.flush();os.fsync(f.fileno())
        except BaseException:
            for path in made:path.unlink()
            raise
        print('Created project-only bridge. No global/provider files changed; no connection or model execution claimed.')
        print(f'Run from {project}: OPENCODE_CONFIG={local / "opencode.json"} <opencode-1.19.3>')
        print('Review permissions. Leave human approval separate; plugin never approves proposals.')
    else:
        binding=json.loads((local/'binding.json').read_text())
        if not args.opencode:parser.error('doctor requires --opencode pointing to the actual binary')
        version=subprocess.run([str(args.opencode),'--version'],check=True,capture_output=True,text=True,timeout=15).stdout.strip()
        if version!='1.19.3':raise ValueError(f'Unsupported harness version: {version}')
        source=(ROOT/'integrations/opencode/src/bridge.ts').read_bytes()
        installed=(project/'.opencode/chronosgraph/bridge.ts').read_bytes()
        if (plugin_dir/'chronosgraph.ts').read_bytes() != b"export { ChronosGraph } from '../chronosgraph/bridge.ts';\n":
            raise ValueError('Unexpected plugin entry exports')
        if source!=installed:raise ValueError('Installed plugin differs from reviewed source')
        scope=urlencode({k:binding[k] for k in ('tenant_graph','expected_revision')})
        pack=bridge_api(binding['api_url'],f'{binding["task_id"]}/context-packs/{binding["pack_id"]}?{scope}')
        task=bridge_api(binding['api_url'],f'{binding["task_id"]}?{scope}')
        state_path=local/'telemetry-state.json'
        state=json.loads(state_path.read_text()) if state_path.exists() else None
        print(json.dumps({'version':version,'plugin_sha256':hashlib.sha256(source).hexdigest(),
            'pack_digest':pack['digest'],'task_id':task['task']['id'],
            'runs_with_received_events':sum(bool(r['events']) for r in task['runs']),
            'pending_local_events':sum(len(r['queue']) for r in state['runs'].values()) if state else None,
            'acceptance':'CONFIG_AND_API_ONLY' if not state else 'RECEIPTS_PRESENT_REVIEW_FULL_WORKFLOW_SEPARATELY',
            'caution':'No doctor result alone proves provider execution, compaction, task success or approval.'},indent=2))


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print(f'BLOCKED: {error}',file=sys.stderr);sys.exit(1)
