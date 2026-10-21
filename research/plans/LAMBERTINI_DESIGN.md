# LAMBERTINI: a unit of work for savings_residuals and counterevidence

Named for Prospero Lambertini (Benedict XIV), who formalized the devil's advocate's search for
counterevidence. Written 2026-10-20 by Claude (Opus). Counts come from the readiness tracker output at
`0430303d7` and `jobs/lambertini` run at repo head `4a7859aad`. Every count is a lead count. None of them
is a yield, and certified stays 0.

## 1. The problem Polya left open

Polya (`research/production/polya-2026-10-20/REPORT.md`) found that no unit of work places anything on two
steps: savings_residuals (open on 14,798 orders) and counterevidence (12,497). Only 25 of the decided
not-ready orders are reachable by stacking every frame.

**Finding 1: neither step is ever the last one open.** Among the 3,221 decided not-ready orders:

| Open steps (largest groups) | Orders |
|---|---:|
| clause_inventory + ending + savings | 1,296 |
| original_text + clause + ending + savings + counterevidence | 649 |
| clause + ending + savings + opus_media | 591 |
| original_text + clause + ending + savings | 352 |
| clause + ending + savings + counterevidence | 155 |
| **savings alone** | **0** |
| **counterevidence alone** | **2** |

Savings is open on 3,185 of these orders, and on 3,134 of them there is no claim. Steps 3 to 6 close only
through a claim, or through the tracker's machine search for counterevidence. A claim that closes savings
therefore has to close clause inventory and ending at the same time. On its own, a "savings unit" makes no
order ready. A design for these two steps can do two things:

- make savings almost free inside the unit that already closes the ending: the ending instrument (Polya F1);
- give counterevidence a machine route for the one class the tracker cannot search: orders with no OFR
  catalog entry.

**How the 138 ready orders closed them.** Every claim was written by hand. Savings states: 101 NO orders
`none_after_bounded_search`, 35 `transferred_or_accrued`, 1 `continuing_independent`, and 1 YES order
`none`. Each claim carries the three machine searches as `later_source_search` entries, and some add their
own reading.

## 2. Unit S: one savings reading per ending instrument, shared by every order it ends

A savings question has two halves:

- **Does the ending instrument save anything?** This is shared by every order the instrument ends. Examples
  are a savings clause, "shall not affect", pending proceedings, a transfer of functions or funds, or an
  incumbent clause.
- **Does this order leave anything behind on its own?** Examples are rights accrued under it, functions or
  property it transferred, and continuing independent effect. This half is per order, and the producer
  reads it during the clause inventory it must do anyway.

`jobs/lambertini` builds a **savings packet** (LSP) for each acting EO whose official FR text is held. The
packet records the source URL, sha256 and page, the sha256 of the held text, every savings-type and
transfer-type phrase with its character offsets, and the offsets where the acting text names each target.
84 packets cover 807 decided-NO orders. EO 12553 alone covers 332, EO 9830 covers 54 and EO 14148 covers 44,
so 3 packets cover half the targets. One reading of a packet, recorded once with a section and page pin,
becomes the `savings_residuals.source` for every claim it serves. Each order then needs only an exception
check ("is this order inside a carve-out?") plus its own-residual check.

**Prefill classes** (`SAVINGS_PREFILL.csv`) for the 3,129 savings-open decided orders that have a draft:

| Class | Open | Meaning | Prefill |
|---|---:|---|---|
| S0_none_candidate | 156 | one EO ending instrument, held text names the order, no savings phrase anywhere in it, no transfer wording near the mention or in the order's own text, no own lead, no conflict | `none_after_bounded_search` |
| S1_transfer_wording | 398 | as S0, but transfer, abolition or personnel wording near the mention or in the order's own text | review |
| S2 / S2b savings phrase | 21 | savings phrase near the mention / elsewhere in the acting text | review |
| S3 own lead / S4 conflict | 12 / 76 | the draft's own savings lead / a draft conflict | review |
| S8 acting not EO / text not held / order not named | 82 / 92 / 50 | PLO, statute or proclamation ending; acting text not held (queue it); acting text does not name the order | review / fetch |
| S9 multiple acting / no end candidate | 35 / 1,859 | wait for the ending | wait |
| Y0 no later events | 188 | YES order with no later events, savings lead or conflict | `none_after_bounded_search` (blocked on current basis) |
| Y1 / Y3 / Y4 | 129 / 36 / 51 | YES with later events / own lead / conflict | review |

**Calibration against the 138 ready claims.** These states were written by hand. They are producer claims,
not certified results. S0 matched 7 of 7, all `none`. S1 split 15 none, 12 transferred and 1 continuing, so
transfer wording does not predict the state. The scratch analysis's broader "no savings phrase near"
class matched 17 of 20 (85%). S0 is a prefill a reader confirms. It is never a closure, and it is not the
reason text a claim needs.

