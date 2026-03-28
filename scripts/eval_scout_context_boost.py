"""Compare two TinyFish web runs: the same objective you define, with vs without scout artifacts.

The baseline arm receives only your objective. The other arm prepends prior swarm output so the
agent can use it as *guidance* (where to look, likely URLs, IA hints)—not as a script to follow
literally.

The remote agent cannot read your local disk; "artifacts" are embedded as JSON in the goal.

Edit the configuration block below, then run from the repository root::

    uv run --project src/backend python scripts/eval_scout_context_boost.py

Reusable tasks live under ``scripts/eval_tasks/`` (see ``scripts/eval_tasks/README.md``). Set
``EVAL_MODE`` to ``"all"`` to run every ``*.json`` task and print a before/after table, or
``"single"`` with ``TASK_FILE`` pointing at one task (or inline config when ``TASK_FILE`` is empty).

Metrics (per arm): ``status``, ``num_of_steps`` from the synchronous run API, and duration from
``started_at``/``finished_at`` when present (else client wall time around ``agent.run``).
"""

from __future__ import annotations

import json
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from tinyfish import BrowserProfile, TinyFish
from tinyfish.runs.types import RunStatus


load_dotenv()

# =============================================================================
# Configuration — edit these values
# =============================================================================

# "single" — one task from TASK_FILE (or inline fallback when TASK_FILE is empty).
# "all" — every scripts/eval_tasks/*.json; prints a before/after suite table.
EVAL_MODE = "all"

# Path to a task JSON under scripts/eval_tasks/ (relative to repo root), or "" to use inline
# URL / OBJECTIVE / ARTIFACTS_DIR / OUT_JSON below. Used only when EVAL_MODE == "single".
TASK_FILE = "scripts/eval_tasks/tinyfish_pricing.json"

# Inline fallback — used only when TASK_FILE is empty.
URL = "https://tinyfish.ai"
OBJECTIVE = (
    "Collect public pricing from the seed site. Return JSON with keys pricing_page_url, plans "
    "(array of {plan_name, billing_period, price_display, price_numeric, currency}), "
    "custom_or_contact_pricing, notes. No markdown fences."
)
ARTIFACTS_DIR = "artifacts/20260328T044713Z_tinyfish.ai"

# Defaults (task JSON may override max_artifact_chars and out_json).
MAX_ARTIFACT_CHARS = 48_000
OUT_JSON = ""

USE_STEALTH = False
RANDOMIZE_ORDER = False
RNG_SEED = 0

# When EVAL_MODE == "all": write combined results here (relative to repo root). Empty = skip.
OUT_JSON_SUITE = "artifacts/eval_suite_latest.json"

# =============================================================================


@dataclass(frozen=True)
class EvalRunConfig:
    task_id: str
    title: str
    url: str
    objective: str
    artifacts_dir: str
    max_artifact_chars: int
    out_json: str


def _load_eval_run_config_from_path(path: Path) -> EvalRunConfig:
    if not path.is_file():
        raise FileNotFoundError(f"Task file not found: {path}")

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    task_id = str(data.get("id", path.stem))
    title = str(data.get("title", task_id))
    url = str(data["url"]).strip()
    artifacts_dir = str(data["artifacts_dir"]).strip()
    base = path.parent

    objective_file = data.get("objective_file")
    if objective_file:
        of = base / str(objective_file)
        if not of.is_file():
            raise FileNotFoundError(f"objective_file not found: {of}")
        objective = of.read_text(encoding="utf-8").strip()
    elif "objective" in data:
        objective = str(data["objective"]).strip()
    else:
        raise ValueError(f"Task {path} must set objective_file or objective")

    mac = int(data["max_artifact_chars"]) if data.get("max_artifact_chars") is not None else MAX_ARTIFACT_CHARS

    if "out_json" in data and data["out_json"] is not None:
        out_json = str(data["out_json"]).strip()
    else:
        out_json = f"artifacts/eval_{task_id}.json"

    return EvalRunConfig(
        task_id=task_id,
        title=title,
        url=url,
        objective=objective,
        artifacts_dir=artifacts_dir,
        max_artifact_chars=mac,
        out_json=out_json,
    )


