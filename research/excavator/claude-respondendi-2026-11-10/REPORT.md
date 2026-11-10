# Respondendi wave, 2026-11-10: lifting the undecided-status bottleneck

Named for the *ius publice respondendi*, by which Augustus let vetted jurists answer with standing authority, so that
each opinion did not need the emperor. The owner asked (2026-11-10) for a research workflow "to figure out an
ingenious way to lift this bottleneck for this project permanently. i don't want to have to answer for adoption
manually every time."

**Result in one paragraph.** The undecided route does not fail because the answers are unknowable. Of Papinian's 84
failed undecided attempts, none was genuinely unknowable, and the held evidence on main supports a status for 65 of
them (59 if six NOs that rest on statutes or rules not naming the order stay open). They failed on plumbing: the
frozen dossier cannot cite evidence the repository already holds, no undecided order can ever get a YES, a
self-executing order can never get a NO, and a valid status is thrown away whenever its lifecycle sheet is
unfinished. Adoption is the other bottleneck: the owner has approved every one of the 16 proposals ever offered on
this route, by the same standard, one ask at a time. This wave built **Respondendi** (`jobs/respondendi-adoption/`):
one standing rule the owner approves once (ask A-20261110-respondendi-standing-rule), limited in version 1 to a lot defined in advance
(express, named, unqualified revocations: 687 undecided orders already have such a held ending provision on an
acceptable original), with a status-only tier, cross-family audits that cover every member until the error bound is
met, adjudication, a stop rule, a cadence limit and reversal. The red team's verdict on the first draft shaped it:
the draft did not bound the error rate it claimed to. Projected conversion on the undecided route rises from a
measured 7.5% (16 of 212) to about 17-27% with the rule and status-only tier, and to about 45-60% for EO 7532 and
later once the routing fixes land. **Version 2** (section 7, ask A-20261110-respondendi-standing-rule-v2) puts every kind of undecided order under
one approval: express revocations (active), own terms (active), spent on issue including amendment-only orders (F5),
YES with a positive current source (F3) and working texts (F6). Each kind opens by itself, on its own audit
probation, when the merged claim kit declares its route live. After two hostile review rounds, 468 orders are
reachable today and 1,468 once F3, F5 and F6 land. Nothing here adopted a status, changed a count or certified
anything. Human-certified: 0.

## 1. Diagnosis: why 84 of Papinian's 90 undecided attempts did not become adoptable

