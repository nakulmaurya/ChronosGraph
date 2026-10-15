"""Conservative, source-linked constraints. Extraction is evidence, not policy promotion.

Repository-wide constraints are kept separate from local override/demo governance:
no invented supersession, validity dates or blanket GOVERNS edges.
"""
import ast
import hashlib
import re
import tomllib
from pathlib import Path

LIMIT = 512000


def extract_rules(root, paths):
    root = Path(root)
    records = []

    def add(path, line, rule, scope='repository', target=''):
        records.append({'source_path':path,'source_line':line,'rule':rule,
            'scope':scope,'target_path':target})

    for name in ('pyproject.toml','README.md','AGENTS.md','CLAUDE.md'):
        path = root/name
        if not path.is_file() or path.is_symlink() or path.stat().st_size>LIMIT:
            continue
        text = path.read_text(encoding='utf-8',errors='replace')
        if name == 'pyproject.toml':
            try:
                config = tomllib.loads(text)
            except tomllib.TOMLDecodeError:
                continue
            values = [(['project','requires-python'],'Required Python version'),
                (['tool','ruff','line-length'],'Ruff configured line length'),
                (['tool','ruff','target-version'],'Ruff target Python version'),
                (['tool','mypy','strict'],'Mypy configured strict mode')]
            for keys, label in values:
                value = config
                for key in keys:
                    value = value.get(key) if isinstance(value,dict) else None
                if value is not None and isinstance(value,(str,int,bool)):
                    section = ''
                    line = None
                    for number, source_line in enumerate(text.splitlines(),1):
                        table = re.fullmatch(r'\s*\[([^\[\]]+)\]\s*(?:#.*)?',source_line)
                        if table:
                            section = table[1].strip()
                        if section == '.'.join(keys[:-1]) and re.match(
                                r'\s*'+re.escape(keys[-1])+r'\s*=',source_line):
                            line = number
                            break
                    # Inline/dotted/quoted table syntax is not assigned an invented location.
                    if line is not None:
                        add(name,line,f'{label}: {value}')
        else:
            fenced = False
            for line, sentence in enumerate(text.splitlines(),1):
                if sentence.lstrip().startswith(('```','~~~')):
                    fenced = not fenced
                    continue
                # Only explicit normative engineering sentences, not inferred prose.
                if not fenced and len(sentence)<=400 and re.search(r'\b(must|never|required|do not)\b',sentence,re.I) and re.search(
                    r'\b(python|async|sync|typing|mypy|ruff|lint|read.only|query|queries|test|tests)\b',sentence,re.I):
                    add(name,line,sentence.strip())
    for name in sorted(paths):
        path = root/name
        if not path.is_file() or path.is_symlink() or path.stat().st_size>LIMIT:
            continue
        try:
            import tokenize
            with tokenize.open(path) as stream:
                tree = ast.parse(stream.read())
            doc = ast.get_docstring(tree,clean=False)
            if not doc:
                continue
            start = tree.body[0].lineno
            for offset,sentence in enumerate(doc.splitlines()):
                if len(sentence)<=400 and re.search(r'\b(must|never|required|do not)\b',sentence,re.I) and re.search(
                    r'\b(async|sync|typing|read.only|query|queries|test|tests)\b',sentence,re.I):
                    add(name,start+offset,sentence.strip(),'module',name)
        except (SyntaxError,UnicodeError,ValueError):
            continue
    return records[:200]


def enrich_repository(graph, root, revision, origin, paths):
    records = extract_rules(root,paths)
    for record in records:
        ident = 'repo_rule_'+hashlib.sha256((revision+'\0'+str(record)).encode()).hexdigest()[:24]
        url = origin+'/blob/'+revision+'/'+record['source_path']+'#L'+str(record['source_line']) if origin else ''
        graph.query('''MERGE (d:Decision {id:$id}) SET d.rule=$rule,d.scope=$scope,
            d.target_path=$target_path,d.source_path=$source_path,d.source_line=$source_line,
            d.source_revision=$revision,d.source_url=$url,d.source_type='REPO_EXTRACTED_RULE',
            d.status='EXTRACTED',d.validity_basis='SOURCE_REVISION_NOT_OVERRIDE_CLOCK'
            ''', {**record,'id':ident,'revision':revision,'url':url})
    return len(records)
