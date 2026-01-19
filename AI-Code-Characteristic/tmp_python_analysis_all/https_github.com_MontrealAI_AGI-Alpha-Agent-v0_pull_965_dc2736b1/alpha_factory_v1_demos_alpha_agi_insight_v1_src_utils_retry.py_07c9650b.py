from __future__ import annotations

from typing import Callable, TypeVar, Any

try:  # pragma: no cover - optional dependency
    import backoff
except Exception:  # pragma: no cover - fallback if missing
    backoff = None

from .logging import _log
import asyncio
import inspect
import time

T = TypeVar("T")


def with_retry(func: Callable[..., T], *, max_tries: int = 3) -> Callable[..., T]:
    """Wrap *func* with exponential backoff and logging."""

    def _log_retry(details: dict[str, Any]) -> None:
        _log.warning(
            "Retry %d/%d for %s due to %s",
            details["tries"],
            max_tries,
            getattr(details.get("target"), "__name__", "call"),
            details.get("exception"),
        )

    if backoff is not None:
        return backoff.on_exception(
            backoff.expo,
            Exception,
            max_tries=max_tries,
            jitter=backoff.full_jitter,
            on_backoff=_log_retry,
        )(func)

    is_async = inspect.iscoroutinefunction(func)

    if is_async:

        async def wrapper(*args: Any, **kwargs: Any) -> T:
            for attempt in range(max_tries):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:  # pragma: no cover - runtime errors
                    if attempt + 1 >= max_tries:
                        raise
                    _log_retry(
                        {
                            "tries": attempt + 1,
                            "exception": exc,
                            "target": func,
                        }
                    )
                    await asyncio.sleep(2**attempt * 0.1)

        return wrapper

    def wrapper(*args: Any, **kwargs: Any) -> T:
        for attempt in range(max_tries):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # pragma: no cover - runtime errors
                if attempt + 1 >= max_tries:
                    raise
                _log_retry(
                    {
                        "tries": attempt + 1,
                        "exception": exc,
                        "target": func,
                    }
                )
                time.sleep(2**attempt * 0.1)

    return wrapper
