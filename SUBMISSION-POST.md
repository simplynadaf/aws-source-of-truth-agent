---
# Dev.to submission post - AWS Source of Truth Agent (Sanity Challenge, Path One)
# Draft. Fill the [IMAGE: ...] placeholders before publishing. A/B the two titles.
# Required tag: sanitychallenge
title (A - first-person / recognition): "Your AWS docs, pricing page, and console disagree. I built an agent that knows which one is telling the truth."
title (B - search-optimized): "Which AWS number is actually current? An agent that reconciles the docs, then checks reality (Sanity Context + Nova)"
tags: sanitychallenge, aws, ai, devtools
cover_image: [COVER: three conflicting numbers 32 / 1000 / 0.023 crossed out -> one green "the live one", AWS + Sanity marks. 1280x720, verify at 480x270.]
---

You copied a limit straight out of the AWS docs - a default vCPU quota, a concurrency
ceiling, a per-GB price - shipped it, and it was wrong in production. If you've run
anything real on AWS, you've felt this. The number you trusted was stale.

Here's the uncomfortable part: right now, for the same fact, three official-looking AWS
sources can give you three different answers. An older User Guide page, the Service
Quotas console, and a pricing page were each "true" on a different date. Nothing tells
you which one is live.

**TL;DR** - I built an agent for the Sanity Challenge (Path One) that answers *"which AWS
value is actually current?"* It reads a typed fact dataset through **Sanity Context**,
reconciles the conflicting sources **deterministically** (the model can't pick the
winner), returns the current value **with both claims and their sources** - and then does
the thing no other entry does: it asks the **live AWS API** whether even the reconciled
record is still true, and honestly reports the drift.

- Sanity project id: **`0q5ohtvv`**
- Code: https://github.com/simplynadaf/aws-source-of-truth-agent
- Stack: Amazon **Nova Pro** on Bedrock + **Strands Agents** (Python) + **Sanity Context**
  / Knowledge Base + read-only live AWS.

---

## Why keyword search can't save you (the negative control)

The challenge sets a specific bar: *"the strongest submissions show an agent that only
works because the content was structured. If a keyword search would have gotten you the
same answer, aim higher."*

So I didn't just claim keyword search fails - I shipped it and ran it. Here's a TF-IDF
search over the same source text, asked for the *current standard vCPU quota*:

```text
Keyword/TF-IDF baseline for: "current standard vCPU quota"

  0.0849  S3/price:  S3 Standard storage ... = 0.023  (also carries an older value: 0.021)
  0.0651  EC2/quota: Running On-Demand Standard ... = 5 (also carries an older value: 32)
  0.0563  RDS/versionSupport: PostgreSQL oldest major = 13 (also carries an older value: 11)
  0.0000  Lambda/limit: Default concurrent executions = 1000
  0.0000  EC2/regionalAvailability: Graviton4 (R8g) = Available
```

Look at that top result. I asked about **vCPU quota** and keyword overlap ranked an **S3
price** first. Worse: the row I actually wanted carries *two* numbers (5 and 32) and the
baseline has no idea which is current or that they contradict. It returns rows. It does
not reconcile them. That's the hard part, and it's real.

