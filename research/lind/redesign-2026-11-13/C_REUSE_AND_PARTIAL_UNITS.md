# C. Reusable research and partial units of progress (analyst 3 of 3, 2026-11-12)

Repository HEAD read: `ed1df44a3053488ed60911864da2acbe4e74e945`. Nothing was launched, no git state was changed, and no web
access was used. I worked from committed outputs only.

How numbers are labelled:
- **[obs]** a count I computed or read, with its path.
- **[interp]** my reading of what the count means.
- **[proj]** a projection I have not measured.
- **[unres]** a question I did not settle.

Tracker counts come from `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`, generation 43290372543-1, 15,002 orders,
1,251 ready **[obs]**.

## Summary

1. **The best lever is the 126 railway emergency-board orders, not a new acquisition.**
   - **What is already in place.** The owner's rule exists (D-20261108-board-rule). The bytes of every report are stored
     and re-hashed (`jobs/eumenes-nmb-reports/output/SUMMARY.json`: 119 PDFs covering 126 orders) **[obs]**.
   - **What blocks them.** Of the 126, 123 are not ready, and 117 have exactly one blocker, `FIRST_END_UNRESOLVED`
     **[obs]**.
   - **Where they sit in the plan.** These 117 are 54% of Bentham's rank-9 action `production.one_step_away` (117 of 217,
     `jobs/bentham/output/strata/production.one_step_away.txt`) **[obs]**.
   - **Resolved or only cited?** One legal analysis (the rule) settles the end mechanism for all of them. Each order
     still needs one mechanical per-order fact (the transmittal-letter date) plus an exception check.
   - **Touched vs resolved:** 126 touched; up to 117 resolvable **[proj]**, less those with extensions, supplemental
     reports or mismatched reports. That subtraction is not measured.
   - **Attempted?** No board production has run **[obs]**: Kean wiring note on D-20261108-board-rule ("No production
     run yet").
2. **"Official EO 13286" is not an acquisition.** The official text is already held. The claim kit still represents
   EO 13286 as an American Presidency Project mirror **[obs]**. The general form of this defect reaches 1,415 target
   orders **[obs]**. Fixing it makes sources citable for those orders; it decides nothing for them.
3. **The National Emergencies Act continuation notices are a shared citation.**
   - 94 orders' blocked producer text names them **[obs]**.
   - They are not in the fetch queue, and Bentham counts them as 0 orders because the tracker has no blocker code for
     them **[obs]**.
   - Each emergency has its own series of notices, so this is roughly one acquisition per emergency, not one in total.
     It settles only the emergency predicate, and each order still needs its own clause analysis.
4. **Partial research is being lost and redone.**
   - **Not readable by the next wave.** 1,090 written blocked gaps sit in 215 `decisions.csv` files, and 498 blocked
     `ASSESSMENT.jsonl` rows carry a basis sentence. The claim kit's prior-research discovery cannot see either format
     **[obs, code]**.
   - **Repeated orders.** 258 orders were attempted in two or more waves. 130 were blocked or unresolved more than once
     **[obs]**.
   - **Verification thrown away.** Reviewers' affirmed findings inside rejected claims are dropped when work is carried
     forward **[obs, code]**.
   - **Accepted statuses not in the ledger.** 42 orders have an accepted status review but are still undecided in the
     ledger **[obs]**.

---

## Q1. Where one effort could settle questions for many orders

There are two kinds of shared effort:
- **Reusable research:** one analysis settles the same proposition for many orders.
- **Shared citation:** one document that each order must still be analysed against, clause by clause.

### Lever 1: emergency-board orders (National Mediation Board reports plus EO 12553). Reusable research plus one mechanical fact per order

**Counts [obs]:**
- **Coverage.** 126 orders have stored report PDFs. 3 are ready and 123 are not.
- **Blocker combinations among the 126:**

  | Blockers | Orders |
  |---|---:|
  | only `FIRST_END_UNRESOLVED` | 117 |
  | `FIRST_END_UNPROVED` + `NO_CLAUSE_INVENTORY` + `SAVINGS_RESIDUALS_NOT_CLOSED` | 5 |
  | only `CLAIM_INCOMPLETE` | 1 |
  | none (ready) | 3 |

- **What the blocker means.** `FIRST_END_UNRESOLVED` is set by `jobs/readiness-tracker/tracker.py:842` when a v2
  claim's end is only a `not_later_than` bound. Here that bound is the formal revocation (EO 12553 or EO 12379).
- **EO 12553 is a shared citation, not a resolution.**
  - It touches 228 orders in `jobs/claim-kit/output/MISSING_SOURCES.jsonl` ("target provision not located"); 45 are
    ready and 183 are not.
  - The ending step is open for all 183.
  - 55 of the 183 are `FIRST_END_UNRESOLVED`; the others are 51 with no provisional status and 48 with no clause
    inventory.
  - The formal revocation is an upper bound, not the first end (owner ruling R3; Haloander `board_rule.txt`).

**What still has to be done for each order after the shared work [interp, from `research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt`]:**
- **(a)** Read the transmittal-letter date from the order's own report.
- **(b)** Check for amendments that extend the reporting time, and for supplemental reports or reconvening.
- **(c)** Compute the no-change sentence's end at 30 days after the report, using the inclusive reading and stating the
  exclusive reading as the alternative.
- **(d)** Decide any other clause (compensation, another officer's duty) on its own evidence.
- **(e)** Block the order if the report's board number, parties or date do not match it.
- **(f)** File a replacement proposal and get a named owner adoption (D-20261110-papinian-board-bytes).

**Attempted?**
- **Haloander (2026-11-07).** Drafted the rule. At that time 79 reports were held, 58 had never been requested and 9 had
  been requested but not found (`evidence/R3_BOARD_REPORTS.csv`). It enqueued the 58, and its budget ran out before a
  pilot.
- **Eumenes (2026-11-10).** Stored the bytes (F-20261110-nmb-reports-stored).
- **Not yet confirmed.** I did not confirm that the checker adapter patch
  (`research/encyclopedie-campaign/storage/checker_adapter.patch`) is merged; the Kean wiring note on
  D-20261110-papinian-board-bytes says "Upload and adapter not built" **[unres]**.

**Assessment [interp]:**
- This is the only candidate where the legal analysis is already done and owner-approved, the evidence is already held
  with verified bytes, and the remaining per-order work is a date lookup plus a bounded exception check.
- Bentham ranks `production.one_step_away` at 138.6 expected dossiers for $72. More than half of that stratum is these
  orders, but Bentham prices them at generic one-step rates, not as a known class.

### Lever 2: official texts held but registered as mirrors (EO 13286 and 1,302 other actors). A registration fix that makes sources citable

**Counts [obs]:**
- **The official text is held.** `jobs/fr-originals/output/texts/EO_13286.txt` is the govinfo PDF of 68 FR 10619
  (sha256 `0f74e21c…`). Dorotheus already cited it on 2026-11-06 (dorotheus-yesprobe y03, EO 12146).
- **The kit still uses the mirror.** Of the kit's actor representations for EO 13286 (213 lines mention it in
  `jobs/claim-kit/output/ACTING_REPRESENTATIONS.jsonl`), the representations used are graded `mirror_transcription`,
  from the American Presidency Project or the Opus zip.
- **The blocked targets' dossiers carry the mirror grade.** All 11 YES targets that Papinian named as blocked on EO 13286
  have a current dossier with the mirror grade (`jobs/claim-kit/output/dossiers/EO_*.json`).
- **Scale.** EO 13286 acts on 87 targets: 44 undecided, 35 YES not ready, 5 NO not ready, 3 ready.
- **General form.** 1,303 actors appear in the kit's acting representations only with mirror (or no) grade, although
  `jobs/fr-originals/output/texts/EO_<n>.txt` exists for them. They act on 1,415 distinct targets: 914 undecided,
  282 NO not ready, 79 YES not ready, 140 ready.

**Resolved or cited? [interp]:**
- A shared citation. Switching the representation to the official printing removes the "later event rests on a mirror"
  block for every target at once.
- Each target still needs its own clause-level reading of what EO 13286 changed, and whether the change ends, transfers
  or continues each clause.
- The fr-originals texts are OCR leads ("Not an authenticated transcription: check the PDF pages"), so a page or quote
  recheck may still be owed **[unres]**.
- This matches F-20261104-5 ("later orders registered only as APP mirrors though official FR texts are held"). That
  finding recommended registration on 2026-11-04. On 2026-11-10 Papinian logged it as an acquisition
  (F-20261110-papinian-eo13286-mirror), so the record now misnames the remedy.

### Lever 3: National Emergencies Act continuation notices. A shared citation, about one acquisition per emergency

**Counts [obs]:**
- **Producer text.** I classified the blocked and unresolved gap text in every `ASSESSMENT.jsonl` and `decisions.csv`
  under `research/excavator/` by regex, so the counts are approximate. 94 orders' gaps name continuation notices,
  the National Emergencies Act or 50 U.S.C. 1622(d). Now 91 of them are YES not ready, 2 are NO not ready and 1 is
  undecided.
- **Papinian:** 34 of 225 drawn YES orders were blocked only by these notices (F-20261110-papinian-nea-notices).
- **Fetch queue.** No continuation-notice request is in `research/readiness/FETCH_QUEUE.jsonl`. Its 14 lines matching
  "continuation" are other things: board continuation, FACA charters.
- **Bentham.** `acquire.nea_continuation_notices` shows `orders: 0` and `yield_lift_not_counted: 292`, because the
  tracker has no blocker code for it (`jobs/bentham/output/CANDIDATES.json`).

**What still has to be done for each order [interp, case EO 13350 in Papinian y08 `decisions.csv`]:**
- The notices settle only one fact: the emergency continued through 2026-10-14.
- EO 13350 also needs a clause-level date for EO 13668's 2014 termination of the EO 13303 prohibitions that it modified,
  and actor texts for EO 13303 and EO 13315.
- Each emergency (Iraq, Iran, Somalia, Russia, and others) needs its own notice series, so this is a set of small
  acquisitions grouped by emergency.

### Lever 4 (worked case requested by the coordinator): the Manual for Courts-Martial family

**Facts:**
- **From the coordinator, verified by the parallel investigation:**
  - EO 12473 rescinds the 1969 Manual "prescribed by Executive Order No. 11476, as amended by Executive Order Nos. 11835,
    12018, 12198, 12233, 12306, 12340, 12383, and 12460 … effective August 1, 1984", saving proceedings begun before
    that date.
  - EO 12315 also amends the Manual but is not in the list.
  - No later-events or acting-representation pair links EO 12473, as actor, to any of these nine orders.
- **What I checked [obs]:**
  - **The ten orders (EO 11476 plus the nine amenders, counting EO 12315) are all undecided and not ready.**
    - Nine are at steps_done 1 with only `NO_PROVISIONAL_STATUS`.
    - EO 12198 is at 0, adding `ORIGINAL_FOUND_NEEDS_PAGE_CHECK|ONLY_COMPILED_TRANSCRIPTION_FOUND`.
  - **EO 12473 itself is YES, not ready.**
  - **Only one family member has been attempted:** EO 12340, in Lind, where the producer found the held EO 12473 text
    and was blocked because it was not in the dossier (`claude-lind-2026-11-12/FAILURES.md`, category IN).
  - **The direction of the kit's links is wrong.** In `MISSING_SOURCES.jsonl` the kit lists EO 12473 as actor for 9
    later Manual amenders, EO 13447 through EO 14130, which act on EO 12473 rather than the reverse.
  - **Sections that are not amendments to the Manual,** from grep of `jobs/fr-originals/data/full_run/texts/`:
    - EO 12315: sec. 6 (effective August 1, 1981) and sec. 7 (the Secretary of Defense shall transmit the amendments to
      Congress).
    - EO 12306: sec. 3 (Military Rule of Evidence 410 timing) and sec. 4 (transmit to Congress).
    - EO 12460: sec. 6 (effective immediately) and sec. 7 (transmit to Congress).

**Applying the owner's answer to A-20261106-pothier part (2) [interp]:**
- **The rule.** Under D-20261021-strike-and-insert plus D-20261028-evidence-decides, each amending command is spent on
  issue (or on its stated effective date). The inserted text lives inside the parent until the parent ends. Each claim
  records both.
- **The shared memo.** One reviewed memo can settle, for all ten orders:
  - the parent's end, 1984-08-01, by EO 12473;
  - the saving for proceedings begun before that date, as a disclosed residual;
  - the rule for an amender's exhausted command.
- **What each order still needs** (per-order inserts):
  - **(i)** Its own effective date, for example EO 12315 sec. 6.
  - **(ii)** Its independent non-amending commands. The transmit-to-Congress duties in EO 12306, 12315 and 12460 need
    evidence of performance, or must stay open under D-20261028.
  - **(iii)** Whether a later amender rewrote an earlier amender's inserted text before 1984. This would give an earlier
    clause end. Example: the preamble of EO 12340 refers to EO 12315, so later amenders may have replaced inserted
    paragraphs.
  - **(iv)** For EO 12315 only: a stated inference that its inserted text ended with the rescinded Manual even though
    it is not named. Under D-20261021-unnamed-instruments, the instrument that names the parent (EO 11476) ends the
    parent. The inserted text ends with the parent; the unnamed amending order is not itself ended by a revocation.
  - **(v)** For EO 12198 only: an official original with a page check.
- **Count.** Touched 11 (the parent, 9 amenders, and EO 12473 as actor). The memo fully settles the end question for
  about 6 of the 10 undecided orders: those with only amending sections (11476, 11835, 12018, 12233, 12340, 12383).
  The other 4 (12198, 12306, 12315, 12460) are only cited by it until their per-order item is closed. All 10 still need
  a status decision and review **[proj]**. Point (iii) is unchecked for all of them **[unres]**.

**The parallel proposal: a reviewed shared memo with per-order inserts, versus the act-override route [interp]:**
- **What the act-override route is.** `research/readiness/act_overrides/` holds 223 reviewed actor→target rows in 3
  Rastell files, including 32 for EO 12553 and 26 for EO 9830. It fixes one thing: the kit knows that actor X names
  target Y, at a span. It would fix the Lind EO 12340 integration block.
- **What it carries and what it lacks.** It carries no legal conclusion, savings analysis or exception list.
- **What the memo adds.** For this family it would add the parent-end-plus-saving analysis once, so 10 producers would
  not each re-derive it.
- **Risks, both recorded in Kean:**
  - F-20261023-2: "A shared source is not a shared legal answer".
  - F-20261021-3 and F-20261025-1: Norton produced zero independently reviewed reusable answers, and the ordinary batch
    already shares facts within one batch.
- **The test.** The memo is worth it only if it is reviewed once and then applied per order with a checked insert, and
  only for families above roughly 5 orders that share an ending instrument.
- **Recommendation.** Use the act override for the link, and the memo only for the shared legal step. The Manual family
  is a reasonable 10-order test, provided the per-order inserts (i) to (v) stay mandatory.

### Levers that were attempted earlier and are limited by acquisition (brief)

- **Family rules.** 0 of 748 certificates passed, because 552 of 571 targets had no located original (F-20261017-3).
- **Norton store.** `jobs/norton/output/CENSUS.json` holds 3 reviewed answers and 13 applications, with
  `additional_integrated_ready_cases` 0 **[obs]**. The machinery for reusable facts exists, but production waves do not
  write into it (see Q2).
- **Public Land Orders.** Pothier's land family has 1,270 members: 485 no, 4 yes, 781 open. The open ones need Bureau of
  Land Management (BLM) withdrawal case records and the PLO texts themselves (F-20261106-pothier-land). The owner allowed
  "no" leads to rest on BLM's tables of Public Land Orders, with a gap disclosed, but a filed claim still needs the PLO's
  own text. This is an acquisition-limited shared citation.
- **World War II termination.** No blocked producer text in the wave folders matched hostilities, World War,
  1946-12-31, 1947-07-25 or 1952-04-28 **[obs]**. Pothier's war family is 263 members, 228 open, and is said to be
  blocked on Alien Property Custodian records, not on the termination dates. I found no evidence that a shared World
  War II memo would decide many orders now **[interp]**.
- **CIS / Kaufman-Rogowski census deposit.** This is census work (the unnumbered series, A-20261112-cis-unnumbered-check),
  not lifecycle resolution. Not measured here.

---

## Q2. Is the pipeline counting the wrong unit of progress?

### What exists outside the "ready" count [obs]

| Store | Count | Path |
|---|---:|---|
| Producer `ASSESSMENT.jsonl` rows | 662 in 49 files, 6 waves (498 blocked, 148 submit, 16 unresolved); every blocked row has an `operative_force_basis` sentence and a blocker | `research/excavator/*/*/packet/ASSESSMENT.jsonl` |
| Producer `decisions.csv` rows | 2,926 in 215 files, 34 waves (1,093 blocked, 980 submit, 849 unresolved); 1,090 blocked rows carry a written `unresolved_material_gaps` | `research/excavator/**/decisions.csv` (named folder levels only) |
| Distinct orders attempted | 1,792; 240 in 2 waves, 18 in 3 waves | same |
| Orders blocked or unresolved in more than one wave | 130 (89 still not ready) | same |
| Blind reviews | 922 verdicts (632 upheld, 228 rejected, 62 upheld after reveal) in 149 files | `research/excavator/**/reviews/*.jsonl` |
| Rejected reviews | 228 on 139 orders (planted controls included, not separated); 117 had exactly one defect; 83 (on 65 orders) affirm verified elements in their `reasoning` | same |
| Accepted status reviews | 121 accept and 1 reject in 122 files, on 95 orders; **42 of those orders are still undecided in the ledger** (Sinclair 12, Papinian 10, Lind 8, Herschel 4, Codex 4, Haloander 3, other 2) | `research/excavator/**/overlay/EO_*/*/STATUS_REVIEW.json` |
| Tracker partial steps | 1,645 orders at 3-5 of 6 steps done, not ready | `READINESS_BY_ORDER.csv` `steps_done` |

The most frequent repeated pairs of waves:
- Apollo→Erasmus: 58 orders.
- Theophilus→Haloander: 26.
- Dorotheus-yesprobe→Papinian: 19.
- Icecore→Papinian: 17.

Some of these were deliberate rework.

### Is any of it carried into the next wave? Mostly not [obs, code reading]

- **Prior research does not see producer assessments.**
  - `jobs/claim-kit/prior_research.py` is the kit's carrier of prior work. Its notice reads "Prior producer/reviewer
    assertions, not new findings".
  - It scans only `.json` and `.jsonl` files (lines 120-135), so `decisions.csv` is never read.
  - It keys records on `instrument_id` plus a known schema (lines 427-455). `ASSESSMENT.jsonl` rows use `id` and have no
    schema, so they are invisible too.
- **Case EO 11023.**
  - Dorotheus (2026-11-06, yesprobe y02) blocked it on the Coast and Geodetic Survey statutes replaced by Pub. L. 107-372.
  - Papinian's packet four days later (y01 `PACKET.json#/prior_research`) records `no_prior_research_located` for all
    25 orders, EO 11023 included.
  - Papinian blocked it again on the same statute gap: "Text of Public Law 107-372 and the repealed 1948 Act".
- **Case EO 12146.**
  - Dorotheus cited the official EO 13286 text (`jobs/fr-originals/data/full_run/texts/EO_13286.txt`).
  - Papinian later blocked EO 12146 on "EO 13286 actor context … not read".
  - The earlier wave held the answer to the later wave's blocker.
- **Rejected reviews lose their verified findings.**
  - When a review is attached as prior work, only `REVIEW_KEYS` are kept (line 97). Those keys omit `reasoning`,
    `defects` and `evidence_checked`.
  - **Case EO 13476 (Lind, arm A, rejected).** The reasoning verifies:
    - identity (73 FR 60605-60607);
    - "all 71 quotes and hashes match";
    - the inventory is complete;
    - the sec. 4(d) sunset is correctly quoted;
    - no extension was found;
    - "The whole-order end of 2009-02-20 is right".
  - It rejects for two defects: a wrong count (31 vs 34) and the sec. 4(a) supersession dated at the sunset instead of
    on issue.
  - None of the verified material reaches a later packet in structured form.
- **Accepted statuses sit outside the ledger.**
  - Lind's 8 accepted NO statuses, among them EO 9739 (status accepted, lifecycle blocked on the end of the EO 9834
    sec. 3 saving), are still blank in the ledger. Status-only adoption waits on Respondendi
    (A-20261110-respondendi-standing-rule).
