set -eu
BASE="$HOME/ChronosGraph-task-integration"
PY="$HOME/ChronosGraph-quality-batch1/.venv/bin/python"
"$PY" - "$BASE" <<'PY'
from pathlib import Path
import json,subprocess,sys,tempfile
base=Path(sys.argv[1]); root=Path(Path('/tmp/chronos-task-acceptance-root').read_text());r=json.loads((root/'setup-receipt.json').read_text());python=str(Path.home()/'ChronosGraph-quality-batch1/.venv/bin/python')
with tempfile.TemporaryDirectory(prefix='chronos-setup-check-') as d:
 p=Path(d)/'project';p.mkdir()
 args=[python,str(base/'scripts/setup-task-opencode.py'),'install','--project',str(p),'--backend',str(base/'backend'),'--python',python,'--tenant',r['tenant_graph'],'--revision',r['expected_revision'],'--task',r['task_id'],'--plan',r['plan_id'],'--pack',r['pack_id']]
 subprocess.run(args,check=True,capture_output=True)
 config=json.loads((p/'.chronosgraph-local/opencode.json').read_text())
 assert config['mcp']['chronosgraph']['command'][0]==python
 entry=(p/'.opencode/plugins/chronosgraph.ts').read_text();assert entry.count('export')==1 and '../chronosgraph/bridge.ts' in entry
 before={str(f.relative_to(p)):f.read_bytes() for f in p.rglob('*') if f.is_file()}
 retry=subprocess.run(args,capture_output=True,text=True);assert retry.returncode==1 and 'Create-only' in retry.stderr
 assert before=={str(f.relative_to(p)):f.read_bytes() for f in p.rglob('*') if f.is_file()}
 doctor=subprocess.run([python,str(base/'scripts/setup-task-opencode.py'),'doctor','--project',str(p),'--opencode','/tmp/chronos-agent-eval.NCqYrI/tools/opencode'],check=True,capture_output=True,text=True)
 assert json.loads(doctor.stdout)['acceptance']=='CONFIG_AND_API_ONLY'
 p2=Path(d)/'symlink-project';p2.mkdir();(p2/'.opencode').mkdir();outside=Path(d)/'outside';outside.mkdir();(p2/'.opencode/chronosgraph').symlink_to(outside,target_is_directory=True)
 blocked=args.copy();blocked[blocked.index('--project')+1]=str(p2)
 result=subprocess.run(blocked,capture_output=True,text=True);assert result.returncode==1 and 'symlinked' in result.stderr and not list(outside.iterdir())
 print('PASS: venv interpreter preserved; one-export plugin loader; create-only retry unchanged; live doctor CONFIG_AND_API_ONLY; symlinked implementation directory refused')
PY