## 3. Unit C: a bounded, recorded counterevidence search per order

Counterevidence is open on 884 decided orders:

- **688 with no OFR catalog entry** (`NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE`): 685 are pre-1937 and 3 are
  other. The tracker counts the machine search only for orders in the 1937+ catalog. The searches did run
  on these orders, though: later-events read notes on 1937+ records and 17,521 saved texts (2,049 edges
  target 662 pre-1937 orders), and current-law reads the U.S. Code and CFR by number.
- **159 with a contrary current-law or later-events lead**, and **36 with a quarantined conflict**. These are
  the devil's-advocate cases proper. They stay agent and human judgment.

`jobs/lambertini` writes a **counterevidence record** (LCR) for each of the 688. Each record has four
claim-shaped search entries:

1. OFR notes on later catalogued orders.
2. The saved-text scan, with its coverage: numbered EOs after the order and before 1937 whose text was
   scanned. The median is 98.8%, and the minimum is 36.9% for the oldest orders.
3. U.S. Code and CFR.
4. **New:** the 1944 WPA Historical Records Survey numbered list (1-8030). Later summaries are searched for
   the order's number, in OCR forms such as `E. 0. [9]`, or for its date next to an ending or changing word.

Each record also lists every lead, plus what was **not** searched: unheld pre-1937 texts, Statutes at Large
indexes, agency records, and the WPA unnumbered list. It is marked `draft_not_claim`.

| Class | Records | Next |
|---|---:|---|
| C0 no lead found, original text held | 18 | copy the record into the claim after reading it (once Q-L2 is ruled) |
| C1 a later-events, contrary or WPA lead (109 date and 74 number matches) | 112 | a producer reads each lead; a WPA lead for a NO order is often the ending itself |
| C2 original text open, no lead | 558 | wait for the original (ProQuest/compiled-transcription rulings) |

The record does not light the step. The tracker reads only claims and its own catalog route. A producer
copies the entries into `later_source_search` after reading the leads. Whether this record is an adequate
search for a pre-1937 order is a reading of the codebook, which goes to the owner (Q-L2).

## 4. What stays human or owner judgment

- **Q-L1 (owner, reading of the codebook, not a change):** may a claim state `none_after_bounded_search`
  when (a) the ending instrument's full text, read once, has no savings, transfer or continuation provision
  reaching the order, and (b) the producer's clause inventory finds nothing in the order that accrued,
  transferred or continued? A yes makes Unit S a template. The reason text is still written per order.
- **Q-L2 (owner):** for an order with no OFR catalog record, is the LCR, with its stated coverage and
  stated gaps, an adequate bounded later-source search? If yes, a later tracker change could treat a C0
  record as a machine route. That is the tracker's owner's change to make, not Lambertini's.
- **Q-L3 (owner):** should savings_residuals ever be recorded in `EXHAUSTED.jsonl`? Lambertini says no.
  `none_after_bounded_search` is a finding about the law, not a failure to find a source, and the README's
  evidence rule (ladder `exhausted_proposed` or a route-by-route search) fits original text, not savings.
  Lambertini writes no EXHAUSTED line.
