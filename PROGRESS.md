# PROGRESS - AWS Source of Truth Agent (Sanity Challenge, Path One)

Last updated: 2026-09-28

## TL;DR
Python rewrite (Strands + Amazon Nova Pro on Bedrock) of the Path One entry is
well underway. The deterministic core is BUILT and TESTED against real AWS APIs.
Remaining: import seed into Sanity, run the full Nova agent end-to-end, build the
Knowledge Base + MCP endpoint, write the submission post, push to GitHub.

## Deadline
Sanity Challenge submissions due 2026-10-04 23:59 PDT. Tag: #sanitychallenge.

## Confirmed decisions
- Model: amazon.nova-pro-v1:0 on Bedrock. VERIFIED working in us-east-1 (Converse
  returned NOVA_OK; list-foundation-models shows ACTIVE, ON_DEMAND).
- Agent framework: Strands Agents (Python) v1.53.0 already installed.
  - APIs confirmed: strands.Agent, strands.tool, strands.models.BedrockModel,
    strands.tools.mcp.MCPClient (has native url=/headers= constructor + tool_filters
    + prefix - good for two-endpoint GROQ+KB design). mcp streamablehttp_client available.
- Language: Python for the agent; TypeScript only for the Sanity schema; NDJSON seed.
- Structured content: Sanity Context MCP + awsFact schema/Knowledge Base.
- Live cross-check: read-only AWS (Service Quotas / Pricing / EC2 / RDS) - the differentiator.

## Sanity project (created)
- Name: aws-source-of-truth
- Project ID: 0q5ohtvv  (HARD submission requirement)
- Org ID: op7a9oe06
- Plan: Growth Trial (Context + KB available)
- Dataset: production (NOT yet created/imported)
- Org token: stored in gitignored .env (SANITY_ORGANIZATION_TOKEN). Rotate after challenge.

## Architecture (best-of-best, locked)
Single Strands agent (Nova Pro) with 3 tools + a fail-closed guard:
1. fetch_candidate_facts(service, factType, region) -> GROQ over structured awsFacts.
2. reconcile_facts(facts) -> DETERMINISTIC winner by source precedence + effectiveDate.
   Model cannot fake this.
3. verify_live(...) -> read-only live AWS API cross-check: agree / drift / unavailable.
4. guard: releases model prose only if reconcile ran AND model value == reconciled
   value; else replaces with a deterministic answer. Footer states what was checked.
Plus: keyword TF-IDF baseline (control experiment), and a --no-llm offline path so
judges can run the core with no token (public dataset + local reconcile + live check).

## KEY INSIGHT (frame the writeup around this)
The live AWS API is just another - most authoritative - source. Live values on this
account DRIFT from the demo seed (EC2 vCPU live=16 vs seed 5; Lambda live=10 vs 1000;
RDS oldest major live=11 vs 13; R8g availability = AGREE). That drift is NOT a bug: the
agent reconciles the recorded sources, THEN checks reality and honestly reports when even
the reconciled record is stale. No other entry queries a live authoritative API, so none
can show live drift. Seed is clearly labeled demo/account-dependent. Keep seed as-is.

## Files built (under aws-source-of-truth-agent/)
- agent/config.py            env + friendly errors + retrieval-mode detection
- agent/reconcile.py         deterministic reconcile (precedence: console/pricing 5 >
                             changelog 4 > officialDocs 3 > blog 1; then effectiveDate)
- agent/sanity_client.py     credential-free GROQ HTTP client (public dataset) + fetch_facts
- agent/aws_live.py          read-only live check (service-quotas, pricing, ec2, rds)
- agent/guard.py             fail-closed guard + build_deterministic_answer
- agent/core.py              Strands + Nova Pro agent, 3 tools, ask() with guard + trail
- agent/ask.py               CLI: python -m agent.ask "question"
- agent/reconcile_offline.py CLI: python -m agent.reconcile_offline --service EC2 --type quota
- agent/baseline.py          CLI: python -m agent.baseline "query"  (TF-IDF control, stdlib)
- tests/test_core.py         5 offline tests - ALL PASSING
- requirements.txt           strands-agents, boto3, python-dotenv
- sanity/seed/aws-facts.ndjson  5 real-AWS facts (example.com URLs removed; real quota
                             codes L-1216C47A, L-B99A9384 for live-checking)
- .env                       secrets (gitignored)
- PROJECT-FACTS.md           IDs + stack

