"""Native copy success, destination collision, and owned cleanup; no fake DB."""
import uuid
import pytest
from redis.exceptions import ResponseError
from app.db.client import db_manager


def test_copy_preserves_native_graph_and_rejects_existing_destination():
    source='repo_test_copy_'+uuid.uuid4().hex
    destination=source+'_clone'
    graph=db_manager.get_graph(source)
    try:
        graph.query('CREATE (:CopyProbe {value:42})')
        copied=db_manager.copy_graph(source,destination)
        assert copied.ro_query('MATCH (n:CopyProbe) RETURN n.value').result_set==[[42]]
        with pytest.raises(ResponseError):
            db_manager.copy_graph(source,destination)
        assert copied.ro_query('MATCH (n:CopyProbe) RETURN count(n)').result_set==[[1]]
    finally:
        for name in (destination,source):
            if name in db_manager.list_tenant_graphs():db_manager.get_graph(name).delete()


def test_sandbox_still_cleans_after_body_failure():
    source='repo_test_copy_'+uuid.uuid4().hex
    graph=db_manager.get_graph(source);graph.query('CREATE (:CopyProbe {value:42})')
    sandbox=None
    try:
        with pytest.raises(ValueError,match='owned-body-failed'):
            with db_manager.ephemeral_sandbox(source) as (copied,name,_):
                sandbox=name
                assert copied.ro_query('MATCH (n) RETURN count(n)').result_set==[[1]]
                raise ValueError('owned-body-failed')
        assert sandbox not in db_manager.list_tenant_graphs()
    finally:graph.delete()
