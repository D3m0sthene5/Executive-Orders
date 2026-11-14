# Evidence brief for the redesign (analyst 1 of 3), 2026-11-13

Written for the parallel redesign effort ("Sol"). It records what the evidence establishes, and it tests why script
drafting (Nalimov) reaches so few orders.

**Basis**
- Repository HEAD: `ed1df44a3053488ed60911864da2acbe4e74e945`. Paths are relative to the repository root, with
  short commits from `git log -1 --format=%h -- PATH`.
- No paid agent, job or network call was used. One zero-token local rerun: `jobs/nalimov-tablebase/census.py
  --data . --out SCRATCH/census --evidence-cache SCRATCH/evidence`, about 2 minutes. Its `first_blocker` and
  `any_blocker` counts are identical to the committed `research/lind/nalimov-recensus-2026-11-12/CENSUS.json`
  (observed). That commit has no per-order CSV, and the rerun supplied the per-order rows used in Part B.
- Labels: **[obs]** observed, at the path given; **[int]** interpretation; **[proj]** projection; **[unres]**
  unresolved.
- Human-certified whole-lifecycle count: 0.

---

## Part A. Evidence brief

### A1. Lind stage-0 pilot (0 of 30 ready)

Paths:
- `research/excavator/claude-lind-2026-11-12/REPORT.md` (41eeacc77);
- `FAILURES.md` (58a9d2f0f);
- `RECOVERY.md`;
- the plan `research/lind/stage0/WAVE.json`;
- Kean `F-20261112-lind-stage0`.

| | |
|---|---|
| **Establishes [obs]** | On the repaired kit, 30 random never-attempted undecided orders (15 pass all Larrey gates, 15 pass hard gates only) gave **0 ready**. Funnel: 7 dispatch-blocked, 15 blocked by the producer, 8 status decisions accepted (all NO), 7 claims reviewed, 1 upheld by both arms (EO 12753). EO 12753 then failed completion as `custody_record_only`. Failure categories over the 30, overlapping: missing evidence (ME) 22, integration (IN) 5, factual/legal error (FL) 4, internal inconsistency (II) 3, custody (CU) 2. Of the 6 genuine claims, 5 had authoring defects that blind review caught: a wrong count, a self-contradiction, the wrong body named, an imprecise date, misapplied P2. Both arms caught the planted control. Cost $23.07 list price (coordinator $10.16, producers $5.79, reviewers $7.12). |
| **Does not establish** | Population yields (n = 15 per group). Whether hard-only orders are worthless: no hard-only order got past review, but that is not a yield estimate. Whether a different authoring method would avoid the 5 defects. |
| **[int]** | Two separate limits: (a) **evidence**: 22 of 30 lack a needed source; (b) **authoring**: 5 of 6 written claims carried defects. Review worked: every defect was caught, and there was no false uphold except a custody gap that the checker caught. The status half is easy: 8 of 8 statuses were accepted. |
| **[unres]** | The repair yield of the 6 correctable claims. Both repairs await owner asks `A-20261112-lind-adopt-12753` and `A-20261112-lind-repair-12437-11943`. |

### A2. Nalimov re-census and prescreen on the repaired kit

Paths:
- `research/lind/nalimov-recensus-2026-11-12/CENSUS.json` and `PRESCREEN.json` (ed1df44a3);
- the earlier census `research/nalimov/census/CENSUS.csv` (36cff91d1);
- `research/nalimov/REPORT.md`;
- `research/lind/DESIGN_CHALLENGE_2026-11-12.md` (dbbc9c8f9);
- Kean `F-20261112-design-challenge`.