- **The tracker and Bentham do not see these blockers.**
  - The tracker has no blocker code for "continuation notice missing" or "later-event actor registered as mirror".
  - Bentham therefore prices those acquisitions at 0 orders. Kean itself says to count them "from producer assessment
    rows, not from the tracker" (F-20261110-papinian-nea-notices).
- **Precedent for a partial unit.**
  - fr-originals and Photius `FRAGMENTS.jsonl` already carry one partial unit, the original text. The tracker credits it
    as `step_original_text` without any claim.
  - Norton's `REVIEWED_ANSWERS.jsonl` and claim-kit `factual_events.py` already define a reviewed factual event that the
    kit consumes as an explicit later event. It holds 3 answers.

**[interp]**
- Progress is measured only as a complete 6/6 dossier, and Bentham optimises dossiers per dollar. Lifecycle research
  that is verified but incomplete has no unit that is stored, credited or carried forward.
- The cost appears as repeat attempts (130 orders blocked more than once) and as reviewer verification that has to be
  bought again on resubmission.
- The amount actually lost in dollars is **[unres]**. Repeat attempts and rework were not priced.

### A reusable partial unit (proposal; needs owner approval)

**One record: a "verified lifecycle proposition".** Each proposition has a type:

| Type | What it states |
|---|---|
| `event_occurred` | a later instrument, a report, an amendment |
| `clause_end` | scope id, date, date kind (exact or not later than), mechanism |
| `current_predicate` | a statute or CFR section current on 2026-10-14 |
| `source_identity` | this text is order N, from this printing |
| `search_negative` | a named search over a named corpus and date range found nothing |