## Existing (from original TS build, kept)
- sanity/schemaTypes/awsFact.ts   typed schema (carries over)
- README.md                       [DONE 2026-09-29] rewritten for the Python/Strands/Nova stack
- .env.example                    [DONE 2026-09-29] fixed: stale OpenAI vars -> Bedrock/Nova + Sanity vars
- SUBMISSION-POST.md              [DONE 2026-09-29] Dev.to draft written (appreciation arc, A/B titles,
                                  project id 0q5ohtvv, real verified numbers, [IMAGE] placeholders)
- The old TypeScript agent (src/*.ts) is superseded by agent/*.py - to be removed/retired.

## Tests / verification done
- 5/5 deterministic unit tests pass (reconcile 5-over-32; guard replace wrong 32;
  guard trust correct 5; guard fail-closed no-reconcile; Lambda clean single-source).
- Live AWS cross-check hit REAL APIs read-only and returned real values (drift/agree).
- Full deterministic answer + live annotation renders correctly for EC2 vCPU.

## NEXT STEPS (in order)
1. [DONE 2026-09-28] Dataset `production` already existed + public; imported 5 seed facts
   via the Content Lake mutation API (write token). Verified 5 awsFacts readable on the
   public no-token GROQ path; EC2 conflict intact (current 5 / old 32).
2. [DONE 2026-09-28] Ran the FULL Strands + Nova Pro agent end-to-end on all 5 facts.
   All guard-TRUSTED. 2 drifts (EC2 5->live 16, RDS 13->live 11), 2 agrees (S3, Graviton),
   1 unavailable (Lambda). Fixed a Nova tool-arg-relay bug with a server-side fact-cache
   fallback in reconcile_facts (facts still real, model cannot fake). 5/5 unit tests pass.
   Full record: VERIFIED-nova-run.md.
3. Build the Knowledge Base in the Sanity dashboard (Context): purpose, dataset source
   + upload docs-sources/*, build entries, resolve the 32-vs-5 Issue, pin an Instruction.
   Create the Context MCP endpoint; put its URL in .env (SANITY_CONTEXT_MCP_URL).
   NEEDS: org-level API token with Context Viewer permission (from user).  <-- ONLY BLOCKER
4. Run agent against the live Context MCP (KB mode) + capture proof.
5. [README DONE 2026-09-29] [POST DRAFTED 2026-09-29 -> SUBMISSION-POST.md; needs the KB
   dashboard screenshots + cover image + final title pick before publish]. Optional web viewer.
6. Push public repo to GitHub. Optional: upload an Agent Session transcript.

## DECISIONS LOCKED (2026-09-28, made from research + real checks, not guesses)
- GitHub target: **simplynadaf** (CONFIRMED via `gh auth status` - authenticated account
  with repo/delete_repo/workflow scopes; git user simplynadaf/simplynadaf@gmail.com).
  Repo will be public: github.com/simplynadaf/aws-source-of-truth-agent.
- Web viewer: **YES - minimal static viewer** (plain HTML/Astro: question -> reconciled
  answer + both claims + sources + tool trail + live-drift banner). Reason: "Usability" is
  a scored criterion and the benchmark competitor (Errata Desk) has a polished live site.
  TIMEBOXED - build only AFTER the core end-to-end run is proven; never at the cost of the
  Oct 4 deadline. Recorded terminal + viewer screenshots is the acceptable fallback.
- Agent session: **both.** Primary technical proof = the Nova/Strands run with its tool
  trail. PLUS a supplementary OFFICIAL Claude Code session over the same Sanity Context MCP
  for the "encouraged" embed - `claude` (Claude Code) IS installed here and IS on DEV's
  supported agent-session list, so this is cheap, not scope creep.

## STILL TO CONFIRM (not blocking)
- Context visible in the Sanity dashboard (maybe under Labs) - verify during KB build step.

## Writeup framing locked (see RESEARCH-perception-and-views.md for full rationale)
Order: keyword search returns 3 numbers (SHOW the TF-IDF negative control) -> structured
KB reconciles to 1 cited answer (dashboard screenshots of the 32-vs-5 Issue resolution;
make the KB visibly load-bearing) -> then check the live authoritative AWS API and honestly
report drift (our unique, defensible edge). Label the demo seed loudly up front. A/B two
titles (one first-person/recognition, one search-optimized) + a result-showing cover.