| | |
|---|---|
| **Establishes [obs]** | Of 11,214 undecided orders, 726 have a predicate-passing express named whole revocation. **14** produce a complete script draft, all EO ≥ 7532. **10** pass the kit assembler, `check_claim` and the actual checker offline (EO 10302, 10779, 10918, 11056, 11232, 11352, 11361, 11512, 12737, 13765). 4 fail at the checker (`pass_with_unverified` or `mechanical fail`). The other kinds produce no complete drafts: `decided_express` 0 of 2,210 decided-NO-not-ready orders; `amendment_only` 0 of 601; `own_terms` 0. |
| **Does not establish** | Anything about review outcomes. No script draft has been verified by the arms; the calibration plan was signed and never run (`D-20261110-nalimov-calibration-v3-signed`). Nor the projected 2-6x cost saving, which is untested. |
| **New observation [obs]** | **EO 11274** was complete in the earlier census and passed the earlier prescreen. It was one of the 8 drafts in the owner-signed calibration plan (`research/nalimov/calibration/WAVE.json`, line 19). On the repaired kit it is blocked by a held U.S. Code note (5 U.S.C. 3345 note). The note records the order "as amended by Pub. L. 101-509, title V, § 529 [title I, § 112(c)], Nov. 5, 1990". The earlier draft therefore omitted a lifecycle amendment by statute. **[int]:** script drafts can be complete by the kit's gates and still be wrong as lifecycles, so the verify step is not optional. **[unres]:** whether blind arms would have caught it. |
| **[int]** | The script reaches about 1.9% of express candidates (14/726) and about 0.1% of undecided orders (14/11,214). See Part B for why. |

### A3. Source-first (NIRA shared analysis) and why it stalled elsewhere

Paths:
- `research/excavator/claude-nira-sweep-2026-10-29/{REPORT.md,SHARED_ANALYSIS.md,COSTS.json}` (36cff91d1);
- Kean `F-20261029-5` (worked).

Failures elsewhere:
- `F-20261017-3` (family rules);
- `F-20261021-3` and `F-20261025-1` (Norton);
- `F-20261019-1` (X1);
- `F-20261106-pothier-class-events`.

| | |
|---|---|
| **Establishes [obs]** | NIRA had one reviewed shared legal analysis, the S.J. Res. 113 §2 repeal of 1935, attached to packets. Results: 132 attempted, 91 filed, 10 of 10 controls caught. In a matched 6-order pair it used 3.26M against 7.01M weighted tokens, and in treatment batches 0.24M against 1.75M weighted tokens per filed claim. Source-first stalled elsewhere: family rules passed 0 of 748 certificates, because 552 of 571 targets had no located original; Norton produced 0 reviewed reusable answers, and the ordinary batch already investigates a shared fact once; X1 typed 90% exactly, but only 52 of 8,014 old orders had a status and held text (5 claims). |
| **Does not establish** | That a shared analysis helps outside a family with **one common ending event and held per-order texts**. NIRA was a decided family. |
| **[int]** | Shared analysis cuts the *legal reasoning* cost once per family. It does nothing for the per-order evidence gap, and that gap is what binds elsewhere. Its own remaining blocker was conditions, stays and committees attached to approvals (about 20). |

### A4. Review reuse and mechanical receipts

Paths:
- `research/excavator/claude-tribonian-2026-11-04/REPORT.md`, section "Paired review trial" (36cff91d1);
- `evidence/LIND_TRIAL.json`;
- Kean `F-20261104-1` (failed);
- Cujas: `F-20261108-cujas-photius-recheck`, `F-20261108-cujas-c02-c03`, `F-20261108-cujas-usage`;
- Haloander route: `F-20261107-haloander-recovery`.

| | |
|---|---|
| **Paired trial, establishes [obs]** | 85 claims, each reviewed by two fresh Opus arms; arm B also had per-claim `blind_verify.py` receipts. **No measurable saving:** cache read 53.7M against 52.4M, output 185k against 186k, 279 against 270 calls, 3,653 against 3,739 active seconds. Receipts failed closed on raw custody for every claim, and they cannot express page records or confirmation flags. **Second-reviewer effect:** arms disagreed on 7 of 85, and 3 of 4 B-only rejections were confirmed defects. Reviewer variation exceeded the arm effect. |
| **Cujas, establishes [obs]** | Re-checking Photius-stale working texts by carrying earlier reviewed Tribonian sheets, with a Sonnet producer and two blind Opus arms, filed 21 of 25, then 23 of 25 and 24 of 25: 68 of 75 overall, 0 controls missed, 0 completion exceptions. Cost about $39 for the wave, coordinator about $16 of it; c01 workers about $0.41 per filed claim. |
| **Does not establish** | That review can be made cheaper by pre-computed receipts. The cost is reading sources and judging law. Cujas shows reuse of *prior reviewed claims* works for *recovery* (re-verifying text against an official printing). It says nothing about new undecided orders. |
| **[int]** | Reuse succeeds when the earlier legal work is already reviewed and only the source binding changes. Mechanical aids for reviewers have not paid. |

### A5. Negative results a redesign must not rediscover

