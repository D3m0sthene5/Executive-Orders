# Domat: a batch-by-type status route for the undecided pre-1937 orders (plan, 2026-11-25)

Named for Jean Domat (1625-1696), whose *Les lois civiles dans leur ordre naturel* arranged the civil law by kinds of
rule so that each case could be decided from the rule of its kind. Plan only: no code, no model call, no spend, and no
status, census, readiness or certified count changed (certified whole-lifecycle count: 0).

## Conclusion

A batch route can assign provisional statuses to about 2,100 of the 11,057 orders whose only tracker blocker is
`NO_PROVISIONAL_STATUS`, at an estimated **$0.05 to $0.45 per adopted status for the top types, about $0.27 averaged
over the whole pool (high case $0.70), against $3.33 (Bentham) and $7.71 (Papinian, measured) on today's per-order
route.** This assumes the review standard is kept or raised: every member is read by two blind arms, every batch
carries typed planted controls, an auditor of another family samples each stratum, and the owner adopts by merged
pull request under an approved lot card. The saving has three sources. The status proposal is made by a script from
records already held. Two short readings of many orders share one instruction block. Only orders whose held records
already support a status are attempted, so few attempts are wasted.

The route reaches only the orders that already have a decided lead. Of the 6,853 status-only pre-1937 orders, 2,107
carry a Pothier doctrine lead that decides them (2,056 NO, 51 YES). The other 4,746 have open leads or none. For those,
no reading of held material can produce a status, and the route can only name the record that would settle each one
(BLM withdrawal case files, Federal Register texts of Public Land Orders, the Forest Service chronology, the Official
Register of the civil service). The largest X1 type, the 1,355 one-person civil-service waivers, is almost entirely in
that second group. The 4,204 post-1937 orders have no X1 type and no Pothier doctrine. They can be batched by the
kind of basis record the claim kit holds (an express revocation, or a current-law record), but their texts are long
and need more judgment, so they gain less (section 6).

Adopting a status does not make an order ready. The tracker reports only the first blocker. Once the status is
adopted, the order's clause-inventory, ending-basis, savings and counterevidence steps (all still `open` for 11,056 of
the 11,057) become its blockers. For three lot kinds (spent on issue, amending only, own terms) the lifecycle claim is
mechanical enough for a scripted draft, read by the same two arms in the same batch. That needs one zero-token
prerequisite first: the claim kit must accept the ProQuest replicas and official printings that the tracker already
credits. Today the kit holds an acceptable original for only 111 of those 1,327 orders.

## 1. Why X1's batch sheets never became statuses

X1 (`jobs/x1-class-engine`, `research/production/x1-2026-10-19/REPORT.md`) types the old orders well: 90% exact type
on a fresh holdout. Its sheets were never turned into statuses, and the records show six separate reasons.

1. **X1 was built to produce leads, and its rules were approved only as leads.** All 22 type rules are
   `reviewed_frozen:approve_pattern_lead_only` (`jobs/x1-class-engine/output/TYPE_RULES_CHECK.json`). The sheets route
   5,297 rows to `status_first`, that is, back to the claim kit's per-order status-overlay route. No tool takes a
   reviewed type plus a held ending record and proposes a status.
2. **The inputs were missing in October.** Only 52 of 8,014 old orders had both a status and a held text. 46 of the 52
   pilot rows were blocked by missing originals or missing ending instruments (F-20261019-1). The texts have since
   arrived. On the 2026-11-25 tracker, 10,789 of the 11,057 status-only orders have their original-text step `done`, and
   3,737 of those rest on ProQuest replicas that passed the Photius page check (F-20261125-photius-peiresc-full).
3. **The claim kit still refuses those texts.** In the kit's compiled overlay inputs (claim-kit run of 2026-11-24
   23:13Z), 3,578 status-only pre-1937 orders whose tracker credit rests on a replica have no acceptable original and no
   clause inventory. Another 1,596 have clauses but no acceptable original. Only 576 of the 6,853 have an acceptable
   original in the kit. The Larrey triage gates keep most X1-class orders out of the undecided route for
   `original_not_usable` or `no_status_basis_record`. The pass rates under its hard gates are 83 of 1,723 spent, 1,217
   of 2,968 land, 337 of 1,733 standing and 60 of 285 swept. The owner decisions that would let the kit accept these
   texts (D-20261106-photius-p4 and -r37) are recorded as not wired. Accursius F6 found that `assemble.py` still refuses
   R37 and P4 texts (`working_text.GRADES`).
