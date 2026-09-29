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


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"\nAll {len(tests)} deterministic tests passed.")
