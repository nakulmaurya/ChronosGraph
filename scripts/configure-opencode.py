"""Generate an opt-in local OpenCode MCP config; never install dependencies or run code.

Official CLI's permission prompts stay enabled (especially bash: ask). No headers,
provider identity, API keys or automatic host-execution approvals are generated.
"""
import argparse
import json
import os
import tempfile
from pathlib import Path


def configuration(backend: Path, python: Path, port: int, model: str):
    if not (backend / 'app/mcp_server/server.py').is_file():
        raise ValueError('Backend must contain app/mcp_server/server.py')
    if not python.is_file():
        raise ValueError('Python executable does not exist')
    if not 1 <= port <= 65535:
        raise ValueError('DB port must be between 1 and 65535')
    if '/' not in model:
        raise ValueError('Model must be provider/model')
    return {
        '$schema': 'https://opencode.ai/config.json',
        'model': model,
        'share': 'disabled',
        'permission': {'*': 'ask', 'bash': 'ask'},
        'mcp': {'chronosgraph': {
            'type': 'local',
            'command': [str(python), '-m', 'app.mcp_server.server'],
            'cwd': str(backend),
            'environment': {
                'PYTHONPATH': str(backend),
                'FALKORDB_HOST': '127.0.0.1',
                'FALKORDB_PORT': str(port),
                'CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD': '1',
            },
            'enabled': True,
            'timeout': 30000,
        }},
    }


def write_configuration(data, output: Path):
    """Publish a complete owner-only file atomically, without overwriting a target."""
    fd, temporary = tempfile.mkstemp(prefix='.chronos-opencode-', dir=output.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        # Same-directory hard link publishes only after a complete write, and
        # fails if the user already has a target; unlike replace(), never clobbers.
        os.link(temporary, output)
    finally:
        os.unlink(temporary)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--backend', type=Path, required=True)
    p.add_argument('--python', type=Path, required=True)
    p.add_argument('--db-port', type=int, default=6379)
    p.add_argument('--model', default='opencode/deepseek-v4.1-flash-free')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        data = configuration(a.backend.resolve(), a.python.resolve(), a.db_port, a.model)
        write_configuration(data, a.output)
    except (ValueError, OSError) as e:
        p.exit(1, f'{e}\n')
    print('Created local config. Review it, then use OPENCODE_CONFIG=<output> opencode.')
    print('MCP tools require explicit permission; do not use --auto for approval/execution.')


if __name__ == '__main__':
    main()
