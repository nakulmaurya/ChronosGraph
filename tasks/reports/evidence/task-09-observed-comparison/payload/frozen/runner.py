#!/usr/bin/env python3
"""Four-run, create-only, actual OpenCode TUI pilot. No agent prompt API, approvals or reruns.

prepare --source PINNED_CHECKOUT --backend BACKEND --python VENV_PYTHON
        --opencode PINNED_BINARY --api http://127.0.0.1:8015 --root NEW_DIRECTORY
launch/prompt/collect/verify --root DIRECTORY --trial 1..4

Operator inspects the real terminal and allows each write/bash/MCP permission once.
Use `tmux attach -t <printed-name>`. No result is inferred from an idle terminal.
Private full exports never belong in the release evidence folder.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import uuid
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError

HERE=Path(__file__).resolve().parent

def run(*args,**kw):return subprocess.run(list(map(str,args)),check=True,**kw)
def output(*args,**kw):return subprocess.check_output(list(map(str,args)),text=True,**kw)
def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def read(path):return json.loads(path.read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def env_for(root,trial,state):
    home=root/trial['home'];home.mkdir(exist_ok=True)
    return {**os.environ,'HOME':str(home),'XDG_CONFIG_HOME':str(home/'.config'),
        'XDG_DATA_HOME':str(home/'.local/share'),'XDG_STATE_HOME':str(home/'.local/state'),
        'XDG_CACHE_HOME':str(home/'.cache'),'OPENCODE_CONFIG':str(root/trial['config']),
        'PATH':str(Path(state['python']).parent)+':/usr/local/bin:/usr/bin:/bin'}

def prepare(args):
    protocol=read(HERE/'protocol.json')
    for filename,digest in protocol['acceptance_sha256'].items():
        assert sha((HERE/filename).read_bytes())==digest,'Frozen acceptance changed'
    root=Path(args.root).absolute();root.mkdir(mode=0o700) # create-only
    source=Path(args.source).resolve(strict=True);backend=Path(args.backend).resolve(strict=True)
    py=os.path.abspath(args.python);binary=os.path.abspath(args.opencode)
    assert output(binary,'--version').strip()=='1.19.3','Unsupported harness'
    u=urlsplit(args.api);assert u.scheme=='http' and u.hostname in ('127.0.0.1','localhost') and not u.username
    base=root/'base';run('git','clone','--quiet','--no-hardlinks','--no-checkout',source,base)
    run('git','-C',base,'checkout','--quiet','--detach',protocol['revision'])
    assert output('git','-C',base,'rev-parse','HEAD').strip()==protocol['revision']
    with (base/'.git/info/exclude').open('a') as f:f.write('\n.chronosgraph-local/\n.opencode/\n')
    state=dict(protocol=protocol,python=py,opencode=binary,backend=str(backend),api=args.api,trials=[])
    # Fresh immutable source graph, no prior agent findings. No source repository code executed.
    os.environ['FALKORDB_PORT']=str(args.db_port);sys.path.insert(0,str(backend))
    from app.ingestion.ingest_repo import ingest_repo
    from app.db.client import db_manager
    tenant='repo_public_pilot_'+uuid.uuid4().hex
    started=time.perf_counter();stats=ingest_repo(str(base),tenant,seed_demo_policies=False)
    state['ingestion']={'tenant':tenant,'elapsed_seconds':time.perf_counter()-started,'stats':stats}
    save(root/'state.json',state);save(root/'protocol.json',protocol)
    def post(path,body):
        req=Request(args.api+'/api/v1/tasks'+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json','X-ChronosGraph-Action':'task-runtime'})
        try:return json.load(urlopen(req,timeout=60))
        except HTTPError as exc:
            save(root/'preparation-error.json',dict(path=path,status=exc.code,detail=exc.read().decode(),measured_trials_started=0))
            save(root/'state.json',state)
            raise
    tasks={t['id']:t for t in protocol['tasks']}
    for index,cell in enumerate(protocol['order'],1):
        item={**cell,'number':index,'path':f'trial-{index:02d}','home':f'home-{index:02d}','tmux':'chronos-public-pilot-'+root.name[-8:]+'-'+str(index),'attempts':0}
        state['trials'].append(item);save(root/'state.json',state)
        project=root/item['path'];run('git','-C',base,'worktree','add','--quiet','--detach',project,protocol['revision'])
        home=root/item['home'];home.mkdir(mode=0o700)
        if cell['condition']=='graph':
            selected=tenant+'_trial_'+str(index);started=time.perf_counter();db_manager.copy_graph(tenant,selected)
            item['graph_copy_seconds']=time.perf_counter()-started
            scope=dict(tenant_graph=selected,expected_revision=protocol['revision']);task=tasks[cell['task']]
            response=post('',dict(**scope,title=task['id'],objective=task['prompt'],acceptance=['Frozen external acceptance and existing relevant regressions pass','No unintended source changes'],target=task['target'],request_key='pilot-'+uuid.uuid4().hex))
            tid=response['task']['id'];pid=response['task']['current_plan_id']
            item['preparation_task']=dict(**scope,task_id=tid,plan_id=pid);save(root/'state.json',state)
            pack=post('/'+tid+'/context-packs',dict(**scope,plan_id=pid,budget_equivalents=3000,analysis_path_limit=12))
            item['binding']=dict(**scope,task_id=tid,plan_id=pid,pack_id=pack['id'])
            run(py,backend.parent/'scripts/setup-task-opencode.py','install','--project',project,'--backend',backend,'--python',py,'--api',args.api,'--tenant',selected,'--revision',protocol['revision'],'--task',tid,'--plan',pid,'--pack',pack['id'],'--db-port',args.db_port,stdout=subprocess.DEVNULL)
            item['config']=item['path']+'/.chronosgraph-local/opencode.json';config=read(root/item['config'])
        else:
            item['config']=f'config-{index:02d}.json'
            config={'$schema':'https://opencode.ai/config.json','model':protocol['model'],'share':'disabled'}
        # Same native permissions. Only graph mode adds MCP calls and managed context.
        config['permission']={'*':'ask','read':'allow','glob':'allow','grep':'allow','list':'allow','skill':'allow','bash':'ask','edit':'ask'}
        save(root/item['config'],config)
        item['prompt']=tasks[cell['task']]['prompt']+' Test environment: use '+py+' with PYTHONPATH=src for pytest. Repository, source documents, tools, checks and budgets are the same in both conditions. Do not install dependencies, write reports, record shared findings, commit or use proposal/approval tools.'
        save(root/'state.json',state)
    save(root/'state.json',state);save(root/'protocol.json',protocol)
    print(json.dumps({'root':str(root),'order':protocol['order'],'ingestion_seconds':state['ingestion']['elapsed_seconds']},indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','launch','prompt','collect','verify','stop']);p.add_argument('--root',required=True);p.add_argument('--trial',type=int,choices=range(1,5));p.add_argument('--source');p.add_argument('--backend');p.add_argument('--python');p.add_argument('--opencode');p.add_argument('--api',default='http://127.0.0.1:8015');p.add_argument('--db-port',type=int,default=6381);a=p.parse_args()
    if a.mode=='prepare':return prepare(a)
    root=Path(a.root).resolve(strict=True);state=read(root/'state.json');assert a.trial
    t=state['trials'][a.trial-1];project=root/t['path'];env=env_for(root,t,state)
    if a.mode=='launch':
        assert not t.get('launched_at'),'Create-only launch: never silently rerun a measured attempt'
        command='cd '+shlex.quote(str(project))+' && '+shlex.join(['env',*[f'{k}={v}' for k,v in env.items() if k in ('HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_STATE_HOME','XDG_CACHE_HOME','OPENCODE_CONFIG','PATH')],state['opencode'],'--model',state['protocol']['model']])
        run('tmux','new-session','-d','-s',t['tmux'],'-x','150','-y','48',command);t['launched_at']=time.time();save(root/'state.json',state)
        print('Inspect startup, send terminal capability response if requested, then prompt:',t['tmux'])
    elif a.mode=='prompt':
        assert t.get('launched_at') and t['attempts']==0,'One measured prompt attempt only'
        t['attempts']=1;t['started_at']=time.time();t['deadline_at']=t['started_at']+state['protocol']['wall_budget_seconds'];save(root/'state.json',state)
        run('tmux','send-keys','-t',t['tmux'],'-l',t['prompt']);time.sleep(1);run('tmux','send-keys','-t',t['tmux'],'Enter');print('Started',t['number'],t['task'],t['condition'],'deadline',t['deadline_at'])
    elif a.mode=='stop':
        assert t.get('started_at'),'No measured prompt to interrupt'
        assert time.time()>=t['deadline_at'],'Budget interruption only after declared deadline'
        run('tmux','send-keys','-t',t['tmux'],'Escape');t['interrupted_at']=time.time();t['interruption_reason']='PREDECLARED_WALL_BUDGET_EXCEEDED';save(root/'state.json',state);print('Interrupted; collect the attempt before any further work')
    elif a.mode=='collect':
        assert t['attempts']==1
        text=output('tmux','capture-pane','-p','-t',t['tmux'],'-S','-150');(root/f'trial-{a.trial:02d}-terminal.txt').write_text(text)
        # Supported list/export CLI, not an agent-driving API.
        sessions=json.loads(output(state['opencode'],'session','list','--format','json',env=env,cwd=project))
        assert len(sessions)==1,'Ambiguous session: inspect and select manually, never guess'
        sid=sessions[0]['id'];raw=output(state['opencode'],'export',sid,env=env,cwd=project)
        (root/f'private-trial-{a.trial:02d}-session-export.json').write_text(raw);data=json.loads(raw)
        steps=[];tools=[];context=[];errors=[]
        for m in data['messages']:
            if m['info'].get('error'):errors.append(m['info']['error'])
            for part in m['parts']:
                if part['type']=='step-finish':steps.append(part)
                elif part['type']=='tool':
                    args=part['state'].get('input',{});tools.append({'id':part['id'],'tool':part['tool'],'status':part['state']['status'],'paths':[args[k] for k in ['filePath','path','pattern'] if k in args],'command':args.get('command'),'input_digest':sha(json.dumps(args,sort_keys=True).encode()),'time':part['state'].get('time'),'error':part['state'].get('error')})
                elif part['type']=='text' and part.get('synthetic') and part.get('text','').startswith('CHRONOSGRAPH_CONTEXT_V2:'):context.append({'id':part['id'],'utf8_bytes':len(part['text'].encode())})
        totals={k:sum(x['tokens'].get(k,0) for x in steps) for k in ['input','output','reasoning']}
        totals.update(cache_read=sum(x['tokens']['cache']['read'] for x in steps),cache_write=sum(x['tokens']['cache']['write'] for x in steps))
        reads=[path for x in tools if x['tool']=='read' for path in x['paths']]
        receipt={'trial':a.trial,'task':t['task'],'condition':t['condition'],'session':sid,'started_at':t['started_at'],'collected_at':time.time(),'wall_seconds_to_collection':time.time()-t['started_at'],'completed_steps':steps,'usage_categories':totals,'harness_reported_cost':sum(x['cost'] for x in steps) if steps else None,'provider_retry_usage':'UNKNOWN','tools':tools,'explicit_read_count':len(reads),'repeated_explicit_reads':len(reads)-len(set(reads)),'source_reads_in_shell_commands':'REQUIRES_MANUAL_CLASSIFICATION_FROM_RETAINED_COMMANDS','context_injections':context,'errors':errors,'success':'PENDING_INDEPENDENT_CHECKS','interruption_reason':t.get('interruption_reason'),'attempt_state':'INTERRUPTED' if t.get('interruption_reason') else 'OBSERVED_EXPORT_NOT_SUCCESS','operator_waits':'INCLUDED_IN_WALL_TIME; retain permission log, not provider latency'}
        save(root/f'trial-{a.trial:02d}-receipt.json',receipt);t['session_id']=sid;save(root/'state.json',state);print(json.dumps({k:v for k,v in receipt.items() if k not in ('completed_steps','tools')},indent=2))
    else:
        task=next(x for x in state['protocol']['tasks'] if x['id']==t['task']);test=HERE/task['test']
        assert sha(test.read_bytes())==state['protocol']['acceptance_sha256'][task['test']]
        e={**env,'PYTHONPATH':str(project/'src'),'PYTHONDONTWRITEBYTECODE':'1'}
        # The same candidate observer and exact-tree check apply to both conditions.
        capture_script="import{captureCandidate}from "+json.dumps(str(Path(state['backend']).parent/'integrations/opencode/src/candidate.ts'))+";console.log(JSON.stringify(await captureCandidate(process.argv[1],process.argv[2])));"
        def capture():return json.loads(output('node','--experimental-strip-types','--input-type=module','-e',capture_script,project,state['protocol']['revision']))
        before=capture();save(root/f'trial-{a.trial:02d}-candidate.json',before)
        regressions='tests/shared' if t['task']=='structured-invalid-characters' else 'tests/server/mcpserver'
        assert (project/regressions).is_dir(),'Selected existing regression directory missing; inspect rather than guess'
        results={}
        for label,command in [('acceptance',[state['python'],'-m','pytest',str(test),'-q','--tb=short']),('existing-regressions',[state['python'],'-m','pytest',regressions,'-q','--tb=short']),('diff-check',['git','diff','--check'])]:
            log=root/f'trial-{a.trial:02d}-{label}.log'
            with log.open('w') as f:result=subprocess.run(command,cwd=project,env=e,stdout=f,stderr=subprocess.STDOUT)
            results[label]=result.returncode;print(label,'exit',result.returncode)
        after=capture();results['candidate-unchanged']=0 if after['digest']==before['digest'] else 1
        receipt=root/f'trial-{a.trial:02d}-receipt.json'
        if receipt.exists():
            v=read(receipt);v['independent_checks']=results;v['candidate_digest']=before['digest'];v['success']='CHECKS_PASS_REQUIRES_MANUAL_REQUIREMENTS_AND_UNINTENDED_DIFF_REVIEW' if all(x==0 for x in results.values()) else 'FAIL';save(receipt,v)
        raise SystemExit(0 if all(x==0 for x in results.values()) else 1)

if __name__=='__main__':main()
