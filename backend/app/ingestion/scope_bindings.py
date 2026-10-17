"""Lexical binding evidence for conservative Python call resolution."""
import ast


def collect_bindings(tree):
    frames = {'': {'kind': 'module', 'bindings': {}}}

    class Collector(ast.NodeVisitor):
        scope = ''

        def bind(self, name, kind):
            frames[self.scope]['bindings'].setdefault(name, []).append(kind)

        def visit_Name(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                self.bind(node.id, 'unknown')

        def visit_Attribute(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Del)) and isinstance(node.value, ast.Name):
                self.bind(node.value.id, 'unknown')
            self.generic_visit(node)

        def visit_Global(self, node):
            for name in node.names:
                self.bind(name, 'unknown')

        visit_Nonlocal = visit_Global

        def visit_Import(self, node):
            for alias in node.names:
                self.bind(alias.asname or alias.name.split('.')[0], 'import')

        def visit_ImportFrom(self, node):
            for alias in node.names:
                if alias.name == '*':
                    frames[self.scope]['wildcard'] = True
                else:
                    self.bind(alias.asname or alias.name, 'import')

        def visit_ExceptHandler(self, node):
            if node.name:
                self.bind(node.name, 'unknown')
            self.generic_visit(node)

        def visit_MatchAs(self, node):
            if node.name:
                self.bind(node.name, 'unknown')
            self.generic_visit(node)

        visit_MatchStar = visit_MatchAs

        def visit_MatchMapping(self, node):
            if node.rest:
                self.bind(node.rest, 'unknown')
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            # Decorators may replace the function object; do not guess through them.
            self.bind(node.name, 'unknown' if node.decorator_list else 'function')
            for expression in [*node.decorator_list, *node.args.defaults,
                               *(v for v in node.args.kw_defaults if v is not None)]:
                self.visit(expression)
            parent = self.scope
            self.scope = '.'.join(filter(None, [parent, node.name]))
            frame = frames.setdefault(self.scope, {'kind': 'function', 'bindings': {}})
            args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            for arg in [*args, *([node.args.vararg] if node.args.vararg else []),
                        *([node.args.kwarg] if node.args.kwarg else [])]:
                self.bind(arg.arg, 'parameter')
            if frames[parent]['kind'] == 'class':
                positional = [*node.args.posonlyargs, *node.args.args]
                decorators = [ast.unparse(d) for d in node.decorator_list]
                receiver = positional[0].arg if positional else None
                if (not decorators and receiver == 'self') or (decorators == ['classmethod'] and receiver == 'cls'):
                    frame.update(receiver=receiver, owner_class=parent)
            for statement in node.body:
                self.visit(statement)
            self.scope = parent

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node):
            self.bind(node.name, 'unknown')
            for expression in [*node.decorator_list, *node.bases]:
                self.visit(expression)
            parent = self.scope
            self.scope = '.'.join(filter(None, [parent, node.name]))
            frames.setdefault(self.scope, {'kind': 'class', 'bindings': {}})
            for statement in node.body:
                self.visit(statement)
            self.scope = parent

        def visit_Lambda(self, node):
            # Lambda/comprehension calls are explicitly unresolved by the extractor.
            for expression in [*node.args.defaults, *(v for v in node.args.kw_defaults if v is not None)]:
                self.visit(expression)

        def visit_ListComp(self, node):
            # Avoid leaking comprehension-local targets into the enclosing scope.
            # Named expressions bind outside comprehensions; conservatively block them.
            for child in ast.walk(node):
                if isinstance(child, ast.NamedExpr):
                    self.visit(child.target)

        visit_SetComp = visit_ListComp
        visit_DictComp = visit_ListComp
        visit_GeneratorExp = visit_ListComp

    Collector().visit(tree)
    return frames
