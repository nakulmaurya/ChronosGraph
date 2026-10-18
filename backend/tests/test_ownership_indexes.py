"""Native FalkorDB plans, idempotent DDL and copy parity; no mocked DB."""
import uuid
import pytest
from app.db.client import db_manager
from app.db.ownership_indexes import ensure_ownership_indexes, ownership_index_state, OWNERSHIP_INDEXES


@pytest.fixture
def graph():
    name = 'repo_test_' + uuid.uuid4().hex
    g = db_manager.get_graph(name)
    g.query('''UNWIND range(0,1999) AS i
      CREATE (:OwnershipSource {id:'source_'+toString(i)}),
      (:OwnershipRule {id:'rule_'+toString(i),pattern:'src/'+toString(i)+'.py'}),
      (:DeclaredOwner {name:'@owner_'+toString(i),kind:'USERNAME'})''')
    try:
        yield g
    finally:
        if name in db_manager.list_tenant_graphs():
            g.delete()


def test_ownership_point_lookups_use_native_indexes_and_preserve_results(graph):
    cases = [('OwnershipSource','id','source_1777'),
             ('OwnershipRule','id','rule_1777'),
             ('DeclaredOwner','name','@owner_1777')]
    before = {}
    for label,prop,value in cases:
        q = f'MATCH (n:{label} {{{prop}:$value}}) RETURN properties(n)'
        before[label] = graph.ro_query(q, {'value':value}).result_set
        assert 'Index Scan' not in str(graph.explain(q, {'value':value}))
    ensure_ownership_indexes(graph)
    for label,prop,value in cases:
        q = f'MATCH (n:{label} {{{prop}:$value}}) RETURN properties(n)'
        assert graph.ro_query(q, {'value':value}).result_set == before[label]
        assert 'Index Scan' in str(graph.explain(q, {'value':value}))
    assert all(ownership_index_state(graph)[key] == 'OPERATIONAL' for key in OWNERSHIP_INDEXES)


def test_repeat_setup_preserves_properties_and_does_not_duplicate_indexes(graph):
    before = graph.ro_query('MATCH (n) RETURN labels(n),properties(n) ORDER BY id(n)').result_set
    ensure_ownership_indexes(graph)
    state = ownership_index_state(graph)
    ensure_ownership_indexes(graph)
    assert ownership_index_state(graph) == state
    assert graph.ro_query('MATCH (n) RETURN labels(n),properties(n) ORDER BY id(n)').result_set == before
    # A name index must not merge different declared-owner kinds or alter matching.
    graph.query("CREATE (:DeclaredOwner {name:'@owner_1777',kind:'TEAM'})")
    assert graph.ro_query("MATCH (o:DeclaredOwner {name:'@owner_1777',kind:'USERNAME'}) RETURN count(o)").result_set == [[1]]
    assert graph.ro_query("MATCH (o:DeclaredOwner {name:'@owner_1777',kind:'TEAM'}) RETURN count(o)").result_set == [[1]]


def test_graph_copy_preserves_ownership_index_and_lookup(graph):
    ensure_ownership_indexes(graph)
    name = 'repo_test_' + uuid.uuid4().hex
    clone = db_manager.copy_graph(graph.name, name)
    try:
        q = 'MATCH (n:OwnershipRule {id:$id}) RETURN n.pattern'
        assert clone.ro_query(q, {'id':'rule_1777'}).result_set == [['src/1777.py']]
        assert 'Index Scan' in str(clone.explain(q, {'id':'rule_1777'}))
        assert all(ownership_index_state(clone)[key] == 'OPERATIONAL' for key in OWNERSHIP_INDEXES)
    finally:
        if name in db_manager.list_tenant_graphs():
            clone.delete()
