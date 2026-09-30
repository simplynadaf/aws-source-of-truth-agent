"""CLI: import the seed awsFacts into the Sanity dataset (one-time / on change).

Reads sanity/seed/aws-facts.ndjson and createOrReplace's each doc into the
`production` dataset via the Content Lake mutation API. Needs a WRITE token
(dataset editor/developer), passed as SANITY_WRITE_TOKEN so it never has to sit
in .env next to the Context Viewer token.

  SANITY_WRITE_TOKEN=sk... python -m agent.import_seed
  SANITY_WRITE_TOKEN=sk... python -m agent.import_seed --only fact-ebs-gp3-max-iops

After importing new/changed facts, rebuild the Knowledge Base entries in the
Sanity dashboard (Context -> the KB -> Rebuild) so the Context MCP serves them.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from typing import Any

from .config import config

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "sanity", "seed", "aws-facts.ndjson")


def _load_seed() -> list[dict[str, Any]]:
    with open(SEED) as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="Import seed awsFacts into Sanity.")
    p.add_argument("--only", nargs="*", default=None,
                   help="import only these _id prefixes (default: all)")
    args = p.parse_args()

    token = os.environ.get("SANITY_WRITE_TOKEN", "").strip()
    if not token:
        print("Set SANITY_WRITE_TOKEN to a dataset write token (editor/developer). "
              "The Context Viewer token in .env cannot write.")
        return 2

    facts = _load_seed()
    if args.only:
        facts = [f for f in facts if any(f["_id"].startswith(o) for o in args.only)]
    if not facts:
        print("No matching facts to import.")
        return 1

    mutations = {"mutations": [{"createOrReplace": f} for f in facts]}
    url = (f"https://{config.project_id}.api.sanity.io/v2021-06-07"
           f"/data/mutate/{config.dataset}?returnIds=true")
    req = urllib.request.Request(
        url, data=json.dumps(mutations).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    ids = out.get("results", []) or out.get("documentIds", [])
    print(f"Imported {len(facts)} fact(s) into {config.dataset}:")
    for f in facts:
        print(f"  - {f['_id']} ({f['service']}/{f['factType']} = {f['currentValue']})")
    print("\nNext: rebuild the Knowledge Base entries in the Sanity dashboard so the "
          "Context MCP serves the new facts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
