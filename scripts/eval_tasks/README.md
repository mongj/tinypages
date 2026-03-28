# Eval tasks (scout context boost)

Each **task** pairs a seed `url`, a prior swarm `artifacts_dir`, and an **objective** for the TinyFish agent.

## Why these tasks are “hard mode”

Merged scout output (`flows.json`) is mostly **shallow IA**: entry URLs, nav labels, flow names. It generally does **not** include:

- Exact prices, dated events, legal quotes, install commands, or API strings  
- Behavior after toggles, search routing, or “count what’s on screen”  
- Cross-page reconciliation

The eval objectives are written to **force** that kind of extraction. The **playbook** arm should still win on steps or time when hints shorten the hunt—even though **answers are not copy-pastable from the artifact JSON**.

## Layout

- `<id>.json` — metadata (`id`, `title`, `url`, `artifacts_dir`, and either `objective_file` or inline `objective`)
- `<id>.txt` — long-form objective when referenced by `objective_file`

Paths under `artifacts_dir` are relative to the **repository root**.

## Tasks

| ID | Site | What makes it harder than the playbook |
|----|------|------------------------------------------|
| `tinyfish_pricing` | tinyfish.ai | Toggle-state prices, doc domain, privacy URL, integration grid count |
| `docs_tinyfish_nav` | docs.tinyfish.ai | Verbatim pip/install lines, auth quote, rate-limit numbers |
| `hckr_explore` | hckr.cc → nushackers.org | Dated upcoming sessions, hackathon reg status, contribute paths |
| `wikipedia_portal` | www.wikipedia.org | Search routing for a fixed query, above-fold language count, non-Latin label |
| `iras_gst_info` | iras.gov.sg | Two cited IRAS pages: rate % + consumer display rules |

Each objective asks for a `playbook_used_how` field so you can see whether the agent credited the scout context.

## Add a new task

1. Copy an existing `.json` and change `id`, `title`, `url`, and `artifacts_dir`.
2. Write a `.txt` that demands **live** facts the swarm file does not already contain.
3. Optional: `out_json` (default `artifacts/eval_<id>.json`; `""` skips the report file), `max_artifact_chars`.

## Run

In `scripts/eval_scout_context_boost.py`:

- **`EVAL_MODE = "all"`** — runs every `scripts/eval_tasks/*.json`, prints an ASCII **before/after** table (baseline vs playbook), and writes **`OUT_JSON_SUITE`** (default `artifacts/eval_suite_latest.json`) with all runs.
- **`EVAL_MODE = "single"`** — runs one task from **`TASK_FILE`** (or inline config when `TASK_FILE` is empty), prints full per-arm output and optional per-task JSON.

`uv run --project src/backend python scripts/eval_scout_context_boost.py`
