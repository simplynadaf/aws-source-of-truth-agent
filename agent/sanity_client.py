"""
Minimal Sanity read client over the public GROQ HTTP API.

Used two ways:
  1. The offline/`--no-llm` path and tests fetch candidate awsFact records
     WITHOUT needing a Context token - a public dataset answers anonymous
     GROQ queries. This is what lets a judge run the deterministic path.
  2. A fallback if the Context MCP endpoint is not configured yet.

The agent's *primary* retrieval is the Sanity Context MCP (see agent.py); this
client is the credential-free complement, not a replacement.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from .config import config

API_VERSION = "v2025-02-19"


def _query_url(project_id: str, dataset: str, groq: str) -> str:
    q = urllib.parse.quote(groq, safe="")
    return (
        f"https://{project_id}.api.sanity.io/{API_VERSION}"
        f"/data/query/{dataset}?query={q}"
    )


def groq(query: str, *, project_id: str | None = None, dataset: str | None = None,
         timeout: int = 20) -> list[dict[str, Any]]:
    """Run an anonymous GROQ query against a public dataset. Returns result rows."""
    pid = project_id or config.project_id
    ds = dataset or config.dataset
    url = _query_url(pid, ds, query)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("result", []) or []


def fetch_facts(service: str | None = None, fact_type: str | None = None,
                region: str | None = None, **kw: Any) -> list[dict[str, Any]]:
    """Fetch awsFact records, optionally filtered by service/factType/region.

    Filtering happens in GROQ on typed fields - the whole point of structured
    content. A keyword search could not do this cleanly.
    """
    clauses = ['_type == "awsFact"']
    params: list[str] = []
    if service:
        clauses.append(f'service == "{service}"')
    if fact_type:
        clauses.append(f'factType == "{fact_type}"')
    if region:
        # match the region or global facts
        clauses.append(f'(region == "{region}" || region == "global")')
    filt = " && ".join(clauses)
    projection = (
        "{service, factType, key, quotaCode, currentValue, unit, region, "
        "effectiveDate, source, supersedes, notes}"
    )
    return groq(f"*[{filt}]{projection}", **kw)
