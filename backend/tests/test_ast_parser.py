from app.ingestion.ast_parser import parse_python_source, parse_python_file, resolve_import


def test_class_scoped_methods_do_not_collide():
    source = 'class A:\n def query(self): return self.run()\nclass B:\n def query(self): return 1\n'
    data = parse_python_source(source, 'pkg/core.py')
    assert [f['qualified_name'] for f in data['functions']] == ['pkg/core.py:A.query', 'pkg/core.py:B.query']
    assert data['calls'][0]['caller'] == 'pkg/core.py:A.query'


def test_nested_calls_not_attributed_to_outer():
    data = parse_python_source('def outer():\n def inner():\n  target()\n inner()\n', 'm.py')
    assert [(c['caller'], c['expression']) for c in data['calls']] == [('m.py:outer.inner', 'target'), ('m.py:outer', 'inner')]


def test_async_and_signature():
    data = parse_python_source('async def run(x: int, /, *, timeout=3) -> str:\n return await work(x)\n', 'm.py')
    fn = data['functions'][0]
    assert fn['is_async'] and 'timeout=3' in fn['signature'] and '-> str' in fn['signature']


def test_syntax_error_returns_diagnostic():
    data = parse_python_source('def broken(:', 'bad.py')
    assert data['errors'] and data['errors'][0]['line'] == 1
    assert data['functions'] == []


def test_relative_import_and_alias():
    data = parse_python_source('from .graph import Graph as G\nfrom .. import shared\n', 'pkg/sub/core.py')
    known = {'pkg/sub/graph.py', 'pkg/shared.py', 'pkg/__init__.py'}
    assert data['imports'][0]['alias'] == 'G'
    assert resolve_import(data['imports'][0], 'pkg/sub/core.py', known) == ['pkg/sub/graph.py']
    assert 'pkg/shared.py' in resolve_import(data['imports'][1], 'pkg/sub/core.py', known)


def test_external_import_not_fabricated():
    data = parse_python_source('import nonexistent\n', 'm.py')
    assert resolve_import(data['imports'][0], 'm.py', {'m.py'}) == []


def test_dynamic_calls_remain_unresolved():
    data = parse_python_source('def f(obj):\n return obj.query()\n', 'm.py')
    assert data['calls'][0]['expression'] == 'obj.query'
    assert data['calls'][0]['resolution'].startswith('unresolved')


def test_source_is_never_executed(tmp_path):
    marker = tmp_path / 'should-not-exist'
    source = f'open({str(marker)!r}, "w").write("danger")\n'
    parse_python_source(source, 'untrusted.py')
    assert not marker.exists()


def test_file_encoding_and_digest(tmp_path):
    file = tmp_path / 'latin.py'
    file.write_bytes(b'# coding: latin-1\nx="caf\xe9"\n')
    data = parse_python_file(file, relative_to=tmp_path)
    assert not data['errors'] and data['file']['path'] == 'latin.py'
    assert len(data['file']['sha256']) == 64


def test_nested_classes_keep_full_scope():
    data = parse_python_source('class A:\n class B:\n  def run(self): return 1\n', 'm.py')
    assert data['functions'][0]['qualified_name'] == 'm.py:A.B.run'


def test_decorator_calls_use_enclosing_scope():
    data = parse_python_source('def outer():\n @decorate()\n def inner():\n  body()\n', 'm.py')
    assert [(c['caller'], c['expression']) for c in data['calls']] == [('m.py:outer', 'decorate'), ('m.py:outer.inner', 'body')]
