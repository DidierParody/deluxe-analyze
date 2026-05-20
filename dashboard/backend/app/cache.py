"""Minimal in-memory TTL cache for expensive GDS queries.

The graph topology only changes when the ETL runs (~ every 15 min in
production), so a 5-minute TTL is safe and dramatically improves UX
for the Louvain / Betweenness / PageRank endpoints (Louvain alone
takes ~25s per call against the 41k-edge graph).
"""
from __future__ import annotations

import time
from threading import Lock
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_lock = Lock()
_store: dict[str, tuple[float, Any]] = {}


def cached(key: str, ttl_seconds: int, producer: Callable[[], T]) -> T:
    now = time.monotonic()
    with _lock:
        hit = _store.get(key)
        if hit is not None and now - hit[0] < ttl_seconds:
            return hit[1]
    # Compute outside the lock to avoid blocking other readers
    value = producer()
    with _lock:
        _store[key] = (now, value)
    return value


def invalidate(prefix: str | None = None) -> None:
    with _lock:
        if prefix is None:
            _store.clear()
            return
        for k in list(_store):
            if k.startswith(prefix):
                _store.pop(k, None)
