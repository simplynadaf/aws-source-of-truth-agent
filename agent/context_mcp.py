"""
Live Sanity Context MCP client (Knowledge Base mode) - stdlib only.

This is the agent's PRIMARY retrieval path. It talks to the hosted Context MCP
endpoint (SANITY_CONTEXT_MCP_URL) over JSON-RPC / streamable HTTP, using the
Knowledge Base tools the endpoint exposes:

  - initial_context        -> the KB id + entry outline
  - knowledge_base_search  -> ranked entry paths for a query
  - knowledge_base_read    -> full entry content by path

The point of the challenge: the answer must come through Sanity's STRUCTURED
content. So we search the KB, read the winning entry, and parse the reconciled
awsFact fields (current value, superseded value, source, effective date) out of
the KB entry. reconcile.py then still makes the deterministic call.

No third-party deps: the endpoint speaks plain JSON-RPC over HTTPS POST and
returns either application/json or a one-line text/event-stream `data:` frame,
so urllib is enough (this mirrors the verified curl handshake).
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Any, Optional

from .config import config

_PROTOCOL = "2025-06-18"


class ContextMCPError(RuntimeError):
    pass


def _post(payload: dict[str, Any], *, timeout: int = 40) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        config.mcp_url,
        data=body,
        headers={
            "Authorization": f"Bearer {config.sanity_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8").strip()
    # The endpoint may answer as SSE: one or more `data: {...}` lines. Take the last.
    if raw.startswith("event:") or "\ndata:" in raw or raw.startswith("data:"):
        line = [l for l in raw.splitlines() if l.startswith("data:")][-1]
        raw = line[len("data:"):].strip()
    return json.loads(raw)


def _call_tool(name: str, arguments: dict[str, Any]) -> str:
    """Call an MCP tool and return its text content (raises on error frames)."""
    resp = _post({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    if "error" in resp:
        raise ContextMCPError(resp["error"].get("message", str(resp["error"])))
    result = resp.get("result", {})
    if result.get("isError"):
        txt = _first_text(result)
        raise ContextMCPError(txt or "tool returned isError")
    return _first_text(result)


def _first_text(result: dict[str, Any]) -> str:
    for item in result.get("content", []) or []:
        if item.get("type") == "text":
            return item.get("text", "")
    return ""


def kb_id() -> str:
    """Discover the knowledge base id from initial_context (cached per process)."""
    global _KB_ID
    if _KB_ID:
        return _KB_ID
    text = _call_tool("initial_context", {})
    m = re.search(r"Knowledge base id:\s*`([^`]+)`", text)
    if not m:
        raise ContextMCPError("Could not find a knowledge base id in initial_context.")
    _KB_ID = m.group(1)
    return _KB_ID


_KB_ID: Optional[str] = None


def search(query: str) -> list[dict[str, Any]]:
    """Return ranked KB entries [{path, score, title}] for a query."""
    text = _call_tool("knowledge_base_search", {"knowledgeBase": kb_id(), "query": query})
    rows: list[dict[str, Any]] = []
    # Lines look like:  1. `ec2/quotas_and_limits` (score 20.99): Title...
    for line in text.splitlines():
        m = re.match(r"\s*\d+\.\s+`([^`]+)`\s+\(score\s+([0-9.]+)\)\s*:\s*(.*)", line)
        if m:
            rows.append({"path": m.group(1), "score": float(m.group(2)),
                         "title": m.group(3).strip()})
    return rows


def read(paths: list[str]) -> str:
    """Read full KB entry content for the given entry paths."""
    return _call_tool("knowledge_base_read", {"knowledgeBase": kb_id(), "paths": paths})
