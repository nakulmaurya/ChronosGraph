from client import timeout_result
from worker import should_retry

def test_timeout_contract():
    assert timeout_result() == {'ok': False, 'reason': 'timeout'}
    assert should_retry() is True
