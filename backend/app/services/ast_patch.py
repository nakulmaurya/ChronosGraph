"""Bounded additive AST overlays. Never imports or executes submitted Python."""
import json
from fastapi import HTTPException
from app.ingestion.ast_parser import parse_python_source, resolve_import
from app.ingestion.seed_repos import resolve_call

SOURCE = 'AST_PATCH_SIMULATION'


def parse_patch(code, path, original=None):
    if len(code) > 32000:
        raise HTTPException(422, 'Python patch is limited to 32000 characters')
    from app.services.unified_patch import patch_source
    code, semantics = patch_source(code, path, original)
    if len(code) > 1000000:
        raise HTTPException(422, 'Reconstructed Python source exceeds 1000000 characters')
    item = parse_python_source(code, path)
    item['patch_semantics'] = semantics
    if item['errors']:
        raise HTTPException(422, {'message': 'Invalid Python patch', 'errors': item['errors']})
    if sum(len(item[k]) for k in ('functions', 'classes', 'imports', 'calls')) > 500:
        raise HTTPException(422, 'Python patch is limited to 500 AST observations')
    return item


def apply_patch(graph, item, simulation):
    """Preserve existing snapshot edges; add only syntax-backed, resolved edges.

    Source roots are aliases for lookup only. Multiple actual matches are never
    guessed. Unresolved expressions are returned as evidence on the target file.
    """
    path = item['file']['path']
    known = {r[0] for r in graph.ro_query('MATCH (f:File) RETURN f.path').result_set}
    definitions = {r[0] for r in graph.ro_query('MATCH (f:Function) RETURN f.qualified_name').result_set}
    definitions.update(f['qualified_name'] for f in item['functions'])
    roots = {''}
    for p in known:
        if p.startswith('src/'):
            roots.add('src/')
        if '/src/' in p:
            roots.add(p.split('/src/', 1)[0] + '/src/')
    imports = set()
    call_targets = [set() for _ in item['calls']]
    for root in roots:
        aliases = {p[len(root):]: p for p in known if p.startswith(root)}
        names = set(aliases)
        alias_definitions = {d[len(root):] for d in definitions if d.startswith(root)}
        for record in item['imports']:
            # Relative imports resolve against the actual file path, even when
            # absolute imports use a package's src-root alias.
            lookup_path = path[len(root):] if path.startswith(root) else path
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
    for label, key in [('Class', 'classes'), ('Function', 'functions')]:
        for definition in item[key]:
            graph.query(f'''MATCH (f:File {{path:$path}})
              MERGE (n:{label} {{qualified_name:$name}})
              SET n.name=$symbol,n.file_path=$path,n.source_type=$source,n.simulation_id=$simulation
              MERGE (f)-[r:DEFINES]->(n) SET r.source_type=$source,r.simulation_id=$simulation''',
              {'path': path, 'name': definition['qualified_name'], 'symbol': definition['name'],
               'source': SOURCE, 'simulation': simulation})
    for target in sorted(imports):
        graph.query('''MATCH (a:File {path:$path}),(b:File {path:$target})
          MERGE (a)-[r:IMPORTS]->(b) SET r.source_type=$source,r.simulation_id=$simulation''',
          {'path': path, 'target': target, 'source': SOURCE, 'simulation': simulation})
    for call, target in resolved:
        graph.query('''MATCH (a:Function {qualified_name:$caller}),(b:Function {qualified_name:$target})
          MERGE (a)-[r:CALLS {line:$line}]->(b)
          SET r.source_type=$source,r.simulation_id=$simulation,r.resolution='conservative_static' ''',
          {'caller': call['caller'], 'target': target, 'line': call['line'], 'source': SOURCE, 'simulation': simulation})
    graph.query('''MATCH (f:File {path:$path}) SET f.patch_source_type=$source,
      f.patch_semantics=$semantics,f.patch_sha256=$sha,
      f.patch_imports=$imports,f.patch_resolved_calls=$calls,f.patch_unresolved_calls=$unresolved,
      f.patch_call_targets=$targets,f.patch_unresolved_expressions=$expressions''',
      {'path': path, 'source': SOURCE, 'semantics': item['patch_semantics'], 'sha': item['file']['sha256'], 'imports': sorted(imports),
       'calls': len(resolved), 'unresolved': len(unresolved), 'targets': [t for _, t in resolved],
       'expressions': json.dumps(unresolved)})
    return set(imports) | {target.split(':', 1)[0] for _, target in resolved}