Method. Six Fable 5.2 workers (effort high) each read about 14 failed orders in full: the assessment row, the
producer sheet, the producer report, the frozen `EVIDENCE.json`/`DOSSIER.json`, `STATUS_DECISION.json`, the
dispatch check, the status review and both blind arms (and the after-reveal reviews for the two planted controls).
Each then searched the held texts on main for the decisive later-event or current-status source. Three more Fable
workers tried to refute every "unknowable", "rule too strict" and "route defect" classification, every "yes", and
every claimed held source. A seventh worker classified the 27 Haloander failures (whole number range), and an eighth
gathered what Kean and the code already record. Per-order results: `DIAGNOSIS.csv` (one row per order, with the
refuter's verdict) and `DIAGNOSIS.json`.

Papinian, 84 failed orders, after refutation (each refuter checked every order of two groups; 11 of 84
classifications were corrected, 0 held-source claims were false):

| Primary cause | Orders | Held evidence supports NO | YES | Unknown |
|---|---:|---:|---:|---:|
| Route or tool defect (held but not routed, or a wrong machine artifact) | 37 | 22 | 12 | 3 |
| Missing later-event evidence | 24 | 8 | 0 | 16 |
| Rule too strict for what is knowable | 13 | 10 | 3 | 0 |
| Producer error | 10 | 10 | 0 | 0 |
| Genuinely unknowable | 0 | | | |
| **Total** | **84** | **50** | **15** | **19** |

Missing later-event evidence, by kind: current-status source 8, fact date (completion of a task, an appointment,
the end of a seizure) 8, statute 4, FR rule or agency notice 2, land order 1, unnamed later instrument 1. Six of the
50 NOs (EO 8490, 8617, 9181, 9231, 9372, 9408) rest on a statute or general rule that does not name the order; under
D-20261021-unnamed-instruments and the answer to A-20261106-1 those stay open on the formal end (functional
exhaustion disclosed), so the conservative count of decidable orders is 59, not 65.

Haloander, 27 failed orders across the whole number range (not refuted): route or tool defect 10, missing later
event 11, rule too strict 5, producer error 1, unknowable 0; held evidence supports NO for 12, YES for 3, unknown 12.
Below EO 7532, 6 of 14 are decidable NO now from the order's own words or a held later order; the other 8 need fact
or land sources that no better printing would supply.

Where the attempts stopped: 67 producer-blocked, 6 dispatch-blocked, 1 rejected by the status reviewer, 8 rejected
by the lifecycle arms after the status was accepted, and 2 genuine planted-control claims rejected or never reviewed.

### The causes, by mechanism (Papinian and Haloander together)

1. **Held evidence never reaches the frozen dossier (route defect; the largest cause).** The dossier is built from
   later-events EO-to-EO edges, clause-drafts and current-law predicate leads. Selden's FR acting texts and statutes,
   FR citers, Montfaucon page checks, Photius GPO printings, theophilus-sources section texts and the U.S. Code note
   texts are not consumed, and `build.py:427` drops any actor not in the EO census (every public land order). Examples:
   EO 13354 (EO 13470 held; actor text over 50,000 bytes gets no id, `build.py:224-229`), EO 14231
   (EO 14389 of 2026-02-20 held), EO 2738 (EO 3377 held; later-events has no edges from replica texts).
2. **YES is impossible on the undecided route (tool defect).** No undecided dossier has a `CURRENT:` record.
   `current_evidence.py:17` refuses `#` pointers and `:77` accepts only .txt/.xml/.html, while current-law publishes the
   U.S. Code note texts as `USC_EO_NOTES.jsonl` (1,028 notes); theophilus section texts are declared under other
   orders' ids. Measured on main: 1,518 undecided orders have a current-law lead, 0 become a `CURRENT:` record.
   `status_overlay.py:686-690` then refuses every YES. Papinian: 15 failed orders lean YES on held
   evidence (EO 8695, 10624, 11225, 11866, 12661, 13329, 13411, 13505, 13647, 13748, 14051, 14191, 14233, 14318,
   14435).
3. **A NO needs an `ACT:`/`TERM:`/`ACTOR_TEXT:` id (rule too strict for what is knowable).** A self-executing order
   (a revocation-only order such as EO 12379, a land restoration such as EO 7621 or 5739), an amendment-only order
   whose consequence lives in its parent (EO 12178, 12378, 13552; the owner's Pothier answer P2) and an order whose
   decisive sentence was machine-typed `report_deadline` (EO 13116, 13064) have no admissible basis, however plain the
   held text (`status_overlay.py:678-685`). A `SUPPLEMENT:` excerpt can never be a basis (`source_supplement.py:119`).
4. **The text gate refuses working texts (rule too strict; dominant below EO 7532).** `status_overlay.py:691-693`
   requires `acceptable_as_original`, so the 2026-10-21 transcription ruling and the 2026-10-31 working-text ruling do
   not apply on this route. Measured on main: 6,052 of 10,691 undecided orders (56.6%) cannot get any status proposal,
   4,325 of them credited by the tracker as `original_supported` (ProQuest replicas checked, machine-read GPO
   printings, official printings). Jacquard adopted 888 status-only NOs on held working texts; this route refuses
   the same kind of text. Haloander: EO 3761, 2145, 4041, 341A blocked only by this gate.
5. **A valid status is discarded when the lifecycle sheet is unfinished (route defect).** 26 of 90 Papinian producers
   filed an approved NO status decision; only 17 were sent to the status reviewer (16 accepted), because status
   review runs only for members whose lifecycle sheet was submitted. 9 valid decisions (EO 10350, 10771, 11360,
   11575, 12072, 13024, 13204, 14036, 14072) were never reviewed. Of the 10 lifecycle rejections after an accepted
   status, none disputed the status: they were inventory gaps (4), a missed U.S. Code note sentence (2), a missed
   amendment, a strike-and-insert misreading, a wrong FR page and a preamble-only later-event span.
6. **Machine artifacts are wrong (tool defects).** The clause segmenter misses letter-spaced OCR headings
   (`S e c . 2 .`, `excavate.py:25`), Carter-era decimal sections (`1-101`) and restarts across Parts; fr-originals
   page spans stop on the first page when a GovInfo PDF bundles orders (EO 8494, 8617, 11905, 13294's page); OCR
   reads `[No. 7573]` as `[No. 75731` and sets a page check; `machine_hits_for_this_order` reports 0 when
   `MENTIONS.csv` has rows; theophilus `instrument_ids` are treated as the text's identity (42 bogus
   `ACT:EO:13329>EO:12333` records); `checker.py:933-947` fails verbatim quotes with footnote-fused numbers (EO 9446).
7. **Byte custody (tool defect).** FR PDFs whose text is committed are `custody_record_only` while Ptolemy is paused
   (EO 10603, 10917, 13411, 14223; Haloander 10955, 13820, 13836).
8. **Producer errors (checklist).** Missed U.S. Code notes, a "bound means block" rule applied to expressly revoked
   large orders (EO 14036 with 132 clauses), the strike-and-insert ruling misapplied, a dated pause read as
   emergency-dependent (EO 14198). The undecided prompt has none of the YES route's current-law and later-event
   checklist.
9. **Genuinely missing evidence (acquisition).** Fact dates for one-person waivers and wartime seizures (EO 7778,
   9408, 9554, 4770, 5094, 9025), land-status records for withdrawals and refuges (EO 8104, 8153, 8511, 8649, 9124,
   9390, 2225, 5495, 3748), and a few statutes and agency rules. These are the orders where the honest answer is
   "open until a source is found", and the rule never fills them.

**What the refuters changed.** Four "yes" readings were withdrawn: EO 13013 and 11315 are amendment-only (spent on
issue under the owner's Pothier answer P2, the surviving text belongs to the parent), EO 7721's held evidence stops
in 1940, and EO 9680's NO was rejected by the batch's own status reviewer (an undated wind-up command keeps it open;
EO 10917 has the same wording). EO 14223 is a report order, which the 2026-10-21 report-deadline ruling keeps open
until express revocation. EO 8724 and 10803 were producer errors, not kit rules (a usable TERM record was in the
dossier; EO 10803's statute has a savings clause). EO 8790, 8494 and 10917 move to missing evidence: fixing their
tool defects would not decide them. The refuters applied one standard to performed one-time commands: unknown unless
a held source dates the performance.

### Earlier findings, and what is fixed on main today

The prior-findings worker checked each recorded defect against main (854514831e):
- Dorotheus defect 1 (transcription refusal on the overlay route): **not fixed** (`status_overlay.py:691-693`).
- Selden supplement reach to undecided dossiers: **fixed** (48da66f755), but a supplement still cannot be a status
  basis, and 4,174 undecided orders have no ACT, TERM or current-law lead at all.
- Bentham's undecided rate: **fixed in code** (measure.py 410-422), but it reads only Haloander's 3 of 30; Papinian's
  90-order sample has no `DISPOSITION.json` with `undecided_measure`, and the plan's 0.10 rate ignores that 6,052
  orders cannot get a proposal and none can get a YES.
- Pothier's 2,139 family-doctrine status leads are read by no claim-kit code or undecided prompt.
- Mechanical ceiling today: at most 3,550 of 10,691 undecided orders can get a NO proposal, and 0 a YES.

## 2. Permanent fixes, one per major cause

| # | Cause | Fix | Kind | Orders it reaches (measured basis) |
|---|---|---|---|---|
| F1 | adoption by per-order owner decision | **Respondendi standing rule** (built, this PR) | route | the lot: 687 undecided orders with a held named whole-scope ending (652 with no page check owed); 7 of the 9 past owner adoptions are in it |
| F2 | valid status discarded with an unfinished lifecycle | **status-only tier**: publish as `partial_research`, adopt the status alone (built, this PR) and send every valid status decision to review (checklist item 15) | route | Papinian: 9 unreviewed valid NO decisions of 90 |
| F3 | no `CURRENT:` record | current-law publishes each U.S. Code note as an attributed .txt extract with a SOURCES.jsonl declaration (url and sha of the release-point zip); theophilus declares section texts by their own identity | job + tool | 1,518 undecided with current-law leads; Papinian 15 YES-leaning; pool: 769 undecided orders printed as U.S. Code notes (734 with no ending signal), 453 named in eCFR text |
| F4 | held acting texts not routed | the dossier freezer reads Selden acting texts, statutes and FR citers, Photius printings and PLO texts as `ACTOR_TEXT`, with ids for overflow texts; a held, hash-verified `SUPPLEMENT:` official text may be a basis | tool | 22 Papinian route-defect orders where held evidence supports NO; pool: about 238 orders gain an ending only from a U.S. Code ended-status note or an amender's status line |
| F5 | NO basis for self-executing and amendment-only orders | an `OWN_TEXT` basis: the held original's exact operative sentence, with mechanism `spent_on_issue` or `follows_parent` and, for the parent case, the parent's end; `report_deadline` typing reviewed | rule (kit) | Papinian 12178, 12378, 12379, 13013, 13116, 13552, 7621; Haloander 5739, 341A; pool: Pothier holds 1,131 own-text NO leads (530 spent on issue, 601 merged into parent), 103 on acceptable originals until F6 |
| F6 | text gate | accept a working text the tracker already credits (`original_supported` grades, or a Lachmann working-text confirmation), with the standing replace-and-recheck note | rule (kit) | 4,325 undecided orders; 369 of them already have a whole-scope ending ACT |
| F7 | machine artifacts | segmenter headings (letter-spaced, decimal, Part restarts); fr-originals multi-order page spans; OCR closing tags; `machine_hits` from MENTIONS.csv; theophilus identity | tool | inventory rejections (4 of 10 lifecycle rejections) and several blocks |
| F8 | producer errors | `jobs/respondendi-adoption/UNDECIDED_CHECKLIST.md` for producers and arms (written, this PR) | prompt | 7 of 84 producer errors; 10 lifecycle rejections; all 10 Papinian lifecycle rejections were checkable items on the list |
| F9 | byte custody | Ptolemy's release-asset store for the FR PDFs whose text is committed (D-20261106-encyclopedie-storage) | acquisition | 7 orders across the two probes; pool: 1,361 acceptable-original undecided orders are custody-only, only 111 in Ptolemy's queue |
| F10 | missing facts and land records | shared acquisition jobs: Official Register appointment facts; PLO texts and BLM/BIA land-status records; NEA continuation notices | acquisition | the genuinely open orders |

Pool counts are machine leads measured on main by the fixes designer (`DESIGNS.json`, design:fixes), upper bounds on
eligibility, not findings about any order. It also recommends parking the fact-date families (one-person waivers,
wartime seizures, about 16 of 117 diagnosed orders, all unknown) out of draws until a source exists.

F3-F7 change pinned compiler or policy files (`status_overlay.py`, `build.py`, `current_evidence.py`,
`excavate.py`), so each needs its own reviewed PR, a claim-kit rebuild and re-prepared packets. They are proposed as
separate sessions, not done here. F5 and F6 apply rulings the owner has already made (D-20261028-evidence-decides,
the 2026-10-21 transcription ruling, the 2026-10-31 working-text ruling, the Pothier P2 answer); they need no new
policy, only the kit to stop refusing what those rulings allow.

## 3. The standing adoption rule and the machinery (version 1; superseded by version 2, section 7)

This section records version 1 as first built and reviewed; section 7 gives the rule now asked for.

**Rule:** `jobs/respondendi-adoption/RULE.md`, sha256 `85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934` (LF bytes; `respondendi.py rule-sha`). In short:

- **Scope, one lot (the "Hexapla" lot, after Origen's side-by-side texts):** the order's whole-order end is an
  express, named, unqualified end by a later order or proclamation. A zero-token check reads the claim's located
  ending quote: an ending verb in the clause around the order's number, no qualifier (in part, so far as, except, to
  the extent ...), no section heading in between, the end on or after the actor's signing date. Own-terms ends,
  amendment-only orders, statutes, working texts and every YES stay on named owner decisions until each has its own
  lot. Measured size: 687 undecided orders have such a held provision on an acceptable original (652 with no page
  check owed); in Papinian's random draw, 22 of 90 were in this class and 6 of them were adopted today.
- **Conditions per order:** admitted inside a Bentham action; undecided and in the census; an independent status
  review accepted it; both blind arms (separate contexts, distinct from the producer and the status reviewer) upheld
  the exact claim hash; every planted control rejected by every arm, at least 2 a review set, of 2 kinds, one
  status-determining (partial end presented as whole, transfer presented as end, later event removed, swapped ending
  source, wrong order's text); the checker passed the exact claim; every file pinned. Status-only tier: a
  `partial_research` claim whose open gaps are only `unresolved_material_gaps` and whose checker passed the
  original-text, ending-basis, savings and counterevidence steps adopts its status and files no claim.
- **Audit plan (after Wald's sequential analysis):** per process stratum (prompts, checklist, kit code, lot, model
  families), every member is audited by a person or another model family until the 95% upper bound on the error
  rate is 5% (59 audits with no confirmed error, 93 with one, 124 with two; the Jacquard standard, D-20261031-jacquard);
  then 20% of each lot, at least 2, seeded by the plan's hash. Nothing reaches the ledger before its audits. A
  disagreement goes to a third reviewer; only a confirmed error counts, keeps that order out and forces a full audit
  of its lot. Two confirmed errors in 59 audits, or a bound above 10% after 30, stop the stratum until the owner
  resumes it. A disagreement unadjudicated for 7 days blocks every adoption.
- **Limits:** 60 orders a lot, 300 a week, one lot a day. Frozen overlay evidence pins the whole status ledger, so
  each adoption stales packets in flight; adopting once a day after the batches complete bounds the rebuild churn.
- **Reversal:** the row leaves the ledger and the lot's rows; a filed claim stays (claim files are append-only,
  `publication_audit`) with an unresolved source-audit hold; a pinned reversal record says why.

**Machinery:** `respondendi.py plan | audit-record | adjudicate | adopt | reverse | status | report | verify`. Every
`--write` refuses unless a committed Kean decision and a committed owner-ruling file under
`research/readiness/owner_rulings/` both carry `respondendi-rule-sha256:85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934`. `adopt` writes the lot's
`ADOPTION_ROWS.csv`, `LOT.json`, `AUDITS.jsonl` and `RULE_AT_ADOPTION.md`, appends the ledger rows, inserts one
pinned `accepted_additions` entry, files whole-case claims byte-identical to the reviewed proposal lines, runs
`population.validate_inputs`, and restores every byte if the decided count did not grow by exactly the adopted
orders. It changes no pinned compiler file (`population.py` untouched). 42 tests in v1 (67 in v2), run by road-tests.

**Replay on real receipts.** Under the first draft, every condition held for the 9 orders the owner adopted
(Haloander 3, Papinian 6) except the admission receipt, which predates `admission.py`, and no other proposal line
exists in those completions. Under version 1, 7 of the 9 are in the lot (EO 12082 and 7814 end by their own terms),
and no past completion qualifies, because each review set had one untyped date-shift control. The first lots
therefore come from the next wave, run by `UNDECIDED_CHECKLIST.md`.

**What the red team changed** (`DESIGNS.json`, design:redteam-throughput). The first draft let one disagreement
stop everything and audited 34% of lots while all arms were one model family. Under the measured cross-family
non-uphold rate of 2 of 31 (Sinclair), a run of 59 clean audits has a 1.9% chance, so probation would not have ended
and about 19 stops would each have needed an owner decision. Common-mode errors sit in the dossier itself
(`current-law:usc 0 hits` false for 9 orders; a neighbour order's text as the sole clause), so a different family
helps on commission errors and not on omissions; the removed-later-event plant defeated reviewers of both families
in Septuagint. Hence the lot restriction, full audit to the bound, adjudication, typed controls and the stratum
fingerprint.

**What an agent cannot do with it.** It cannot adopt without the two committed owner artifacts. Nothing in code can
tell who wrote a committed file; the real guard is that both reach main only through a pull request the owner
merges, as every count-changing change does today.

## 4. Throughput, before and after

Measured today (undecided route, both arms Anthropic, owner adoption by named decision):

| Measure | Value | Basis |
|---|---|---|
| Adopted per attempted order, EO >= 7532 | 6 of 90 = 6.7% (95% 2.5-13.9%) | Papinian u01b, u02, u03 |
| Adopted per attempted order, whole range | 3 of 30 = 10% (2.1-26.5%); below EO 7532: 0 of 14 | Haloander |
| Pooled, three probes | 16 of 212 = 7.5% (4.4-12.0%) | Dorotheus 7/92, Haloander, Papinian |
| Workers per attempted order | 0.51 USD (Papinian 46.23/90), 0.40 (Haloander 12.12/30) | wave cost records |
| Workers per adopted status | 7.71 USD (Papinian), 4.04 (Haloander) | same |
| Owner decisions | one ask and one hand commit per batch (A-20261107-haloander-adopt, A-20261110-papinian-adopt-u01b/-u23; 9999c3a6bf, 936fa6ff55) | Kean |
| Whole pool at today's rate | about 800 of 10,691 (470-1,280) | 7.5% (4.4-12.0%) x 10,691 |

Projected (per 90 attempts on EO 7532 and later unless stated; each line adds to the one above):

| Step | Adopted statuses | Basis and uncertainty |
|---|---|---|
| S0 today | 6 (6.7%) | measured |
| S1 Respondendi rule, lot only | 6, with no owner decision per batch | the lot is 22 of 90 of the draw (24%, 16-35%); 6 of those 22 adopted today (27%, 11-50%); cost moves from owner time to cross-family audits (every member until 59) |
| S2 + status-only tier, every valid decision reviewed | 15-22 (17-24%) | 26 valid NO decisions of 90 (19.8-39.4%); status review accepted 16 of 17; 0 of 10 arm rejections disputed the status; within the lot the red team projects 20 of 22 (91%, 71-99%) with one correction pass |
| S3 + F3-F8 routing and kit fixes, more lots | 40-55 (45-60%) | held evidence supports a status for 59-65 of the 84 failures plus the 6 adopted (65-71 of 90, the upper bound); discounted for producer completion (26 of 47 NO-leaning orders filed a decision today), status review (94%) and arm agreement; each new class needs its own lot and audit plan |
| Below EO 7532, S3 | 25-40% | Haloander: 6 of 14 decidable NO on held evidence once F5/F6 land; the other 8 need fact or land sources (F10) |

Over the whole pool after S3: about 1,900-2,500 statuses for EO 7532 and later (4,215 orders) and 1,600-2,600 below
(6,459 orders), against about 800 at today's rate. Under rule v1 alone (lot only), the reachable population is the
687 lot orders, of which about 90% could be adopted after one correction pass (about 620), against about 165 at
today's in-lot rate. These are projections, not measurements; the first lots under the
rule are the measurement, and Bentham should rank the undecided action on them. At about 0.5 USD of workers per
attempted order plus audits (34% of adopted orders on probation), working the whole pool costs on the order of
6,000-8,000 USD list, spread over the weekly cap.

## 5. What the owner is asked

**A-20261110-respondendi-standing-rule-v2** (recorded in Kean, `HANDOFF/KEAN_ASKS.md`; it supersedes A-20261110-respondendi-standing-rule, which asked
about v1): approve `jobs/respondendi-adoption/RULE.md` version 2 (sha256 `b37743092fa817a43add4fdc12733a11faf03c7692f7f1949579eff110d2a659`) as a standing rule. **Recommended:
yes.**

- **What approval covers.** Undecided-route proposals of every lot kind in the rule are adopted after the audits it
  requires, without a per-order or per-kind decision. Kinds whose route is not yet on main open by themselves when
  the claim kit's fix merges, each on its own probation.
- **How to approve.** Commit, through a merged pull request, an owner-ruling file under
  `research/readiness/owner_rulings/` and a Kean decision whose ruling is exactly
  `Owner approves respondendi-rule-sha256:b37743092fa817a43add4fdc12733a11faf03c7692f7f1949579eff110d2a659`. The agent who records the owner's answer does that, as for every
  other owner decision.
- **To approve fewer kinds or other numbers,** amend the rule; the recording agent computes the new hash.
- **What does not change.** Statuses stay provisional AI hypotheses, human-certified stays 0, and count-changing pull
  requests still need the owner's merge.

**Not asked here, but needed for S3.** F5 and F6 carry out rulings already on the books (the 2026-10-21
transcription ruling, the 2026-10-31 working-text ruling, the Pothier P2 answer, D-20261028-evidence-decides), so they
need code review, not new policy. Two doctrinal questions the refuters found unsettled are left for the owner's
existing rulings to govern, not asked again: undated wind-up commands after an abolition (EO 9680, 10917) and report
orders (EO 14223, the 2026-10-21 report-deadline ruling).

## 6. Costs of this wave

List price from `jobs/necker-costs/PRICES.json` (Fable 5.2 priced by its Fable 5 row, cache reads 1 USD per million),
last usage per message id (`WORKERS.json`):

| Role | Model, effort | Agents | Output tokens | Cache reads | USD | Wall time (UTC) |
|---|---|---:|---:|---:|---:|---|
| Diagnosis (6 Papinian groups, Haloander, prior findings) | Fable 5.2, high | 8 | 645,020 | 124.1 M | 184.75 | 13:50-14:12 |
| Refuters | Fable 5.2, high | 3 | 171,658 | 25.3 M | 42.27 | 14:12-14:24 |
| Designers (fixes, standing rule, red team) | Fable 5.2, high | 3 | 145,886 | 11.8 M | 27.51 | 14:24-14:33 |
| Hostile red team of v2 (two rounds) | Fable 5.2, high | 1 | 144,226 | 13.3 M | 28.66 | 15:21-16:09 |
| Coordinator (this session: diagnosis, v1, v2, code, report) | Opus 5.5 | 1 | 464,384 | 129.6 M | 41.85 | 13:36-16:31 |
| **Total** | | **16** | | | **325.04** | |

Owner's instruction: Fable 5.2 on High for the research storm. Coordination stayed on Opus (legal judgment, rule
design, integration, all code); no production claim batch ran and no dossier was produced.

## 7. Version 2: every lot kind under one approval (owner follow-up, 2026-11-10)

The owner found v1's single lot "really really disappointing" and asked for one rule usable across the whole census:
one approval for every kind of undecided order, each new kind opening on its own probation with no owner decision
per kind. Version 2 (`RULE.md`, sha256 `b37743092fa817a43add4fdc12733a11faf03c7692f7f1949579eff110d2a659`) does that. Two rounds of hostile review by a separate Fable 5.2
context reshaped it.

**Kinds.** The kind is fixed by the kit-emitted record the status decision cites, never by the producer's wording:
- an `ACT:` record: express named revocation;
- a `TERM:` record: own terms;
- an `OWN_TEXT:` record: spent on issue, including amendment-only orders under the owner's Pothier answer P2 of
  2026-11-09;
- a `CURRENT:` record: YES.

A kind with a route is active only while GitHub's main declares that route live: `UNDECIDED_ROUTES` in
`jobs/claim-kit/status_overlay.py`. That constant was agreed with the F3-F6 session (Accursius); only the pull
request that makes a route's gate live adds its name, and a test there ties the constant to the gate. The kit's
OWN_TEXT gate re-derives each record from the frozen original, so a hand-written record fails.

The working-text basis (F6) opens the same way. An outer-bound lot for one-person orders is reserved: it enters only
by an amendment after the owner decides the Ulpian ask.

**Reachable orders per kind, measured on main.** Sources: `KINDS.json` and `measure_kinds.py`, which apply the rule's
own predicates to the compiled leads. Each order is counted once, in the order below. These are eligibility upper
bounds from machine leads, not findings; each order still needs the full route and its audits.

| Kind | Text basis | State on main today | Reachable orders | Below EO 7532 | EO 7532 and later |
|---|---|---|---:|---:|---:|
| `express_named_revocation` | original | active | 468 | 0 | 468 |
| `express_named_revocation` | working | active; working text needs F6 | 2 | 0 | 2 |
| `own_terms` | original | active | 0 | 0 | 0 |
| `own_terms` | working | active; working text needs F6 | 0 | 0 | 0 |
| `spent_on_issue` | original | needs F5 (route own_text) | 103 | 103 | 0 |
| `spent_on_issue` | working | needs F5 (route own_text); working text needs F6 | 660 | 660 | 0 |
| `yes_current` | original | needs F3 (route current) | 234 | 0 | 234 |
| `yes_current` | working | needs F3 (route current); working text needs F6 | 1 | 1 | 0 |
| `no kind reaches it on held leads` | - | - | 9,223 | 5,710 | 3,513 |

**What the numbers mean.**
- 468 orders are reachable by the kinds active today (all express revocations).
- 763 more once F5 is merged. The F5 classifier itself reaches 763 undecided orders, with measured precision of
  42 of 50, so every spent-on-issue member is audited.
- 235 more once F3 is merged, and 2 once F6 is merged.
- That makes 1,468 in all. The first v2 draft claimed 3,465, and v1 620. The difference is the
  price of the two review rounds. Each screen they added keeps a measured way of adopting a wrong status out of the
  lot.
- Own terms reaches 0 today: no machine TERM text both sets an expiry for "this order" and is free of later acts,
  extension wording and actor texts. The kind stays in the rule and opens as soon as cleaner TERM records exist.
- Two limits make the count low for old orders:
  - the second witness was measured only from the OFR catalog, which starts at EO 7532 (older orders' frozen
    histories carry other notes the tool reads);
  - spent-on-issue below EO 7532 was counted from Pothier's P1/P2 leads.
- The 9,223 orders no kind reaches need sources first (Linnaeus's bulk sources by order type) or remain open. The
  rule never fills a gap.

**What the two review rounds changed.**
- *Express check.* In round 1, all 31 adversarial quotes passed: partial, negated, conditional, future and revival
  texts, and digit-only matches such as EO 341 for EO 341A.
  - Now: one clean sentence of the cited `ACT:` provision introduces "Executive Order (No.) N" by its full id.
  - Every sentence naming the order must be free of qualifiers, with an extended list after round 2, and no
    "is amended" may stand before the verb.
  - Words broken at line ends are rejoined before matching.
  - The claim must quote the provision, and the end must equal the record's effective date.
  - Exceptions and savings refuse.
  - A second witness is required: an anchored catalog entry, "Revoked by: EO <actor>", with no parenthesis or
    partial wording.
  - Any catalog act after the claimed end refuses, as do reinstatement leads and same-actor partial leads.
  - `body_abolished` is out.
- *Activation.*
  - Round 1: activation was a record prefix anyone could write. It is now `UNDECIDED_ROUTES` on GitHub's main.
  - The kit's own gates (`_sealed`, `_decision_errors`, `_review_errors`) are re-run.
  - The kit files must equal main's.
  - The proposal must bind the bundle's exact decision and review hashes.
- *YES.* It no longer rests on absence:
  - a positive `CURRENT:` record;
  - an allow-list of catalog labels;
  - no ending signal in any observation, event or current-law lead;
  - no missing source, no actor text, no ending TERM kind;
  - every machine search complete;
  - a `later_event_removed` control planted on a YES claim;
  - every member audited forever, and a stop on one confirmed error.
- *Own terms and spent on issue.*
  - Own terms takes only whole-order stated terms whose text sets an expiry for the order, with no extension wording
    and no later act of any kind.
  - Spent on issue needs a whole-scope `OWN_TEXT:` record whose whole-order test found no continuing sentence.
  - Spent on issue has no status-only tier and is always fully audited.
- *Approvals.*
  - Round 2: a conditional approval ("... for the express kind only") was read as a full approval.
  - Approval is now the exact phrase, read from GitHub's main.
  - The local origin/main must equal `git ls-remote` at the moment of writing, so a hand-moved ref refuses.
  - A partial approval needs an amended rule with a new hash, which keeps the owner's one-approval design.
  - A suspension counts on any mention, so natural wording fails closed.
- *Audits.*
  - Round 2: any file was accepted as evidence.
  - Each audit and adjudication now pins its own file in the lot's `audit-evidence/` folder, never reused, naming the
    order and its exact claim hash. An AI's evidence is a JSON run receipt whose model id gives its family. A person
    must be on the rule's `human_auditors` list (today: the owner).
  - Only in-sample agreeing audits of adopted lots count.
  - Reversals count as errors, in date order.
  - An order with a confirmed error or a reversal never returns under the rule.
- *Stops.*
  - Stops apply per kind across process changes, so a new prompt cannot escape a stop.
  - A resume names an audit count no larger than the findings that existed, so an inflated count resumes nothing.
- *Mechanics.*
  - The command line takes no dates.
  - Each member is sampled by its own claim hash, so lot composition cannot steer the sample.
  - Completions have a maximum age.
  - The second-reversal bug and re-planning of expired plans are fixed.
  - `verify` checks audits and their evidence.
- *Known limits, not fixed:*
  - There is no fresh re-freeze comparison, because frozen evidence pins the whole ledger.
  - Provision and catalog texts are not re-read from held files.
  - Prompts are still named by the planner.
  - Control kinds are labels recorded by the coordinator.
  - All of these are mitigated, not closed, by the cross-family audit of every member during probation.

**Replay of the 9 past owner adoptions under v2:** 5 qualify (EO 11957, 12348, 9245, 10679, 11962). The other four
stay on named decisions:
- EO 9674 ("the office established by Executive Order No. 9674 ... terminated") ends a body, not the order by name.
- EO 10733 and 7814 cite no qualifying record.
- EO 12082 is an own-terms end that cites a later order.

No past completion qualifies outright, because each review set had one untyped control.

## Files

`DIAGNOSIS.csv` (one row per failed order, 84 Papinian and 27 Haloander, with the refuter's verdict), `DIAGNOSIS.json`
(every worker's full return), `DESIGNS.json` (the three design reports), `WORKERS.json` (model, tokens, time and list
price per worker), `MEASURES.json`, `workflow.js` (the workflow script). Code: `jobs/respondendi-adoption/`.