4. **Class adoption was tried once and corrected.** Under the 2026-10-31 Jacquard ruling (X1 spent and swept classes
   only), no sampled lot passed the zero-miss test. The failures were L1 11/59, L4 33/59 and L5 22/59, because X1 type
   labels are broader than the texts (F-20261031-jacquard-wave1). A full review then adopted 714 statuses at about 8k
   Sonnet tokens each (F-20261031-jacquard-wave2). Ulpian later found that the L1 lot card's premise was not supported
   by evidence. That premise was "at least 14 years old", and the owner declined it (D-20261110-ulpian-no-floor). The
   correction returned 33 wave-1 and 486 wave-2 waiver statuses to undecided (F-20261110-ulpian-l1r-correction). That
   correction is why 1,355 one-person waivers dominate today's status-only pool. The failure came from the card's legal
   premise, not from batch reading: the blind arms agreed on 547 of 556 rows and caught 18 of 18 controls.
5. **No class ruling covers land or standing types, and nothing reads the Pothier leads.** The owner adopted the 11
   Pothier doctrines as first-step guidance only. The answer to A-20261106-pothier says: "Sampled adoption of a family's
   no leads stays a later ask under the 2026-10-31 Jacquard rule." That later ask was never put. Linnaeus found 1,072
   orders with a decided Pothier lead that no claim-kit code reads (F-20261110-linnaeus-no-lead-types).
6. **The standing adoption rule is not approved.** Respondendi v2 (A-20261110-respondendi-standing-rule-v2, open)
   requires each order's full overlay-route claim. Its zero-token predicates read kit records (`ACT:`, `TERM:`,
   `OWN_TEXT:`, `CURRENT:`) on acceptable originals, which the pre-1937 orders mostly lack (point 3).

## 2. Where the 11,057 status-only orders fall (measured)

Method: `READINESS_BY_ORDER.csv` on main (generation 45572901968-1, 2026-11-25 08:12Z) was streamed with `git show`.
An order is counted when `ready_for_human_review` is not `yes` and `blockers` is exactly `NO_PROVISIONAL_STATUS`, which
gives 11,057 of the 13,708 not-ready orders. These orders were joined on `instrument_id` with X1 `TYPES.csv` (8,043 rows,
EO 1 to 7531), Pothier `LEADS.jsonl` and the claim kit's `OVERLAY_INPUTS*.jsonl`.

- **Inside X1 (pre-1937): 6,853.** By class: land 2,968, standing 1,733, spent 1,723, swept 285, unknown 144. By X1
  confidence: high 3,420, medium 2,384, low 905, none 144.
- **Outside X1: 4,204.** Of these, 4,202 are EO 7532 or later. The other two are EO 6585 and EO 7010F, numbers that
  were admitted to the census after X1 ran.

In the table below, "Decided lead" means a Pothier doctrine lead that decides the order. The lot columns use the
lot kinds of section 3. "Kit original" counts decided-lead orders that have an acceptable original in the claim kit
today.

| X1 type (rule) | Status-only | High | Medium | Low | Decided lead | A1 spent | A2 amends | B named or PLO | C own terms | D life bound | E yes | Kit original |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cs_waiver_individual (TR-CS-WAIVER) | 1,355 | 845 | 491 | 19 | 111 | 1 | 13 | 4 | 2 | 91 | 0 | 2 |
| land_withdrawal_general (TR-LAND-WITHDRAWAL) | 1,184 | 626 | 536 | 22 | 371 | 130 | 9 | 206 | 25 | 0 | 1 | 40 |
| national_forest_boundary (TR-NATIONAL-FOREST) | 737 | 260 | 477 | 0 | 312 | 179 | 13 | 111 | 9 | 0 | 0 | 18 |
| cs_rules_amendment (no rule) | 567 | 533 | 30 | 4 | 390 | 3 | 372 | 15 | 0 | 0 | 0 | 27 |
| military_naval_reservation (TR-MILITARY-RESERVATION) | 346 | 193 | 144 | 9 | 156 | 57 | 8 | 91 | 0 | 0 | 0 | 4 |
| organization_agency (no rule) | 251 | 0 | 0 | 251 | 35 | 7 | 12 | 15 | 1 | 0 | 0 | 0 |
| indian_reservation_trust (TR-INDIAN-RESERVATION) | 230 | 138 | 90 | 2 | 93 | 6 | 8 | 9 | 69 | 0 | 1 | 14 |
| regulations_issuance (no rule) | 224 | 0 | 0 | 224 | 66 | 4 | 57 | 4 | 1 | 0 | 0 | 0 |
| bird_refuge (TR-BIRD-REFUGE) | 205 | 139 | 65 | 1 | 67 | 14 | 3 | 36 | 1 | 0 | 13 | 4 |
| tariff_customs (no rule) | 176 | 84 | 92 | 0 | 79 | 38 | 1 | 8 | 0 | 0 | 32 | 4 |
| 26 other X1 types and unknown | 1,578 | 602 | 459 | 373 | 427 | 119 | 96 | 131 | 69 | 10 | 4 | 54 |
| **All pre-1937** | **6,853** | **3,420** | **2,384** | **905** | **2,107** | **558** | **592** | **628** | **177** | **101** | **51** | **167** |
| Post-1937 (no X1 type, no Pothier doctrine) | 4,204 | | | | | | | | | | | 4,064 |

