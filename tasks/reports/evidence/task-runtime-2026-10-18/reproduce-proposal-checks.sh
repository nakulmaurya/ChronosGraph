set -eu
BASE="$HOME/ChronosGraph-task-integration"
PY="$HOME/ChronosGraph-quality-batch1/.venv/bin/python"
ROOT=$(cat /tmp/chronos-proposal-acceptance-root)
"$PY" - "$ROOT" <<'PY'
import ast,json,sys,hashlib,subprocess
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
root=Path(sys.argv[1]);r=json.loads((root/'setup-receipt.json').read_text());scope={k:r[k] for k in ('tenant_graph','expected_revision')}
with urlopen('http://127.0.0.1:8011/api/v1/proposals?'+urlencode({'tenant_graph':r['tenant_graph'],'revision':r['expected_revision']})) as response:props=json.load(response)['proposals']
assert len(props)==1, len(props)
p=props[0];actual=(root/'repo/client.py').read_text();base=subprocess.check_output(['git','-C',str(root/'repo'),'show','HEAD:client.py'],text=True)
assert p['proposed_files']=={'client.py':actual}
assert p['status']=='PROPOSED' and not p['executions'] and not p.get('approved_proposal_hash')
assert all(p[k]==r[k] for k in ('task_id','plan_id','pack_id')) and p['declared_rationale']
def without_docstrings(text):
 t=ast.parse(text)
 for n in ast.walk(t):
  if isinstance(n,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(n.body[0].value,ast.Constant) and isinstance(n.body[0].value.value,str):n.body=n.body[1:]
 return ast.dump(t,include_attributes=False)
assert without_docstrings(base)==without_docstrings(actual)
changed=subprocess.check_output(['git','-C',str(root/'repo'),'diff','--name-only'],text=True).splitlines();assert changed==['client.py'],changed
with urlopen('http://127.0.0.1:8011/api/v1/tasks/'+r['task_id']+'?'+urlencode(scope)) as response:task=json.load(response)
run=next(x for x in task['runs'] if x['id']==p['agent_run_id']);assert not run['missing_sequences']
(root/'proposal-runtime-receipt.json').write_text(json.dumps(task,indent=2));(root/'proposal-receipt.json').write_text(json.dumps(p,indent=2))
print(json.dumps({'proposal_id':p['id'],'status':p['status'],'task_id':p['task_id'],'plan_id':p['plan_id'],'pack_id':p['pack_id'],'agent_run_id':p['agent_run_id'],'session_id':run['session_id'],'proposal_hash':p['proposal_hash'],'file_sha256':hashlib.sha256(actual.encode()).hexdigest(),'checks':['actual proposal equals edited full file','AST unchanged excluding docstrings','only client.py changed','no approval or execution','managed task/plan/pack/run match','no event sequence gaps']},indent=2))
PY
cd "$ROOT/repo"
"$PY" -m pytest tests/test_contract.py -q
 git diff --check
