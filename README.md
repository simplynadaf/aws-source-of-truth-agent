# AWS Source of Truth Agent

A **Path One** submission for the [Sanity Challenge](https://dev.to/challenges/sanity-2026-09-16).

An agent that answers **"which AWS value is actually current?"** when the docs, the
pricing page, and the Service Quotas console disagree. It reads a typed AWS fact
dataset through **Sanity Context** (a Knowledge Base, or public GROQ), reconciles the
conflicting sources **deterministically**, and returns the current value **with both
claims and their sources**. Then it does the thing no recorded-source agent can: it
asks the **live authoritative AWS API** whether even the reconciled record is still true,
and honestly reports the drift.

This clears the challenge's bar - *"an agent that only works because the content was
structured"* - because a plain keyword search over the same sources returns several
different numbers and no way to tell which is live (we ship that negative control; see
`agent/baseline.py`). The typed `awsFact` schema lets the agent filter on real fields
(`service`, `region`, `factType`) and reconcile by **source precedence + effectiveDate**
instead of fuzzy-matching prose.

> Related to the contradiction-desk submissions in the challenge (MTG errata, travel
> fees), but taken into the AWS / DevOps domain and extended with a **live** system-of-record
> cross-check - so we can show drift against *reality*, not only drift between documents.

---

## Stack

- **Model:** Amazon **Nova Pro** (`amazon.nova-pro-v1:0`) on **Amazon Bedrock**, us-east-1.
- **Agent framework:** **Strands Agents** (Python). Three tools + a fail-closed guard.
- **Structured content:** a typed **`awsFact`** schema in **Sanity**, read via **Context**
  (Knowledge Base mode) or the credential-free public GROQ path.
- **Live cross-check:** read-only AWS Service Quotas / Price List / EC2 / RDS.
- Sanity project id: **`0q5ohtvv`** (the submission's hard requirement).

The model orchestrates the tools and phrases the answer. It **cannot** pick which value
wins - a deterministic reconcile does that, and a guard releases the prose only if it
matches the reconciled value. That division of labour is the integrity story.

---

## What's in here

```
agent/
  config.py            # env loading with friendly errors + retrieval-mode detection
  sanity_client.py     # credential-free GROQ client over the PUBLIC dataset + fetch_facts
  reconcile.py         # DETERMINISTIC winner: source precedence, then effectiveDate
  aws_live.py          # read-only live check (service-quotas, pricing, ec2, rds)
  guard.py             # fail-closed guard + build_deterministic_answer
  core.py              # Strands + Nova Pro agent: 3 tools, ask() with guard + tool trail
  ask.py               # CLI: python -m agent.ask "question"     (full LLM agent)
  reconcile_offline.py # CLI: deterministic, NO-LLM, NO-token path (judges can run this)
  baseline.py          # CLI: TF-IDF keyword control (proves structure is load-bearing)
sanity/
  schemaTypes/awsFact.ts   # typed AWS fact (service/factType/region/source/supersedes)
  seed/aws-facts.ndjson    # 5 real-AWS demo facts; two carry an explicit superseded value
docs-sources/
  source-a-*.md   # DEMO: an outdated docs value (32 vCPUs)
  source-b-*.md   # DEMO: the current console value (5 vCPUs) that should win
tests/
  test_core.py    # 5 offline unit tests (reconcile + guard); all passing
```

> The values in `sanity/seed/` and `docs-sources/` are **clearly-labelled demo data**
> used to demonstrate the reconciliation mechanism. Quota codes (e.g. `L-1216C47A`) are
> real so the agent can live-check them, but the specific numbers are account-dependent -
> verify live AWS numbers in your own account before relying on them.

---

## Quick start (no token, no model, no AWS write)

A judge can run the deterministic core against the **public** Sanity dataset with nothing
installed but Python and boto3. This is the credential-free path.

```bash
pip install -r requirements.txt

# 1) The negative control: keyword search returns several rows, cannot pick a winner.
python -m agent.baseline "current standard vCPU quota"

# 2) The structured fix: deterministic reconcile -> one cited answer (+ live AWS check).
python -m agent.reconcile_offline --service EC2 --type quota --region us-east-1
#    add --no-live to skip the AWS call entirely.
```

`reconcile_offline` reads the public dataset over anonymous GROQ, reconciles the
conflicting facts, and (unless `--no-live`) cross-checks the winner against the live
read-only AWS API. No Context token and no model are involved.

---

## Full agent (Nova Pro on Bedrock)

```bash
cp .env.example .env
# fill in the Bedrock region + (optionally) the Sanity Context MCP URL/token.
pip install -r requirements.txt

python -m agent.ask \
  "What is the current default On-Demand Standard vCPU quota in us-east-1, and does any source still show a different number?"
```

Expected shape of a good answer: the current value (**5** vCPUs), then the superseded
value (**32** vCPUs) with the source that still shows it and why the current one wins,
a **live-drift** line (the account's live quota is **16**), and a **tool trail** printed
underneath proving the agent read the structured content and ran the deterministic
reconcile.

**Credentials.** The agent uses standard AWS credentials (env vars, shared config, or an
instance role). It needs `bedrock:InvokeModel` for Nova plus read-only
`Describe*/Get*/List*` for the live check. It never writes.

---

## Build the Knowledge Base (one-time, in the Sanity Dashboard)

The `reconcile_offline` / `baseline` paths need none of this. Do it to run the LLM agent
in **Knowledge Base mode** through the Context MCP.

1. **Create a Sanity project** and a `production` dataset. Note the **project id**
   (`0q5ohtvv` here) - the hard requirement for the submission post.
2. Add the schema in `sanity/schemaTypes/` to a Studio and **deploy** it
   (`sanity schema deploy`), then import the seed:
   ```bash
   npx sanity dataset import sanity/seed/aws-facts.ndjson production
   ```
3. In **Dashboard > Context > New knowledge base**, set a specific **Purpose**, e.g.
   *"Answer 'which value is current' for AWS quotas, limits, prices, and version support.
   Reconcile official docs, pricing pages, and the Service Quotas console."*
4. **Add sources:**
   - a **Dataset source** with a complete GROQ projection, e.g.
     `*[_type == "awsFact"]{service, factType, key, currentValue, unit, region, effectiveDate, source, supersedes, notes}`
   - upload the two files in `docs-sources/` as a **File source** (they carry the
     conflicting EC2 vCPU values, 32 vs 5).
5. **Build entries.** Wait for status = "Entries up to date."
6. **Review Issues.** The build should raise the EC2 vCPU conflict (32 vs 5). Resolve it
   in favour of the current console value; that decision becomes a standing instruction.
7. Put the endpoint in `.env` as `SANITY_CONTEXT_MCP_URL`, forcing KB mode and naming the
   KB: `...?mode=knowledge_base&knowledgeBases=kbXXXX`. Set `SANITY_ORGANIZATION_TOKEN`
   to an **org** token with **Context Viewer** permission.

## Retrieval mode notes

- The MCP's **sources** decide the mode. KB-only sources -> Knowledge Base mode. A dataset
  source -> GROQ mode. Attach BOTH and the dataset source wins and KB sources are silently
  ignored. Force a mode with `?mode=knowledge_base` or `?mode=groq` on the URL.
- For a catalog too big for the 150-doc KB beta cap, stay in GROQ mode and enable dataset
  embeddings instead. Both count for Path One.
- `config.retrieval_mode()` prints which mode the current URL will use.

## Tests

```bash
python -m pytest tests/ -q     # 5 offline unit tests: reconcile + fail-closed guard
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Missing SANITY_...` | required env value blank | copy `.env.example` to `.env`; see "Full agent" |
| `HTTP 401` | token missing/malformed or wrong org | use an ORG token; check org id in the URL |
| `HTTP 403 contextGrantRequired` | token is a project token, not org | recreate at org level with Context Viewer |
| `groq_query` shows up in KB mode | a dataset source is attached | remove it or force `?mode=knowledge_base` |
| Bedrock `AccessDenied` on Nova | model not enabled / no `InvokeModel` | enable Nova Pro in Bedrock; grant `bedrock:InvokeModel` |
| reconcile got 0 facts (LLM path) | Nova relayed an empty tool arg | handled: `reconcile_facts` falls back to the last real fetch (facts still real) |

## Sanity project id

The submission post includes the project id **`0q5ohtvv`** (hard requirement). It is also
echoed by `python -m agent.ask` from `SANITY_PROJECT_ID`.
