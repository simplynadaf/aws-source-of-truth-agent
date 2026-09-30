# Knowledge Base + Context MCP build runbook (browser steps for the org admin)

This is the ONE remaining blocker. It is a browser + your Sanity login task (SSO), so
you run it; I cannot drive your login. Follow top to bottom. ~10 minutes.

Project: aws-source-of-truth | Project ID: `0q5ohtvv` | Org ID: `op7a9oe06` | Dataset: `production`

---

## Step 0 - Enable Context (org admin, one time)
1. Go to https://www.sanity.io/manage/org/labs  (your org: op7a9oe06).
2. Find **Context / Knowledge Bases** and toggle it **on**.
   - Without this, the "New knowledge base" button does not appear.

## Step 1 - Deploy the schema (needed for a dataset-source MCP endpoint)
Dataset-source endpoints require a deployed schema (Studio v5.1.0+). Tell me if you want
me to run this from here (the project-level token in .env has developer role, so it can),
or run it yourself in the project dir:
```
npx sanity schema deploy
```

## Step 2 - Create the Knowledge Base
1. Open the **Context** app in the Sanity Dashboard (https://www.sanity.io/manage -> your
   project -> Context; may be under Labs/Apps).
2. Click **New knowledge base**.
3. **Title:** `AWS source of truth`
4. **Purpose** (paste exactly):
   > Answers "which AWS value is current?" for a small set of AWS facts (quotas, limits,
   > prices, version support, regional availability). When sources disagree, it identifies
   > the current value, names the superseded one, and cites the source for each.
5. Click **Create knowledge base**.

## Step 3 - Add the dataset as a source
1. Click **Add source** -> choose **Dataset**.
2. Select project `aws-source-of-truth` (0q5ohtvv), dataset **production**.
   - This is the dataset that already holds the 5 `awsFact` docs (incl. the EC2 32-vs-5 conflict).

## Step 4 - Build entries
1. Click **Build entries**.
2. Wait until the status reads **Entries up to date**.
3. If it says Build failed / no sources processed: remove the bad source, re-add, rebuild.

## Step 5 - Resolve the conflict (THE screenshot for the post)
1. Open **Issues**. You should see a conflict on the EC2 On-Demand Standard vCPU quota:
   - Claim A: **32 vCPUs** (older EC2 user-guide snapshot)
   - Claim B: **5 vCPUs** (Service Quotas console, effectiveDate 2026-06-01)
2. Resolve it by choosing **5 vCPUs (Service Quotas console)** as ground truth.
   - Reason to note if prompted: "New accounts start at a lower default; the console
     reflects the live per-account value; the old static doc snapshot does not."
3. **>>> SCREENSHOT this Issues view (before + after resolve). This is [IMAGE 2] in the post. <<<**
   - Also screenshot the **Entries** tree once built ([IMAGE], optional but nice).

## Step 6 - (Optional) pin an Instruction
In the **Instructions** view, add:
> When the EC2 On-Demand Standard vCPU quota conflicts, trust the Service Quotas console
> value over any static user-guide snapshot.
Anchor it to the dataset source. (Resolving the issue in Step 5 usually creates this
automatically - only add manually if it did not.)

## Step 7 - Create the MCP endpoint
1. In the Context app, create an **MCP** (endpoint).
2. **Name:** `aws-sot`  (CANNOT be changed later; keep it short/lowercase).
3. **Source:** attach the **Knowledge Base** you just built (AWS source of truth).
   - An endpoint whose sources are all Knowledge Bases automatically serves KB tools.
4. Save. The Context app then shows the **endpoint URL**. It looks like:
   ```
   https://api.sanity.io/v1/context/organizations/op7a9oe06/mcp/aws-sot
   ```
5. **>>> COPY that exact URL and paste it back to me. <<<**

## Step 8 - The TOKEN (important nuance)
The MCP endpoint needs an **ORGANIZATION-level API token with Context Viewer permission**,
created under **Manage > API > Tokens at the ORGANIZATION level** - NOT a project token.
- The token currently in .env is a PROJECT-level robot token (developer+editor on 0q5ohtvv).
  It is great for schema deploy + dataset read/write, but may NOT authorize the Context MCP.
1. Go to https://www.sanity.io/manage/org/op7a9oe06  -> **API** -> **Tokens** (org level).
2. **Add API token**, name `context-viewer`, permission **Context Viewer** (or Viewer if
   that is the only option that mentions Context).
3. Copy it once and paste it back to me (I store it in the gitignored .env).

## What I do once you paste back the MCP URL (+ org token if different)
1. Put `SANITY_CONTEXT_MCP_URL=<the url>` (and the org token) into `.env`.
2. List tools on the endpoint to confirm it serves KB tools (`initial_context`, etc.).
3. Run the Strands + Nova Pro agent in **Knowledge Base mode** against the endpoint and
   capture the tool trail (proof the KB is load-bearing, not GROQ).
4. Slot the KB screenshots into SUBMISSION-POST.md, pick the A/B title, and it is
   publish-ready.

## If Context will not enable / token blocked (fallback, still valid for Path One)
The rules accept EITHER a Knowledge Base OR a Context MCP endpoint over the dataset with
**embeddings enabled**. If KB beta is unavailable on the plan, create a plain **dataset**
MCP endpoint (Step 7 with the dataset as source, embeddings on) and we run in GROQ mode.
The deterministic reconcile + live drift story still holds; we lose only the visible
"Issues" screenshot. Do NOT block the Oct 4 deadline on the KB beta.
