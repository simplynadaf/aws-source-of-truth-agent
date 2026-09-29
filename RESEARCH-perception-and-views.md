# Deep research: how it looks, what judges/people think, what drives views

Last updated: 2026-09-28. This is the "soft, decisive" research (the tie-breaker),
separate from the technical decisions in PROGRESS.md. Sources are cited inline.

## 1. How this is ACTUALLY judged (official, from the announcement)

Path One is scored on exactly four things (Sanity Challenge announcement, dev.to):
1. **Meaningful use of Sanity Context and structured content**
2. **Technical implementation and code quality**
3. **Use of Knowledge Bases**
4. **Usability**

Prizes: 3 x $500 for Path One (+ DEV++ + badge). 5 winners total across both paths.
Submissions due Oct 4 23:59 PDT. Winners announced Oct 22. Hard requirement: Sanity
project ID or public dataset URL in the post (we have 0q5ohtvv + will make dataset public).

The single most important line in the whole announcement, quoted verbatim intent:
> "The strongest submissions will show an agent that only works because the content was
> structured. If a keyword search would have gotten you the same answer, aim higher."

This is why our keyword TF-IDF baseline (control experiment) is a genuine weapon: we can
PROVE keyword search returns three different numbers with no way to pick, and the
structured reconcile + KB picks the live one. Almost nobody else will show the negative
control. Lead the writeup with it.

Also: "Optional but encouraged: embed your agent session." We should embed a real agent
session transcript (they support Claude Code, Gemini CLI, Codex, Copilot CLI, Pi -> we
need one of those; our Strands/Nova run is not on that list, so we may need to ALSO drive
a session through a supported CLI, OR treat the transcript as a nice-to-have and rely on a
recorded terminal + tool-trail. OPEN ITEM - see section 6).

## 2. What judges reward (from 542 winning submissions analysed)

Source: aniruddhaadak, "I Read All 70 Past DEV Challenges + 542 Winning Submissions".
Judge behaviour is remarkably consistent across every past challenge:

The 5 traits every winner shares:
1. **One clear, single, original concept.** Kitchen-sink projects blur into noise.
   Judges literally say "wholly unique entry with nothing else quite like it."
2. **Real, demonstrable utility.** "immediately useful to anyone looking to..."
3. **Polished execution, not just working code.** Demo vs shipped product.
4. **Strong WRITING carries the submission.** THE most under-rated, most-repeated
   deciding factor. "writing quality carried it across the finish line." DEV is a
   writing platform first. Spend as much time on the post as on the code, maybe more.
5. **Load-bearing use of the sponsor tech** (here: Sanity Context + Knowledge Bases),
   explained as the right tool for a real problem, not bolted on.

The 5 things that KILL a submission:
1. Vague/generic concept (title could belong to 50 others).
2. Demo that hides the product (no screenshots, no visible working thing).
3. Writing that reads like a README / changelog instead of a story.
4. Sponsor tech bolted on as an afterthought (KB decorative, not decisive).
5. No measurable impact / no numbers.

Winner vocabulary to consciously earn: "simple but elegant", "wholly unique",
"immediately useful", "seamlessly integrates", "masterfully executed".

## 3. The competitive field (what we are actually up against)

Path One entries already public (from the announcement comments):
- **Errata Desk** (luisprimecore) - THE benchmark to beat. MTG rules errata across three
  platforms (paper / MTGO / Arena) that switch on different dates. Read it in full.
  Why it is strong:
    * Genuinely original, emotionally resonant domain (MTG players feel this pain).
    * DETERMINISTIC in-force logic (the model does not pick the winner) - same core
      integrity idea we have. He did it first, publicly.
    * 272 rulesClaim docs, 54/54 test battery, live public dataset, embeddings on.
    * THREE Context MCP endpoints (desk / sign / sources) with tool-scoping.
    * Multilingual (valueFr/De/Es). A Workflows angle (asked->derived->awaiting->signed,
      only a human can sign). Embedded a real agent session showing REFUSALS.
    * Polished multi-surface live site + Studio + GitHub.
  Where WE can still beat or differentiate it:
    * **Live authoritative cross-check.** Errata Desk reconciles RECORDED sources. It
      never queries a live system of record to ask "is even the reconciled record still
      true?" We do (read-only AWS Service Quotas / Pricing / EC2 / RDS). This is our one
      unique, defensible story: drift against reality, not just drift between documents.
    * **The negative control.** He implies keyword search fails; we SHOW it with a
      TF-IDF baseline side by side. Directly answers the judges' "if keyword search would
      have gotten the same answer, aim higher" line with evidence.
    * Domain reach: AWS quotas/limits/pricing is a pain literally every one of the judges
      and most readers have felt. MTG is niche (a strength for charm, a weakness for
      "immediately useful to me, the judge").