def _load_eval_run_config() -> EvalRunConfig:
    root = _repo_root()
    if not TASK_FILE.strip():
        return EvalRunConfig(
            task_id="inline",
            title="Inline configuration",
            url=URL.strip(),
            objective=OBJECTIVE.strip(),
            artifacts_dir=ARTIFACTS_DIR.strip(),
            max_artifact_chars=MAX_ARTIFACT_CHARS,
            out_json=OUT_JSON.strip(),
        )

    path = Path(TASK_FILE.strip())
    if not path.is_absolute():
        path = root / path
    return _load_eval_run_config_from_path(path)


def _iter_task_json_paths() -> list[Path]:
    d = _repo_root() / "scripts" / "eval_tasks"
    return sorted(p for p in d.glob("*.json") if p.is_file())


@dataclass
class ArmResult:
    label: str
    status: str
    ok: bool
    num_of_steps: int | None
    duration_api_sec: float | None
    duration_client_sec: float
    run_id: str | None
    error_message: str | None
    result_payload: dict[str, Any] | None


@dataclass
class TaskEvalOutcome:
    task_id: str
    title: str
    baseline: ArmResult | None
    boosted: ArmResult | None
    artifacts_path: Path | None
    error: str | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_artifact_context(artifacts_dir: Path, max_chars: int) -> str:
    if not artifacts_dir.is_dir():
        raise FileNotFoundError(f"Not a directory: {artifacts_dir}")
    flows = artifacts_dir / "flows.json"
    if flows.is_file():
        raw = flows.read_text(encoding="utf-8")
    else:
        parts: list[str] = []
        for p in sorted(artifacts_dir.glob("*.json")):
            if p.name == "run_meta.json":
                continue
            parts.append(p.read_text(encoding="utf-8"))
        raw = "\n".join(parts) if parts else "{}"
    raw = raw.strip()
    if max_chars > 0 and len(raw) > max_chars:
        raw = raw[:max_chars] + "\n... [truncated by MAX_ARTIFACT_CHARS]"
    return raw


def _goal_with_artifacts(base_goal: str, artifact_blob: str) -> str:
    return (
        "The JSON below is from earlier automated scouts of this site (flows, entry points, "
        "notes). Use it to guide your decisions—where to navigate first, what to look for—but "
        "it may be wrong or out of date; always confirm on the live site. Your choices and plan "
        "are yours; this is background context only.\n\n"
        f"```json\n{artifact_blob}\n```\n\n"
        "---\n\n"
        "Objective:\n"
        f"{base_goal.strip()}"
    )


def _goal_baseline(base_goal: str) -> str:
    return base_goal.strip()


def _run_arm(
    client: TinyFish,
    *,
    label: str,
    goal: str,
    url: str,
    browser_profile: BrowserProfile,
) -> ArmResult:
    t_client0 = time.perf_counter()
    resp = client.agent.run(goal=goal, url=url, browser_profile=browser_profile)
    client_sec = time.perf_counter() - t_client0

    api_sec: float | None = None
    if resp.started_at is not None and resp.finished_at is not None:
        api_sec = (resp.finished_at - resp.started_at).total_seconds()

    err_msg = None
    if resp.error is not None:
        err_msg = resp.error.message

    ok = resp.status == RunStatus.COMPLETED
    raw_result = resp.result
    result_payload: dict[str, Any] | None = raw_result if isinstance(raw_result, dict) else None

    return ArmResult(
        label=label,
        status=str(resp.status),
        ok=ok,
        num_of_steps=resp.num_of_steps,
        duration_api_sec=api_sec,
        duration_client_sec=client_sec,
        run_id=resp.run_id,
        error_message=err_msg,
        result_payload=result_payload,
    )


def _duration_sec(r: ArmResult) -> float | None:
    if r.duration_api_sec is not None:
        return float(r.duration_api_sec)
    if r.duration_client_sec is not None:
        return float(r.duration_client_sec)
    return None


