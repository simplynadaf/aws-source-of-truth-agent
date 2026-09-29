"""
The control experiment: run a keyword/TF-IDF search over the SAME source text
the structured facts came from, and show that it returns several rows and
cannot tell you which value is current.

This is the other arm of the challenge's bar - "if a keyword search would have
gotten you the same answer, aim higher." We do not assert we cleared it; we run
the baseline and show the result.

  python -m agent.baseline "current standard vCPU quota"

Pure standard library (no sklearn) so a judge can run it with nothing installed.
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter

from . import sanity_client


def _doc_text(fact: dict) -> str:
    """The prose a keyword index would see: the human-readable fields + sources."""
    parts = [
        fact.get("service", ""), fact.get("factType", ""), fact.get("key", ""),
        f'{fact.get("currentValue","")} {fact.get("unit","")}',
        (fact.get("source") or {}).get("name", ""),
        (fact.get("notes") or ""),
    ]
    ss = fact.get("supersedes") or {}
    if ss:
        parts.append(f'{ss.get("value","")} {ss.get("stillShownBy","")} {ss.get("reason","")}')
    return " ".join(p for p in parts if p)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tfidf_rank(query: str, docs: list[str]) -> list[tuple[float, int]]:
    q = _tokens(query)
    tokenized = [_tokens(d) for d in docs]
    n = len(docs)
    df = Counter()
    for toks in tokenized:
        for t in set(toks):
            df[t] += 1

    def idf(t: str) -> float:
        return math.log((n + 1) / (df.get(t, 0) + 1)) + 1

    scores = []
    for i, toks in enumerate(tokenized):
        tf = Counter(toks)
        length = len(toks) or 1
        score = sum((tf.get(t, 0) / length) * idf(t) for t in q)
        scores.append((round(score, 4), i))
    return sorted(scores, reverse=True)


def main() -> int:
    query = " ".join(sys.argv[1:]).strip() or "current standard vCPU quota"
    facts = sanity_client.fetch_facts()
    if not facts:
        print("No facts in the public dataset yet (import the seed first).")
        return 1

    docs = [_doc_text(f) for f in facts]
    ranked = _tfidf_rank(query, docs)

    print(f'Keyword/TF-IDF baseline for: "{query}"\n')
    print("It can rank documents by term overlap, but it cannot tell you which")
    print("VALUE is current, or that two of these rows contradict each other:\n")
    for score, i in ranked[:5]:
        f = facts[i]
        cur = f.get("currentValue")
        old = (f.get("supersedes") or {}).get("value")
        conflict = f" (also carries an older value: {old})" if old else ""
        print(f"  {score:6.4f}  {f.get('service')}/{f.get('factType')}: "
              f"{f.get('key')[:48]} = {cur}{conflict}")

    print("\nThe baseline returns rows. It does not reconcile them. The structured")
    print("reconcile step (python -m agent.reconcile_offline) does.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
