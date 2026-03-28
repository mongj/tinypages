"""Aggregate failure taxonomy and validation stats from scout artifacts (for manual rubric scoring)."""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_assessment(artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = Counter(str(a.get("status")) for a in artifacts)
    val_issues: Counter[str] = Counter()
    for a in artifacts:
        for issue in a.get("validation_issues") or []:
            val_issues[str(issue)] += 1

    attempts_profile: Counter[str] = Counter()
    for a in artifacts:
        for att in a.get("attempts") or []:
            if isinstance(att, dict):
                attempts_profile[str(att.get("browser_profile", ""))] += 1

    flow_counts: list[int] = []
    for a in artifacts:
        p = a.get("result_payload")
        if isinstance(p, dict) and isinstance(p.get("flows"), list):
            flow_counts.append(len(p["flows"]))
        else:
            flow_counts.append(0)

    return {
        "scout_count": len(artifacts),
        "status_histogram": dict(statuses),
        "validation_issue_histogram": dict(val_issues),
        "attempts_by_browser_profile": dict(attempts_profile),
        "flows_per_scout": flow_counts,
        "total_flows_extracted": sum(flow_counts),
        "notes": (
            "Use eval/rubric.json expected_flows to manually mark found/missed/wrong per site, "
            "then compute recall against total_flows_extracted and merged flows.json."
        ),
    }
