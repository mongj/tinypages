"""Merge and dedupe flow records from multiple scout artifacts."""

from __future__ import annotations

import re
from typing import Any


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _flow_dedupe_key(flow: dict[str, Any]) -> str:
    name = _norm(str(flow.get("name", "")))
    eps = flow.get("entry_points") or []
    first_url = ""
    if isinstance(eps, list) and eps:
        ep0 = eps[0]
        if isinstance(ep0, dict):
            first_url = _norm(str(ep0.get("url") or ""))
    fid = _norm(str(flow.get("id", "")))
    return f"{name}|{first_url}|{fid}"


def _site_understanding_from_artifacts(artifacts: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick ``site_understanding`` from the ``purpose`` scout payload, if present."""
    chosen: dict[str, Any] | None = None
    run_id: Any = None
    for art in artifacts:
        if str(art.get("scout_id", "")) != "purpose":
            continue
        p = art.get("result_payload")
        if not isinstance(p, dict):
            continue
        su = p.get("site_understanding")
        if not isinstance(su, dict):
            continue
        chosen = dict(su)
        run_id = art.get("run_id")
    if chosen is None:
        return None
    chosen["_provenance"] = {"scout_id": "purpose", "run_id": run_id}
    return chosen


def merge_flow_artifacts(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    """
    artifacts: list of saved run records, each with optional parsed.result_payload (dict with flows).
    Returns merged index with provenance per flow.
    """
    by_key: dict[str, dict[str, Any]] = {}
    for art in artifacts:
        scout_id = str(art.get("scout_id", "unknown"))
        run_id = art.get("run_id")
        payload = art.get("result_payload")
        if not isinstance(payload, dict):
            continue
        flows = payload.get("flows")
        if not isinstance(flows, list):
            continue
        for flow in flows:
            if not isinstance(flow, dict):
                continue
            key = _flow_dedupe_key(flow)
            if key not in by_key:
                copy = dict(flow)
                copy["_provenance"] = [{"scout_id": scout_id, "run_id": run_id}]
                by_key[key] = copy
            else:
                prov = by_key[key].setdefault("_provenance", [])
                if isinstance(prov, list):
                    prov.append({"scout_id": scout_id, "run_id": run_id})
    merged_flows = list(by_key.values())
    global_notes: list[str] = []
    for art in artifacts:
        p = art.get("result_payload")
        if isinstance(p, dict) and isinstance(p.get("notes"), str) and p["notes"].strip():
            global_notes.append(f"[{art.get('scout_id')}]: {p['notes'].strip()}")
    site_understanding = _site_understanding_from_artifacts(artifacts)
    out: dict[str, Any] = {}
    if site_understanding is not None:
        out["site_understanding"] = site_understanding
    out["merged_flows"] = merged_flows
    out["merge_count"] = len(merged_flows)
    out["source_runs"] = len(artifacts)
    out["collected_notes"] = global_notes
    return out
