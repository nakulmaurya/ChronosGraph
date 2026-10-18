"""Native HTTP build declarations: explicit unknown, never guessed from paths."""
import pytest
from test_real_world_repos import client


@pytest.mark.parametrize('value,expected',[('a'*40,'a'*40),('',None),('A'*40,None),('/private/host/path',None)])
def test_build_identity_is_bounded_declared_metadata(client,monkeypatch,value,expected):
    monkeypatch.setenv('CHRONOSGRAPH_BUILD_COMMIT',value)
    response=client.get('/api/v1/release/identity');assert response.status_code==200
    data=response.json();assert data['application_commit']==expected
    assert data['status']==('DECLARED' if expected else 'UNRECORDED')
    assert data['basis']=='DEPLOYMENT_ENVIRONMENT_DECLARATION_NOT_CRYPTOGRAPHIC_ATTESTATION'
    assert '/private/' not in response.text and data['model_calls']==0
