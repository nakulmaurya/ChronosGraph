"""Predeclared external acceptance for OWNED SYNTHETIC retry-after case.
Not provided as source files to the worker; not a public-repository benchmark.
"""
import inspect
import pytest
import client
import worker

@pytest.mark.parametrize('fn',[client.timeout_result,worker.should_retry])
def test_keyword_only_api(fn):
    p=inspect.signature(fn).parameters['retry_after']
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is None
    with pytest.raises(TypeError):fn(3)

def test_default_contract_and_retry_branch():
    assert client.timeout_result()=={'ok':False,'reason':'timeout'}
    assert client.timeout_result(retry_after=None)=={'ok':False,'reason':'timeout'}
    assert worker.should_retry() is True

@pytest.mark.parametrize('delay',[0,1,37])
def test_opt_in_metadata(delay):
    assert client.timeout_result(retry_after=delay)=={'ok':False,'reason':'timeout','retry_after':delay}
    assert worker.should_retry(retry_after=delay) is True

@pytest.mark.parametrize('bad',[True,False,1.5,'3',[],{}])
@pytest.mark.parametrize('fn',[client.timeout_result,worker.should_retry])
def test_invalid_type_is_not_silently_accepted(fn,bad):
    with pytest.raises(TypeError):fn(retry_after=bad)

@pytest.mark.parametrize('fn',[client.timeout_result,worker.should_retry])
def test_negative_delay_rejected(fn):
    with pytest.raises(ValueError):fn(retry_after=-1)

def test_worker_uses_dependency_and_propagates(monkeypatch):
    seen=[]
    def observed(**kwargs):
        seen.append(kwargs)
        return {'ok':True,'reason':'timeout'}
    monkeypatch.setattr(worker,'timeout_result',observed)
    assert worker.should_retry(retry_after=3) is False
    assert seen==[{'retry_after':3}]
