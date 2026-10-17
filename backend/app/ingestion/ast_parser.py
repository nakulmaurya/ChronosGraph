"""Conservative Python source extraction with lexical scope and import provenance.

Calls are syntax observations, not proof of runtime dispatch. Dynamic/ambiguous
calls remain unresolved instead of being guessed from a matching method name.
"""
from __future__ import annotations

import ast
import hashlib
import tokenize
from pathlib import Path
from typing import Any


def parse_python_source(source_code: str, file_path: str) -> dict[str, Any]:
    """Parse source without executing it. Return structured errors for invalid Python."""
    path = Path(file_path).as_posix()
    result: dict[str, Any] = {
        "file": {"path": path, "name": Path(path).name,
                 "loc": len(source_code.splitlines()),
                 "source_text": source_code, "source_chars": len(source_code),
                 "source_utf8_bytes": len(source_code.encode('utf-8')),
                 "sha256": hashlib.sha256(source_code.encode()).hexdigest()},
        "classes": [], "functions": [], "imports": [], "calls": [], "errors": [],
    }
    try:
        tree = ast.parse(source_code, filename=path)
    except (SyntaxError, ValueError, RecursionError) as exc:
        result["errors"].append({"message": str(exc), "line": getattr(exc, "lineno", None)})
        return result

    from app.ingestion.scope_bindings import collect_bindings
    result["scope_bindings"] = collect_bindings(tree)

    class Extractor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.scopes: list[tuple[str, str]] = []
            self.dynamic_scope = 0

        def qualify(self, name: str) -> str:
            return f"{path}:{'.'.join([s[0] for s in self.scopes] + [name])}"

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            result["classes"].append({
                "name": node.name, "qualified_name": self.qualify(node.name),
                "file_path": path, "start_line": node.lineno, "end_line": node.end_lineno,
                "bases": [ast.unparse(b) for b in node.bases],
                "docstring": (ast.get_docstring(node) or "")[:2000],
            })
            # Class bases and decorators execute in the enclosing scope.
            for expr in [*node.decorator_list, *node.bases]:
                self.visit(expr)
            self.scopes.append((node.name, "class"))
            for statement in node.body:
                self.visit(statement)
            self.scopes.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            scope_name = ".".join(s[0] for s in self.scopes)
            result["functions"].append({
                "name": node.name, "qualified_name": self.qualify(node.name),
                "file_path": path, "signature": f"{node.name}({ast.unparse(node.args)})"
                + (f" -> {ast.unparse(node.returns)}" if node.returns else ""),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "start_line": node.lineno, "end_line": node.end_lineno,
                "parent_scope": scope_name,
                "docstring": (ast.get_docstring(node) or "")[:2000],
                "owner_class": next((n for n, t in reversed(self.scopes) if t == "class"), None),
            })
            for expr in [*node.decorator_list, *node.args.defaults,
                         *(v for v in node.args.kw_defaults if v is not None)]:
                self.visit(expr)
            self.scopes.append((node.name, "function"))
            for statement in node.body:
                self.visit(statement)
            self.scopes.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                result["imports"].append({"module": alias.name, "level": 0,
                    "name": None, "alias": alias.asname or alias.name.split('.')[0],
                    "bound_target": alias.name if alias.asname else alias.name.split('.')[0],
                    "line": node.lineno, "scope": ".".join(s[0] for s in self.scopes)})

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            for alias in node.names:
                result["imports"].append({"module": node.module or "", "level": node.level,
                    "name": alias.name, "alias": alias.asname or alias.name,
                    "line": node.lineno, "scope": ".".join(s[0] for s in self.scopes)})

        def visit_dynamic_scope(self, node) -> None:
            self.dynamic_scope += 1
            self.generic_visit(node)
            self.dynamic_scope -= 1

        visit_Lambda = visit_dynamic_scope
        visit_ListComp = visit_dynamic_scope
        visit_SetComp = visit_dynamic_scope
        visit_DictComp = visit_dynamic_scope
        visit_GeneratorExp = visit_dynamic_scope

        def visit_Call(self, node: ast.Call) -> None:
            caller = next((i for i in range(len(self.scopes)-1, -1, -1)
                           if self.scopes[i][1] == "function"), None)
            if caller is not None:
                expression = ast.unparse(node.func)
                result["calls"].append({
                    "caller": f"{path}:{'.'.join(s[0] for s in self.scopes[:caller+1])}",
                    "callee_name": expression.split('.')[-1], "expression": expression,
                    "line": node.lineno,
                    "resolution": "unresolved_static_expression",
                    "dynamic_scope": bool(self.dynamic_scope),
                })
            self.generic_visit(node)

    Extractor().visit(tree)
    return result


def parse_python_file(file_path: str | Path, *, relative_to: str | Path | None = None) -> dict[str, Any]:
    """Respect Python encoding declarations; never import downloaded source."""
    path = Path(file_path)
    with tokenize.open(path) as stream:
        stream.reconfigure(newline='')
        source = stream.read()
    label = path.relative_to(relative_to).as_posix() if relative_to else path.as_posix()
    return parse_python_source(source, label)


def module_name(file_path: str) -> str:
    parts = Path(file_path).with_suffix('').parts
    if parts and parts[-1] == '__init__':
        parts = parts[:-1]
    return '.'.join(parts)


def resolve_import(record: dict[str, Any], file_path: str, known_files: set[str]) -> list[str]:
    """Resolve package-relative imports only to files that actually exist."""
    module = record['module']
    level = record['level']
    if level:
        package = list(Path(file_path).parent.parts)
        if level > len(package):
            return []
        package = package[:len(package)-level+1]
        module = '.'.join([*package, *([module] if module else [])])
    candidates = [module]
    if record['name'] and record['name'] != '*':
        candidates.append('.'.join(filter(None, [module, record['name']])))
    resolved = set()
    for candidate in candidates:
        stem = candidate.replace('.', '/')
        for path in [stem + '.py', stem + '/__init__.py']:
            if path in known_files and path != file_path:
                resolved.add(path)
    return sorted(resolved)
