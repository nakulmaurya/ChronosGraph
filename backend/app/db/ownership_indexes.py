"""Targeted native range indexes for pinned CODEOWNERS ingestion.

Only called by the writer before ownership MERGEs, never by read-only discovery.
Do not swallow DDL failures or silently claim that an index is available.
"""
import time

OWNERSHIP_INDEXES = (
    ('OwnershipSource', 'id'),
    ('OwnershipRule', 'id'),
    ('DeclaredOwner', 'name'),
)


def ownership_index_state(graph):
    result = graph.ro_query('CALL db.indexes()')
    names = [column[1] for column in result.header]
    state = {}
    for values in result.result_set:
        row = dict(zip(names, values))
        if row['entitytype'] != 'NODE':
            continue
        for prop, kinds in row['types'].items():
            if 'RANGE' in kinds:
                state[(row['label'], prop)] = row['status']
    return state


def ensure_ownership_indexes(graph, timeout_seconds=10):
    """Idempotently create fixed-schema indexes and await native readiness.

    Caller owns the source/tenant writer lock. The bound covers polling, not a
    hard server-side DDL deadline. An error propagates to ingestion's cleanup.
    """
    state = ownership_index_state(graph)
    for label, prop in OWNERSHIP_INDEXES:
        if (label, prop) not in state:
            graph.query(f'CREATE INDEX FOR (n:{label}) ON (n.{prop})')
    deadline = time.monotonic() + timeout_seconds
    while True:
        state = ownership_index_state(graph)
        if all(state.get(key) == 'OPERATIONAL' for key in OWNERSHIP_INDEXES):
            return
        if time.monotonic() >= deadline:
            raise RuntimeError('CODEOWNERS range indexes did not become operational')
        time.sleep(0.01)
