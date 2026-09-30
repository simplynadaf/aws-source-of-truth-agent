"""
Fail-closed answer guard.

The model is not allowed to have the last word on the verdict. The guard holds
the model's prose and releases it only if ALL of these hold:
  1. the deterministic reconcile step actually ran, and
  2. the model's stated current value matches the reconciled current value, and
  3. when the live AWS check shows DRIFT, the model does not misrepresent the
     reconciled record as the live value (a common, plausible-sounding slip):
     the model must mention BOTH the reconciled value and the live value, and
     must not claim the reconciled value "is" the live one.

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
    # A crisp one-line verdict first, so a reader (or a demo viewer) gets the
    # answer without parsing the whole block.
    live_val = (live or {}).get("liveValue")
    status = (live or {}).get("status")
    if status == "drift" and live_val is not None:
        verdict = (f"Verdict: the reconciled records say {rec.current_value} "
                   f"{rec.unit}".rstrip()
                   + f", but the live AWS API reports {live_val} right now "
                     f"(the recorded sources are stale for this account).")
    elif status == "agree":
        verdict = (f"Verdict: {rec.current_value} {rec.unit}".rstrip()
                   + " (reconciled record confirmed by the live AWS API).")
    else:
        verdict = f"Verdict: {rec.current_value} {rec.unit}".rstrip() + "."

    lines = [
        verdict,
        "",
        f"Current value (reconciled): {rec.current_value} {rec.unit}".rstrip(),
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
    status = (live or {}).get("status")
    live_val = (live or {}).get("liveValue")

    footer_bits = []
    if rec.ran:
        footer_bits.append(
            f"reconciled {rec.considered} structured fact(s) -> current = {rec.current_value}"
        )
    if live:
        footer_bits.append(f"live AWS check = {status}")
    footer = "Checked: " + "; ".join(footer_bits) if footer_bits else "Checked: nothing"

    def replaced(reason: str) -> dict[str, Any]:
        return {"answer": build_deterministic_answer(rec, live), "trusted": False,
                "reason": reason, "footer": footer}

    if not rec.ran:
        return replaced("reconcile_facts did not run")

    if not _contains_value(model_text, rec.current_value):
        return replaced("model answer did not match the reconciled current value")

    # Drift-aware honesty check: if the live API disagrees with the reconciled
    # record, the model must surface BOTH numbers and must not present the
    # reconciled value as the live one. Otherwise the deterministic answer wins.
    if status == "drift" and live_val is not None:
        if not _contains_value(model_text, str(live_val)):
            return replaced("live check shows drift but the model omitted the live value")
        # Catch the exact slip we observed: "is <live>, as verified live" while
        # the reconciled value is different - that misstates the record as live.
        misstates_live_as_current = re.search(
            rf"\bis\b[^.]*\b{re.escape(str(live_val))}\b[^.]*\bverified live\b",
            model_text or "", re.IGNORECASE,
        )
        if misstates_live_as_current:
            return replaced("model presented the live drift value as the reconciled current value")

    return {"answer": (model_text or "").strip(), "trusted": True,
            "reason": "model answer matches the reconciled verdict", "footer": footer}
