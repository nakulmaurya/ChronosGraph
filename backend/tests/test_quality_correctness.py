"""Counterexamples from the review: assert user outcomes, not old implementation."""
import subprocess
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.ingestion import ingest_repo as ingestion
from app.ingestion.ast_parser import parse_python_source
from app.ingestion.dependencies import analyze_dependencies
from app.services import import_jobs


def request(origin):
    return SimpleNamespace(url=SimpleNamespace(hostname='127.0.0.1'), headers={
        'origin':origin, 'x-chronosgraph-action':'public-import'})


def test_default_launcher_origin_can_start_opted_in_import(monkeypatch):
    monkeypatch.setenv('CHRONOSGRAPH_ENABLE_BROWSER_IMPORT','1')
    monkeypatch.delenv('CHRONOSGRAPH_UI_ORIGINS',raising=False)
    import_jobs.authorize(request('http://127.0.0.1:3001'))
    import_jobs.authorize(request('http://127.0.0.1:3004'))


def test_operator_origin_is_shared_and_fail_closed(monkeypatch):
    from app.local_boundary import local_ui_origins
    monkeypatch.setenv('CHRONOSGRAPH_ENABLE_BROWSER_IMPORT','1')
    monkeypatch.setenv('CHRONOSGRAPH_UI_ORIGINS','http://127.0.0.1:3999')
    assert local_ui_origins()==['http://127.0.0.1:3999']
    import_jobs.authorize(request('http://127.0.0.1:3999'))
    with pytest.raises(HTTPException): import_jobs.authorize(request('http://127.0.0.1:3004'))
    for bad in ['*','https://evil.example','http://evil.example:3999','http://127.0.0.1:3999/','http://user@localhost:3999','null','']:
        monkeypatch.setenv('CHRONOSGRAPH_UI_ORIGINS',bad)
        with pytest.raises(ValueError): local_ui_origins()


@pytest.mark.parametrize('ref',[None,'main'])
def test_branch_import_resolves_current_source_not_cached_head(tmp_path,monkeypatch,ref):
    root=tmp_path/'source';root.mkdir();monkeypatch.setattr(ingestion,'CACHE',tmp_path/'cache')
    def git(*args):
        return subprocess.check_output(['git','-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-C',str(root),*args]).decode().strip()
    git('init','--quiet','-b','main');(root/'a.py').write_text('VALUE=1\n');git('add','.');git('commit','--quiet','-m','one')
    first=git('rev-parse','HEAD');assert ingestion.repository_source(str(root),ref)[1]==first
    (root/'a.py').write_text('VALUE=2\n');git('add','.');git('commit','--quiet','-m','two');second=git('rev-parse','HEAD')
    assert ingestion.repository_source(str(root),ref)[1]==second
    assert git('rev-parse','HEAD')==second and (root/'a.py').read_text()=='VALUE=2\n'
    assert ingestion.repository_source(str(root),first)[1]==first  # explicit immutable pin
    git('reset','--quiet','--hard',first)
    assert ingestion.repository_source(str(root),ref)[1]==first  # rewritten branch, not last cached checkout
    cached=ingestion.repository_source(str(root),first)[0]
    subprocess.run(['git','-C',str(cached),'remote','set-url','origin',str(tmp_path/'absent')],check=True)
    with pytest.raises(subprocess.CalledProcessError): ingestion.repository_source(str(root),ref)
    assert ingestion.repository_source(str(root),first)[1]==first  # exact local pin works offline


@pytest.mark.parametrize('root',['','src/','packages/lib/src/'])
@pytest.mark.parametrize('statement,call',[
    ('import pkg.mod','pkg.mod.helper()'),
    ('import pkg.mod as m','m.helper()'),
    ('from pkg import mod','mod.helper()'),
    ('from pkg import mod as m','m.helper()'),
    ('from . import mod','mod.helper()'),
])
def test_ordinary_module_import_calls_resolve_exact_target(root,statement,call):
    path=root+'pkg/app.py'
    items={p:parse_python_source(s,p) for p,s in {
        path:statement+'\ndef run():\n    return '+call+'\n',
        root+'pkg/__init__.py':'',root+'pkg/mod.py':'def helper():\n    return 1\n'}.items()}
    definitions={f['qualified_name'] for i in items.values() for f in i['functions']}
    imports,resolved,unknown=analyze_dependencies(items[path],set(items),definitions)
    assert root+'pkg/mod.py' in imports
    assert [target for _,target in resolved]==[root+'pkg/mod.py:helper']
    assert unknown==[]


