"""Execute multiple scouts with asyncio + AsyncTinyFish (bounded concurrency).

Each scout uses the async TinyFish API: ``agent.queue()`` (run-async) then poll
``runs.get()`` until the run is terminal. This matches server-side concurrent
agent execution rather than holding one long blocking ``agent.run()`` request
per scout.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tinyfish import AsyncTinyFish, BrowserProfile, NotFoundError
from tinyfish.runs.types import Run, RunStatus

from merge_flows import merge_flow_artifacts
from retries import (
    async_sleep_backoff,
    should_retry_infrastructure,
    should_try_stealth_retry,
    summarize_exception,
)
from scout_prompts import build_goal, list_scout_ids
from scout_schema import parse_scout_result, validate_parsed_shape

# Slightly above default automation HTTP timeout (600s) so slow runs can finish.
_DEFAULT_POLL_MAX_WAIT_SEC = 720.0
_POLL_INITIAL_INTERVAL = 2.0
_POLL_MAX_INTERVAL = 20.0


@dataclass
class AttemptLog:
    browser_profile: str
    ok: bool
    detail: dict[str, Any] = field(default_factory=dict)


async def _poll_run_until_terminal(
    client: AsyncTinyFish,
    run_id: str,
    *,
    max_wait_seconds: float = _DEFAULT_POLL_MAX_WAIT_SEC,
) -> Run | None:
    """Poll ``GET /v1/runs/{id}`` until COMPLETED, FAILED, or CANCELLED. None if deadline exceeded."""
    import logging
    logger = logging.getLogger("tinypages.poll")

    deadline = time.monotonic() + max_wait_seconds
    interval = _POLL_INITIAL_INTERVAL
    while time.monotonic() < deadline:
        try:
            run = await client.runs.get(run_id)
        except NotFoundError:
            logger.info("[poll] run_id=%s not found, retrying", run_id)
            await asyncio.sleep(min(interval, max(0.0, deadline - time.monotonic())))
            interval = min(_POLL_MAX_INTERVAL, interval * 1.25)
            continue
        logger.info("[poll] run_id=%s status=%s (type=%s)", run_id, run.status, type(run.status).__name__)
        if run.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
            return run
        wait = interval
        if run.error is not None and run.error.retry_after is not None:
            wait = max(wait, float(run.error.retry_after))
        await asyncio.sleep(min(wait, max(0.0, deadline - time.monotonic())))
        interval = min(_POLL_MAX_INTERVAL, interval * 1.25)
    try:
        final = await client.runs.get(run_id)
        if final.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED):
            return final
    except NotFoundError:
        pass
    return None


def _run_record_from_polled_run(run: Run) -> dict[str, Any]:
    out: dict[str, Any] = {
        "http_ok": True,
        "run_id": run.run_id,
        "status": str(run.status),
        "num_of_steps": None,
        "result_raw": run.result,
        "error": run.error.model_dump(mode="json") if run.error else None,
        "execution": "queue_poll",
    }
    if run.status != RunStatus.COMPLETED:
        out["http_ok"] = False
        out["failure_kind"] = "run_not_completed"
    return out


async def _run_once(
    client: AsyncTinyFish,
    seed_url: str,
    scout_id: str,
    browser_profile: BrowserProfile,
    *,
    poll_max_wait_seconds: float = _DEFAULT_POLL_MAX_WAIT_SEC,
) -> dict[str, Any]:
    goal = build_goal(scout_id, seed_url)
    queued = await client.agent.queue(
        goal=goal,
        url=seed_url,
        browser_profile=browser_profile,
    )
    if queued.error is not None or not queued.run_id:
        return {
            "http_ok": False,
            "run_id": queued.run_id,
            "status": "QUEUE_FAILED",
            "num_of_steps": None,
            "result_raw": None,
            "error": queued.error.model_dump(mode="json") if queued.error else {"message": "queue returned no run_id"},
            "failure_kind": "queue_failed",
            "execution": "queue_poll",
        }

    run = await _poll_run_until_terminal(client, queued.run_id, max_wait_seconds=poll_max_wait_seconds)
    if run is None:
        return {
            "http_ok": False,
            "run_id": queued.run_id,
            "status": "POLL_TIMEOUT",
            "num_of_steps": None,
            "result_raw": None,
            "error": {
                "message": f"Run did not reach terminal status within {poll_max_wait_seconds}s",
                "category": "UNKNOWN",
            },
            "failure_kind": "poll_timeout",
            "execution": "queue_poll",
        }
    return _run_record_from_polled_run(run)


async def execute_scout(
    client: AsyncTinyFish,
    seed_url: str,
    scout_id: str,
    *,
    max_attempts: int = 4,
    poll_max_wait_seconds: float = _DEFAULT_POLL_MAX_WAIT_SEC,
) -> dict[str, Any]:
    """Run one scout with lite-first, backoff, and optional stealth retry."""
    attempts_log: list[AttemptLog] = []
    profile: BrowserProfile = BrowserProfile.LITE
    stealth_tried = False
    last_payload: dict[str, Any] | None = None

    for attempt in range(max_attempts):
        try:
            raw = await _run_once(
                client,
                seed_url,
                scout_id,
                profile,
                poll_max_wait_seconds=poll_max_wait_seconds,
            )
            attempts_log.append(
                AttemptLog(
                    browser_profile=profile.value,
                    ok=raw.get("http_ok") is True
                    and raw.get("status") == RunStatus.COMPLETED.value,
                    detail=raw,
                )
            )
            status = raw.get("status")
            if status == RunStatus.COMPLETED.value:
                rr = raw.get("result_raw")
                parsed = parse_scout_result(rr if isinstance(rr, dict) else None)
                validation_issues = validate_parsed_shape(parsed, scout_id)
                return {
                    "scout_id": scout_id,
                    "seed_url": seed_url,
                    "run_id": raw.get("run_id"),
                    "status": status,
                    "num_of_steps": raw.get("num_of_steps"),
                    "result_raw": raw.get("result_raw"),
                    "result_payload": parsed,
                    "validation_issues": validation_issues,
                    "error": raw.get("error"),
                    "attempts": [
                        {"browser_profile": a.browser_profile, "ok": a.ok, "detail": a.detail}
                        for a in attempts_log
                    ],
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                }

            err_obj = raw.get("error") or {}
            msg = str(err_obj.get("message", "") if isinstance(err_obj, dict) else "")
            synthetic_exc = Exception(msg)
            if not stealth_tried and should_try_stealth_retry(synthetic_exc):
                profile = BrowserProfile.STEALTH
                stealth_tried = True
                continue
            if should_retry_infrastructure(synthetic_exc) and attempt < max_attempts - 1:
                await async_sleep_backoff(attempt)
                continue
            if attempt < max_attempts - 1:
                await async_sleep_backoff(attempt)
                continue
            last_payload = {
                "scout_id": scout_id,
                "seed_url": seed_url,
                "run_id": raw.get("run_id"),
                "status": status,
                "num_of_steps": raw.get("num_of_steps"),
                "result_raw": raw.get("result_raw"),
                "result_payload": None,
                "validation_issues": ["run_status_not_completed"],
                "error": raw.get("error"),
                "attempts": [
                    {"browser_profile": a.browser_profile, "ok": a.ok, "detail": a.detail}
                    for a in attempts_log
                ],
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
            break

        except Exception as exc:  # noqa: BLE001 — boundary: capture all SDK errors
            attempts_log.append(
                AttemptLog(
                    browser_profile=profile.value,
                    ok=False,
                    detail={"exception": summarize_exception(exc)},
                )
            )
            if not stealth_tried and should_try_stealth_retry(exc):
                profile = BrowserProfile.STEALTH
                stealth_tried = True
                continue
            if should_retry_infrastructure(exc) and attempt < max_attempts - 1:
                await async_sleep_backoff(attempt)
                continue
            if attempt < max_attempts - 1:
                await async_sleep_backoff(attempt)
                continue
            last_payload = {
                "scout_id": scout_id,
                "seed_url": seed_url,
                "run_id": None,
                "status": "EXCEPTION",
                "num_of_steps": None,
                "result_raw": None,
                "result_payload": None,
                "validation_issues": ["exception_before_complete"],
                "error": summarize_exception(exc),
                "attempts": [
                    {"browser_profile": a.browser_profile, "ok": a.ok, "detail": a.detail}
                    for a in attempts_log
                ],
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
            break

    return last_payload or {
        "scout_id": scout_id,
        "seed_url": seed_url,
        "run_id": None,
        "status": "UNKNOWN",
        "error": {"message": "exhausted_retries"},
        "result_payload": None,
        "validation_issues": ["unknown_state"],
        "attempts": [
            {"browser_profile": a.browser_profile, "ok": a.ok, "detail": a.detail} for a in attempts_log
        ],
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_swarm(
    seed_url: str,
    scout_ids: list[str],
    *,
    parallelism: int = 2,
    max_attempts: int = 4,
    poll_max_wait_seconds: float = _DEFAULT_POLL_MAX_WAIT_SEC,
    progress: Callable[[str, dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    scout_ids = [s for s in scout_ids if s in list_scout_ids()]
    sem = asyncio.Semaphore(max(1, parallelism))

    async with AsyncTinyFish() as client:

        async def bounded(sid: str) -> tuple[str, dict[str, Any]]:
            async with sem:
                row = await execute_scout(
                    client,
                    seed_url,
                    sid,
                    max_attempts=max_attempts,
                    poll_max_wait_seconds=poll_max_wait_seconds,
                )
            return sid, row

        tasks = [asyncio.create_task(bounded(sid)) for sid in scout_ids]
        results_by_id: dict[str, dict[str, Any]] = {}
        for fut in asyncio.as_completed(tasks):
            sid, row = await fut
            results_by_id[sid] = row
            if progress:
                progress(sid, row)

    return [results_by_id[s] for s in scout_ids if s in results_by_id]


def write_artifacts(out_dir: Path, seed_url: str, artifacts: list[dict[str, Any]]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "seed_url": seed_url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scouts": [a.get("scout_id") for a in artifacts],
        "tinyfish_execution": "queue_then_poll_runs_api",
    }
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    for art in artifacts:
        rid = art.get("run_id") or f"no_run_id_{art.get('scout_id')}"
        path = out_dir / f"{art.get('scout_id')}_{rid}.json"
        path.write_text(json.dumps(art, indent=2, default=str), encoding="utf-8")
    merged = merge_flow_artifacts(artifacts)
    merged["seed_url"] = seed_url
    merged["created_at"] = meta["created_at"]
    (out_dir / "flows.json").write_text(json.dumps(merged, indent=2, default=str), encoding="utf-8")
    return out_dir
