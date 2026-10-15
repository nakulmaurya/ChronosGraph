"""Strict single-file unified patch reconstruction; no filesystem writes or execution."""
import re
from fastapi import HTTPException


def patch_source(text, path, original=None):
    if not text.startswith(('diff --git ', '--- ', '@@ ')):
        return text, 'ADDITIVE_SNIPPET_OVERLAY'
    if original is None:
        raise HTTPException(422, 'Unified diff requires captured source at the ingested revision; enrich or re-ingest first')
    lines = text.splitlines(keepends=True)
    index = 0
    old_path = new_path = None
    if lines[0].startswith('diff --git '):
        index += 1
        if index < len(lines) and lines[index].startswith('index '):
            index += 1
    if index < len(lines) and lines[index].startswith('--- '):
        old_path = lines[index][4:].strip().split('\t')[0]
        index += 1
        if index >= len(lines) or not lines[index].startswith('+++ '):
            raise HTTPException(422, 'Unified diff requires matching --- and +++ headers')
        new_path = lines[index][4:].strip().split('\t')[0]
        index += 1
        if old_path.removeprefix('a/') != path or new_path.removeprefix('b/') != path:
            raise HTTPException(422, 'Diff must modify the first selected existing file; renames/additions/deletions are unsupported')
    source = original.splitlines(keepends=True)
    output = []
    cursor = 0
    hunks = 0
    while index < len(lines):
        header = re.fullmatch(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\r\n]*(?:\r?\n)?', lines[index])
        if not header:
            raise HTTPException(422, 'Unsupported or multi-file diff; supply one complete file patch')
        old_start, old_count, new_start, new_count = [int(x) if x is not None else 1 for x in header.groups()]
        start = old_start - 1 if old_count else old_start
        if start < cursor or start > len(source):
            raise HTTPException(422, 'Overlapping or out-of-range patch hunk')
        output.extend(source[cursor:start]); cursor = start
        expected_new = new_start - 1 if new_count else new_start
        if len(output) != expected_new:
            raise HTTPException(422, 'Patch new-file offsets do not match')
        index += 1
        removed = added = 0
        while index < len(lines) and not lines[index].startswith('@@ '):
            line = lines[index]
            if not line or line[0] not in ' +-':
                raise HTTPException(422, 'Invalid unified diff body')
            prefix, value = line[0], line[1:]
            index += 1
            if index < len(lines) and lines[index].startswith('\\ No newline at end of file'):
                value = value.removesuffix('\n').removesuffix('\r')
                index += 1
            if prefix in ' -':
                if cursor >= len(source) or source[cursor] != value:
                    raise HTTPException(422, 'Patch context does not match captured source revision')
                cursor += 1; removed += 1
            if prefix in ' +':
                output.append(value); added += 1
        if removed != old_count or added != new_count:
            raise HTTPException(422, 'Patch hunk line counts do not match')
        hunks += 1
    if not hunks:
        raise HTTPException(422, 'Unified diff has no hunks')
    output.extend(source[cursor:])
    return ''.join(output), 'VALIDATED_UNIFIED_DIFF_ADDITIVE_OVERLAY'