| Result (Kean id) | What was learned [obs] |
|---|---|
| Mommsen unranked pools `F-20261110-mommsen-unranked-pools` (failed) | About half a week's Codex allowance (about 520M input tokens) gave 12 claims on branches, 0 merged. 83% of reserved orders were in no Bentham action, and 57% of decided-not-ready orders below EO 7532 have no accepted source text. Lesson enforced: `jobs/claim-kit/admission.py` (f26ccf68f) refuses orders outside a Bentham action; an unranked refusal is a stop. |
| Icecore `F-20261105-icecore` (stopped_at_gate) | A finished wave's yield describes the orders it drew, not those left. Tribonian's 47.6% NO yield fell to 3.3% on a random sample of what remained. Measure the remaining stratum first. |
| Respondendi diagnosis `F-20261110-respondendi-diagnosis` | Papinian's 84 undecided failures: route or tool defect 37, missing later-event evidence 24, rule too strict 13, producer error 10, genuinely unknowable 0. Held evidence supports a status for 65 of 84. |
| Kit not rebuilt `F-20261112-kit-not-rebuilt` (failed) | The cause list on the 87 failures was route/tool 34, missing 33, rule 15, producer 5. A merged fix is not in effect until claim-kit is rebuilt; check `jobs/claim-kit/output/STATUS.json` against the fix's merge time. |
| Haloander / Papinian `F-20261110-papinian-undecided-u23` (stopped_at_gate) | Status review is the easy half: 16 of 17 NO statuses accepted, while 6 of 16 lifecycle claims survived both arms. Producers skip U.S. Code notes and later amendments. |
| Junto `F-20261017-1` (failed), `F-20261020-4` (inconclusive) | 20 candidate savers, 0 measured; the one matched test used 21.8% *more* input tokens. A saving counts only when measured. |
| Dorotheus `F-20261106-dorotheus-wave-cost` (failed) | Multi-order packets with full dossier views cost about 1.38M context tokens per attempt, because shared evidence is reloaded per producer. |
| Paired receipts `F-20261104-1` (failed) | See A4. |
| Re-completion `F-20261104-2` (partly_worked) | Re-completing after custody retention was refused because the Valla review context had changed and filenames were shadowed. 47 reviewed claims are stranded. |
| Integrated-kit o26-o30 `F-20261104-5` (failed) | 60 orders, 9 submitted, 2 filed. Producer-added sources outside the mandatory list fail custody at completion. |
| Board and page readers `F-20261108-6..9` (stopped_at_gate) | 4 × 50 page-lead checks gave 0-1 pass each; the Bentham gate said STOP. |
| Runner deadline `F-20261112-runner-deadline` (failed) | A job that runs past the 6-hour runner limit publishes nothing. Time real items first and write ledgers every batch. |
| Low-tier blind readers `F-20261108-montfaucon-control-binding` (failed) | Cheaper readers missed planted substitutions; their verdicts were quarantined. |
| Soft gates `F-20261112-soft-gates-untested` | Use soft gates to order the queue, not to exclude orders, until a prospective test measures what they keep out. |

### A6. Reusable machinery (do not rebuild)

Maturity labels are [obs] from READMEs and Kean. "Production" means it ran in filed waves.

| Tool | What it does | Maturity |
|---|---|---|
| `jobs/claim-kit` | Compiles held texts, ACT/TERM/CHAIN/OWN_TEXT records, dossiers, blank sheets; `kit.py complete`; `status_overlay` | production |
| `jobs/claim-kit/admission.py` | Refuses orders outside a named Bentham action | production (enforced) |
| `jobs/claim-checker` | Zero-token mechanical half of review (hashes, quote spans, custody) | production |
| `jobs/valla` | Pins the review context so completions are reproducible | production; brittle on re-completion (F-20261104-2) |
| `jobs/current-law` | U.S. Code/eCFR scan, `MENTIONS.csv` with roles and cautions | production |
| `jobs/later-events`, `jobs/status-history` | Later acts and dated OFR status history per order | production |
| `jobs/cotton-capture-custody`, `jobs/astra-source-retention` | Retain the exact bytes of sources (cures `custody_record_only`) | used |
| `jobs/fr-originals`, `jobs/source-ladder` | Official FR originals and the acquisition ladder | production; open multi-document span defect |
| `jobs/maudslay-conveyor` | Scripts the clerical batch stages (reserve, apply, batch-check, plant, review, reveal, complete); `--producer nalimov` | built and tested; status-overlay stage built by `F-20261110-nalimov-overlay-stage` [unres: merged and used?] |
| `jobs/nalimov-tablebase` | Census, script drafter, prescreen, packets by acting order, typed controls | built and tested; never run against reviewers |
| `jobs/respondendi-adoption` | Standing adoption rule with audit probation | built; rule v2 awaits owner (`A-20261110-respondendi-standing-rule-v2`) |
| `jobs/larrey-triage` + `jobs/llull/kit_features.py` | Zero-token pre-dispatch gates from what the kit would freeze | built; used in the Lind draw; soft gates untested prospectively |
| `jobs/pothier` | Class doctrines (P2 amendment-merged, PD-CLASS-EVENTS) and status leads | built; leads read by no kit code (Respondendi) |
| `jobs/bentham`, `jobs/augur-launch`, `jobs/kean`, `jobs/savigny-supervisor` | Ranking, launch gate, shared register, spend supervisor | production governance |
| `jobs/hamilton-token-audit`, `jobs/necker-costs` | Telemetry from transcripts; list prices | production |
| Blind two-arm review with planted controls and the both-uphold rule | Quality control | production; 0 missed valid controls in NIRA, Cujas and Lind |