In this table "B" combines lot kinds B1 (406, a later instrument names the order), B2 (108, a BLM Public Land Order
table row) and B3 (114, an express class instrument or the abolition of the order's subject). About 400 Pothier leads
across the land, forest, military and refuge families rest on BLM Public Land Order tables while the Public Land
Order's own text is not held. Several of these sit in B1 under the lead kind `ended_by_later_instrument`. Of the 2,107
decided-lead orders, 1,100 have their text credit from a checked ProQuest replica, and 71 are transcription-dependent.

The post-1937 orders have different records in the kit. 923 have a whole-order end candidate (841 revocations, 92
supersessions, mostly from the OFR disposition notes), 1,463 have a current-law predicate, and about 2,045 have
neither.

## 3. The route

A lot is defined in advance by deterministic criteria on held records: lot kind, Pothier doctrine and branch, X1
type, and text basis. The type label never defines a lot on its own (lesson of Jacquard wave 1). Each lot has a lot
card. The card states the legal premise of the status, cites every ruling, statute and table the premise rests on by
SHA-256, and lists the outlier conditions of the X1 type rule. The lot kinds follow Respondendi's kinds so that its
audits and stop rules can be reused:

| Kind | Status | Premise (each pinned on the card) | Rows today |
|---|---|---|---:|
| A1 spent on issue | NO, ended on signing | The order only revokes, restores, eliminates or relinquishes; Pothier P1 | 558 |
| A2 amending only | NO, command spent on signing; inserted text lives in the parent | Pothier P2 as the owner applied it (answer to A-20261106-pothier; D-20261021-strike-and-insert) | 592 |
| B1 named later instrument | NO, on the acting instrument's effective date | A held later order, statute or proclamation names the order and ends it whole | 406 |
| B2 Public Land Order table | NO, on the Public Land Order's date | BLM's official table row "revoking EO No. N"; the Public Land Order's own text is not held | 108 |
| B3 class instrument or abolition | NO | An express class instrument (EO 7076, EO 89, ANCSA s.19(a)) or the abolition of the order's subject | 114 |
| C own terms | NO, on the stated date | A stated date or period in the order's own text, with no extension held | 177 |
| D life bound | NO, not later than B + 44,724 days | The Ulpian rule (D-20261110-ulpian-life-bound); a quoted, dated fact about the named person | 101 |
| E current | YES | A held current-law text names the order (19 CFR 101.3 ports; refuge statutes) | 51 |

### 3.1 What a script checks on each order (zero tokens)

- **Identity and completeness.** The census number and date must appear in the order's own text, read from the
  order's heading onward. Federal Register-era replicas start with the tail of the preceding order (lesson of Peiresc
  stage 0). Texts that are cut off are held out; Jacquard held out 44 for this reason. Texts that run into a
  neighbouring order in a compiled volume are cut at the next order's heading.
- **Type pattern.** The TR rule's pattern must match the order's own text, not only the WPA summary or the APP title.
  The check fails closed: a command word outside the recognised form puts the row out of the lot (lesson of Accursius
  F5). It also excludes orders with more than one operative clause, orders that name several persons (waivers), and
  rows whose text reads as another type.
- **Lead.** The Pothier doctrine's SHA-256 must equal the pinned value. The lead's basis kind must match the lot. For
  kinds B1 to B3, the acting instrument must be dated after the order, held (text or official table row), and must
  print the order's number with an identity check. The number test is a lead only: it refuses state governors'
  orders, hyphenated numbers and citation lists (lesson of Accursius F4).