[IMAGE: side-by-side - keyword baseline output (3 numbers, no winner) vs the agent's one cited answer.]

---

## How the structure fixes it

Every fact is a typed `awsFact` document in Sanity - not a blob of prose:

```jsonc
{
  "_type": "awsFact",
  "service": "EC2", "factType": "quota", "region": "us-east-1",
  "key": "Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances",
  "quotaCode": "L-1216C47A",
  "currentValue": "5", "unit": "vCPUs",
  "effectiveDate": "2026-06-01",
  "source": { "name": "Service Quotas console", "kind": "serviceQuotasConsole", "url": "..." },
  "supersedes": {
    "value": "32",
    "stillShownBy": "An older EC2 user-guide snapshot",
    "reason": "New accounts start at a lower default; the console reflects the live per-account value, an old static doc snapshot does not."
  }
}
```

Because `source.kind`, `effectiveDate`, and `supersedes` are **typed fields**, the agent
can reconcile deterministically. The rule is boring on purpose:

> **source precedence** (console / pricing page > changelog > official docs > blog),
> then **most recent `effectiveDate`** as the tie-breaker.

A flat document couldn't do this. The content model *is* the feature. In the Sanity
Knowledge Base build, that same conflict surfaces as an **Issue** (32 vs 5) you resolve
once, and the resolution becomes a standing instruction the agent reads.

[IMAGE: Sanity dashboard - the Knowledge Base "Issues" view showing the EC2 32-vs-5 conflict resolved in favour of 5.]

Crucially, **the model does not choose the winner.** Nova Pro orchestrates the tools and
phrases the answer, but a deterministic `reconcile` picks the value and a **fail-closed
guard** releases the model's prose only if it matches the reconciled value. If they
disagree, the guard replaces the answer with the deterministic one. The LLM literally
cannot invent the number.

---

## The twist that earns the share: even the reconciled record can be stale

Reconciling recorded sources gives you the best answer *the documents* can offer. But
documents rot. So the agent takes one more step that a pure content agent can't: it asks
the **live authoritative AWS API** - read-only Service Quotas, the Price List API, EC2,
RDS - whether the reconciled value is still true.

Here's the real run across all five facts (Nova Pro, us-east-1, read-only throughout):

| Fact | Reconciled (from the record) | Superseded | Live AWS | Result |
|------|------------------------------|-----------|----------|--------|
| EC2 On-Demand Standard vCPU quota | **5** (console) | 32 (old user guide) | **16** | DRIFT |
| Lambda concurrent executions | 1000 (dev guide) | - | unavailable | trusted |
| S3 Standard $/GB-mo | 0.023 (pricing page) | 0.021 (stale blog) | 0.023 | AGREE |
| RDS PostgreSQL oldest major | **13** (release notes) | 11 (old tutorial) | **11** | DRIFT |
| Graviton4 (R8g) availability | Available (instance types) | - | Available | AGREE |

Read the EC2 row left to right: the docs say **32**, the record reconciles to **5**, and
the live account quota is actually **16**. *Three different numbers, and the agent shows
you all three and where each came from* - instead of confidently handing you one wrong
one. The drift isn't a bug. It's the honest answer: here's the current record, and here's
where reality has already moved past it.

[IMAGE: terminal - `python -m agent.ask "..."` showing the cited EC2 answer + the live-drift line + the tool trail (fetch -> reconcile -> verify_live).]

You can reproduce the deterministic core with **no token and no model** - it reads the
public dataset over anonymous GROQ:

```bash
python -m agent.reconcile_offline --service EC2 --type quota --region us-east-1
```

---

## What didn't work (the honest part)

- **Nova dropped a tool argument.** On the first full run, `fetch_candidate_facts`
  returned a row but Nova relayed an empty JSON string to `reconcile_facts`, so it saw
  zero facts - and the guard correctly **fail-closed to "Not verified"** rather than
  guess. That refusal was actually the design working. The fix: cache the last real fetch
  server-side and fall back to it, so the facts still come from Sanity, never from the
  model. (Amazon Nova has a known quirk relaying large JSON tool results.)
- **Knowledge Bases have a ~150-doc beta cap.** Fine for this dataset; for a bigger
  catalog you stay in GROQ mode with dataset embeddings. Both count for Path One.
- **The live check lives outside Sanity**, and it's account-specific - a judge without my
  AWS account can't reproduce the exact live numbers. So the live layer is *additive and
  clearly labelled*; the cited answer is produced by the Sanity Knowledge Base, and the
  demo seed is labelled demo data up top.
- **My model isn't on the "supported agent session" list.** Nova/Strands is the technical
  proof (with its tool trail); I also ran a session through a supported CLI over the same
  Context MCP for the embed.

---

## The reusable takeaway

Strip the AWS specifics and you're left with a pattern for **any** conflicting-source
problem: **type your sources, reconcile by precedence + effective date, guard the answer
so the model can't fake the winner, then verify against the live system of record when one
exists.** That shape works for API version support, pricing, compliance clauses, medical
dosing, legal terms - anywhere "which version is current?" is the actual question.

The lesson that stuck with me: an agent's value here wasn't a smarter model. It was
**structured content plus the humility to say "the record says 5, but reality says 16."**

Project id **`0q5ohtvv`** - code and a run-it-yourself credential-free path are in the
repo. If your docs and your console have ever disagreed, I'd love to hear which number
bit you.

<!-- Required challenge tag: #sanitychallenge -->
