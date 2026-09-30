<div align="center">

# 🌊 AWS Source of Truth

### When your AWS docs, pricing page, and Service Quotas console disagree, an agent that knows which one is telling the truth, then checks the live API to see if even that record has drifted.

[![Sanity Challenge](https://img.shields.io/badge/Sanity%20Challenge-Path%20One-0891B2?style=for-the-badge&logo=sanity&logoColor=white)](https://dev.to/challenges/sanity-2026-09-16)
[![Sanity Context](https://img.shields.io/badge/Powered%20by-Sanity%20Context-0B2942?style=for-the-badge&logo=sanity&logoColor=white)](https://www.sanity.io/docs/context)
[![AWS](https://img.shields.io/badge/Checks-Live%20AWS%20API-0369A1?style=for-the-badge&logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Nova Pro](https://img.shields.io/badge/Model-Amazon%20Nova%20Pro-0D9488?style=for-the-badge&logo=amazon&logoColor=white)](https://aws.amazon.com/ai/generative-ai/nova/)
[![Strands](https://img.shields.io/badge/Agents-Strands-155E75?style=for-the-badge&logo=awslambda&logoColor=white)](https://strandsagents.com)

[![Live Demo](https://img.shields.io/badge/🌊%20Live%20Demo-See%20it%20in%20your%20browser-0891B2?style=for-the-badge&logo=github&logoColor=white)](https://simplynadaf.github.io/aws-source-of-truth-agent/)
[![Read the Article](https://img.shields.io/badge/📝%20Read%20the%20Article-Dev.to-0A0A0A?style=for-the-badge&logo=devdotto&logoColor=white)](https://dev.to/sarvar_04)

[![Stars](https://img.shields.io/github/stars/simplynadaf/aws-source-of-truth-agent?style=social)](https://github.com/simplynadaf/aws-source-of-truth-agent/stargazers)
[![Forks](https://img.shields.io/github/forks/simplynadaf/aws-source-of-truth-agent?style=social)](https://github.com/simplynadaf/aws-source-of-truth-agent/network/members)
[![Issues](https://img.shields.io/github/issues/simplynadaf/aws-source-of-truth-agent)](https://github.com/simplynadaf/aws-source-of-truth-agent/issues)

---

**Sanity project id:** `0q5ohtvv` · **⭐ If a stale AWS number has ever bitten you in production, give this a star.**

[The Problem](#-the-problem) • [Why Search Fails](#-why-keyword-search-cant-save-you) • [How Structure Fixes It](#-how-the-structure-fixes-it) • [The Twist](#-the-twist-even-the-reconciled-record-can-be-stale) • [Getting Started](#-getting-started) • [FAQ](#-faq)

</div>

<details>
<summary><b>📖 Table of Contents</b></summary>

- [The Problem](#-the-problem)
- [Why Keyword Search Can't Save You](#-why-keyword-search-cant-save-you)
- [How the Structure Fixes It](#-how-the-structure-fixes-it)
- [The Twist: Even the Reconciled Record Can Be Stale](#-the-twist-even-the-reconciled-record-can-be-stale)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Getting Started](#-getting-started)
- [Build the Knowledge Base](#-build-the-knowledge-base-one-time-in-the-sanity-dashboard)
- [Project Structure](#-project-structure)
- [The Integrity Story (why the model can't fake it)](#-the-integrity-story-why-the-model-cant-fake-it)
- [Least-Privilege IAM Policy](#-least-privilege-iam-policy)
- [What Didn't Work](#-what-didnt-work-the-honest-part)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [License](#-license)

</details>

---

## 🤔 The Problem

You copied a limit straight out of the AWS docs, a default vCPU quota, a concurrency ceiling, a per-GB price, shipped it, and it was **wrong in production**. If you have run anything real on AWS, you have felt this. The number you trusted was stale.

Here is the uncomfortable part: right now, for the same fact, three official-looking AWS sources can give you three different answers. An older User Guide page, the Service Quotas console, and a pricing page were each "true" on a different date. Nothing tells you which one is live.

**This repo builds a Path One agent for the [Sanity Challenge](https://dev.to/challenges/sanity-2026-09-16)** that answers *"which AWS value is actually current?"* It reads a typed fact dataset through **Sanity Context**, reconciles the conflicting sources **deterministically** (the model cannot pick the winner), returns the current value **with both claims and their sources**, then does the thing no other entry does: it asks the **live AWS API** whether even the reconciled record is still true, and honestly reports the drift.

> 🌊 **See it live:** [simplynadaf.github.io/aws-source-of-truth-agent](https://simplynadaf.github.io/aws-source-of-truth-agent/) — the `32 → 5 → 16` reconciliation story, all five cited facts, and the agent's tool trail on one page.

---

## 🔎 Why keyword search can't save you

The challenge sets a specific bar: *"the strongest submissions show an agent that only works because the content was structured. If a keyword search would have gotten you the same answer, aim higher."*

So we did not just claim keyword search fails, we shipped it. Here is a TF-IDF search over the same source text, asked for the **current standard vCPU quota**:

```text
Keyword/TF-IDF baseline for: "current standard vCPU quota"

  0.0849  S3/price:  S3 Standard storage ... = 0.023  (also carries an older value: 0.021)
  0.0651  EC2/quota: Running On-Demand Standard ... = 5 (also carries an older value: 32)
  0.0563  RDS/versionSupport: PostgreSQL oldest major = 13 (also carries an older value: 11)
  0.0000  Lambda/limit: Default concurrent executions = 1000
  0.0000  EC2/regionalAvailability: Graviton4 (R8g) = Available
```

Look at the top result. We asked about **vCPU quota** and keyword overlap ranked an **S3 price** first. Worse, the row we actually wanted carries *two* numbers (5 and 32) and the baseline has no idea which is current or that they contradict. It returns rows. It does not reconcile them. That is the hard part, and it is real. Ship the control yourself: `python -m agent.baseline "current standard vCPU quota"`.

---

## 🧩 How the structure fixes it

Every fact is a typed `awsFact` document in Sanity, not a blob of prose:

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

Because `source.kind`, `effectiveDate`, and `supersedes` are **typed fields**, the agent can reconcile deterministically. The rule is boring on purpose:

> **source precedence** (console / pricing page > changelog > official docs > blog), then **most recent `effectiveDate`** as the tie-breaker.

A flat document could not do this. The content model *is* the feature. In the Sanity Knowledge Base build, that same conflict surfaces as an **Issue** (32 vs 5) you resolve once, and the resolution becomes a standing instruction the agent reads.

---

## 🌊 The twist: even the reconciled record can be stale

Reconciling recorded sources gives you the best answer *the documents* can offer. But documents rot. So the agent takes one more step a pure content agent cannot: it asks the **live authoritative AWS API**, read-only Service Quotas, the Price List API, EC2, RDS, whether the reconciled value is still true.

Here is the real run across all five facts (Nova Pro, us-east-1, read-only throughout):

| Fact | Reconciled (from the record) | Superseded | Live AWS | Result |
|------|------------------------------|-----------|----------|--------|
| EC2 On-Demand Standard vCPU quota | **5** (console) | 32 (old user guide) | **16** | 🟠 DRIFT |
| Lambda concurrent executions | 1000 (dev guide) | — | unavailable | ✅ trusted |
| S3 Standard $/GB-mo | 0.023 (pricing page) | 0.021 (stale blog) | 0.023 | 🟢 AGREE |
| RDS PostgreSQL oldest major | **13** (release notes) | 11 (old tutorial) | **11** | 🟠 DRIFT |
| Graviton4 (R8g) availability | Available (instance types) | — | Available | 🟢 AGREE |

Read the EC2 row left to right: the docs say **32**, the record reconciles to **5**, and the live account quota is actually **16**. *Three different numbers, and the agent shows you all three and where each came from,* instead of confidently handing you one wrong one. The drift is not a bug. It is the honest answer: here is the current record, and here is where reality has already moved past it.

---

## 🧠 How It Works

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  🧑 "which vCPU quota      🌊 Strands agent (Nova Pro)      📚 Sanity Context │
│      is current?"                                                           │
│  ┌──────────────┐    ┌───────────────────────────┐    ┌──────────────────┐ │
│  │ user asks     │──▶│ 1. fetch_candidate_facts  │───▶│ typed awsFact docs│ │
│  └──────────────┘    │ 2. reconcile_facts (det.) │    │ Knowledge Base /  │ │
│                      │ 3. verify_live (read-only)│    │ public GROQ       │ │
│                      └──────────────┬────────────┘    └──────────────────┘ │
│                                     │                                       │
│                       🔒 fail-closed guard: release model prose ONLY if     │
│                       it matches the deterministically reconciled value     │
│                                     │                                       │
│                                     ▼                                       │
│                       🔒 READ-ONLY AWS: service-quotas · pricing · ec2 · rds │
│                       (Get / Describe / List, never create/modify/delete)   │
└───────────────────────────────────────────────────────────────────────────┘
```

**The model orchestrates, it does not decide.** Nova Pro drives the three tools and phrases the answer, but a deterministic `reconcile` picks the value and a **fail-closed guard** releases the prose only if it matches the reconciled value. If they disagree, the guard replaces the answer with the deterministic one. The LLM literally cannot invent the number.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| 🧠 Model | [Amazon Nova Pro](https://aws.amazon.com/ai/generative-ai/nova/) (`amazon.nova-pro-v1:0`) on Bedrock, us-east-1 |
| 🤖 Agent runtime | [Strands Agents](https://strandsagents.com) (Python): 3 tools + a fail-closed guard |
| 📚 Structured content | typed **`awsFact`** schema in [Sanity](https://www.sanity.io/), read via **Context** (Knowledge Base) or credential-free public GROQ |
| 🔒 Live cross-check | read-only AWS Service Quotas · Price List API · EC2 · RDS |
| 🐍 SDK | Python 3.10+, `boto3` |
| 🌊 Viewer | single-file static page (GitHub Pages), zero build step |

---

## 📋 Prerequisites

| # | Requirement | Details |
|---|---|---|
| 1 | **Python 3.10+** | `python3 --version` to check |
| 2 | **AWS credentials** *(for the live check + LLM)* | read-only `Describe*/Get*/List*` **+ `bedrock:InvokeModel`** for Nova Pro. Not needed for the credential-free offline path |
| 3 | **Amazon Nova Pro** | enable model access in the Bedrock console (`us-east-1`) **and** grant `bedrock:InvokeModel` |
| 4 | *Sanity Context token* | **Optional.** Only for Knowledge Base mode; the offline path reads the public dataset with no token |

---

## 🚀 Getting Started

### Quick start (no token, no model, no AWS write)

A judge can run the deterministic core against the **public** Sanity dataset with nothing installed but Python and boto3.

```bash
git clone https://github.com/simplynadaf/aws-source-of-truth-agent.git
cd aws-source-of-truth-agent
pip install -r requirements.txt

# 1) The negative control: keyword search returns several rows, cannot pick a winner.
python -m agent.baseline "current standard vCPU quota"

# 2) The structured fix: deterministic reconcile -> one cited answer (+ live AWS check).
python -m agent.reconcile_offline --service EC2 --type quota --region us-east-1
#    add --no-live to skip the AWS call entirely.
```

`reconcile_offline` reads the public dataset over anonymous GROQ, reconciles the conflicting facts, and (unless `--no-live`) cross-checks the winner against the live read-only AWS API. No Context token and no model are involved.

### Full agent (Nova Pro on Bedrock)

```bash
cp .env.example .env         # fill Bedrock region + (optionally) the Sanity Context MCP URL/token
pip install -r requirements.txt

python -m agent.ask \
  "What is the current default On-Demand Standard vCPU quota in us-east-1, and does any source still show a different number?"
```

Expected shape: the current value (**5** vCPUs), the superseded value (**32**) with the source that still shows it and why the current one wins, a **live-drift** line (the account's live quota is **16**), and a **tool trail** proving the agent read the structured content and ran the deterministic reconcile.

> 🔒 **Secrets stay local.** `.env` is git-ignored; only `.env.example` (a placeholder) is tracked. The agent uses standard AWS credentials and never writes to your account.

---

## 📚 Build the Knowledge Base (one-time, in the Sanity Dashboard)

The `reconcile_offline` / `baseline` paths need none of this. Do it to run the LLM agent in **Knowledge Base mode** through the Context MCP.

1. **Create a Sanity project** + a `production` dataset. Note the **project id** (`0q5ohtvv` here), the hard requirement for the submission post.
2. Deploy the schema in `sanity/schemaTypes/` and import the seed:
   ```bash
   npx sanity dataset import sanity/seed/aws-facts.ndjson production
   ```
3. **Dashboard → Context → New knowledge base**, set a specific **Purpose** (e.g. *"Answer 'which value is current' for AWS quotas, limits, prices, and version support"*).
4. **Add sources:** a **Dataset source** (`*[_type == "awsFact"]{...}`) plus the two files in `docs-sources/` as a **File source** (they carry the conflicting EC2 vCPU values, 32 vs 5).
5. **Build entries**, wait for "Entries up to date."
6. **Review Issues.** The build raises the EC2 vCPU conflict (32 vs 5). Resolve it in favour of the current console value; that decision becomes a standing instruction.
7. Put the endpoint in `.env` as `SANITY_CONTEXT_MCP_URL` (`...?mode=knowledge_base&knowledgeBases=kbXXXX`) and set `SANITY_ORGANIZATION_TOKEN` to an **org** token with **Context Viewer** permission.

---

## 📁 Project Structure

```
aws-source-of-truth-agent/
├── README.md
├── LICENSE
├── requirements.txt              # strands-agents, boto3, python-dotenv
├── .env.example                  # copy to .env and fill in (Bedrock + Sanity Context)
├── agent/                        # the agent (run with `python -m agent.<name>`)
│   ├── config.py                 # env loading + retrieval-mode detection
│   ├── context_mcp.py            # live Sanity Context MCP client (Knowledge Base mode)
│   ├── sanity_client.py          # credential-free GROQ over the PUBLIC dataset
│   ├── reconcile.py              # DETERMINISTIC winner: source precedence, then effectiveDate
│   ├── aws_live.py               # read-only live check (service-quotas, pricing, ec2, rds)
│   ├── guard.py                  # fail-closed guard + build_deterministic_answer
│   ├── core.py                   # Strands + Nova Pro agent: 3 tools, ask() with guard + trail
│   ├── ask.py                    # CLI: python -m agent.ask [--json] "question"  (full LLM agent)
│   ├── reconcile_offline.py      # CLI: deterministic, NO-LLM, NO-token path (judges run this)
│   ├── baseline.py               # CLI: TF-IDF keyword control (proves structure is load-bearing)
│   └── import_seed.py            # CLI: import the seed facts into the dataset (write token)
├── sanity/
│   ├── schemaTypes/awsFact.ts    # typed AWS fact (service/factType/region/source/supersedes)
│   └── seed/aws-facts.ndjson     # real-AWS demo facts; several carry an explicit superseded value
├── docs-sources/                 # DEMO: an outdated value (32) vs the current console value (5)
├── docs/index.html               # the web viewer
├── sanity.config.ts              # Sanity Studio config
├── sanity.cli.ts                 # Sanity CLI config (schema deploy)
└── tests/test_core.py            # offline unit tests (reconcile + guard + keyword trap); all passing
```

> The values in `sanity/seed/` and `docs-sources/` are **clearly-labelled demo data**. Quota codes (e.g. `L-1216C47A`) are real so the agent can live-check them, but the specific numbers are account-dependent, verify live AWS numbers in your own account before relying on them.

---

## 🔐 The Integrity Story (why the model can't fake it)

Strands runs the agent; a deterministic function picks the winner; a guard gates the output.

> The values in `sanity/seed/` and `docs-sources/` are **clearly-labelled demo data**. Quota codes (e.g. `L-1216C47A`) are real so the agent can live-check them, but the specific numbers are account-dependent, verify live AWS numbers in your own account before relying on them.

---

## 🔐 The Integrity Story (why the model can't fake it)

Strands runs the agent; a deterministic function picks the winner; a guard gates the output.

```python
# reconcile.py — the model does not run this logic
winner = max(facts, key=lambda f: (SOURCE_PRECEDENCE[f.source.kind], f.effectiveDate))

# guard.py — release model prose ONLY if it matches the reconciled value
if reconciled_value in model_answer:
    return model_answer            # trusted
return build_deterministic_answer(winner)   # fail-closed: replace with the real value
```

That division of labour is the whole point: **structured content plus the humility to say "the record says 5, but reality says 16."** Strip the AWS specifics and it is a reusable pattern for any conflicting-source problem: type your sources, reconcile by precedence + effective date, guard the answer, then verify against the live system of record when one exists.

---

## 🔐 Least-Privilege IAM Policy

Every account read is a `Describe`, `Get`, or `List`, and the only non-read action is `bedrock:InvokeModel` scoped to Nova Pro. Nothing creates, modifies, or deletes any resource.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyLiveCheck",
      "Effect": "Allow",
      "Action": [
        "servicequotas:GetServiceQuota",
        "pricing:GetProducts",
        "ec2:DescribeInstanceTypeOfferings",
        "rds:DescribeDBEngineVersions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "InvokeNovaProOnly",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0",
        "arn:aws:bedrock:*:*:inference-profile/us.amazon.nova-pro-v1:0"
      ]
    }
  ]
}
```

> ⚠️ **Nova Pro is two separate things.** (1) **Model access:** enable `amazon.nova-pro-v1:0` once in the Bedrock console under *Model access* (`us-east-1`), a Bedrock grant no IAM policy can do for you. (2) **Invoke permission:** the `bedrock:InvokeModel` statement above. You need both.

---

## 🧾 What Didn't Work (the honest part)

- **Nova dropped a tool argument.** On the first full run, `fetch_candidate_facts` returned a row but Nova relayed an empty JSON string to `reconcile_facts`, so it saw zero facts, and the guard correctly **fail-closed to "Not verified"** rather than guess. That refusal was the design working. Fix: cache the last real fetch server-side and fall back to it, so the facts still come from Sanity, never from the model. (Amazon Nova has a known quirk relaying large JSON tool results.)
- **Knowledge Bases have a ~150-doc beta cap.** Fine for this dataset; for a bigger catalog you stay in GROQ mode with dataset embeddings. Both count for Path One.
- **The live check lives outside Sanity** and is account-specific, so a judge without this AWS account cannot reproduce the exact live numbers. The live layer is *additive and clearly labelled*; the cited answer is produced by the Sanity Knowledge Base.

---

## 🐛 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Missing SANITY_...` | required env value blank | copy `.env.example` to `.env` |
| `HTTP 401` | token missing/malformed or wrong org | use an ORG token; check org id in the URL |
| `HTTP 403 contextGrantRequired` | token is a project token, not org | recreate at org level with Context Viewer |
| `groq_query` shows up in KB mode | a dataset source is attached | remove it or force `?mode=knowledge_base` |
| Bedrock `AccessDenied` on Nova | model not enabled / no `InvokeModel` | enable Nova Pro in Bedrock; grant `bedrock:InvokeModel` |
| reconcile got 0 facts (LLM path) | Nova relayed an empty tool arg | handled: `reconcile_facts` falls back to the last real fetch (facts still real) |

---

## ❓ FAQ

<details>
<summary><b>Why can't a keyword or vector search do this?</b></summary>

Search ranks rows by similarity, it returns all the conflicting numbers and cannot tell you which is current or that two rows contradict. The agent reconciles by typed fields (source precedence + effectiveDate), which only works because the content is structured. The repo ships the TF-IDF control (`agent/baseline.py`) so you can see search fail on the same data.
</details>

<details>
<summary><b>Does the model choose the answer?</b></summary>

No, by design. A deterministic `reconcile` picks the winning value and a fail-closed guard releases the model's prose only if it matches. If the model drifts, the guard replaces it with the deterministic answer. The LLM cannot invent the number.
</details>

<details>
<summary><b>Is the live AWS check safe to run?</b></summary>

Yes, by IAM policy, not by hope. Every call is a `Get` / `Describe` / `List`. Attach the least-privilege policy above and the "can't touch anything" property is literally true.
</details>

<details>
<summary><b>Can I run it without a Sanity token or an LLM?</b></summary>

Yes. `python -m agent.reconcile_offline` reads the public dataset over anonymous GROQ, reconciles deterministically, and cross-checks live AWS, no token, no model. That is the credential-free path a judge can run.
</details>

<details>
<summary><b>Are the numbers real?</b></summary>

The seed is clearly-labelled demo data used to demonstrate the mechanism, but the quota codes are real and the live check hits real read-only AWS APIs. The `32 → 5 → 16` story is a real recorded run; the specific live numbers are account-dependent.
</details>

---

## 📝 License

MIT, see the [LICENSE](LICENSE) file.

---

## 👨‍💻 Author

**Sarvar Nadaf** | Cloud Architect | Cloud, AI Infrastructure & DevOps

[![LinkedIn](https://img.shields.io/badge/LinkedIn-sarvar04-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/sarvar04/)
[![GitHub](https://img.shields.io/badge/GitHub-simplynadaf-181717?style=flat-square&logo=github)](https://github.com/simplynadaf)
[![Dev.to](https://img.shields.io/badge/Dev.to-sarvar__04-0A0A0A?style=flat-square&logo=devdotto&logoColor=white)](https://dev.to/sarvar_04)

---

<div align="center">

**If a stale AWS number has ever cost you, consider giving this a ⭐**

*Built with 🌊 on AWS: Strands • Amazon Nova Pro • Sanity Context • read-only AWS*

</div>
