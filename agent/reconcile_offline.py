"""CLI: deterministic, NO-LLM path so a judge can run the core with no token.

Fetches candidate facts from the PUBLIC Sanity dataset over anonymous GROQ,
reconciles them deterministically, and live-checks against AWS. No model, no
Context token required.

  python -m agent.reconcile_offline --service EC2 --type quota --region us-east-1
"""
from __future__ import annotations

import argparse

from . import sanity_client
from .aws_live import verify_live
from .reconcile import reconcile
from .guard import build_deterministic_answer


def main() -> int:
    p = argparse.ArgumentParser(description="Deterministic reconcile (no LLM).")
    p.add_argument("--service", default="")
    p.add_argument("--type", dest="fact_type", default="")
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--no-live", action="store_true", help="skip the live AWS check")
    args = p.parse_args()

    facts = sanity_client.fetch_facts(
        service=args.service or None,
        fact_type=args.fact_type or None,
        region=args.region or None,
    )
    print(f"Fetched {len(facts)} structured fact(s) from the public dataset.")
    rec = reconcile(facts)

    live = None
    if not args.no_live and rec.current_value is not None:
        winner = next((f for f in facts if f.get("currentValue") == rec.current_value), {})
        live = verify_live(
            rec.service, rec.fact_type, rec.region, rec.current_value,
            quota_code=winner.get("quotaCode"), key=rec.key,
        )

    print("\n=== Deterministic answer (no model involved) ===\n")
    print(build_deterministic_answer(rec, live))
    print(f"\n[reconcile ran: {rec.ran}; considered {rec.considered} fact(s)]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
