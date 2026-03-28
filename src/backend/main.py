"""CLI: run TinyFish flow scouts (async concurrent) and write artifacts + merged flows.json."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from assessment import build_assessment
from run_batch import run_swarm, write_artifacts
from scout_prompts import SCOUT_SPECS, list_scout_ids


def _parse_scouts(arg: str | None) -> list[str]:
    all_ids = list_scout_ids()
    if arg is None or arg.strip() == "" or arg.strip().lower() == "all":
        return all_ids
    parts = [p.strip() for p in arg.split(",") if p.strip()]
    unknown = [p for p in parts if p not in SCOUT_SPECS]
    if unknown:
        raise SystemExit(f"Unknown scout id(s): {unknown}. Valid: {all_ids}")
    return parts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TinyFish semantic flow scouts (MVP swarm).")
    parser.add_argument(
        "--url",
        required=True,
        help="Seed URL to open (homepage or deep link).",
    )
    parser.add_argument(
        "--scouts",
        default="all",
        help=f"Comma-separated scout ids or 'all'. Valid: {','.join(list_scout_ids())}.",
    )
    parser.add_argument(
        "--out-dir",
        default="",
        help="Output directory for JSON artifacts. Default: artifacts/<iso-timestamp>_<host-slug>.",
    )
    parser.add_argument(
        "--parallelism",
        type=int,
        default=2,
        help="Max concurrent scouts via asyncio semaphore (default 2). Uses AsyncTinyFish.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=4,
        help="Max attempts per scout including lite/stealth and backoff retries.",
    )
    parser.add_argument(
        "--poll-timeout",
        type=float,
        default=720.0,
        help="Max seconds to poll each queued run via GET /v1/runs/{id} (default 720).",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Less console output (still writes JSON files).",
    )
    args = parser.parse_args(argv)
    load_dotenv()

    seed_url = args.url.strip()
    scout_ids = _parse_scouts(args.scouts)
    if not args.out_dir:
        from urllib.parse import urlparse

        host = urlparse(seed_url).netloc.replace(":", "_") or "site"
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path("artifacts") / f"{ts}_{host}"
    else:
        out_dir = Path(args.out_dir)

    if not args.quiet:
        print(f"Seed URL: {seed_url}")
        print(f"Scouts: {scout_ids} (parallelism={args.parallelism})")
        print(f"Output: {out_dir.resolve()}")

    def on_progress(sid: str, row: dict) -> None:
        if args.quiet:
            return
        st = row.get("status")
        nflows = 0
        p = row.get("result_payload")
        if isinstance(p, dict) and isinstance(p.get("flows"), list):
            nflows = len(p["flows"])
        print(f"  done scout={sid} status={st} flows={nflows} run_id={row.get('run_id')}")

    artifacts = asyncio.run(
        run_swarm(
            seed_url,
            scout_ids,
            parallelism=args.parallelism,
            max_attempts=args.max_attempts,
            poll_max_wait_seconds=args.poll_timeout,
            progress=on_progress,
        )
    )
    write_artifacts(out_dir, seed_url, artifacts)
    assess = build_assessment(artifacts)
    (out_dir / "assessment.json").write_text(json.dumps(assess, indent=2), encoding="utf-8")
    if not args.quiet:
        print(json.dumps(assess, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
