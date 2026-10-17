"""Pure parser regressions: no database, downloaded code execution or network."""
import pytest
from app.ingestion.ast_parser import parse_python_source
from app.ingestion.dependencies import analyze_dependencies, resolve_call
from app.services.ast_patch import analyze_dependencies as patch_dependencies


def analyze(sources, entry='a.py'):
    items = {path: parse_python_source(code, path) for path, code in sources.items()}
    assert all(not i['errors'] for i in items.values())
    definitions = {f['qualified_name'] for i in items.values() for f in i['functions']}
    return analyze_dependencies(items[entry], set(items), definitions)


@pytest.mark.parametrize('body', [
    'def run(helper): return helper()',
    'def run(*helper): return helper()',
    'def run(**helper): return helper()',
    'def run(*, helper): return helper()',
    'def run():\n helper = lambda: 2\n return helper()',
    'def run():\n helper()\n helper = lambda: 2',
    'def run():\n for helper in []: helper()',
    'def run():\n with manager() as helper: helper()',
    'def run():\n try: pass\n except Exception as helper: helper()',
    'def run():\n global helper\n return helper()',
    'def outer():\n helper = lambda: 2\n def run():\n  nonlocal helper\n  return helper()',
    'def outer(helper):\n def run(): return helper()',
    'def run(value):\n match value:\n  case {"x": helper}: helper()',
    'def run():\n return [helper() for helper in []]',
    'def run():\n return (lambda helper: helper())(None)',
    'helper = lambda: 2\ndef run(): return helper()',
])
def test_shadowed_and_dynamic_calls_do_not_become_module_edges(body):
    _, resolved, _ = analyze({'a.py': 'def helper(): return 1\n' + body + '\n'})
    assert not [target for _, target in resolved if target == 'a.py:helper']


def test_unshadowed_module_function_resolves():
    _, resolved, unknown = analyze({'a.py': 'def helper(): return 1\ndef run(): return helper()\n'})
    assert [target for _, target in resolved] == ['a.py:helper']
    assert unknown == []


def test_nearest_lexical_function_wins_not_module_candidate():
    _, resolved, _ = analyze({'a.py': 'def helper(): return 1\ndef outer():\n def helper(): return 2\n return helper()\n'})
    assert [target for _, target in resolved] == ['a.py:outer.helper']


def test_method_does_not_close_over_class_namespace():
    _, resolved, _ = analyze({'a.py': 'def helper(): return 1\nclass A:\n def helper(self): return 2\n def run(self): return helper()\n'})
    assert [target for _, target in resolved] == ['a.py:helper']


@pytest.mark.parametrize('declaration', ['', '    self = other\n'])
def test_receiver_assignment_blocks_method_guess(declaration):
    source = 'class A:\n def helper(self): return 1\n def run(self):\n' + declaration + '    return self.helper()\n'
    _, resolved, _ = analyze({'a.py': source})
    assert [target for _, target in resolved] == ([] if declaration else ['a.py:A.helper'])


def test_staticmethod_parameter_named_self_is_not_method_receiver():
    _, resolved, _ = analyze({'a.py': 'class A:\n def helper(self): return 1\n @staticmethod\n def run(self): return self.helper()\n'})
    assert resolved == []


def test_local_import_does_not_leak_to_sibling_function():
    _, resolved, _ = analyze({'a.py': 'def setup():\n from b import helper\ndef run(): return helper()\n', 'b.py': 'def helper(): return 1\n'})
    assert resolved == []


@pytest.mark.parametrize('binding', ['helper = other', 'from c import helper'])
def test_rebound_import_stays_unknown(binding):
    _, resolved, _ = analyze({'a.py': f'from b import helper\n{binding}\ndef run(): return helper()\n', 'b.py': 'def helper(): return 1\n', 'c.py': 'def helper(): return 2\n'})
    assert resolved == []


@pytest.mark.parametrize('root', ['', 'src/', 'packages/lib/src/'])
def test_src_root_resolves_consistently_for_ingestion_and_patch(root):
    path = root + 'pkg/a.py'
    sources = {path: 'from pkg.b import helper as alias\ndef run(): return alias()\n', root + 'pkg/b.py': 'def helper(): return 1\n'}
    items = {p: parse_python_source(s, p) for p, s in sources.items()}
    definitions = {f['qualified_name'] for i in items.values() for f in i['functions']}
    initial = analyze_dependencies(items[path], set(items), definitions)
    replacement = patch_dependencies(items[path], set(items), definitions)
    assert patch_dependencies is analyze_dependencies
    assert initial == replacement
    assert initial[0] == {root + 'pkg/b.py'}
    assert [target for _, target in initial[1]] == [root + 'pkg/b.py:helper']


def test_relative_import_with_src_root():
    imports, resolved, unknown = analyze({'src/pkg/a.py': 'from .b import helper\ndef run(): return helper()\n', 'src/pkg/b.py': 'def helper(): return 1\n'}, 'src/pkg/a.py')
    assert imports == {'src/pkg/b.py'}
    assert [target for _, target in resolved] == ['src/pkg/b.py:helper']
    assert unknown == []


def test_conflicting_source_roots_remain_unknown():
    _, resolved, unknown = analyze({'a.py': 'from pkg.b import helper\ndef run(): return helper()\n', 'pkg/b.py': 'def helper(): return 1\n', 'src/pkg/b.py': 'def helper(): return 2\n'})
    assert resolved == [] and unknown == ['helper']


def test_binding_metadata_absent_fails_closed():
    assert resolve_call({'caller':'a.py:run', 'expression':'helper'}, {'imports':[]}, {'a.py'}, {'a.py:helper'}) is None


def test_decorated_callable_is_not_guessed_through_wrapper():
    _, resolved, _ = analyze({'a.py': '@decorate\ndef helper(): return 1\ndef run(): return helper()\n'})
    assert resolved == []


def test_reassigned_class_method_is_not_guessed():
    _, resolved, _ = analyze({'a.py': 'class A:\n def helper(self): return 1\n helper = other\n def run(self): return self.helper()\n'})
    assert resolved == []


def test_instance_attribute_reassignment_blocks_receiver_guess():
    _, resolved, _ = analyze({'a.py': 'class A:\n def helper(self): return 1\n def run(self):\n  self.helper = other\n  return self.helper()\n'})
    assert resolved == []