def _render_ascii_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    lines = [sep]

    def fmt_row(cells: list[str]) -> str:
        return "|" + "|".join(f" {cells[i]:<{widths[i]}} " for i in range(len(cells))) + "|"

    lines.append(fmt_row(headers))
    lines.append(sep)
    for row in rows:
        lines.append(fmt_row(row))
    lines.append(sep)
    return "\n".join(lines)


def _cell_ok(ok: bool) -> str:
    return "Y" if ok else "N"


def _cell_steps(n: int | None) -> str:
    return "—" if n is None else str(n)


def _cell_sec(r: ArmResult | None) -> str:
    if r is None:
        return "—"
    d = _duration_sec(r)
    return "—" if d is None else f"{d:.2f}"


def _delta_steps_str(b: ArmResult, p: ArmResult) -> str:
    if b.num_of_steps is None or p.num_of_steps is None:
        return "—"
    return str(p.num_of_steps - b.num_of_steps)


def _delta_sec_str(b: ArmResult, p: ArmResult) -> str:
    tb, tp = _duration_sec(b), _duration_sec(p)
    if tb is None or tp is None:
        return "—"
    return f"{tp - tb:+.2f}"


def _winner_steps_label(b: ArmResult, p: ArmResult) -> str:
    if not (b.ok and p.ok):
        return "—"
    if b.num_of_steps is None or p.num_of_steps is None:
        return "—"
    if p.num_of_steps < b.num_of_steps:
        return "playbook"
    if p.num_of_steps > b.num_of_steps:
        return "baseline"
    return "tie"


def _winner_time_label(b: ArmResult, p: ArmResult) -> str:
    if not (b.ok and p.ok):
        return "—"
    tb, tp = _duration_sec(b), _duration_sec(p)
    if tb is None or tp is None:
        return "—"
    if tp < tb:
        return "playbook"
    if tp > tb:
        return "baseline"
    return "tie"


def _print_suite_table(outcomes: list[TaskEvalOutcome]) -> None:
    headers = [
        "task_id",
        "OK₀",
        "OK₁",
        "steps₀",
        "steps₁",
        "Δ steps",
        "sec₀",
        "sec₁",
        "Δ sec",
        "fewer steps",
        "faster",
    ]
    rows: list[list[str]] = []
    pb_steps_wins = 0
    pb_time_wins = 0
    comparable_steps = 0
    comparable_time = 0

    for o in outcomes:
        if o.error:
            rows.append(
                [
                    o.task_id,
                    "—",
                    "—",
                    "—",
                    "—",
                    o.error[:48] + ("…" if len(o.error) > 48 else ""),
                    "—",
                    "—",
                    "—",
                    "—",
                    "—",
                ]
            )
            continue
        assert o.baseline is not None and o.boosted is not None
        b, p = o.baseline, o.boosted
        ws = _winner_steps_label(b, p)
        wt = _winner_time_label(b, p)
        if b.ok and p.ok and b.num_of_steps is not None and p.num_of_steps is not None:
            comparable_steps += 1
            if ws == "playbook":
                pb_steps_wins += 1
        if b.ok and p.ok and _duration_sec(b) is not None and _duration_sec(p) is not None:
            comparable_time += 1
            if wt == "playbook":
                pb_time_wins += 1

        rows.append(
            [
                o.task_id,
                _cell_ok(b.ok),
                _cell_ok(p.ok),
                _cell_steps(b.num_of_steps),
                _cell_steps(p.num_of_steps),
                _delta_steps_str(b, p),
                _cell_sec(b),
                _cell_sec(p),
                _delta_sec_str(b, p),
                ws,
                wt,
            ]
        )

    print()
    print("=== Suite summary: before (₀ baseline, no playbook) vs after (₁ with scout artifacts) ===")
    print(_render_ascii_table(headers, rows))
    print()
    print(
        f"Playbook wins: {pb_steps_wins}/{comparable_steps} on steps, "
        f"{pb_time_wins}/{comparable_time} on time (among runs where both arms succeeded "
        "and the metric was available)."
    )
    print("Negative Δ steps / Δ sec means the playbook arm used fewer steps or less time.")


