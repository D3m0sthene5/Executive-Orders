# Excavator funnel: cutting agent time and tokens per claim (2026-10-18)

Selection made before implementation, in the format of `research/stage19/FUNNEL.md`. It is based on the
measured cost of the 2026-10-18 claim swarm (19 agents, branch `wire-new-sources`). That swarm produced 176
reviewer-accepted claims (132 complete) for decided-NO orders revoked or superseded by one named EO.
Ready for human review went from 1 to 130 in the local run.

## What the swarm actually spent (measured from the agent transcripts)

| Measure | Value |
|---|---|
| Agents / wall time | 19 agents; producers 19–34 min each, reviewers 9–15 min, about 56 min end to end |
| Tokens | 5.7M new input (cache writes), **370M cached input re-read**, 42k output |
| Tool calls | 1,694. Producers ran 63–148 calls for about 25 orders; reviewers ran 53–102 |
| Time waiting on tools | about 35 of about 360 agent-minutes. The rest is the model reading and reasoning |
| Activities by call count | claim JSON building and printing 600; reading order texts 438; claim-checker runs 153; codification and later-event lookups 126 |
| Text pulled into context | 3.6M characters from claim building and printing; 2.0M from order texts; 0.7M from checker output |

**What drives the cost:** every tool call re-sends the whole context, so cost is **turns × context size**. The
work was not slow because tools were slow. It was slow and expensive because agents built claims in about
130 small steps per batch while their context grew to around 300k tokens.

**What the agents did by hand** (176 accepted claims compared with their machine drafts):

- **Clause inventory.** The draft had **no** inventory for 95 orders (54%). Agents rewrote 50 more, partly reused 24 and took only 7 unchanged. Yet 69 orders (39%) have a single clause.
- **First end.** For **108 of the 136** whole-order ends, the accepted date was **not** among the draft's proposals. Agents found it themselves, through fixed terms in the order itself, effective-date wording in the acting EO, or an amendment chain.
- **Later events.** 53 claims carry 5 or more later events, found by hand-tracing amendment chains (one family, EO 11248, has 40 amenders).
- **Savings.** 122 were "none after bounded search" and 36 "transferred or accrued", each decided by reading phrases a machine can surface.
- **Claim JSON.** Hand-assembled, median 11.5k characters, rationale 1.3k.
- **Rejections.** Reviewers rejected 21 of 197. The main cause was a **missed earlier end**: the order's own term, an earlier partial amendment, or an amendment mistaken for an end. Machines can surface candidates for exactly these.

## C. Ten ways to cut agent turns and context per finished claim

| # | Distinct concept | What it removes from agent work | Principal limit |
|---:|---|---|---|
| 1 | **Claim assembler from decision sheets** | Agent writes one compact row per clause (state, end pointer, savings choice, rationale). A job expands it into full Stage 19 JSON with sources, sha256, pages and exact quotes, then gate-checks it. Replaces most of the 600 build calls and the large JSON output. | Only as good as the pointers the agent picks. |
| 2 | **Clause segmenter v2** | Fills the 95 missing inventories and fixes common splits. Covers one-paragraph orders (`#whole`), amendment orders ("is amended by adding/striking"), numbered lists and schedules, with exact spans and pages. | OCR damage and unusual layouts still need an eye. |
| 3 | **Acting-provision locator** | For each (target, acting EO) pair, extracts the sentence naming the target, the actor's signing and filing date, its effective-date wording, and savings or "pending matters" phrases. | Generic references ("all orders inconsistent herewith") name no target. |
| 4 | **Own-terms end detector** | Flags fixed terms ("for a period of four years"), sunsets, "until", temporary bodies, conditions and report deadlines in the order itself. These are earlier-end candidates and the top cause of rejections. Never turns a deadline into an end date. | Finds wording, not facts (whether a report was filed). |
| 5 | **Amendment-chain compiler** | Builds, for each target, every corpus order naming it with amend, revoke, supersede, transfer or abolish verbs, dated, with the sections touched. This gives a `later_events` skeleton and conflict flags (the EO 10610 case reviewers caught). | Indirect or statutory changes are only partly visible. |
| 6 | **One-file order dossier** | Puts everything for one order on one page: clause spans, actor provision, chain, end candidates, savings phrases, machine searches, the draft's gate errors. Producer and reviewer each read it once instead of re-opening texts (438 reads). | A dossier can hide what it leaves out; it must list its gaps. |
| 7 | **Batch review sheets for look-alike orders** | One table of 50–100 same-pattern orders (for example pay-level placements under EO 11248, single-clause committee orders) approved row by row. A job turns approved rows into claims (Astra's suggestion). | Only for genuinely uniform families; outliers must drop out. |
| 8 | **Effective-date resolver** | Classifies effective wording ("upon signing", "as of the close of the pay period…", "30 days after publication", "on and after") into an exact date or an explicit *variable* flag (the EO 9687 case). | Wording may be ambiguous; variable dates stay open. |
| 9 | **In-process pre-gate** | Runs `claim_gate` and an exact-quote check inside the assembler in milliseconds, so agents stop looping the full claim-checker (153 runs). | Custody and GPO-hash checks still need the real checker. |
| 10 | **Context-lean agent protocol** | A workflow rule, not a job. One short-lived agent per order or small family, fed only its dossier. Scripts print summaries, never whole texts. Bounds context so cached re-reads stop compounding. | More agents means more start-up overhead; family reasoning must be passed in explicitly. |

### Selected build

Combine **2, 3, 4, 5, 6, 8 and 9** into one zero-token job, provisionally `jobs/claim-kit`, and add **1** as its
second half. Everything is machine output and a lead, and nothing fills a judgment field by itself.

- **Excavator stage:**
  - segmenter v2 (2);
  - acting-provision locator with the effective-date resolver (3, 8);
  - own-terms end detector (4);
  - amendment-chain compiler (5).
- **Packaging stage:** one dossier per decided order (6), plus a blank decision sheet pre-filled with machine candidates.
- **Assembly stage:** reads decision sheets committed by agents and emits full claims, pre-gated with an exact-quote check (1, 9). claim-checker and the tracker then run as now.

Use **7** for the uniform families the excavators reveal. Adopt **10** in the next swarm's prompts. Measure
before scaling.

**Why this cut:**
- It targets the measured costs: hand-built JSON, re-reading texts, missing inventories, and ending dates found by hand.
- It also targets the main reason claims were rejected: missed earlier ends.
- It keeps every legal judgment with the agent and the reviewer.
- It keeps the Stage 19 claim format and the existing gate, checker and tracker unchanged.

**Success test (a pilot before any scale-up):** run the next 50 decided orders (one Codification family set)
through `claim-kit` and a context-lean swarm. Compare against this baseline:

- about 33k new-input tokens and about 2.1M cached re-reads per accepted claim (5.7M and 370M over 176);
- about 8 tool calls per accepted claim across producer and reviewer (1,474 calls);
- about 11% reviewer rejection.

The kit pays off only if tokens per accepted claim fall substantially **and** the rejection rate does not rise.
Also have a person spot-check 10–15 of the 130 ready claims to measure the true error rate, which no machine
or AI reviewer here can establish.
