"""CLI: ask the agent a question (Strands + Nova Pro), guarded answer.

  python -m agent.ask "What is the current default Standard vCPU quota ..."
"""
from __future__ import annotations

import sys

from .core import ask


def main() -> int:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print('Ask something, e.g.:\n  python -m agent.ask '
              '"What is the current default Standard on-demand vCPU quota in us-east-1?"')
        return 1

    out = ask(question)
    g = out["guarded"]

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