def _print_summary(a: ArmResult, b: ArmResult) -> None:
    print("\n=== Results ===")
    for r in (a, b):
        print(f"\n[{r.label}]")
        print(f"  status:          {r.status}")
        print(f"  success:         {r.ok}")
        print(f"  num_of_steps:    {r.num_of_steps}")
        print(f"  duration (API):  {r.duration_api_sec}")
        print(f"  duration (client): {r.duration_client_sec:.3f}s")
        print(f"  run_id:          {r.run_id}")
        if r.error_message:
            print(f"  error:           {r.error_message}")

        print("  result payload:")
        if r.result_payload is not None:
            print(json.dumps(r.result_payload, indent=2, ensure_ascii=False))
        else:
            print("    (none)")

    print("\n=== Comparison (lower is better for time / steps) ===")
    if a.ok and b.ok:
        faster = a if (a.duration_api_sec or a.duration_client_sec) <= (b.duration_api_sec or b.duration_client_sec) else b
        fewer = a if (a.num_of_steps or 10**9) <= (b.num_of_steps or 10**9) else b
        print(f"  Faster (by recorded duration): {faster.label}")
        print(f"  Fewer steps:                   {fewer.label}")
    elif a.ok:
        print("  Only baseline succeeded.")
    elif b.ok:
        print("  Only with-artifacts succeeded.")
    else:
        print("  Neither run completed successfully.")


def _run_eval(
    *,
    url: str,
    objective: str,
    artifacts_dir: str,
    max_artifact_chars: int,
    use_stealth: bool,
    randomize_order: bool,
    rng_seed: int,
) -> tuple[list[ArmResult], Path]:
    base_goal = objective.strip()
    if not base_goal:
        raise ValueError("Objective is empty; fix the task file or inline OBJECTIVE.")

    artifacts_path = Path(artifacts_dir)
    if not artifacts_path.is_absolute():
        artifacts_path = (_repo_root() / artifacts_path).resolve()

    artifact_blob = _load_artifact_context(artifacts_path, max_artifact_chars)
    goal_baseline = _goal_baseline(base_goal)
    goal_boosted = _goal_with_artifacts(base_goal, artifact_blob)

    browser_profile = BrowserProfile.STEALTH if use_stealth else BrowserProfile.LITE

    arms: list[tuple[str, str]] = [
        ("baseline_no_artifacts", goal_baseline),
        ("with_scout_artifacts", goal_boosted),
    ]
    if randomize_order:
        rng = random.Random(rng_seed)
        rng.shuffle(arms)

    results: list[ArmResult] = []

    with TinyFish() as client:
        for label, goal in arms:
            r = _run_arm(
                client,
                label=label,
                goal=goal,
                url=url.strip(),
                browser_profile=browser_profile,
            )
            results.append(r)

    return results, artifacts_path