- **Per order, always agent and then human:** the own-residual reading, any S1-S4 or Y1-Y4 order, every C1
  lead, every contrary lead or quarantined conflict, and the D6 question ("was any later event that ended
  or changed this clause removed or ignored?"). Independent human certification stays separate, and the
  certified count stays 0.

## 5. Zero-agent part (built): `jobs/lambertini/`

`lambertini.py build` (about 12 s, standard library) writes `SAVINGS_PACKETS.jsonl`, `SAVINGS_PREFILL.csv`,
`COUNTEREVIDENCE_RECORDS.jsonl`, the pool files and `SUMMARY.json`. `probe` draws a seeded random batch.
`test_lambertini.py` has 9 tests, all passing. They check:

- the class rules send every unsafe case to a reader;
- one packet is built per acting order and shared by all its targets;
- `Page 36` does not count as naming EO 36;
- OCR cites are found;
- coverage is counted;
- no claim or EXHAUSTED file is written;
- the draw is deterministic.

`job.py` and `needs.txt` are there for Actions. This work was not pushed.

## 6. Probe P1 (savings line), registered before any production

- **Pool LAMBS (Llull censuses D-20261020-18 and -20; LAMBC is D-20261020-19, 18 orders, 0 strict):** the S0 orders whose original text and counterevidence are
  done, less the 4 orders already in Rastell batches, which leaves 115. Every order holds `status_present`
  and `original_text_held`. On `ending_or_current_lead2`, 3 hold it (2.6% strict) and 102 are leads (91.3%).
  Gate rev 2 counts only ACT records with an effective date. The held acting text that names the order is
  exactly the route that the gate misses.
- **Batch:** 20 orders, drawn as `random.Random(sha256("lambertini-P1-tracker-0430303d7"))`. They come from
  5 acting instruments, so 5 savings readings serve 20 orders. The 10 EO 12553 targets overlap Rastell's
  EO 12553 work, which covers the ACT provision. Coordinate in HANDOFF before claiming them.
- **Producer:** Opus. Follow `jobs/claim-kit/AGENT_PROTOCOL.md`. Read each packet once and record it, then
  write full claims: clause inventory, ending from the held acting text, savings, and counterevidence copied
  from `MACHINE_LATER_SEARCH.jsonl`.
- **Review:** an independent Opus reviewer with the held source texts and an explicit D6 step (Mountweazel
  configuration), trying to refute each item.
- **Measures:** upheld per attempt; agreement between the S0 prefill and the savings state the reviewer
  accepts; minutes per order.
- **Gate:** scale to the remaining 95 orders only if at least 5 of 20 are upheld and at most 2 of 20 savings
  states are overturned. Stop the line after 2 failed probes.

- **Forecasts (registered, plan `lambertini-P1`):**
  - L-20261020-17: upheld per attempt, p10 0.00, p50 0.15, p90 0.45. It is flagged CEILING_EXCEEDED on
    purpose, because the gate does not see the held-text route.
  - L-20261020-18: S0 prefill agreement, p50 0.8, class `new:`.
  - L-20261020-19: P(gate passed) = 0.2.
  - All three resolve from `research/excavator/lambertini-2026-10-20/OUTCOME.json` by 2026-11-03.

**Probe P2 (counterevidence line), not drawn.** Audit 20 random C0 or C1 records that have original text.
The reviewer searches HathiTrust for the WPA list, the Statutes at Large and Richardson, looking for a
material later event the record missed. Measure the miss rate. This feeds Q-L2. Register before running it.

## 7. Premortem answers (Llull wheel, 12 questions, 0 auto_fail)

- **Unmeasured prerequisite (Q1, Q2).** The 14,798 and 3,185 counts describe the problem; they are not the
  pool. The probe pool is LAMBS: 115 orders hold status and original text. On ending, 3 are held strict and
  102 are leads. No forecast uses the larger counts.
- **Selection bias (Q3).** S0 is the easiest savings class by construction. The P1 rate is measured on LAMBS
  only and must not be carried over to S1-S4, Y or C classes.
- **Cost shift (Q4, Q5).** The reviewer pays: the measured `minutes_per_accepted.modern_claim_reviewer_only`
  is 15.4. One packet reading saves producer time only. P1 measures minutes per order for producer and
  reviewer together.
- **Proxy unit (Q6).** Packets and records are inputs. Success is counted only as upheld orders and ready
  orders.
- **Access (Q7).** The 92 S8 orders whose acting text is not held go to FETCH_QUEUE, not to a hand fetch.
  P1 needs no fetch.
- **Invented rates (Q8, Q9).** The 85% comes from the scratch calibration (17 of 20 ready claims, `a2.py`)
  and is not a base rate. The 98.8% is the median `coverage.share` in `COUNTEREVIDENCE_RECORDS.jsonl`. P1
  registers its own prefill agreement as `new:` with a wide interval.
- **Owner policy (Q10, Q11).** Q-L1, Q-L2 and Q-L3 are unapproved. Nothing in P1 or in any forecast counts
  on them. C2 waits on the original text, not on a ruling.
- **Unconsidered route (Q12).** The zero-agent route is `jobs/lambertini`, and it is built. A cheaper route
  for pre-1937 counterevidence would be a full-text parse of the 1944 WPA list's disposition remarks. The
  current parse holds summaries only.

## 8. Risks

- **Reach is not yield.** At most 115 orders and 5 readings are touched, and clause inventory and ending
  are still open on 113 of the 119 S0 orders. Bowditch Y2 upheld 6% and Craigellachie 0 of 23.
- **The S0 prefill may be right for the wrong reason.** A list-style revocation (EO 12553) has no savings
  clause, but the order itself may have transferred functions. The own-residual check is the guard, and
  the reviewer must test it.
- **The phrase lists are English regexes over OCR.** A savings clause in odd wording or a broken OCR layer
  reads as "none". Every packet reading is done on the full text, not on the phrases.
- **WPA date matches are weak:** several orders share a date. They are leads only, and the list is a finding
  aid, never an original.
- **AI statuses are hypotheses.** The codebook is unchanged, nothing is adopted into the reconciled CSV,
  no tier is promoted, and certified stays 0.
