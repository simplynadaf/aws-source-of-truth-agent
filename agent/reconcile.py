"""
Deterministic reconciliation over structured awsFact records.

This is the part the model is NOT allowed to fake. Given a set of awsFact
records (as returned from the Sanity dataset/KB) that describe the SAME fact,
`reconcile()` decides the current winner using explicit rules - source
precedence and effective date - not the LLM's opinion. The agent's answer is
then guarded (see guard.py): if this function did not run, the answer is
reported as "Not verified".

A plain keyword search returns several rows and cannot rank them. This does.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional

# Source precedence for AWS "which value is current" questions. Higher wins.
# The live per-account console and the official pricing page beat static doc
# snapshots and (especially) third-party blogs.
SOURCE_PRECEDENCE: dict[str, int] = {
    "serviceQuotasConsole": 5,  # live, per-account, authoritative for quotas
    "pricingPage": 5,           # authoritative for prices
    "changelog": 4,             # release notes track the current floor
    "officialDocs": 3,          # official but can be a stale snapshot
    "blog": 1,                  # third-party, lowest trust
}


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


@dataclass
class ReconcileResult:
    service: str
    fact_type: str
    key: str
    region: str
    current_value: Optional[str]
    current_source: Optional[dict[str, Any]]
    unit: str = ""
    superseded_value: Optional[str] = None
    superseded_source: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    ran: bool = False  # proof the deterministic step executed
    considered: int = 0
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "service": self.service,
            "factType": self.fact_type,
            "key": self.key,
            "region": self.region,
            "currentValue": self.current_value,
            "currentSource": self.current_source,
            "supersededValue": self.superseded_value,
            "supersededSource": self.superseded_source,
            "reason": self.reason,
            "ran": self.ran,
            "considered": self.considered,
            "notes": self.notes,
        }


def _precedence(fact: dict[str, Any]) -> int:
    kind = ((fact.get("source") or {}).get("kind")) or ""
    return SOURCE_PRECEDENCE.get(kind, 0)


def reconcile(facts: list[dict[str, Any]]) -> ReconcileResult:
    """Pick the current winner among awsFact records for one fact.

    Rule order:
      1. Highest source precedence wins (console/pricing > docs > blog).
      2. Tie-break on the most recent effectiveDate.
      3. If a winner carries an explicit `supersedes` block, surface the losing
         value and the reason from the data (not invented).
    """
    if not facts:
        return ReconcileResult(
            service="", fact_type="", key="", region="",
            current_value=None, current_source=None,
            ran=True, considered=0,
            notes=["No matching facts were retrieved."],
        )

    def sort_key(f: dict[str, Any]) -> tuple[int, date]:
        d = _parse_date(f.get("effectiveDate")) or date.min
        return (_precedence(f), d)

    ordered = sorted(facts, key=sort_key, reverse=True)
    winner = ordered[0]
    src = winner.get("source") or {}

    result = ReconcileResult(
        service=winner.get("service", ""),
        fact_type=winner.get("factType", ""),
        key=winner.get("key", ""),
        region=winner.get("region", ""),
        current_value=winner.get("currentValue"),
        current_source=src,
        unit=winner.get("unit", ""),
        ran=True,
        considered=len(facts),
    )

    # Prefer an explicit supersedes block recorded in the winning fact.
    supersedes = winner.get("supersedes") or {}
    if supersedes.get("value"):
        result.superseded_value = supersedes.get("value")
        result.superseded_source = {
            "name": supersedes.get("stillShownBy"),
            "url": supersedes.get("stillShownUrl"),
        }
        result.reason = supersedes.get("reason")
    elif len(ordered) > 1:
        # Otherwise, the next-ranked distinct value is the superseded one.
        for other in ordered[1:]:
            if other.get("currentValue") != winner.get("currentValue"):
                result.superseded_value = other.get("currentValue")
                result.superseded_source = other.get("source")
                result.reason = (
                    f"Higher-precedence/newer source "
                    f"({src.get('kind') or 'unknown'}) wins over "
                    f"{(other.get('source') or {}).get('kind') or 'unknown'}."
                )
                break

    return result