---

## Part B. Why Nalimov's reach is narrow

### B1. How the 726 were selected (`jobs/nalimov-tablebase/census.py`, 36cff91d1)

**Selection rule [obs]** (`census.py` lines 65-76 and 238). An order is a candidate when all of these hold:
1. it is undecided: `provisional_status` is empty in `READINESS_BY_ORDER.csv`;
2. it has at least one `ACTING_PROVISIONS` row targeting it with:
   - `scope == whole`;
   - `names_target`;
   - no `reaches_target_via`;
   - a verb in Respondendi's `act_verbs`;
   - a provision of at most 3,000 characters;
3. that provision passes `predicate.named_end_in`: an ending verb naming the order's exact number, with none of about
   40 qualifiers ("in part", "except", "so far as", "until" and others).

Each candidate is then frozen with the kit's own freezer and drafted. "Complete" means the drafter has no blocker and
the kit's `_decision_errors` gate passes.

**What the denominator leaves out [obs]:**

| Outside the 726 | Count | Script result |
|---|---:|---|
| Undecided with no predicate-passing whole named act (implied revocations, partial ends, own terms, spent on issue, YES orders, orders with no held later act) | 10,488 (this row overlaps the amendment-only and own-terms rows below) | not attempted |
| Decided NO, no ready claim (`decided_express`) | 2,210 | 0 complete; 1,266 first-blocked by no express named whole revocation, 758 by an unacceptable original |
| Amendment-only (P2) | 601 | 0 |
| Own terms | 2,554 term records | 0 |
| Decided YES | (in 3,788 decided) | no kind defined |

**Pre-1937 orders are inside the 726 but never complete [obs]:**
- 133 of the 726 are below EO 7532; 0 of the 14 complete drafts are.
- `original_not_acceptable` (121 orders) is almost entirely pre-1937. It is absent from the EO ≥ 7532 top-12
  first-blocker list, so at least 107 of the 121 are below EO 7532.

**Note [unres]:** the census's amendment-only blocker text is hard-coded: "the kit on main emits no OWN_TEXT…".
Lind used OWN_TEXT/PARENT_END records from the merged fixes, so this count may be stale.

### B2. What blocks the 712: blockers come in conjunctions [obs, rerun rows]

The blocked orders carry many blockers each:
- distinct blockers per blocked order: 1 for 71 orders, 2 for 88, 3 for 95, 4 for 99, 5 for 91, 6 or more for 268;
- 46 orders stop at `several_ending_actors`, where the drafter returns early, so their other blockers are unseen.

**[int]:** fixing any one blocker class releases few orders. Only 71 orders have a single blocker:
- `several_ending_actors` 34 (truncated, so not true singles);
- `clause_needs_judgment` 12;
- `current_law_mention_needs_reading` 6;
- `own_term` 4;
- `working_text` 3;
- `inventory_gap` 3;
- 9 others.

### B3. The largest blockers, classified

Classes: (i) inherent legal judgment; (ii) missing inputs or evidence; (iii) drafter or kit implementation, fixable
by code; (iv) a requirement of the current schema or admission rules. Counts are [obs] from `CENSUS.json`; the class
is [int], checked against the cases in B4.

