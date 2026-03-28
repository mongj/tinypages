"""Shared JSON shape for all scout goals (embedded in prompts) and light validation."""

from __future__ import annotations

import json
import re
from typing import Any

# Single schema description embedded in every scout goal so TinyFish returns parseable output.
OUTPUT_SCHEMA: str = """
Return ONLY valid JSON (no markdown fences, no commentary) matching exactly this structure:
{
  "flows": [
    {
      "id": "stable_snake_case_id",
      "name": "Human-readable flow name",
      "intent_category": "browse|buy|support|account|auth|commerce|legal|search|lead|content|dev|booking|locale|onboarding|careers|partner|community|location|configure|billing|investor|media|other",
      "confidence": 0.0,
      "entry_points": [
        {
          "label": "visible text or aria",
          "url": "absolute or relative URL string, or null if unknown",
          "location": "nav|footer|cta|hero|modal|breadcrumb|other"
        }
      ],
      "steps": [
        {
          "order": 1,
          "action": "navigate|click|type|scroll|submit|other",
          "description": "short natural language step"
        }
      ],
      "evidence": {
        "urls_seen": ["URLs you actually saw in the address bar or links"],
        "labels_seen": ["short UI strings that support this flow"],
        "notes": "optional grounding notes"
      },
      "blockers": [
        {
          "type": "captcha|login_required|payment_required|blocked|none|unknown",
          "detail": "what stopped or limited you"
        }
      ]
    }
  ],
  "global_blockers": [
    { "type": "string", "detail": "string" }
  ],
  "notes": "optional run-level notes"
}
""".strip()

PURPOSE_OUTPUT_SCHEMA: str = """
Return ONLY valid JSON (no markdown fences, no commentary) matching exactly this structure:
{
  "flows": [],
  "site_understanding": {
    "one_line_summary": "single sentence: what this site is for",
    "what_the_site_does": "1-3 short paragraphs for downstream agents",
    "primary_audiences": ["who the site appears to serve"],
    "offerings": ["products, services, or content types inferred from the UI"],
    "organization_or_brand": "visible org or brand name, or null if unclear",
    "confidence": 0.0,
    "evidence": {
      "urls_seen": ["URLs you actually saw"],
      "labels_seen": ["headings, nav labels, hero copy that support your summary"],
      "notes": "optional grounding notes"
    }
  },
  "global_blockers": [
    { "type": "string", "detail": "string" }
  ],
  "notes": "optional run-level notes"
}
Provide at least one non-empty string in one_line_summary or what_the_site_does. Do not invent user journeys; flows must be an empty array [].
""".strip()

SHARED_RULES: str = """
Termination and safety:
- Stop after at most 25 browser actions/steps; prefer shallow exploration over deep completion.
- Do NOT enter real credentials, complete real payments, or submit forms that charge money.
- If a CAPTCHA appears, stop immediately and record a global_blocker with type captcha.
- If you cannot reach a screen, still return partial flows with blockers explaining why.
- If nothing matches your scout's focus, return flows: [] and explain in notes.
""".strip()


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text


def _payload_has_scout_shape(parsed: dict[str, Any]) -> bool:
    return isinstance(parsed.get("flows"), list) or isinstance(parsed.get("site_understanding"), dict)


def _normalize_scout_payload(parsed: dict[str, Any]) -> dict[str, Any]:
    """Purpose scout may return site_understanding without flows; coerce flows to []."""
    out = dict(parsed)
    if isinstance(out.get("site_understanding"), dict) and not isinstance(out.get("flows"), list):
        out["flows"] = []
    return out


def parse_scout_result(result: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize TinyFish result: sometimes the model nests JSON in a string field."""
    if result is None:
        return None
    if isinstance(result, dict) and _payload_has_scout_shape(result):
        return _normalize_scout_payload(result)
    for key in ("output", "data", "json", "answer", "result"):
        raw = result.get(key)
        if isinstance(raw, str):
            try:
                parsed = json.loads(_strip_code_fence(raw))
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and _payload_has_scout_shape(parsed):
                return _normalize_scout_payload(parsed)
    # Single string payload
    if len(result) == 1:
        only = next(iter(result.values()))
        if isinstance(only, str):
            try:
                parsed = json.loads(_strip_code_fence(only))
                if isinstance(parsed, dict) and _payload_has_scout_shape(parsed):
                    return _normalize_scout_payload(parsed)
            except json.JSONDecodeError:
                pass
    return result if isinstance(result, dict) else None


def validate_parsed_shape(parsed: dict[str, Any] | None, scout_id: str | None = None) -> list[str]:
    """Return human-readable validation issues (empty list = OK enough for MVP)."""
    issues: list[str] = []
    if parsed is None:
        return ["missing_or_unparseable_payload"]
    if "flows" not in parsed:
        issues.append("missing_flows_key")
    elif not isinstance(parsed["flows"], list):
        issues.append("flows_not_a_list")
    else:
        for i, flow in enumerate(parsed["flows"]):
            if not isinstance(flow, dict):
                issues.append(f"flow_{i}_not_object")
                continue
            for field in ("id", "name"):
                if field not in flow:
                    issues.append(f"flow_{i}_missing_{field}")
    if scout_id == "purpose":
        su = parsed.get("site_understanding")
        if not isinstance(su, dict):
            issues.append("purpose_missing_site_understanding")
        else:
            one_line = su.get("one_line_summary") if isinstance(su.get("one_line_summary"), str) else ""
            what = su.get("what_the_site_does") if isinstance(su.get("what_the_site_does"), str) else ""
            if not (str(one_line).strip() or str(what).strip()):
                issues.append("purpose_site_understanding_missing_summary")
    if "global_blockers" in parsed and not isinstance(parsed["global_blockers"], list):
        issues.append("global_blockers_not_list")
    return issues
