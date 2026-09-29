"""
Fail-closed answer guard.

The model is not allowed to have the last word on the verdict. The guard holds
the model's prose and releases it only if:
  1. the deterministic reconcile step actually ran, and
  2. the model's stated current value matches the reconciled current value.

Otherwise the model's answer is replaced wholesale by a deterministic answer
built from the reconcile result (plus the live cross-check). A footer always
states exactly what was checked, so a reader can tell the verdict came from the
structured data, not the model's memory.

This mirrors the pattern the strongest challenge entries used: a plausible,
confident LLM sentence that the data does not support gets caught here.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from .reconcile import ReconcileResult


def _contains_value(text: str, value: Optional[str]) -> bool:
    if not value:
        return False
    return re.search(re.escape(str(value)), text or "", re.IGNORECASE) is not None


def build_deterministic_answer(rec: ReconcileResult,
                               live: dict[str, Any] | None) -> str:
    """The answer we trust: built from the reconcile result, not the model."""
    if not rec.current_value:
        return ("Not verified: no matching structured fact was retrieved, so "
                "there is nothing to reconcile. I will not answer from memory.")

    src = rec.current_source or {}
    lines = [
        f"Current value: {rec.current_value} {rec.unit}".rstrip(),
        f"  source: {src.get('name')} ({src.get('url')})",
    ]
    if rec.superseded_value:
        ss = rec.superseded_source or {}
        lines.append(f"Superseded value still seen: {rec.superseded_value}")
        if ss.get("name") or ss.get("url"):
            lines.append(f"  shown by: {ss.get('name')} {('(' + ss['url'] + ')') if ss.get('url') else ''}".rstrip())
        if rec.reason:
            lines.append(f"  why current wins: {rec.reason}")
    if live:
        status = live.get("status")
        if status == "agree":
            lines.append(f"Live AWS check: AGREE - {live.get('detail')}")
        elif status == "drift":
            lines.append(f"Live AWS check: DRIFT - {live.get('detail')} "
                         f"(live differs from the reconciled value)")
        else:
            lines.append(f"Live AWS check: unavailable - {live.get('detail')}")
    return "\n".join(lines)


def guard_answer(model_text: str, rec: ReconcileResult,
                 live: dict[str, Any] | None) -> dict[str, Any]:
    """Decide whether to trust the model's prose or replace it.

    Returns {answer, trusted (bool), reason, footer}.
    """
    footer_bits = []
    if rec.ran:
        footer_bits.append(
            f"reconciled {rec.considered} structured fact(s) -> current = {rec.current_value}"
        )
    if live:
        footer_bits.append(f"live AWS check = {live.get('status')}")
    footer = "Checked: " + "; ".join(footer_bits) if footer_bits else "Checked: nothing"

    if not rec.ran:
        det = build_deterministic_answer(rec, live)
        return {"answer": det, "trusted": False,
                "reason": "reconcile_facts did not run", "footer": footer}

    if not _contains_value(model_text, rec.current_value):
        det = build_deterministic_answer(rec, live)
        return {"answer": det, "trusted": False,
                "reason": "model answer did not match the reconciled current value",
                "footer": footer}

    return {"answer": (model_text or "").strip(), "trusted": True,
            "reason": "model answer matches the reconciled verdict", "footer": footer}
