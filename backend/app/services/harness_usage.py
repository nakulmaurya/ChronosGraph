"""Pinned OpenCode usage views. Legacy token snapshots are never called steps."""
CATEGORIES = ('input_tokens','output_tokens','reasoning_tokens','cache_read_tokens','cache_write_tokens')


def aggregate(events):
    legacy, steps, costs, conflicts, cost_conflicts = {}, {}, {}, [], []
    for event in sorted(events, key=lambda e:e['sequence']):
        usage = event.get('usage')
        if usage:
            if usage['basis']=='OPENCODE_ASSISTANT_MESSAGE_CUMULATIVE':
                legacy[usage['request_id']] = usage
            else:
                key = (usage['session_id'], usage['message_id'], usage['part_id'])
                if key in steps and any(steps[key].get(k)!=usage.get(k) for k in (*CATEGORIES,'cost')):
                    conflicts.append('/'.join(key))
                else:
                    steps[key] = usage
        cost = event.get('message_cost')
        if cost:
            old = costs.get(cost['message_id'])
            # An incomplete/older update cannot replace a completed message view.
            if old and old.get('completed_at_ms') is not None and cost.get('completed_at_ms')==old['completed_at_ms'] and old['cost']!=cost['cost']:
                cost_conflicts.append(cost['message_id'])
            if not old or (cost.get('completed_at_ms') is not None and
                    (old.get('completed_at_ms') or 0) < cost['completed_at_ms']) or old.get('completed_at_ms') is None:
                costs[cost['message_id']] = cost
    views = list(steps.values()) if steps else list(legacy.values())
    totals = {k:sum(v[k] for v in views) for k in CATEGORIES}
    mismatches=[]
    for message, cost in costs.items():
        observed=[v for v in steps.values() if v['message_id']==message]
        if cost.get('completed_at_ms') is not None and (not observed or any(v['cost'] is None for v in observed) or
                abs(sum(v['cost'] for v in observed)-cost['cost'])>1e-9):
            mismatches.append(message)
    return {'usage_by_request': list(legacy.values()),  # historical misnamed key retained, explicitly legacy below
        'legacy_usage_basis':'OPENCODE_MESSAGE_LATEST_STEP_TOKENS_CUMULATIVE_COST_LEGACY_LABEL',
        'legacy_usage_totals':{k:sum(v[k] for v in legacy.values()) for k in CATEGORIES},
        'completed_step_usage':list(steps.values()), 'message_cost_reconciliation':list(costs.values()),
        'usage_totals':totals if not conflicts else {},
        'usage_basis':'OPENCODE_COMPLETED_STEP_PART' if steps else 'LEGACY_MESSAGE_SNAPSHOTS_NOT_COMPLETED_STEP_TOTALS' if legacy else 'NO_USAGE_OBSERVED',
        'usage_conflicts':sorted(set(conflicts)), 'message_cost_conflicts':sorted(set(cost_conflicts)), 'cost_reconciliation_mismatches':mismatches,
        'provider_retry_usage':'UNKNOWN_NOT_OBSERVABLE_FROM_COMPLETED_STEPS',
        'usage_integrity':'CONFLICTING_COMPLETED_STEPS' if conflicts else 'PARTIAL_PROVIDER_RETRY_USAGE_UNKNOWN',
        'harness_reported_cost':sum(v['cost'] for v in views) if views and all(v['cost'] is not None for v in views) and not conflicts else None,
        'token_total':None}