- **TrueStay** (ravi_saxena) - hidden resort-fee desk. Same "contradiction desk" shape,
  travel domain. Polished Vercel demo.
- Expect MANY more contradiction-desk clones by Oct 4 (errata / travel / rules). The
  category is getting crowded. Our AWS + live-drift angle is the least crowded corner.

How Sanity itself picks winners (v0 x Sanity winners blog): the refrain is
**"the content model IS the feature."** They rewarded entries where the interesting
behaviour EMERGED from structured fields (age ranges, dietary flags, spice level as a
NUMBER, entity+relationship graphs), not from frontend code. Takeaway for us: make the
schema the star. Show that `service` / `factType` / `region` / `source` / `effectiveDate`
as typed fields are what make reconciliation possible - a flat blob could not do it.

## 4. Honest read on how OUR entry "looks" right now

Strengths (keep leaning in):
- Unique, defensible hook (live drift) no other entry has.
- Integrity story (deterministic reconcile + fail-closed guard) that judges trust.
- The negative control is rare and directly on-criterion.
- Real, universal domain pain.

Risks (fix before submit):
- **Perceived polish gap.** Errata Desk has a slick multi-surface live site. If we ship
  "terminal + strong writeup" only, we look less finished next to it, even if our core is
  deeper. Usability is a scored criterion. => a small, clean web viewer materially helps
  perception, IF it does not eat the deadline. See recommendation.
- **"Is the KB load-bearing?" scrutiny.** Our differentiator (live AWS) lives OUTSIDE
  Sanity. Judges score "Use of Knowledge Bases" and "meaningful use of Sanity Context."
  We must make the KB clearly decisive to the answer, not a lookup we could skip. The
  reconcile + KB Issue resolution (32 vs 5) must be visibly the thing that produces the
  cited answer; live AWS is the *extra* verification layer on top, framed as "and then we
  check reality," not as the main event. Otherwise it reads as "an AWS script that also
  happens to touch Sanity."
- **Nova/Strands is off the supported agent-session list.** Lower perceived "agent-ness"
  if we cannot embed a session. Mitigate with a clean recorded tool-trail, or additionally
  run a supported CLI over the same MCP.
- **Demo seed drift could confuse.** We know the seed is demo data and live values differ;
  a judge skimming could read "your numbers are wrong." Label seed as demo LOUDLY and
  frame drift as the intended lesson, up front.

## 5. What drives VIEWS + REACTIONS on dev.to (the literal tie-breaker if scores tie,
and what gets the post surfaced at all)

- Reactions:views ratio and comments:views are how dev.to surfaces/promotes posts
  (grahamthedev, DEV staff-acknowledged). So EARLY engagement matters: post, then get a
  handful of genuine comments in the first hours.
- What reliably spikes engagement (axrisi, 10k-views breakdown): **narrative + technical
  insight together** - "developers love seeing the WHY behind the build, not just the
  code." Reacting to something real (a real problem, real news) beats a tutorial dump.
- Title is the highest-leverage 100 characters. Make it specific + promise a result +
  create curiosity. NOT "AWS Source of Truth Agent." Better candidates:
    * "Your AWS docs, pricing page, and console disagree. I built an agent that knows
       which one is telling the truth."  (recognition + curiosity, first-person)
    * "Which AWS number is actually current? An agent that reconciles the docs, then
       checks reality." (search-ish, states the payoff)
  A/B two titles is worth it (one recognition/first-person, one search-optimized), as we
  do for YouTube.
