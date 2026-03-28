"""CLI: run TinyFish flow scouts (async concurrent) and write artifacts + merged flows.json."""

from __future__ import annotations

import argparse
import json

from job import normalize_scout_ids, resolve_output_directory, run_job_for_url
from scout_prompts import list_scout_ids


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

    seed_url = args.url.strip()
    try:
        scout_ids = normalize_scout_ids(args.scouts)
    except ValueError as e:
        raise SystemExit(str(e)) from e

    out_dir = resolve_output_directory(seed_url, args.out_dir or None)

    if not args.quiet:
        print(f"Seed URL: {seed_url}")
        print(f"Scouts: {scout_ids} (parallelism={args.parallelism})")
        print(f"Output: {out_dir.resolve()}")

    result = run_job_for_url(
        seed_url,
        scouts=scout_ids,
        out_dir=out_dir,
        parallelism=args.parallelism,
        max_attempts=args.max_attempts,
        poll_timeout=args.poll_timeout,
        quiet=args.quiet,
    )
    if not args.quiet:
        print(json.dumps(result.assessment, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
