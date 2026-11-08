from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, status

from core.config import settings


_attempts: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def check_login_rate_limit(key: str) -> None:
    now = monotonic()
    window_start = now - settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    with _lock:
        recent = _attempts[key]
        while recent and recent[0] <= window_start:
            recent.popleft()
        if len(recent) >= settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Try again later.",
                headers={"Retry-After": str(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)},
            )


def record_login_failure(key: str) -> None:
    with _lock:
        _attempts[key].append(monotonic())


def clear_login_failures(key: str) -> None:
    with _lock:
        _attempts.pop(key, None)
