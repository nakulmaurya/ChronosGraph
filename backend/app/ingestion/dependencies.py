"""Shared conservative static dependency analysis; never executes repository code.

A binding is evidence of a possible target, not runtime dispatch. Rebindings,
parameters, global/nonlocal declarations and ambiguous source roots fail closed.
"""
from app.ingestion.ast_parser import resolve_import


def resolve_call(call, item, known, definitions):
    path, scope = call['caller'].split(':', 1)
    expression = call['expression']
    if call.get('dynamic_scope'):
        return None
    head, *attributes = expression.split('.')
    if not head.isidentifier() or any(not p.isidentifier() for p in attributes):
        return None
    frames = item.get('scope_bindings', {})
    parts = scope.split('.')
    for depth in range(len(parts), -1, -1):
        frame_name = '.'.join(parts[:depth])
        frame = frames.get(frame_name)
        if frame is None or frame['kind'] == 'class':
            continue  # Python methods do not close over class namespaces.
        kinds = frame['bindings'].get(head, [])
        if frame.get('wildcard'):
            return None
        if not kinds:
            continue
        if kinds == ['parameter'] and frame.get('receiver') == head and len(attributes) == 1:
            owner = frames.get(frame['owner_class'], {})
            if owner.get('bindings', {}).get(attributes[0]) != ['function']:
                return None
            target = f"{path}:{frame['owner_class']}.{attributes[0]}"
            return target if target in definitions else None
        if kinds == ['function'] and not attributes:
            name = '.'.join(filter(None, [frame_name, head]))
            target = f'{path}:{name}'
            return target if target in definitions else None
        if kinds != ['import']:
            return None
        matches = set()
        for imp in item['imports']:
            if imp['scope'] != frame_name or imp['alias'] != head or imp.get('name') == '*':
                continue
            for target in resolve_import(imp, path, known):
                symbol = '.'.join(([imp['name']] if imp.get('name') else []) + attributes)
                candidate = f'{target}:{symbol}'
                if candidate in definitions:
                    matches.add(candidate)
        return next(iter(matches)) if len(matches) == 1 else None
    return None


def analyze_dependencies(item, known, definitions):
    """One resolution contract for initial ingestion and full-file simulation."""
    path = item['file']['path']
    roots = {''}
    for p in known:
        if p.startswith('src/'):
            roots.add('src/')
        if '/src/' in p:
            roots.add(p.split('/src/', 1)[0] + '/src/')
    imports = set()
    call_targets = [set() for _ in item['calls']]
    for root in sorted(roots):
        aliases = {p[len(root):]: p for p in known if p.startswith(root)}
        names = set(aliases)
        alias_definitions = {d[len(root):] for d in definitions if d.startswith(root)}
        lookup_path = path[len(root):] if path.startswith(root) else path
        for record in item['imports']:
            imports.update(aliases[p] for p in resolve_import(record, lookup_path, names))
        for index, call in enumerate(item['calls']):
            lookup = {**call, 'caller': call['caller'][len(root):] if call['caller'].startswith(root) else call['caller']}
            candidate = resolve_call(lookup, item, names, alias_definitions)
            if candidate:
                actual_file, symbol = candidate.split(':', 1)
                if actual_file in aliases:
                    call_targets[index].add(aliases[actual_file] + ':' + symbol)
    resolved = [(call, next(iter(targets))) for call, targets in zip(item['calls'], call_targets) if len(targets) == 1]
    unresolved = [call['expression'] for call, targets in zip(item['calls'], call_targets) if len(targets) != 1]
    return imports, resolved, unresolved
