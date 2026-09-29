"""
The AWS Source of Truth agent - Strands + Amazon Nova Pro (Bedrock).

Flow (best-of-best design):
  1. The agent reads candidate awsFact records from the Sanity Context MCP
     (structured content + Knowledge Base use - two of the judging criteria).
  2. It MUST call `reconcile_facts` - a deterministic tool that picks the
     current winner by source precedence + effective date. The model cannot
     fake this verdict.
  3. It MUST call `verify_live` - a read-only cross-check against the live AWS
     API (Service Quotas / Pricing / EC2 / RDS). The differentiator.
  4. A fail-closed guard releases the model's prose only if it matches the
     reconciled verdict; otherwise it is replaced by a deterministic answer.

Usage:
  python -m agent.ask "What is the current default On-Demand Standard vCPU
      quota in us-east-1, and does any source still show a different number?"
"""
from __future__ import annotations

import json
from typing import Any, Optional

from strands import Agent, tool
from strands.models import BedrockModel

from .config import config
from .reconcile import reconcile, ReconcileResult
from .aws_live import verify_live as _verify_live
from . import sanity_client

# Captured out-of-band so the guard and the tool-trail can see what really ran,
# independent of what the model claims it did.
_LAST_RECONCILE: dict[str, Any] = {}
_LAST_LIVE: dict[str, Any] = {}
_LAST_FACTS: list[dict[str, Any]] = []  # last real fetch, so reconcile never depends on the model relaying JSON
_TRAIL: list[str] = []


SYSTEM_PROMPT = """You are the AWS Source of Truth agent.

You answer AWS configuration questions (service quotas, limits, prices, version
support, regional availability) using ONLY structured content retrieved through
your tools. The content was reconciled ahead of time from primary AWS sources.

Follow this procedure every time, in order:
1. Retrieve the candidate facts for the question with `fetch_candidate_facts`
   (filter by service, factType, region when you can).
2. Call `reconcile_facts` with those facts to get the deterministic current
   value. Never decide the winner yourself.
3. Call `verify_live` with the reconciled fact to cross-check the live AWS API.
4. Answer concisely. State the current value first with its source, then, if a
   value was superseded, show the old value, where it is still shown, and why
   the current one wins. Report the live check result (agree / drift /
   unavailable) plainly.

Rules (non-negotiable):
- Ground every number in retrieved content. Never answer AWS values from your
  own training knowledge.
- If reconcile_facts returns no current value, say it is not verified.
- You are read-only. Never suggest changing data or running a write.
- Be concise. No em dashes."""


@tool
def fetch_candidate_facts(service: str = "", fact_type: str = "",
                          region: str = "") -> str:
    """Fetch candidate awsFact records for a question, filtered on typed fields.

    Args:
        service: AWS service, e.g. EC2, S3, Lambda, RDS.
        fact_type: one of quota, limit, price, versionSupport, regionalAvailability.
        region: AWS region code, e.g. us-east-1.
    Returns JSON list of matching structured facts.
    """
    facts = sanity_client.fetch_facts(
        service=service or None, fact_type=fact_type or None, region=region or None
    )
    _LAST_FACTS.clear()
    _LAST_FACTS.extend(facts)
    _TRAIL.append(f"fetch_candidate_facts(service={service!r}, fact_type={fact_type!r}, region={region!r}) -> {len(facts)} rows")
    return json.dumps(facts)


@tool
def reconcile_facts(facts_json: str = "") -> str:
    """Deterministically pick the current winner among awsFact records.

    Args:
        facts_json: JSON list of awsFact records (from fetch_candidate_facts).
            If omitted or empty, the facts from the most recent
            fetch_candidate_facts call are used, so the deterministic verdict
            never depends on the model relaying the JSON correctly.
    Returns JSON with the reconciled current value, superseded value, and reason.
    """
    facts: list[dict[str, Any]] = []
    try:
        parsed = json.loads(facts_json) if isinstance(facts_json, str) and facts_json.strip() else facts_json
        if isinstance(parsed, list):
            facts = parsed
        elif isinstance(parsed, dict):
            facts = [parsed]
    except (json.JSONDecodeError, TypeError):
        facts = []
    # Fall back to the real last fetch if the model passed nothing usable.
    used_fallback = False
    if not facts and _LAST_FACTS:
        facts = list(_LAST_FACTS)
        used_fallback = True
    rec = reconcile(facts)
    _LAST_RECONCILE.clear()
    _LAST_RECONCILE.update(rec.as_dict())
    _LAST_RECONCILE["_obj"] = rec
    _TRAIL.append(
        f"reconcile_facts(n={len(facts)}{', from last fetch' if used_fallback else ''}) "
        f"-> current={rec.current_value}"
    )
    return json.dumps(rec.as_dict())


@tool
def verify_live(service: str, fact_type: str, region: str, claimed_value: str,
                quota_code: str = "", key: str = "") -> str:
    """Cross-check a reconciled value against the live AWS API (read-only).

    Args:
        service: AWS service (EC2, S3, Lambda, RDS).
        fact_type: quota, limit, price, versionSupport, regionalAvailability.
        region: AWS region code.
        claimed_value: the reconciled current value to test.
        quota_code: Service Quotas code when applicable (e.g. L-1216C47A).
        key: the fact key (used for regionalAvailability instance type).
    Returns JSON with status agree/drift/unavailable and the live value.
    """
    res = _verify_live(service, fact_type, region, claimed_value,
                       quota_code=quota_code or None, key=key or None)
    _LAST_LIVE.clear()
    _LAST_LIVE.update(res)
    _TRAIL.append(f"verify_live({service}/{fact_type}) -> {res.get('status')}")
    return json.dumps(res)


def build_agent() -> Agent:
    model = BedrockModel(model_id=config.model_id, region_name=config.region)
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[fetch_candidate_facts, reconcile_facts, verify_live],
    )


def ask(question: str) -> dict[str, Any]:
    """Run the agent, then apply the fail-closed guard. Returns a result dict."""
    from .guard import guard_answer

    _TRAIL.clear()
    _LAST_RECONCILE.clear()
    _LAST_LIVE.clear()
    _LAST_FACTS.clear()

    agent = build_agent()
    result = agent(question)
    model_text = str(result)

    rec_obj: Optional[ReconcileResult] = _LAST_RECONCILE.get("_obj")
    if rec_obj is None:
        rec_obj = ReconcileResult(service="", fact_type="", key="", region="",
                                  current_value=None, current_source=None,
                                  ran=False)
    live = dict(_LAST_LIVE) if _LAST_LIVE else None

    guarded = guard_answer(model_text, rec_obj, live)
    return {
        "question": question,
        "model_text": model_text,
        "guarded": guarded,
        "trail": list(_TRAIL),
        "project_id": config.project_id,
    }
