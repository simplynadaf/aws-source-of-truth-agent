"""CLI: ask the agent a question (Strands + Nova Pro), guarded answer.

  python -m agent.ask "What is the current default Standard vCPU quota ..."
  python -m agent.ask --json "..."     # machine-readable output
"""
from __future__ import annotations

import json
import sys

from .core import ask


def main() -> int:
    argv = sys.argv[1:]
    as_json = False
    if argv and argv[0] in ("--json", "-j"):
        as_json = True
        argv = argv[1:]
    question = " ".join(argv).strip()
    if not question:
        print('Ask something, e.g.:\n  python -m agent.ask '
              '"What is the current default Standard on-demand vCPU quota in us-east-1?"')
        return 1

    out = ask(question, quiet=as_json)
    g = out["guarded"]

    if as_json:
        print(json.dumps({
            "question": out["question"],
            "answer": g["answer"],
            "trusted": g["trusted"],
            "guard_reason": g["reason"],
            "checked": g["footer"],
            "tool_trail": out["trail"],
            "project_id": out["project_id"],
        }, indent=2))
        return 0

    print("\n=== Answer ===\n")
    print(g["answer"])
    print(f"\n[{'TRUSTED model answer' if g['trusted'] else 'GUARD REPLACED model answer'}: {g['reason']}]")
    print(g["footer"])

    if out["trail"]:
        print("\n=== Tool trail (proof it read structured content) ===")
        for step in out["trail"]:
            print(f"  - {step}")

    print(f"\nSanity project id for submission: {out['project_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