- Cover image matters for CTR in the feed. A clean, high-contrast cover (three
  conflicting numbers -> one green "current" answer, with an AWS + Sanity mark) will
  out-click a code screenshot. Reuse the thumbnail skill (purple/black brand, <=3 words,
  show the RESULT: e.g. "32? 1000? -> the live one"). Verify at 480x270.
- Structure that keeps people reading (maps to both judging + engagement): specific title
  -> TL;DR with the payoff + project id -> the pain (three numbers) -> the negative
  control (keyword search fails, shown) -> how the STRUCTURE fixes it (schema + KB Issue
  resolution, screenshots of the Sanity dashboard) -> the twist (live drift vs reality) ->
  honest gotchas -> what I learned. End on reflection, not a summary.
- Show, don't tell: screenshots of the Sanity KB build + the resolved Issue + the tool
  trail + the live-drift annotation. At least 3 images. Judges "cannot evaluate what they
  cannot see."
- Honesty reads as credibility and is explicitly rewarded ("quality and honesty of the
  build process"). Include a real "what didn't work / gotchas" section (Nova not on the
  session list, KB 150-doc beta cap, seed is demo data). This also inoculates against the
  risks in section 4.

## 6. Concrete recommendations (decisions to lock)

1. **FRAME the whole post around the negative control + live drift**, in that order:
   keyword search returns 3 numbers (shown) -> structured KB reconciles to 1 cited answer
   -> then we check the live authoritative API and honestly report drift. This hits the
   exact "aim higher than keyword search" line AND gives us the one thing no competitor has.
2. **Make the Sanity KB visibly load-bearing.** The cited answer must come THROUGH the KB
   Issue resolution (32 vs 5), with dashboard screenshots. Live AWS is the verification
   layer on top, not the headline mechanism. Protects the two KB/Context scored criteria.
3. **Ship a small, clean web viewer** (Astro static page: type a question -> show the
   reconciled answer, both claims + sources, the tool trail, and the live-drift banner).
   Reason: "Usability" is scored, and Errata Desk sets a visible polish bar. Keep it tiny;
   do not let it threaten the Oct 4 deadline. If time is tight, a recorded terminal walk +
   the web viewer screenshots is an acceptable fallback.
4. **Title A/B**: one first-person recognition title, one search-optimized. Pick the
   cover that shows the RESULT (conflicting numbers -> the live one).
5. **Agent session**: try to also run one pass through a DEV-supported CLI over the same
   Context MCP so we can embed an official session; otherwise embed a clean tool-trail and
   say so honestly.
6. **Engagement plan**: publish a day or two before the deadline (not last minute), reply
   to every comment fast, and drop the submission link in the announcement-post comments
   like the other entrants did.
7. **Label the demo seed loudly** and frame drift as the intended lesson at the top.

## 7. Open questions still needing the user
- Web viewer: YES recommended (perception + Usability score). Confirm you want it.
- GitHub target (username/org) for the public repo.
- Do we invest in an official agent-session transcript via a supported CLI, or accept a
  tool-trail? (affects perceived "agent-ness").

RESOLVED 2026-09-28 (checked myself): GitHub = simplynadaf (confirmed via gh auth).
Web viewer = YES, minimal + timeboxed. Agent session = both (Nova/Strands tool-trail +
official Claude Code session; claude is installed and DEV-supported).

---

# 8. PROS / CONS of the core design choices (honest tradeoff pass)

Added 2026-09-28. The tradeoff analysis that was missing - weighing decisions, not just
listing the plan. Each con has a mitigation.

## A. Core bet: AWS "source of truth" + LIVE drift check
PROS: only entry querying a live authoritative system of record (not just recorded docs);
genuinely novel; answers the judges' "aim higher than keyword search" line; universal pain.
CONS + mitigation: live values are account-specific so not reproducible for a judge without
AWS -> the no-token GROQ + local reconcile path runs with zero AWS, live check is an
additive, clearly-labelled layer. Live AWS sits OUTSIDE Sanity -> could look like "an AWS
script that touches Sanity" -> make the KB the mechanism that produces the cited answer;
live AWS is the verification epilogue, not the headline.

