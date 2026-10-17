"""Safe tracked-file metadata independently of Python semantic extraction."""
from pathlib import PurePosixPath
from app.ingestion.ingest_repo import EXCLUDED

LANGUAGES={'.py':'Python','.js':'JavaScript','.jsx':'JavaScript','.ts':'TypeScript','.tsx':'TypeScript',
           '.json':'JSON','.yaml':'YAML','.yml':'YAML','.toml':'TOML','.md':'Markdown','.rs':'Rust','.go':'Go',
           '.java':'Java','.sh':'Shell','.css':'CSS','.html':'HTML'}

def records(entries, revision, origin, parsed):
    if len(entries)>50000:
        raise ValueError('Tracked inventory exceeds 50000 paths; snapshot refused, not silently truncated')
    result=[]
    for entry in entries:
        path=entry['path'];parts=PurePosixPath(path).parts
        if not path or path.startswith('/') or '\\' in path or any(p in ('','.', '..') for p in path.split('/')) or any(ord(c)<32 for c in path):
            raise ValueError('Unsupported tracked inventory path')
        item=parsed.get(path)
        status=('EXCLUDED' if any(p in EXCLUDED for p in parts) else
                'UNSUPPORTED_ENTRY' if entry.get('mode','100644') not in ('100644','100755') else
                'PARSE_FAILED' if item and item['errors'] else 'ANALYZED' if item else 'UNSUPPORTED_LANGUAGE')
        result.append({'path':path,'language':LANGUAGES.get(PurePosixPath(path).suffix.lower(),'Other'),
                       'analysis_status':status,'size_bytes':entry.get('size',0),'git_blob_sha':entry.get('sha',''),
                       'source_revision':revision,'source_url':origin+'/blob/'+revision+'/'+path if origin else ''})
    return result
