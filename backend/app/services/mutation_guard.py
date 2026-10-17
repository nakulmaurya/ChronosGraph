"""Shared local-process then Redis lock order for proposal/policy mutations."""
from contextlib import contextmanager
from fastapi import HTTPException
from redis.exceptions import LockError
from app.db.client import db_manager
from app.services.common import tenant_exists, tenant_lock


@contextmanager
def mutation_guard(tenant):
    tenant_exists(tenant)
    with tenant_lock(tenant):
        lock = db_manager.db.connection.lock(f'chronosgraph:mutate:{tenant}', timeout=60, blocking_timeout=10)
        if not lock.acquire():
            raise HTTPException(409, 'Another mutation is active; retry the same request')
        try:
            yield lock
        finally:
            try:
                lock.release()
            except LockError:
                # Never release a new owner's lease after expiration.
                pass


def require_lease(lock):
    if not lock.owned():
        raise HTTPException(409, 'Mutation lease expired; retry the same request')