| Blocker | First | Any | Class | Basis |
|---|---:|---:|---|---|
| `clause_needs_judgment` | 12 | 430 | **mostly (iii)**, some (i) | Of 2,050 flagged clauses: 254 are "1."-numbered items the item regex misses (it needs ")"); 165 amend other orders, 76 mix a revocation with another command, 33 transfer, 2 abolish (i); in a sample of 10 of the rest, about 8 are code-fixable: lead-ins "I hereby order:", "(a) serve as…", the non-justiciability boilerplate, "this order is effective…", "Section 1. Goals", OCR "1 . … au thorized", the stray segment "1941." |
| `missing_item` | 40 | 373 | (ii)/(iii) | 439 × "target provision not located: EO N" (a later citer whose provision the kit did not locate); 161 notices absent from the census; 66 working texts owing confirmation; 64 machine-segmentation cautions |
| `current_law_mention_needs_reading` | 28 | 297 | mixed (iii)/(i) | 259 mentions are `mentioned_in_printed_eo_text` and 18 `printed_eo_text`, often the ending order's own printed text (iii). 613 are CFR text, search or authority references, which need a current-law reading (i) |
| `ending_source_is_working_text` | 151 | 226 | **(ii)** + (iv) | The only held copy of the ending provision is an APP or other transcription. For 179 of 226 the acting order is FR-era (≥ EO 7316), so the official FR copy is acquirable in principle. The 2026-10-21 working-text ruling bars a script from using the transcription |
| `no_second_witness` | 7 | 223 | **(iv)** | Respondendi requires a catalog note naming the same actor; the evidence is usually just not in the catalog |
| `own_term_needs_reading` | 58 | 218 | (i) | A stated term (mostly `until_event`) may have ended the order before the revocation |
| `inventory_gap` | 7 | 199 | (iii)/(ii) | Operative words outside the clause spans: kit segmentation over OCR |
| `another_instrument_acts` | 94 | 184 | (i), partly (iii)/(iv) | In 103 of 184 the other acts are amendments only, scriptable under P2 if amended text ends with the parent; the rest are partial abolitions, transfers and supersessions (i) |
| `chain_event_by_another_actor`, `catalog_entry_acts_on_order` | — | 184 / 145 | (i) | Another instrument in the history |
| `original_not_acceptable`, `page_check_owed` | 121 / 24 | 121 / 55 | (ii) | Pre-1937 originals |
| `effective_wording_unparsed`, `actor_effective_sentence_needs_reading`, `effective_class_needs_reading` | 57 | 181 | (iii), sometimes (i) | Delayed-effect dates the parser does not read |
| `several_ending_actors` | 34 | 46 | (iv)/(iii) | The predicate requires exactly one actor |
| `actor_savings_sentence`, `savings_phrase_in_provision` | 33 | 104 | (i) | Savings clauses |

### B4. Direct inspection of 8 blocked candidates [obs, evidence frozen by the rerun]

