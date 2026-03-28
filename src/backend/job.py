"""Single entrypoint: run the full scout swarm for a URL and write artifacts + assessment."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import modal
from assessment import build_assessment
from dotenv import load_dotenv
from run_batch import run_swarm, write_artifacts
from scout_prompts import SCOUT_SPECS, list_scout_ids


def normalize_scout_ids(scouts: str | list[str] | None) -> list[str]:
    """Resolve ``all``, comma-separated string, or list to scout ids."""
    all_ids = list_scout_ids()
    if isinstance(scouts, list):
        unknown = [s for s in scouts if s not in SCOUT_SPECS]
        if unknown:
            raise ValueError(f"Unknown scout id(s): {unknown}. Valid: {all_ids}")
        return list(scouts)
    if scouts is None or str(scouts).strip() == "" or str(scouts).strip().lower() == "all":
        return all_ids
    s = str(scouts).strip()
    parts = [p.strip() for p in s.split(",") if p.strip()]
    unknown = [p for p in parts if p not in SCOUT_SPECS]
    if unknown:
        raise ValueError(f"Unknown scout id(s): {unknown}. Valid: {all_ids}")
    return parts


def resolve_output_directory(seed_url: str, out_dir: str | Path | None = None) -> Path:
    """Default ``artifacts/<utc-timestamp>_<host>`` when ``out_dir`` is empty or None."""
    if out_dir is None or (isinstance(out_dir, str) and out_dir.strip() == ""):
        from urllib.parse import urlparse

        host = urlparse(seed_url.strip()).netloc.replace(":", "_") or "site"
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return Path("artifacts") / f"{ts}_{host}"
    return Path(out_dir)


def _default_progress(sid: str, row: dict[str, Any]) -> None:
    st = row.get("status")
    nflows = 0
    p = row.get("result_payload")
    if isinstance(p, dict) and isinstance(p.get("flows"), list):
        nflows = len(p["flows"])
    print(f"  done scout={sid} status={st} flows={nflows} run_id={row.get('run_id')}")


@dataclass(frozen=True)
class JobResult:
    out_dir: Path
    assessment: dict[str, Any]
    artifacts: list[dict[str, Any]]


def run_job_for_url(
    seed_url: str,
    *,
    scouts: str | list[str] | None = "all",
    out_dir: str | Path | None = None,
    parallelism: int = 2,
    max_attempts: int = 4,
    poll_timeout: float = 720.0,
    quiet: bool = False,
    progress: Callable[[str, dict[str, Any]], None] | None = None,
) -> JobResult:
    """Run all scouts for ``seed_url``, write JSON artifacts and ``assessment.json``.

    Loads ``.env`` via ``load_dotenv()`` so a single call works locally; in production
    set environment variables as usual.

    If ``progress`` is omitted and ``quiet`` is False, a default line-per-scout printer
    is used. If ``quiet`` is True and ``progress`` is omitted, nothing is printed from
    this module.
    """
    load_dotenv()
    url = seed_url.strip()
    scout_ids = normalize_scout_ids(scouts)
    out_path = resolve_output_directory(url, out_dir)

    cb: Callable[[str, dict[str, Any]], None] | None
    if progress is not None:
        cb = progress
    elif quiet:
        cb = None
    else:
        cb = _default_progress

    artifacts = asyncio.run(
        run_swarm(
            url,
            scout_ids,
            parallelism=parallelism,
            max_attempts=max_attempts,
            poll_max_wait_seconds=poll_timeout,
            progress=cb,
        )
    )
    write_artifacts(out_path, url, artifacts)
    assess = build_assessment(artifacts)
    (out_path / "assessment.json").write_text(json.dumps(assess, indent=2), encoding="utf-8")
    return JobResult(out_dir=out_path.resolve(), assessment=assess, artifacts=artifacts)


# -- Modal remote job --

app = modal.App("tinypages-indexer")

_modal_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_pyproject("pyproject.toml")
    .workdir("/root/app")
    .add_local_dir(".", remote_path="/root/app")
)


@app.function(
    image=_modal_image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=3600,
)
def run_job_remote(job_id: str, seed_url: str) -> dict:
    """Run all scouts for *seed_url*, writing progress to Supabase along the way."""
    import asyncio
    import logging
    from datetime import datetime, timezone

    from db import get_supabase
    from dotenv import load_dotenv
    from merge_flows import merge_flow_artifacts
    from run_batch import run_swarm
    from scout_prompts import list_scout_ids

    load_dotenv()
    logger = logging.getLogger("tinypages.job")
    logging.basicConfig(level=logging.INFO)

    logger.info("[%s] starting url=%s", job_id, seed_url)
    sb = get_supabase()

    sb.table("jobs").update({"status": "running"}).eq("job_id", job_id).execute()
    logger.info("[%s] status=running", job_id)

    try:
        url = seed_url.strip()
        scout_ids = list_scout_ids()
        logger.info("[%s] running %d scouts", job_id, len(scout_ids))

        artifacts = asyncio.run(
            run_swarm(url, scout_ids, parallelism=2, max_attempts=4, poll_max_wait_seconds=3600.0)
        )
        logger.info("[%s] swarm finished, %d artifacts: %s", job_id, len(artifacts), artifacts)

        merged = merge_flow_artifacts(artifacts)
        logger.info("[%s] merged flows, %d keys", job_id, len(merged))

        sb.table("indexed_pages").upsert({
            "page_url": seed_url,
            "last_indexed_by": job_id,
            "data": merged,
        }).execute()
        logger.info("[%s] wrote indexed_pages to supabase", job_id)

        sb.table("jobs").update({
            "status": "completed",
            "end_time": datetime.now(timezone.utc).isoformat(),
        }).eq("job_id", job_id).execute()
        logger.info("[%s] job completed", job_id)

        return {"status": "completed", "job_id": job_id}

    except Exception:
        logger.exception("[%s] job failed", job_id)
        sb.table("jobs").update({
            "status": "failed",
            "end_time": datetime.now(timezone.utc).isoformat(),
        }).eq("job_id", job_id).execute()
        raise
