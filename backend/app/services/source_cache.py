"""In-memory TTL cache for raw Elexon FUELHH/WINDFOR payloads (not analysis results)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.config import Settings


@dataclass(frozen=True)
class SourcePayload:
    fuelhh: list[dict[str, Any]]
    windfor: list[dict[str, Any]]


CacheKey = tuple[str, str, str, str, str]


def source_cache_key(settings: Settings) -> CacheKey:
    return (
        settings.elexon_base_url,
        settings.delivery_start.isoformat(),
        settings.delivery_end.isoformat(),
        settings.windfor_publish_from,
        settings.windfor_publish_to,
    )


class SourceDataCache:
    """
    TTL cache with single-flight loading per key: concurrent misses share one fetch.

    Failed fetches are not stored; waiters receive the same exception.
    """

    def __init__(
        self,
        ttl_seconds: float,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be >= 0")
        self._ttl = ttl_seconds
        self._clock = clock or time.monotonic
        self._lock = threading.Lock()
        self._entries: dict[CacheKey, tuple[float, SourcePayload]] = {}
        self._inflight: dict[CacheKey, _Inflight] = {}

    @property
    def ttl_seconds(self) -> float:
        return self._ttl

    def invalidate(self, key: CacheKey | None = None) -> None:
        """Drop cached entry(ies). Does not cancel an in-progress fetch."""
        with self._lock:
            if key is None:
                self._entries.clear()
            else:
                self._entries.pop(key, None)

    def _get_valid_locked(self, key: CacheKey) -> SourcePayload | None:
        if self._ttl == 0:
            return None
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, payload = entry
        if self._clock() - stored_at >= self._ttl:
            self._entries.pop(key, None)
            return None
        return payload

    def load(self, key: CacheKey, fetch: Callable[[], SourcePayload]) -> SourcePayload:
        with self._lock:
            cached = self._get_valid_locked(key)
            if cached is not None:
                return cached

            inflight = self._inflight.get(key)
            if inflight is not None:
                waiter = True
            else:
                inflight = _Inflight()
                self._inflight[key] = inflight
                waiter = False

        if waiter:
            return inflight.wait()

        try:
            payload = fetch()
        except Exception as exc:
            inflight.fail(exc)
            with self._lock:
                self._inflight.pop(key, None)
            raise

        with self._lock:
            if self._ttl > 0:
                self._entries[key] = (self._clock(), payload)
            self._inflight.pop(key, None)
        inflight.complete(payload)
        return payload


class _Inflight:
    def __init__(self) -> None:
        self._event = threading.Event()
        self._payload: SourcePayload | None = None
        self._error: BaseException | None = None

    def complete(self, payload: SourcePayload) -> None:
        self._payload = payload
        self._event.set()

    def fail(self, error: BaseException) -> None:
        self._error = error
        self._event.set()

    def wait(self) -> SourcePayload:
        self._event.wait()
        if self._error is not None:
            raise self._error
        assert self._payload is not None
        return self._payload


_default_cache: SourceDataCache | None = None


def get_source_cache(settings: Settings) -> SourceDataCache:
    global _default_cache
    if _default_cache is None or _default_cache.ttl_seconds != settings.elexon_source_cache_ttl_seconds:
        _default_cache = SourceDataCache(settings.elexon_source_cache_ttl_seconds)
    return _default_cache


def reset_source_cache_for_tests() -> None:
    """Clear the process-wide cache singleton (tests only)."""
    global _default_cache
    _default_cache = None
