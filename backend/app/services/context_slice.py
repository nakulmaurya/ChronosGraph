"""Measured payload comparison, not tokenizer output or billed model savings."""
import json
from app.services.common import read


def measure_context(tenant, target, candidate_paths):
    paths = sorted(set(candidate_paths) | {target})
    sizes, _ = read(tenant, '''MATCH (f:File) WHERE f.path IN $paths
        RETURN f.path AS path,f.source_chars AS chars,f.source_utf8_bytes AS bytes
        ORDER BY path''', {'paths':paths})
    signatures, _ = read(tenant, '''MATCH (:File {path:$path})-[:DEFINES]->(f:Function)
        RETURN f.qualified_name AS symbol,f.signature AS signature,f.is_async AS is_async
        ORDER BY symbol LIMIT 101''', {'path':target})
    policies, _ = read(tenant, '''MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(:File {path:$path})
        RETURN d.id AS id,d.rule AS rule,d.source_type AS source_type ORDER BY id LIMIT 21''', {'path':target})
    constraints, _ = read(tenant, '''MATCH (d:Decision {source_type:'REPO_EXTRACTED_RULE'})
        WHERE d.scope='repository' OR d.target_path=$path
        RETURN d.rule AS rule,d.source_path AS source_path,d.source_line AS source_line,
        d.source_revision AS source_revision ORDER BY source_path,source_line LIMIT 21''', {'path':target})
    owners, _ = read(tenant, '''MATCH (c:Contributor)-[:AUTHORED]->(p:PullRequest)-[:MODIFIES]->(:File {path:$path})
        RETURN c.login AS identity,c.name AS name,count(DISTINCT p) AS indexed_commits
        ORDER BY indexed_commits DESC,identity LIMIT 1''', {'path':target})
    payload = {'target':target,'functions':signatures[:100],'active_policies':policies[:20],
        'repository_constraints':constraints[:20], 'top_commit_author':owners,
        'limits':{'function_limit':100,'policy_limit':20,'constraint_limit':20,
            'truncated':len(signatures)>100 or len(policies)>20 or len(constraints)>20},
        'provenance':'STATIC_AST_AND_RULE_SLICE; commit authors are not verified maintainers'}
    preview = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    available = len(sizes)==len(paths) and all(isinstance(r['chars'],int) and isinstance(r['bytes'],int)
        and r['chars']>=0 and r['bytes']>=0 for r in sizes)
    chars = sum(r['chars'] for r in sizes) if available else 0
    byte_count = sum(r['bytes'] for r in sizes) if available else 0
    raw_tokens, compiled_tokens = chars//4, len(preview)//4
    return {'raw_files_context_tokens':raw_tokens,'compiled_slice_context_tokens':compiled_tokens,
        'raw_files_context_chars':chars,'raw_files_context_bytes':byte_count,
        'compiled_slice_context_chars':len(preview),'compiled_slice_context_bytes':len(preview.encode('utf-8')),
        'context_token_reduction_pct':round(100*(raw_tokens-compiled_tokens)/raw_tokens,2) if raw_tokens else 0.0,
        'context_measurement_status':'MEASURED_SOURCE_CHARS_DIV_4' if available else 'SOURCE_SIZES_UNAVAILABLE',
        'context_candidate_files':paths,'compiled_context_slice_preview':preview}
