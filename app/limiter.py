from threading import Lock
from time import time

WINDOW_SECONDS = 15 * 60
MAX_ATTEMPTS = 5

_lock = Lock()
_failures: dict[str, list[float]] = {}


def _recent(ip: str, now: float) -> list[float]:
    kept = [stamp for stamp in _failures.get(ip, []) if now - stamp < WINDOW_SECONDS]
    if kept:
        _failures[ip] = kept
    else:
        _failures.pop(ip, None)
    return kept


def is_limited(ip: str) -> bool:
    now = time()
    with _lock:
        return len(_recent(ip, now)) >= MAX_ATTEMPTS


def record_failure(ip: str) -> None:
    now = time()
    with _lock:
        recent = _recent(ip, now)
        recent.append(now)
        _failures[ip] = recent


def clear_failures(ip: str) -> None:
    with _lock:
        _failures.pop(ip, None)


def reset() -> None:
    with _lock:
        _failures.clear()
