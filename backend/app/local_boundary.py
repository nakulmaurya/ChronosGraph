"""Explicit loopback UI origins shared by CORS and browser mutation checks."""
import os
from urllib.parse import urlsplit

DEFAULT_UI_ORIGINS = ('http://localhost:3001', 'http://127.0.0.1:3001',
                      'http://localhost:3004', 'http://127.0.0.1:3004')


def local_ui_origins():
    configured = os.environ.get('CHRONOSGRAPH_UI_ORIGINS')
    values = configured.split(',') if configured is not None else DEFAULT_UI_ORIGINS
    origins = []
    for value in values:
        value = value.strip()
        parsed = urlsplit(value)
        try:
            port = parsed.port
        except ValueError:
            raise ValueError('CHRONOSGRAPH_UI_ORIGINS requires explicit loopback HTTP origins') from None
        if (parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1')
            or not port or parsed.username or parsed.password or parsed.path
            or parsed.query or parsed.fragment
            or value != f'http://{parsed.hostname}:{port}'):
            raise ValueError('CHRONOSGRAPH_UI_ORIGINS requires explicit loopback HTTP origins')
        if value not in origins:
            origins.append(value)
    if not origins:
        raise ValueError('Configure at least one loopback UI origin')
    return origins