- **Later events.** Every held later edge from Shepard, later-events, Pacioli, Cruden, Selden and the OFR notes is
  listed. Any edge that amends, extends, continues or revives the order after the candidate end puts the row out of the
  lot. This makes the script, not the readers, carry the check that every family of reviewer missed when a planted
  defect removed a later event (Mountweazel D6; F-20261107-septuagint-xfamily).
- **Outlier conditions from the type rule** that a machine can test: Alaska lands; the Philippines and the Canal Zone;
  forest changes in the six states covered by 34 Stat. 1271 after 1907-03-04; overlap with the general withdrawals of
  EO 6910 and EO 6964; residual interests such as reversions, water rights and rights-of-way; amendment-only orders
  whose parent is in the pool. Each such row goes to individual review.
- **Dates.** The effective date is read from its basis (signing, publication, or a stated date). "Until" dates are
  inclusive, with the exclusive reading stated (D-20261021-until-dates). Year-plus-day arithmetic for the life bound
  uses 44,724 days.

The script writes the status proposal and a short evidence row for each order: the operative quote span, the lead's
quote, the dates, and the list of later edges. The script is the producer, as in Nalimov, where "a script may
reconfirm only its own sheet".

### 3.2 What one call per batch still judges

Each batch holds 47 genuine rows and 3 planted controls. For every row, each arm answers a fixed checklist from the
card. Does the order's own text perform only the lot's act? Does the quoted ending provision reach this order whole,
and not only some lands or a partial phrase such as "so far as"? Is the end date right on its basis? Does the text
hold a condition, exception or second command? For D, does the dated fact concern the named person? For A2, is the
order amendment only? Each arm answers uphold, fail or hold, gives a reason and quotes the text.

Two blind arms of different models read every row: Sonnet 5.5 and Opus 5.5, or Sonnet 5.5 and Fable as in Ulpian.
A row is adopted only when both arms uphold it. The coordinator records each disagreement, and a disagreement never
becomes an adoption without a third reading. This is equal to or stronger than today's status review, which has one
independent Opus status reviewer. What the route leaves out is the lifecycle claim, which section 5 covers.

### 3.3 Planted controls and measured quality

Each batch carries at least one control per 15 rows, of at least two kinds, and at least one of them changes the
status. The kinds are:

- a later revoking, reviving or extending edge added to the evidence (the status-determining inverse of D6);
- a second operative clause or a condition appended to the text;
- a text swapped under another order's heading;
- a wrong-type intruder;
- an end date shifted.

Controls are vetted before they are planted. The planter checks that the original text does not already answer the
question (lesson of Ulpian). A known-failure control is used only after a second reviewer agrees that it fails
(lesson of Jacquard wave 2, which voided EO 370 and EO 3031). One missed control voids the batch, which is then read
again by fresh arms.

Each stratum (process fingerprint, lot kind, text basis) starts on probation. On probation an auditor of another
family (Codex, or the owner) re-reads every adopted row until the stratum's 95% upper bound on errors reaches 5%: 59
clean audits, 93 with one confirmed error, 124 with two. After probation the auditor re-reads 20% of each lot. These
are Respondendi's numbers. Respondendi's stop rule applies by kind.

A change to any premise on a card lists every adopted row that rests on it and reopens those rows for reading. Ulpian
showed that one declined premise reached about 570 merged statuses.

### 3.4 Adoption

Adoption is by a pull request the owner merges, adding rows to the status ledger with a `decision_origin` that names
the lot card's hash, the two arms, the control key and the audit. Statuses remain provisional AI hypotheses. The
census and the certified count are unchanged.

## 4. Cost per adopted status

### 4.1 Measured anchors

| Source | What was measured |
|---|---|
| Bentham `PLAN.md`, `status_assignment.undecided` | $1,786 for 5,370 orders, so $0.333 per attempt; yield 3/30 (Haloander), so **$3.33 per adopted status with claim** |
| Whitworth baseline (F-20261110-whitworth-forecast) | **$7.71 per adopted undecided status** (Papinian, measured) |
| Ulpian L1R (`research/ulpian/jacquard-l1r-correction/README.md`) | Two blind arms, 6 batches of about 93 rows: 1,469,701 tokens for 556 orders, **2,640 tokens per order for both arms**; disagreement 9/556 (1.6%); controls 18/18 caught |
| Jacquard wave 2 (`research/excavator/jacquard-2026-10-31-w2/README.md`) | One Sonnet reviewer: 5.9M tokens, 1,037 members, 714 adopted; **adoption rate 0.69; about 8.3k tokens per adopted** |
| Stateless gauge (`research/stateless-calls-2026-11-24/GAUGE_RESULTS.json`) | One-order Opus review call: mean $0.43 (arm A), $0.27 (arm B); one-order Sonnet producer: mean $0.148 |
| Peiresc page check (F-20261125-photius-peiresc-full) | 2,101 short reads for about $35 upper bound, **$0.017 per order** |
| Text sizes (30 held texts sampled per type, `git cat-file`) | Median bytes: waiver 1,314; land 1,247; forest 1,887; civil-service rule 1,625; military 1,962 |

