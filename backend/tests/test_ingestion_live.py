"""Real FalkorDB integration and T-01 acceptance tests; no database substitutes."""
import math
import uuid
import pytest
from app.db.client import db_manager
from app.db import queries
from app.ingestion.seed_repos import REPOS, pagerank, seed_single_repo


@pytest.mark.parametrize('tenant', list(REPOS))
def test_source_graph_has_real_structure_and_provenance(tenant):
    graph=db_manager.get_graph(tenant)
    assert graph.ro_query('MATCH (f:File) RETURN count(f)').result_set[0][0]>=10
    assert graph.ro_query('MATCH (f:Function) RETURN count(f)').result_set[0][0]>=15
    assert graph.ro_query('MATCH (c:Contributor) RETURN count(c)').result_set[0][0]>=5
    assert graph.ro_query('MATCH (p:PullRequest) RETURN count(p)').result_set[0][0]>=5
    rows=graph.ro_query('MATCH (f:File) RETURN f.source_revision,f.source_url,f.sha256,f.pagerank').result_set
    assert all(len(revision)==40 and revision in url and len(digest)==64 for revision,url,digest,_ in rows)
    # Native FalkorDB scores are retained verbatim; a sum-of-one is not an API invariant.
    assert all(math.isfinite(row[3]) and row[3]>=0 for row in rows)
    assert max(row[3] for row in rows)>0
    assert graph.ro_query('MATCH (:File)-[r:IMPORTS]->(:File) RETURN count(r)').result_set[0][0]>0
    assert graph.ro_query('MATCH (:Function)-[r:CALLS]->(:Function) RETURN count(r)').result_set[0][0]>0


@pytest.mark.parametrize('tenant', list(REPOS))
def test_reseed_is_idempotent(tenant):
    graph=db_manager.get_graph(tenant)
    before=graph.ro_query('MATCH (n) RETURN count(n)').result_set[0][0]
    edges_before=graph.ro_query('MATCH ()-[r]->() RETURN count(r)').result_set[0][0]
    seeded=seed_single_repo(tenant)
    assert seeded['nodes']==before and seeded['edges']==edges_before


def test_real_sandbox_isolation_and_exception_cleanup():
    name='test_chronos_'+uuid.uuid4().hex[:8]
    base=db_manager.get_graph(name)
    base.query('CREATE (:File {path:"original.py"})')
    before=set(db_manager.list_tenant_graphs())
    try:
        with pytest.raises(RuntimeError,match='intentional test exception'):
            with db_manager.ephemeral_sandbox(name) as (copy,clone_name,clone_ms):
                assert clone_name in db_manager.list_tenant_graphs() and clone_ms>=0
                copy.query('CREATE (:File {path:"copy-only.py"})')
                assert base.ro_query('MATCH (f:File) RETURN count(f)').result_set[0][0]==1
                raise RuntimeError('intentional test exception')
        assert set(db_manager.list_tenant_graphs())==before
    finally:
        base.delete()


def test_read_only_discovery_rejects_writes():
    name='test_chronos_'+uuid.uuid4().hex[:8]
    graph=db_manager.get_graph(name)
    graph.query('CREATE (:File {path:"readonly.py"})')
    try:
        with pytest.raises(Exception):
            db_manager.ro_query(name,'CREATE (:ForbiddenWrite)')
        assert graph.ro_query('MATCH (n:ForbiddenWrite) RETURN count(n)').result_set[0][0]==0
    finally:
        graph.delete()


def test_vector_index_and_search_are_real():
    name='test_chronos_'+uuid.uuid4().hex[:8]
    graph=db_manager.get_graph(name)
    try:
        db_manager.ensure_indexes(name)
        vector=db_manager.embed_text('connection timeout policy')
        graph.query('CREATE (:Decision {id:"vector-test",embedding:vecf32($embedding)})',{'embedding':vector})
        result=graph.ro_query("CALL db.idx.vector.queryNodes('Decision','embedding',1,vecf32($embedding)) YIELD node,score RETURN node.id,score",{'embedding':vector})
        assert result.result_set[0][0]=='vector-test'
    finally:
        graph.delete()


def test_pagerank_is_computed_and_normalized():
    ranks=pagerank(['a.py','b.py'],[{'source':'a.py','target':'b.py'}])
    assert ranks['b.py']>ranks['a.py'] and math.isclose(sum(ranks.values()),1.0)


@pytest.mark.parametrize('tenant', list(REPOS))
def test_t01_required_policy_chains_have_curated_evidence(tenant):
    """An intentional acceptance gate: do not fabricate history to make it pass."""
    graph=db_manager.get_graph(tenant)
    count=graph.ro_query("MATCH (:Decision {status:'ACTIVE'})-[:SUPERSEDED]->(:Decision {status:'SUPERSEDED'}) RETURN count(*)").result_set[0][0]
    assert count>=4, 'T-01 requires curated decision chains; none were invented from PR titles'


@pytest.mark.parametrize('tenant', list(REPOS))
def test_existing_seed_is_read_only_and_does_not_fetch_source(tenant, monkeypatch):
    import subprocess
    graph = db_manager.get_graph(tenant)
    before = graph.ro_query('MATCH (n) RETURN id(n),properties(n) ORDER BY id(n)').result_set
    def forbidden(*args, **kwargs):
        pytest.fail('Existing snapshot reseeding must not fetch or parse repository source')
    monkeypatch.setattr(subprocess, 'run', forbidden)
    monkeypatch.setattr(subprocess, 'check_output', forbidden)
    result = seed_single_repo(tenant)
    assert result['snapshot_read_only'] is True
    assert result['analysis_status'] == 'EXISTING_SNAPSHOT_PRESERVED_REIMPORT_FOR_NEW_ANALYZER'
    assert graph.ro_query('MATCH (n) RETURN id(n),properties(n) ORDER BY id(n)').result_set == before