Each record carries:
- the quote, span and source sha256, and dependency pins;
- the producer;
- each reviewer's model family and a verdict **on that proposition alone**;
- for negatives, the exact query and corpus edition.

**Rules that keep partial knowledge separate from completeness:**
- **No step is filled by a proposition unless that step's own rule already accepts it.** A clause end fills nothing
  until every clause of the order has one. A negative search is disclosure, never an end (D-20261028: "Disclosure keeps
  a gap visible but never fills it").
- **Publishing a proposition is separate from a status claim.** The site could show "verified events" for an order with
  no status. The ready and certified counts stay unchanged.
- **A proposition is invalidated when any pinned dependency changes,** the way Palsgraf impact selection already works
  (D-20261109-impact-scoped-checks).

**What it would need. I am not assuming permission for any of these:**
1. **An owner rule** that a reviewer's verdict may be scoped to a single proposition. Today review is `scope:
   whole_case`. It would also set whether a proposition upheld inside a rejected claim counts as verified when the
   rejection does not touch it. This is a review-standard change.
2. **A schema change.** Blind review output gains per-proposition attestations, and the producer `ASSESSMENT` /
   decisions output gains structured propositions instead of free text. Norton's model (`jobs/norton/model.py`) is the
   natural home.
3. **A tooling fix.** This one is probably engineering-only, but it changes what producers see, so I would ask first:
   `prior_research.py` should read `ASSESSMENT.jsonl` (`id`) and `decisions.csv`, and keep `reasoning`, `defects` and
   `evidence_checked`.
4. **A Bentham or owner rule** to report verified propositions and steps closed alongside dossiers. It is a secondary
   measure, never in the headline.
5. **An owner decision** on the 42 accepted-but-unadopted statuses: adopt them through Respondendi's status-only tier, or
   state why not.
6. **Tracker blocker codes** for missing continuation notices and for mirror-registered actors, so that Bentham can count
   these levers.

## What I did not verify

- Whether the National Mediation Board checker adapter patch is merged.
- How many of the 117 board orders have extensions, supplemental reports or report mismatches.
- Whether switching the actor representation to the fr-originals text passes the working-text check without a page
  recheck.
- How the 228 rejections split between planted controls and genuine claims.
- The regex classification of gap text is approximate. The "page_check" class (560) is inflated by the word "location".
