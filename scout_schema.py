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
      "intent_category": "browse|buy|support|account|auth|commerce|legal|other",
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


def parse_scout_result(result: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize TinyFish result: sometimes the model nests JSON in a string field."""
    if result is None:
        return None
    if isinstance(result.get("flows"), list):
        return result
    for key in ("output", "data", "json", "answer", "result"):
        raw = result.get(key)
        if isinstance(raw, str):
            try:
                parsed = json.loads(_strip_code_fence(raw))
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get("flows"), list):
                return parsed
    # Single string payload
    if len(result) == 1:
        only = next(iter(result.values()))
        if isinstance(only, str):
            try:
                parsed = json.loads(_strip_code_fence(only))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
    return result if isinstance(result, dict) else None


def validate_parsed_shape(parsed: dict[str, Any] | None) -> list[str]:
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
    if "global_blockers" in parsed and not isinstance(parsed["global_blockers"], list):
        issues.append("global_blockers_not_list")
    return issues