def test_module_call_coverage_does_not_claim_zero_observed_calls():
    item=parse_python_source('def helper(): return 1\nVALUE=helper()\nclass A:\n    VALUE=helper()\ndef run(): return helper()\n','a.py')
    assert item['call_coverage']=={'observed':3,'function_scope':1,'excluded_non_function_scope':2}
    assert item['file']['call_excluded_non_function_scope_count']==2
    assert len(item['calls'])==1  # no invented Function node for module/class initialization


def test_strict_agent_guard_rejects_omissions_before_lookup_or_mutation(monkeypatch):
    from app.services import agent_activity
    from fastapi import HTTPException
    monkeypatch.setenv('CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD', '1')
    touched = []
    monkeypatch.setattr(agent_activity, 'tenant_exists', lambda tenant: touched.append(tenant))

    @agent_activity.instrument('test_guard')
    def operation(tenant_graph='repo_default', expected_revision=None):
        touched.append('operation')

    for arguments in ({}, {'tenant_graph': 'repo_explicit'}, {'expected_revision': 'a'*40}):
        with pytest.raises(HTTPException) as exc:
            operation(**arguments)
        assert exc.value.status_code == 422
    assert touched == []
    import inspect
    parameters = inspect.signature(operation).parameters
    for name in ('tenant_graph', 'expected_revision'):
        assert parameters[name].default is inspect.Parameter.empty


def test_annotation_calls_are_observed_even_when_not_analyzed():
    item = parse_python_source('def f(arg: annotation()) -> result(): return 1\n', 'annotated.py')
    assert item['call_coverage']['observed'] == 2
    assert item['call_coverage']['excluded_non_function_scope'] == 2


@pytest.mark.parametrize('statement,call', [
    ('import pkg.a', 'pkg.a.helper()'),
    ('import pkg.a as m', 'm.helper()'),
    ('from pkg import a', 'a.helper()'),
    ('from pkg import a as m', 'm.helper()'),
    ('from . import a', 'a.helper()'),
])
def test_native_module_import_helper_removal_reports_broken_caller(tmp_path, statement, call):
    """Native ingestion + GRAPH.COPY, not just a parser-only expected edge."""
    import uuid
    from app.db.client import db_manager
    from app.models import DiffImpactRequest
    from app.services.diff_impact import simulate_diff
    root = tmp_path/'native-imports'
    root.mkdir()
    files = {'src/pkg/__init__.py': '',
             'src/pkg/a.py': 'def helper(): return 1\nVALUE = helper()\n',
             'src/pkg/b.py': statement+'\ndef run():\n    return '+call+'\n',
             'tests/test_b.py': 'from pkg.b import run\ndef test_run(): assert run() == 1\n'}
    for path, body in files.items():
        target = root/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    git('init', '--quiet');git('add', '.')
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '--quiet', '-m', 'Module import fixture')
    tenant = 'repo_test_'+uuid.uuid4().hex
    try:
        ingestion.ingest_repo(str(root), tenant)
        names = set(db_manager.list_tenant_graphs())
        result = simulate_diff(DiffImpactRequest(tenant_graph=tenant, file_bodies={'src/pkg/a.py': 'def renamed(): return 8\n'}))
        assert 'src/pkg/b.py:run' in result['potentially_broken_callers']
        assert {'relationship':'CALLS','source':'src/pkg/b.py:run','target':'src/pkg/a.py:helper'} in result['removed_dependencies']
        assert 'tests/test_b.py' in result['impacted_test_files']
        assert result['call_coverage']['before']['excluded_non_function_scope'] == 1
        assert result['call_coverage']['after']['excluded_non_function_scope'] == 0
        assert result['sandbox_cleaned_up'] and set(db_manager.list_tenant_graphs()) == names
        assert db_manager.get_graph(tenant).ro_query("MATCH (f:File {path:'src/pkg/a.py'}) RETURN f.source_text").result_set == [[files['src/pkg/a.py']]]
    finally:
        if tenant in db_manager.list_tenant_graphs():
            db_manager.get_graph(tenant).delete()
