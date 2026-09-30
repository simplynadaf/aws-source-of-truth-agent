"""Offline unit tests for the deterministic core (no network, no model)."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.reconcile import reconcile
from agent.guard import guard_answer, build_deterministic_answer

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "sanity", "seed", "aws-facts.ndjson")


def load_seed() -> list[dict]:
    with open(SEED) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_reconcile_ec2_vcpu_picks_console_over_docs():
    facts = [f for f in load_seed()
             if f["service"] == "EC2" and f["factType"] == "quota"]
    rec = reconcile(facts)
    assert rec.ran is True
    assert rec.current_value == "5", rec.current_value
    assert rec.superseded_value == "32", rec.superseded_value
    assert "console" in (rec.current_source or {}).get("kind", "").lower()
    print("PASS: EC2 vCPU reconciles to 5, supersedes 32")


def test_guard_replaces_when_model_wrong():
    facts = [f for f in load_seed()
             if f["service"] == "EC2" and f["factType"] == "quota"]
    rec = reconcile(facts)
    # model hallucinates 32 (the OLD value)
    out = guard_answer("The current quota is 32 vCPUs.", rec, None)
    assert out["trusted"] is False
    assert "5" in out["answer"]
    print("PASS: guard replaces a wrong model answer (32) with deterministic 5")


def test_guard_trusts_when_model_right():
    facts = [f for f in load_seed()
             if f["service"] == "EC2" and f["factType"] == "quota"]
    rec = reconcile(facts)
    out = guard_answer("The current value is 5 vCPUs, per the console.", rec, None)
    assert out["trusted"] is True
    print("PASS: guard trusts a correct model answer (5)")


def test_guard_catches_drift_misstatement():
    """On drift, the model must not present the live value AS the current value."""
    facts = [f for f in load_seed()
             if f["service"] == "EC2" and f["factType"] == "quota"]
    rec = reconcile(facts)  # current = 5
    live = {"status": "drift", "liveValue": "16",
            "detail": "Service Quotas ec2/L-1216C47A = 16", "api": "service-quotas"}
    # The exact slip observed from Nova: states the live value "is ... verified live".
    bad = ("The current default On-Demand Standard vCPU quota in us-east-1 is 16, "
           "as verified live. The older value of 32 has been superseded. The "
           "reconciled value of 5 did not match.")
    out = guard_answer(bad, rec, live)
    assert out["trusted"] is False, out
    assert "reconciled records say 5" in out["answer"]
    assert "live AWS API reports 16" in out["answer"]
    print("PASS: guard catches the 'live value is current' drift misstatement")


def test_guard_trusts_honest_drift_answer():
    """An answer that surfaces BOTH numbers correctly is trusted on drift."""
    facts = [f for f in load_seed()
             if f["service"] == "EC2" and f["factType"] == "quota"]
    rec = reconcile(facts)  # current = 5
    live = {"status": "drift", "liveValue": "16",
            "detail": "Service Quotas ec2/L-1216C47A = 16", "api": "service-quotas"}
    good = ("The reconciled records say 5 vCPUs (Service Quotas console), and 32 is "
            "a superseded snapshot. The live AWS API currently reports 16, so this "
            "account has drifted from the recorded value.")
    out = guard_answer(good, rec, live)
    assert out["trusted"] is True, out
    print("PASS: guard trusts an honest drift answer that shows both 5 and 16")


def test_guard_fails_closed_when_no_reconcile():
    from agent.reconcile import ReconcileResult
    rec = ReconcileResult(service="", fact_type="", key="", region="",
                          current_value=None, current_source=None, ran=False)
    out = guard_answer("Some confident nonsense.", rec, None)
    assert out["trusted"] is False
    assert "Not verified" in out["answer"]
    print("PASS: guard fails closed when reconcile did not run")


def test_lambda_single_source_no_supersede():
    facts = [f for f in load_seed()
             if f["service"] == "Lambda"]
    rec = reconcile(facts)
    assert rec.current_value == "1000"
    assert rec.superseded_value is None
    print("PASS: Lambda clean single-source (1000, no conflict)")


def test_keyword_baseline_ranks_wrong_but_reconcile_right():
    """The challenge bar: show a case where keyword search returns the WRONG
    answer and structured reconcile returns the right one."""
    from agent import baseline
    facts = [f for f in load_seed()
             if f["service"] == "EBS" and f["factType"] == "limit"]
    assert len(facts) == 2, "expected the current + superseded EBS gp3 IOPS rows"

    # A natural keyword query a user would type.
    query = "maximum IOPS per volume general purpose SSD"
    docs = [baseline._doc_text(f) for f in facts]
    ranked = baseline._tfidf_rank(query, docs)
    keyword_top = facts[ranked[0][1]]["currentValue"]

    rec = reconcile(facts)

    # Keyword search is fooled (ranks the stale 16000 first); reconcile is not.
    assert keyword_top == "16000", f"keyword top was {keyword_top}, expected the wrong 16000"
    assert rec.current_value == "80000", rec.current_value
    assert rec.superseded_value == "16000", rec.superseded_value
    print("PASS: keyword search ranks WRONG (16000); reconcile picks RIGHT (80000)")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\nAll {len(tests)} deterministic tests passed.")