| Order (actor) | Blockers | What the record shows | Class |
|---|---|---|---|
| EO 9925 (EO 10127) | `clause_needs_judgment` ×3, the only blocker | The lead-in "airspace … is hereby reserved … described boundaries:" is followed by items "1. Clinton Engineering Works…", "2. Hanford…", "3. Los Alamos…". The item regex `\(?…\)\s` needs a ")" | (iii) pure code |
| EO 11142 (EO 11302) | `current_law_mention_needs_reading`, the only blocker | 38 U.S.C. 111 note, role `mentioned_in_printed_eo_text`, caution `text_says_revoked_or_superseded`. The snippet is EO 11302's own "Sec. 6. Executive Order No. 11142 … is hereby superseded", which confirms the act. The other two rows are ended-status notes naming EO 11302 | (iii) |
| EO 11274 (EO 13243) | `current_law_mention_needs_reading`, the only blocker | 5 U.S.C. 3345 note: "as amended by Pub. L. 101-509 … 1990 … revoked by Ex. Ord. No. 13…". A real statutory amendment that the lifecycle must carry, so the blocker is correct | (i), lifecycle content |
| EO 10194 (EO 10990) | `clause_needs_judgment` (sec. 5), the only blocker | "Executive Order No. 8071 … is hereby revoked. The records … shall be transferred to the Federal Safety Council." A revocation folded into a one-time transfer, whose completion date is not held | (i) + (iv), exact date |
| EO 8571 (EO 9282) | `clause_needs_judgment` (#whole), the only blocker | A WHEREAS-form land jurisdiction transfer (Cookson Hills), with the whole text as one clause. Whether a transfer is a standing state or done on issue is a legal question | (i), possibly class-ruleable |
| EO 5860 (EO 7856, 7857, 7858) | `several_ending_actors` (drafter stops) | Three orders each say "This order supersedes Executive Order No. 5860 … as amended by Executive Order No. 6650…". EO 6650 amended it (partial), which the drafter never reached | (iv)/(iii) + amendment |
| EO 7703 (EO 8959) | `working_text`, `actor_effective_sentence`, `no_second_witness`, `inventory_gap` | The ending sentence "Executive Order No. 7703 … is hereby revoked" is held only as an APP mirror (common-crawl, 1941). The official 6 FR copy is not held | (ii) mainly, plus (iii) and (iv) |
| EO 8629 (EO 9040) | `another_instrument_acts`: 8875 (amend; abolish, partial), 9024 (amend) | The Office of Production Management: the Priorities Board was abolished by EO 8875 before EO 9040 rescinded the order, with functions moved to the War Production Board | (i), genuine |

**Check [int]:**
- 3 of the 8 are blocked only by code (EO 9925, 11142, and EO 5860's same-date multiple actors).
- 3 are genuine legal or lifecycle content (EO 11274, 8629, 8571).
- 1 is a rule plus a missing date (EO 10194).
- 1 is evidence (EO 7703).

The drafter's conservatism is correct about half the time in this sample. It is not uniformly over-strict.

### B5. How far reach could grow [proj]

The rerun rows were recomputed with blocker classes removed in layers. These are **upper bounds**: they assume each fix
is perfect and each blocker in a class is resolvable.

| Layer (cumulative) | Extra complete drafts | Notes |
|---|---:|---|
| Today | 14 complete, 10 prescreen pass | [obs] |
| L1: (iii) parsing only (clause classifier, inventory, effective-date parsing) | +34 | all EO ≥ 7532 |
| L1': all (iii), including printed-text current-law mentions and date checks | +74 | overstated: in B4, 1 of 2 current-law singles was a real amendment |
| L2: + official FR copy of the ending order acquired | +110 | acquisition, not code |
| L3: + second-witness rule relaxed (owner) | +124 | rule change |
| L4: + amendment-aware drafting (amend-only other acts, chain events) | +151 | needs a P2 ruling applied to amended text |
| L5: + `missing_item` resolved | +247 | mostly kit location of later citers plus notices |
| L6: + acceptable originals and page checks | +307 | pre-1937 acquisition |

**[proj] What realistic code-only fixes would give:**
- Fixing (iii) gives about **+25 to +55 complete drafts**: the +34 upper bound, discounted for the clause share that
  is genuinely legal, up to part of L1'. The total becomes about 40-70 of 726, about 6-10% of express candidates.
- At today's 10/14 prescreen pass rate, that is about **30-50 prescreen-passing drafts**, still under 0.5% of the
  11,214 undecided.
- The verify uphold rate is **unmeasured**. EO 11274 shows that a kit-complete draft can omit a lifecycle event.

**[proj] Cost of the (iii) fixes:**
- A bounded drafter change covering:
  - "1."-numbered and OCR-spaced items;
  - lead-ins ending in "order:";
  - boilerplate, effective-date and policy clauses;
  - a printed-text mention accepted only when it carries the actor's own ending sentence;
  - a delayed-effect date parser;
  - several actors on the same date.
- Tests, plus a fresh independent cross-family review on real drafts. The v1 review found 17 of 36 drafts wrong,
  so every relaxation must be re-reviewed.
- Estimate: 1-2 coordinator sessions at about $10-25 list price each (Lind's coordinator measured $10.16), a review of
  about $5-10, and zero-token reruns. In total about **$20-60 and 1-2 days**.
- That buys about 2-4x the scripted pool, from a very small base.

**[int] Bottom line:**
- Script drafting is a sound narrow tool for a modern express-revocation tail. With code fixes it reaches tens of
  orders, not thousands.
- The first blockers that dominate are evidence (working-text ending sources 151, pre-1937 originals 121) and legal
  content (another instrument 94, own terms 58), not code.
- The levers that grow reach past L1 are acquisition (L2, L6), owner rules (L3, L4) and kit location of later citers
  (L5).
- Do not promote script drafting to a general route. Do not discard it: it is cheap, and its blockers are an exact,
  machine-readable to-do list for the other routes.
