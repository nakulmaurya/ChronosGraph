"""Portable config tests without invoking a model or a database."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('opencode_setup', Path(__file__).resolve().parents[2] / 'scripts/configure-opencode.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_generated_config_requires_permissions_and_snapshot_guard(tmp_path):
    backend = tmp_path / 'backend'
    server = backend / 'app/mcp_server/server.py'
    server.parent.mkdir(parents=True)
    server.write_text('')
    python = tmp_path / 'python'
    python.write_text('')
    c = module.configuration(backend, python, 16379, 'opencode/deepseek-v4.1-flash-free')
    assert c['permission'] == {'*': 'ask', 'bash': 'ask'}
    assert c['share'] == 'disabled'
    m = c['mcp']['chronosgraph']
    assert m['cwd'] == str(backend)
    assert m['environment']['CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD'] == '1'
    assert m['environment']['FALKORDB_PORT'] == '16379'
    assert 'CHRONOSGRAPH_ENABLE_WORKTREE_EXECUTION' not in m['environment']
    assert 'headers' not in c


def test_invalid_backend_is_refused(tmp_path):
    with pytest.raises(ValueError, match='Backend'):
        module.configuration(tmp_path, tmp_path / 'python', 6379, 'opencode/example')


@pytest.mark.parametrize('port', [0, 65536])
def test_invalid_port_refused(tmp_path, port):
    backend = tmp_path / 'backend'
    server = backend / 'app/mcp_server/server.py'
    server.parent.mkdir(parents=True)
    server.touch()
    python = tmp_path / 'python'
    python.touch()
    with pytest.raises(ValueError, match='port'):
        module.configuration(backend, python, port, 'opencode/example')


def test_invalid_model_refused(tmp_path):
    server = tmp_path / 'app/mcp_server/server.py'
    server.parent.mkdir(parents=True)
    server.touch()
    python = tmp_path / 'python'
    python.touch()
    with pytest.raises(ValueError, match='provider/model'):
        module.configuration(tmp_path, python, 6379, 'invalid')


def test_config_publish_never_overwrites(tmp_path):
    output = tmp_path / 'config.json'
    module.write_configuration({'permission': {'bash': 'ask'}}, output)
    original = output.read_bytes()
    assert output.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        module.write_configuration({'changed': True}, output)
    assert output.read_bytes() == original
    assert not list(tmp_path.glob('.chronos-opencode-*'))


def test_interrupted_write_leaves_no_partial_config(tmp_path, monkeypatch):
    output = tmp_path / 'config.json'
    def fail(data, stream, **kwargs):
        stream.write('{')
        raise OSError('injected interrupted write')
    monkeypatch.setattr(module.json, 'dump', fail)
    with pytest.raises(OSError, match='interrupted'):
        module.write_configuration({}, output)
    assert not output.exists()
    assert not list(tmp_path.iterdir())


def test_missing_output_parent_refused(tmp_path):
    with pytest.raises(FileNotFoundError):
        module.write_configuration({}, tmp_path / 'missing' / 'config.json')
