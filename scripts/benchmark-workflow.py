#!/usr/bin/env python3
"""Run only on an explicitly disposable native DB; no network/model/test execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services.workflow_benchmark import DATASETS, evaluate_repository, markdown_table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=20)
    parser.add_argument('--output', type=Path, default=Path('tasks/reports/benchmark-results.json'))
    parser.add_argument('--strict-targets', action='store_true', help='Fail if any 50ms/70%% or indexed-import recall target is missed; still writes measurements')
    args = parser.parse_args()
    if os.environ.get('CHRONOSGRAPH_DISPOSABLE_BENCHMARK') != '1':
        parser.error('Set CHRONOSGRAPH_DISPOSABLE_BENCHMARK=1 only for an isolated DB copy')
    if not 2 <= args.samples <= 100:
        parser.error('--samples requires 2..100')
    from app.db.client import db_manager
    missing = set(DATASETS) - set(db_manager.list_tenant_graphs())
    if missing: parser.error('Required datasets missing: '+', '.join(sorted(missing)))
    report = {'schema_version': 1, 'started_at_unix': int(time.time()),
        'source_commit': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        'python': platform.python_version(), 'platform': platform.platform(),
        'logical_cpus': os.cpu_count(), 'redis_version': db_manager.db.connection.info('server').get('redis_version'),
        'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'evaluator_sha256': hashlib.sha256((Path(__file__).resolve().parents[1]/'backend/app/services/workflow_benchmark.py').read_bytes()).hexdigest(),
        'working_tree_dirty': bool(subprocess.check_output(['git','status','--porcelain'], text=True).strip()),
        'methodology': {'latency': 'Sequential single-client perf_counter wall time; one warmup per operation, nearest-rank p95; not SLA',
            'token_basis': 'Exact bytes; Unicode chars//4 estimates, no exact model tokenizer or billing claims',
            'test_precision': 'Not measured against executed real-repo failures; candidate-file reduction only',
            'isolation': 'Disposable native database plus uniquely owned graph copies; verified delete',
            'task_selection': 'One deterministic highest-indexed-inbound function with current reparsed callers, excluding test directories; not representative of every task'},
        'repositories': [evaluate_repository(t, args.samples) for t in DATASETS], 'model_calls': 0}
    report['finished_at_unix'] = int(time.time())
    report['targets_met'] = all(r['targets']['all_discovery_services_p95_lt_50ms'] and r['targets']['byte_reduction_at_least_70pct'] and r['targets']['indexed_absolute_import_recall_100pct'] for r in report['repositories'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    args.output.with_suffix('.md').write_text(markdown_table(report))
    print(markdown_table(report))
    print('Target status:', 'MET' if report['targets_met'] else 'NOT MET (see per-repository targets)')
    return int(args.strict_targets and not report['targets_met'])


if __name__ == '__main__':
    raise SystemExit(main())