Prices are from `jobs/necker-costs/PRICES.json`. Input is priced at the 5-minute cache-write rate, which is the dearer
case: Sonnet 5.5 $2.50 per million, output $10 per million; Opus 5.5 $5 per million, output $20 per million.

### 4.2 Arithmetic for one batch

The tokens per row are estimated as the order's text (bytes / 4) plus about 400 tokens of lead evidence (150 for a
life-bound fact) plus a 150-token row frame. Each batch also carries a 4,000-token card, and each row produces 150
tokens of output.

| | Waiver (D) | Land withdrawal | National forest |
|---|---:|---:|---:|
| Tokens per row | 630 | 860 | 1,020 |
| Input per batch, 4,000 + 50 x row | 35,500 | 47,000 | 55,000 |
| Sonnet arm per batch | $0.089 + $0.075 = $0.164 | $0.118 + $0.075 = $0.193 | $0.138 + $0.075 = $0.213 |
| Opus arm per batch | $0.178 + $0.150 = $0.328 | $0.235 + $0.150 = $0.385 | $0.275 + $0.150 = $0.425 |
| Both arms per genuine row (/47) | $0.0105 | $0.0123 | $0.0136 |
| Adjudication: 1.6% x $0.43 (high case 19% x $0.43) | $0.007 ($0.082) | $0.007 ($0.082) | $0.007 ($0.082) |
| Cross-family audit (every row, as on probation, priced as one Opus arm) | $0.0085 | $0.0085 | $0.0085 |
| Per row, before coordination | $0.026 ($0.101) | $0.028 ($0.103) | $0.029 ($0.104) |
| Coordination x1.5 (high case x2) | $0.039 ($0.20) | $0.042 ($0.21) | $0.044 ($0.21) |
| Per adopted status at 0.69 adoption (high case 0.5) | **$0.057 ($0.40)** | **$0.061 ($0.42)** | **$0.064 ($0.42)** |

The high-case disagreement rate of 19% is Bartolus's re-count of the Papinian arms (16/83). The coordination factor
is a range: the coordinator was 17% of Papinian's spend, but in Carnot's survey coordinators were over half of past
waves' spend.

**Fixed cost per lot card.** One lot card needs one other-family review plus a re-review, estimated at $25 from
Accursius's $70.69 for five reviewed pull requests. Spread over the top three types' lots:

- **Waivers:** 91 D rows, 63 adopted: (91 x $0.039 + $25) / 63 = **$0.45** per adopted status. Only 91 of the 1,355
  waivers are in reach.
- **Land withdrawals:** 3 cards (A1, B, C), 361 rows, 249 adopted: (361 x $0.042 + $75) / 249 = **$0.36**.
- **National forests:** 3 cards, 312 rows, 215 adopted: (312 x $0.044 + $75) / 215 = **$0.41**.

Cards are shared across types; the A1 card, for example, covers land, forest, military, power-site and water-reserve
orders. About 12 cards cover all 2,107 rows. Over the whole pool, (2,107 x $0.042 + 12 x $25) / (0.69 x 2,107) =
**$0.27 per adopted status**. The high case is (2,107 x $0.21 + $300) / (0.5 x 2,107) = $0.70. On today's route the
same 1,450 statuses would cost $4,830 at Bentham's rate or $11,180 at Papinian's.

### 4.3 What is measured and what is estimated

The token counts per row, the adoption rate, the disagreement rate and the per-call prices are measured, on Ulpian,
Jacquard wave 2, the stateless gauge and Papinian. The batch prices for these particular lots are estimated. The
adoption rate of Pothier-lead lots is not measured: Jacquard's 0.69 came from type-label lots. The Pothier pilot's
1 wrong lead in 129 decided leads (95% upper bound 4.2%) suggests it may be higher, but that pilot read mostly
transcription texts.