def _run_suite() -> list[TaskEvalOutcome]:
    paths = _iter_task_json_paths()
    if not paths:
        raise FileNotFoundError("No scripts/eval_tasks/*.json files found.")

    outcomes: list[TaskEvalOutcome] = []
    n = len(paths)
    print(f"Running {n} tasks (2 API runs each: baseline then playbook).\n", flush=True)

    for i, path in enumerate(paths, start=1):
        try:
            cfg = _load_eval_run_config_from_path(path)
        except Exception as exc:  # noqa: BLE001
            outcomes.append(
                TaskEvalOutcome(
                    task_id=path.stem,
                    title=path.stem,
                    baseline=None,
                    boosted=None,
                    artifacts_path=None,
                    error=str(exc),
                )
            )
            print(f"[{i}/{n}] {path.stem} — config error: {exc}", flush=True)
            continue

        print(f"[{i}/{n}] {cfg.task_id} — {cfg.title}", flush=True)
        print(f"    URL: {cfg.url}", flush=True)

        try:
            results, ap = _run_eval(
                url=cfg.url,
                objective=cfg.objective,
                artifacts_dir=cfg.artifacts_dir,
                max_artifact_chars=cfg.max_artifact_chars,
                use_stealth=USE_STEALTH,
                randomize_order=RANDOMIZE_ORDER,
                rng_seed=RNG_SEED,
            )
        except Exception as exc:  # noqa: BLE001
            outcomes.append(
                TaskEvalOutcome(
                    task_id=cfg.task_id,
                    title=cfg.title,
                    baseline=None,
                    boosted=None,
                    artifacts_path=None,
                    error=str(exc),
                )
            )
            print(f"    run error: {exc}", flush=True)
            continue

        by_label = {r.label: r for r in results}
        b = by_label["baseline_no_artifacts"]
        p = by_label["with_scout_artifacts"]
        outcomes.append(
            TaskEvalOutcome(
                task_id=cfg.task_id,
                title=cfg.title,
                baseline=b,
                boosted=p,
                artifacts_path=ap,
                error=None,
            )
        )
        print(
            f"    done  steps {b.num_of_steps}→{p.num_of_steps}  "
            f"time {_cell_sec(b)}→{_cell_sec(p)} s",
            flush=True,
        )

    return outcomes


def _main_suite() -> int:
    try:
        outcomes = _run_suite()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2

    _print_suite_table(outcomes)

    if OUT_JSON_SUITE.strip():
        out_path = Path(OUT_JSON_SUITE.strip())
        if not out_path.is_absolute():
            out_path = _repo_root() / out_path
        suite_tasks: list[dict[str, Any]] = []
        for o in outcomes:
            if o.error:
                suite_tasks.append(
                    {
                        "task_id": o.task_id,
                        "title": o.title,
                        "error": o.error,
                    }
                )
            else:
                suite_tasks.append(
                    {
                        "task_id": o.task_id,
                        "title": o.title,
                        "artifacts_dir": str(o.artifacts_path) if o.artifacts_path else None,
                        "baseline": asdict(o.baseline) if o.baseline else None,
                        "playbook": asdict(o.boosted) if o.boosted else None,
                    }
                )
        payload = {
            "mode": "all",
            "recorded_at": datetime.now().astimezone().isoformat(),
            "tasks": suite_tasks,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(f"\nWrote suite JSON: {out_path}")

    return 0


def main() -> int:
    mode = EVAL_MODE.strip().lower()
    if mode == "all":
        return _main_suite()
    if mode != "single":
        print("EVAL_MODE must be 'single' or 'all'", file=sys.stderr)
        return 2

    try:
        cfg = _load_eval_run_config()
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    print(f"Task: {cfg.title} ({cfg.task_id})")
    print(f"URL: {cfg.url}")
    print(f"Artifacts: {cfg.artifacts_dir}")

    try:
        results, artifacts_path = _run_eval(
            url=cfg.url,
            objective=cfg.objective,
            artifacts_dir=cfg.artifacts_dir,
            max_artifact_chars=cfg.max_artifact_chars,
            use_stealth=USE_STEALTH,
            randomize_order=RANDOMIZE_ORDER,
            rng_seed=RNG_SEED,
        )
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001
        print(f"Run failed: {e}", file=sys.stderr)
        return 1

    by_label = {r.label: r for r in results}
    baseline = by_label["baseline_no_artifacts"]
    boosted = by_label["with_scout_artifacts"]
    _print_summary(baseline, boosted)

    if cfg.out_json:
        out_path = Path(cfg.out_json)
        if not out_path.is_absolute():
            out_path = _repo_root() / out_path
        payload = {
            "task_id": cfg.task_id,
            "task_title": cfg.title,
            "url": cfg.url.strip(),
            "artifacts_dir": str(artifacts_path),
            "recorded_at": datetime.now().astimezone().isoformat(),
            "arms": [asdict(r) for r in results],
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(f"\nWrote {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
