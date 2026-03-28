"""TinyFish error taxonomy, backoff, and stealth retry heuristics."""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any

from tinyfish import (
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
    SDKError,
)


def parse_api_error_body(exc: SDKError) -> dict[str, Any] | None:
    resp = getattr(exc, "response", None)
    if resp is None:
        return None
    try:
        data = resp.json()
    except Exception:
        return None
    if isinstance(data, dict) and "error" in data and isinstance(data["error"], dict):
        return data["error"]
    return data if isinstance(data, dict) else None


def error_code(exc: SDKError) -> str | None:
    body = parse_api_error_body(exc)
    if not body:
        return None
    code = body.get("code")
    return str(code) if code is not None else None


def should_retry_infrastructure(exc: Exception) -> bool:
    if isinstance(exc, (RateLimitError, InternalServerError, APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exc, BadRequestError):
        code = error_code(exc)
        if code in (
            "SERVICE_BUSY",
            "TIMEOUT",
            "INTERNAL_ERROR",
            "RATE_LIMIT_EXCEEDED",
        ):
            return True
        msg = str(exc.message or "").lower()
        if "busy" in msg or "timeout" in msg or "rate" in msg:
            return True
    return False


def should_try_stealth_retry(exc: Exception) -> bool:
    """Second-attempt heuristic: bot-like blocks may respond as site or infra failures."""
    code = error_code(exc) if isinstance(exc, SDKError) else None
    if code in ("SITE_BLOCKED", "TASK_FAILED", "MAX_STEPS_EXCEEDED"):
        return True
    msg = str(getattr(exc, "message", "") or exc).lower()
    for hint in ("blocked", "captcha", "bot", "cloudflare", "forbidden"):
        if hint in msg:
            return True
    return False


def backoff_delay_seconds(attempt: int, base: float = 2.0, cap: float = 60.0) -> float:
    """Exponential backoff with jitter (seconds)."""
    delay = min(cap, base * (2**attempt))
    return delay * (0.8 + 0.4 * random.random())


def sleep_backoff(attempt: int, base: float = 2.0, cap: float = 60.0) -> None:
    time.sleep(backoff_delay_seconds(attempt, base=base, cap=cap))


async def async_sleep_backoff(attempt: int, base: float = 2.0, cap: float = 60.0) -> None:
    await asyncio.sleep(backoff_delay_seconds(attempt, base=base, cap=cap))


def summarize_exception(exc: Exception) -> dict[str, Any]:
    out: dict[str, Any] = {"type": type(exc).__name__, "message": str(exc)}
    if isinstance(exc, SDKError):
        body = parse_api_error_body(exc)
        if body:
            out["api_error"] = body
        resp = getattr(exc, "response", None)
        if resp is not None:
            out["http_status"] = getattr(resp, "status_code", None)
    return out