Three results would change the conclusion. A stage 0 adoption rate below 0.3 would raise the cost to about $1 per
status. Disagreement above 20% would also raise it, because adjudication would then dominate the cost. A missed
control would stop the lot. The stateless gauge advised against stateless production for full-dossier judgment
(KEEP_AGENT_ROUTE). Stage 0 should therefore run on the agent route by the Ulpian method, which already measured
2,640 tokens per order, with a stateless arm paired against it.

## 5. Full lifecycle claims where the claim is mechanical

For A1, A2 and C (1,327 rows) the claim follows from the same records:

- the whole-order end is the signing date or the stated date;
- the clause inventory is the single operative command;
- the savings are the text merged into the parent (A2) or the residual interests the card names (land reversions);
- the counterevidence is the later-edge list the script already built.

A Nalimov-style drafter can write these claims. Each draft is screened by the kit assembler and the actual claim
checker before any arm is paid. The two arms then read the claim in the same batch row. Nalimov projected $0.10 to
$0.42 per adopted status for such drafts, with a midpoint of $0.17 and 4.9k-token packets (F-20261110-nalimov-census).
Adding a claim roughly doubles the row cost, to about $0.10 to $0.85 per filed order.

This needs two zero-token changes to the claim kit:

1. Accept the tracker-credited texts, carrying out D-20261106-photius-p4 and -r37: R37 printings and P4-checked
   replicas in `working_text.GRADES`, as a separate pull request (lesson of Accursius F6).
2. Build clause inventories for the 3,578 replica-credited orders that have none.

Until then, 111 of the 1,327 orders have a kit original. B and D claims need an acting instrument's own text, or are
`not_later_than` with the first cause unresolved. For those kinds the route proposes the status only.

## 6. Post-1937 orders

The 4,204 post-1937 orders are long Federal Register texts with many clauses. The stateless producers there agreed
with the agent route on only about 40% of outcomes. For these orders, the batch unit is the kit's basis kind, not a
type. The 841 express-revocation candidates can be batched under Respondendi's `express_named_revocation` predicate,
which requires two witnesses: the `ACT:` provision and the catalog note. Rows under the board rule
(D-20261108-board-rule: emergency boards end on the report's transmittal date, not on EO 12553) are held out by
script. The 1,463 orders with a current-law record are batched under `yes_current`, where every YES is audited. The
remaining orders stay on the per-order route. This plan does not estimate their saving, because no batch reading of
long modern orders has been measured.

## 7. Order of work

1. **Zero-token (Domat job):** lot assignment, identity and completeness checks, later-edge exclusion, control
   builder, batch packets, and a forecast per lot. Kean search done (x1, type rule, family rule, undecided, Jacquard,
   Pothier, Ulpian, Respondendi, stateless).
2. **Stage 0 under Augur:** one lane of 30 rows from lot A2 (civil-service rule amendments, 372 rows; card premise P2
   already answered by the owner), scored against this forecast (Whitworth stop rule: above $2.50 per status, or any
   missed control).
3. **Ramp by lot,** in order of rows per card: A2, A1, B1/B2 (land, forest, military), C, D, E.
4. **Kit wiring for claims** (section 5) in parallel, then claims for A1, A2 and C.

## 8. Owner decisions needed

1. **Extend the Jacquard ruling** (2026-10-31) from X1 spent and swept classes to all lots of a lot card. Adoption
   would be by full two-arm reading of every member, typed controls, cross-family audit on probation, and an
   owner-merged pull request. This is the "later ask" left open in the answer to A-20261106-pothier.
2. **Approve each lot card by its hash,** one ruling per card. There are about 12 cards; the first three are A2
   amending-only, A1 spent-on-issue, and B1 land and forest named later instrument.
3. **Public Land Order tables:** may a provisional NO status, as opposed to a filed claim, rest on a BLM Table of Public
   Land Orders row with the gap disclosed? The owner allowed this for a lead (answer to A-20261106-pothier, part 3).
   About 400 leads depend on it.
4. **Measurement:** count statuses adopted without a claim as their own Bentham action (`status_assignment.type_batch`).
   Under D-20261108-undecided-measure, "filed" means status and canonical claim, so these would not count as filed.
5. **Approve the Augur plan for stage 0** (30 rows, lot A2), reviewed by another model family or the owner.

Wiring D-20261106-photius-p4 and -r37 into the claim kit needs no new ruling. It carries out decisions the owner has
already made.
