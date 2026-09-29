# VERIFIED: full Strands + Nova Pro run end-to-end (2026-09-28)

Model: amazon.nova-pro-v1:0 on Bedrock, us-east-1. AWS account 175662053988.
Sanity project 0q5ohtvv, dataset `production` (public), 5 awsFacts imported.
Retrieval path used: public GROQ over the public dataset (Context MCP endpoint not
created yet - that is the next step; the code prefers the MCP URL when set).

All numbers below came from real tool output. Nothing invented. Read-only throughout.

## Result matrix (all 5 facts, all guard-TRUSTED)

| Fact | Reconciled current (from record) | Superseded (still shown) | Live AWS | Guard |
|------|----------------------------------|--------------------------|----------|-------|
| EC2 On-Demand Standard vCPU quota (us-east-1) | 5 (Service Quotas console) | 32 (older EC2 user-guide snapshot) | 16 | DRIFT, TRUSTED |
| Lambda concurrent executions (us-east-1)      | 1000 (Lambda Dev Guide)   | none | unavailable | TRUSTED |
| S3 Standard storage price /GB-mo (us-east-1)  | 0.023 (S3 pricing page)   | 0.021 (stale blog) | 0.023 | AGREE, TRUSTED |
| RDS PostgreSQL oldest supported major         | 13 (release notes)        | 11 (older tutorial) | 11 | DRIFT, TRUSTED |
| Graviton4 (R8g) availability (us-east-1)      | Available (instance types)| none | Available | AGREE, TRUSTED |

Two DRIFTs, two AGREEs, one unavailable. This is the honest mix the writeup uses:
the reconciled record is the best answer from the documents, and the live check shows
when even that record is stale (EC2 5 vs live 16; RDS floor 13 vs live 11).

## Flagship transcript (EC2 vCPU) - the story in one run
Nova drove all three tools in order:
  - fetch_candidate_facts(service='EC2', fact_type='quota', region='us-east-1') -> 1 rows
  - reconcile_facts(n=1, from last fetch) -> current=5
  - verify_live(EC2/quota) -> drift
Guard: TRUSTED (model answer contained the reconciled value 5 AND reported the live drift to 16).
Footer: "Checked: reconciled 1 structured fact(s) -> current = 5; live AWS check = drift".
Three numbers on screen: docs 32 -> reconciled 5 -> live 16.

## Bug found and fixed during this run (documented for the writeup "what didn't work")
First run: fetch returned 1 row but reconcile received n=0, so the guard fail-closed to
"Not verified". Root cause: Amazon Nova does not reliably relay a large JSON tool result
as the next tool's string argument (a known Nova tool-calling quirk). The guard did the
RIGHT thing (refused rather than guessed), which is itself evidence the fail-closed design
works. Fix: cache the last real fetch server-side (_LAST_FACTS) and have reconcile_facts
fall back to it when the model passes empty/malformed JSON. The facts still come from the
real Sanity fetch, not the model, so nothing can be faked. Trail now shows
"reconcile_facts(n=1, from last fetch)". 5/5 unit tests still pass after the change.

## Reproduction (no AWS write, read-only)
    cd aws-source-of-truth-agent
    python3 -m agent.ask "What is the current default On-Demand Standard vCPU quota in us-east-1, and does any source still show a different number?"
Deterministic-only (no LLM, no AWS write, uses public dataset):
    python3 -m agent.reconcile_offline --service EC2 --type quota
