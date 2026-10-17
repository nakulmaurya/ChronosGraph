"""Native graph navigation, with only disposable fixture writes."""
import uuid
import pytest
from fastapi import HTTPException
from app.db.client import db_manager
from app.services.command_center import overview, file_detail, history
from app.ingestion.ast_parser import parse_python_source

@pytest.fixture
def tenant():
    name='repo_test_'+uuid.uuid4().hex
    graph=db_manager.get_graph(name)
    graph.query('''CREATE (:RepoMetadata {status:'READY',repository:'fixture/command-center'}),
      (a:File {path:'src/a.py',sha256:'a',source_revision:'v1',loc:5}),
      (b:File {path:'lib/b.py',sha256:'b',source_revision:'v1',loc:7}),
      (c:File {path:'src/c.py',sha256:'c',source_revision:'v1',loc:3}),
      (f:Function {name:'run',qualified_name:'src/a.py:run',file_path:'src/a.py',start_line:1,end_line:3}),
      (g:Function {name:'help',qualified_name:'lib/b.py:help',file_path:'lib/b.py',start_line:1,end_line:2}),
      (a)-[:DEFINES]->(f),(b)-[:DEFINES]->(g),(a)-[:IMPORTS]->(b),
      (c)-[:IMPORTS]->(a),(f)-[:CALLS]->(g),
      (p:PullRequest {id:'git:fixture',record_kind:'COMMIT',commit_sha:$sha,title:'Update a',committed_at:12}),
      (u:Contributor {name:'Fixture author'}),(u)-[:AUTHORED]->(p),
      (p)-[:MODIFIES {additions:3,deletions:1}]->(a)''',{'sha':'a'*40})
    before=graph.ro_query('MATCH (n) RETURN labels(n),properties(n) ORDER BY id(n)').result_set
    try: yield name
    finally:
        assert graph.ro_query('MATCH (n) RETURN labels(n),properties(n) ORDER BY id(n)').result_set==before
        graph.delete()

def test_folder_map_aggregates_actual_imports_only(tenant):
    data=overview(tenant)
    assert data['counts']['File']==3 and data['counts']['Function']==2
    assert {n['path']:n['files'] for n in data['nodes']}=={'lib/':1,'src/':2}
    assert data['edges']==[{'source':'src/','target':'lib/','count':1}]
    children=overview(tenant,'src/')
    assert {n['path'] for n in children['nodes']}=={'src/a.py','src/c.py'}
    assert children['edges']==[{'source':'src/c.py','target':'src/a.py','count':1}]
    assert 'source_text' not in str(data)

def test_file_inspector_directions_functions_calls_and_not_found(tenant):
    data=file_detail(tenant,'src/a.py')
    assert data['imports']==[{'path':'lib/b.py'}]
    assert data['importers']==[{'path':'src/c.py'}]
    assert data['symbols'][0]['qualified_name']=='src/a.py:run'
    assert data['calls'][0]['source']=='src/a.py:run'
    with pytest.raises(HTTPException) as exc: file_detail(tenant,'missing.py')
    assert exc.value.status_code==404

def test_commit_file_changes_are_indexed_not_invented(tenant):
    data=history(tenant,'a'*40)
    assert data['commits'][0]['author']=='Fixture author'
    assert data['changes']==[{'path':'src/a.py','additions':3,'deletions':1,'binary':None}]
    with pytest.raises(HTTPException): history(tenant,'b'*40)
    with pytest.raises(HTTPException): history(tenant,'../bad')

def test_folder_validation_and_missing_tenant(tenant):
    for prefix in ('../','src','./','src/../'):
        with pytest.raises(HTTPException): overview(tenant,prefix)
    with pytest.raises(HTTPException): overview('repo_test_missing_'+uuid.uuid4().hex)

def test_docstrings_are_bounded_data_not_executed():
    data=parse_python_source('class A:\n    """A class."""\n    def run(self):\n        """A function."""\n        return 1\n','a.py')
    assert data['classes'][0]['docstring']=='A class.'
    assert data['functions'][0]['docstring']=='A function.'

def test_legacy_snapshot_revision_requires_consistent_file_provenance(tenant):
    from app.services.workspace import workspace_snapshot
    assert workspace_snapshot(tenant)['source_revision']=='v1'