## B. Domain: AWS vs a charming niche (MTG / travel)
PROS: immediately useful to the judges themselves (they are devs) - the highest praise
pattern in the data; broad reader base = more views/reactions.
CONS + mitigation: less inherently charming than Errata Desk's MTG; AWS can read dry ->
open with a felt human moment ("you copy-pasted a limit and it was wrong in prod"), not
architecture.

## C. Web viewer (decided YES)
PROS: lifts Usability score; matches the competitor's polish bar; judge sees it work in
10 seconds. CONS + mitigation: build-time risk 6 days out -> static/minimal, timeboxed,
built only after the core run is proven; screenshots are the fallback.

## D. Model: Amazon Nova Pro vs Claude/GPT
PROS: on-brand for an AWS story; verified working; cheap. CONS + mitigation: Nova not on
DEV's supported session list + less familiar name -> lower perceived "agent-ness"; the
fail-closed guard means model choice is NOT load-bearing for correctness (state this as a
plus), and we also embed an official Claude Code session over the same MCP.

## E. TF-IDF negative control (keyword baseline)
PROS: rare; proves "structured content is WHY this works" with evidence; strong
appreciation trigger. CONS + mitigation: adds length -> keep to ONE tight before/after
(three numbers from keyword search -> one cited answer from the KB).

## F. Fail-closed deterministic guard (reconcile decides, not the model)
PROS: trust; "the model cannot fake the winner" is a clean claim judges reward.
CONS + mitigation: invites "is the LLM even doing anything?" -> frame the division of
labour honestly (LLM orchestrates tools + phrases the answer; the guard guarantees it
can't invent the value). That division IS the insight, not a weakness.

# 9. What makes a READER genuinely appreciate this (the appreciation arc)

Appreciation = recognition + a non-obvious insight + honesty + a reusable takeaway
(grounded in axrisi's 10k-view breakdown + the 542-winner "writing carried it" pattern).
Walk the post through this arc IN ORDER:

1. RECOGNITION (emotional entry): "You copied a limit/price/version straight from the AWS
   docs, shipped it, and it was wrong." Every AWS dev/judge nods. Start here, not with
   architecture.
2. THE UNCOMFORTABLE REVEAL: three official AWS sources disagree right now (docs vs pricing
   vs console). Show the three numbers. Reader: "wait, that's real?"
3. THE "I WOULDN'T HAVE THOUGHT OF THAT" MOMENT: keyword search / naive RAG returns three
   numbers with no way to choose - SHOW the negative control failing. Validates the hard
   part is real, so readers respect the solution instead of shrugging.
4. THE CLEAN RESOLUTION: typed schema + KB reconciliation returns ONE cited answer, and the
   model cannot fake which wins. Screenshot the resolved Sanity Issue (32 vs 5).
5. THE TWIST THAT EARNS THE SHARE: even the reconciled record can be stale, so the agent
   asks the LIVE authoritative API and honestly reports drift. The one sentence people
   quote. No other entry has it.
6. THE HONESTY PAYOFF: a real "what didn't work / gotchas" section (Nova off the session
   list, KB 150-doc beta cap, seed is demo data, live-AWS-outside-Sanity tradeoff). Honesty
   is explicitly rewarded and inoculates against the risks in section 4.
7. THE REUSABLE TAKEAWAY (why they bookmark): the PATTERN generalises - "source precedence +
   effectiveDate + a fail-closed guard" solves ANY conflicting-source problem (pricing,
   API versions, compliance docs, medical dosing, legal clauses), not just AWS.

Concrete levers: real resource IDs + real numbers (never invented); one diagram (three
sources -> reconcile -> KB cited answer -> live check -> drift banner); a copy-pasteable
question with the exact tool trail underneath (proof, not claims); end on the takeaway,
not a feature summary.

BOTTOM LINE: the project is technically strong; whether readers APPRECIATE it is decided
almost entirely by the writeup walking this arc. Budget as much care on the post as on the
code - the single most-repeated winner pattern in the data.
