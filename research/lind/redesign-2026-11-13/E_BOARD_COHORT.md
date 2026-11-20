# The 126 railway and airline emergency-board orders: what their apparent readiness means (2026-11-13)

Bounded coordinator check using existing structured records and targeted inspection; no PDFs were re-read in bulk and
nothing was spent on production or review.

**Labels:** [obs] observed in a pinned artifact; [chk] checked here; [int] interpretation; [proj] projection.

## 1. Pinned evidence

| What | Artifact (commit) |
|---|---|
| **The owner's rule** | D-20261108-board-rule; `research/readiness/owner_rulings/2026-11-08-haloander-decisions.md` item 2 (36cff91d1) |
| **The rule's working analysis** (a producer brief written by the Haloander coordinator) | `research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt` (36cff91d1) |
| **The stored report bytes:** 119 PDFs for 126 orders, in the Pergamon release store; re-fetched and re-hashed on every run | `jobs/eumenes-nmb-reports/output/SOURCES.jsonl`, `SUMMARY.json` (36cff91d1); decision D-20261110-papinian-board-bytes |
| **The checker reads that store** (`pergamon_store` custody kind) | `jobs/claim-checker/sources.py` (36cff91d1) [chk] |
| **Readiness per order** | `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv` (generation 2026-11-12T19:57Z) |

Kean D-20261110-papinian-board-bytes still says "not wired". That record is stale: the store and the checker adapter
exist [chk].

What the rule says:
- **The board clause** ends on the date of the held report's transmittal letter.
- **The order's own "no change for thirty days after the report" sentence** is a separate clause, ending at the end of
  the 30th day after that date.
- **Other clauses** are decided on their own evidence.
- **The cleanup revocation** (EO 12553 or EO 12379) remains the formal disposition.
- **Block the order** if the report's board number, creating order, parties or date do not match, or if the date is
  unreadable.

## 2. The derivation of "up to 117 of 126" [chk]

- **Orders:** 126 have a stored report.
- **Status:** all are already decided provisional NO, through the inherited legacy ledger.
- **Claims:** 121 have claims, written by earlier waves (Justinian, Erasmus, Apollo, Tribonian, Astra).
- **Readiness:**
  - 3 are ready (6/6);
  - 117 are at 5 of 6 steps, and their only blocker is `FIRST_END_UNRESOLVED`;
  - 6 have wider gaps (no clause inventory, unproved first end, open savings).

**What the 117 means:** their existing claims end the order at the cleanup revocation, which the tracker no longer
accepts as a first end. It does not mean their histories are almost done.

## 3. Four different things that "ready" can mean here

| Level | The board cohort |
|---|---|
| **Source available** | Yes for 126: report bytes stored, and custody checkable |
| **The shared rule applies** | Directly to the orders that create a board (about 104 of 121 by their operative text [chk]). Not directly to extension and amendment orders: 6 reports each cover a board order plus its own follow-on orders. Examples: PEB-161 covers EO 11168, 11169, 11170 and 11181; PEB-135 covers EO 10919 and 10926; PEB-136 covers EO 10923 and 10933 [chk]. Those follow-on orders need their own chain of reasoning |
| **The historical question resolved** | The ending step only: when the board's task was done and when the order's standstill ran out |
| **A complete researched life history** | No. The completion contract does not ask for: board membership and appointments; the report's findings and recommendations; whether the dispute settled, struck, or went to later boards; and congressional intervention. For example, EO 14077, the 2022 freight board, was by public record followed by a statute settling the dispute [int: not checked in this repository]. The held reports already contain some of this: EO 10045's report records that the parties announced a written agreement ending the strike [chk] |

## 4. Challenging "only a transmittal date and exceptions remain"

That claim is **false for most of the cohort** [chk]:

- **The no-change clause:** 94 of the 117 one-blocker claims carry the order's no-change sentence inside a single
  clause. Only 8 split it out; 15 orders have no such sentence.
- **What the rule then requires:** a separate standstill clause with its own end date. So about 80% of these claims
  need a changed clause inventory and recomputed ends. That is a new claim version, so blind review must be renewed.
  The rule itself routes these as replacement proposals.
- **An unreadable date:** EO 10926's held transmittal date line is OCR-damaged ("June ~0~ 1961"), and its existing
  claim takes the date from the report's cover. A strict reading of the rule says to block.
- **Follow-on orders:** extension and amendment orders share a report with their board order (6 groups, 12 orders).
- **Extra clauses:** at least 5 claims have 3-4 clauses (EO 10015, 10622, 12370, 12495 and others). EO 12495 has no
  whole-order end recorded.
- **Supplemental reports and reconvening:** unresolved. The stored texts are the reports themselves. Keyword hits for
  "reconvene" are hearing procedure, not later reports [chk]. Settling it needs an index of supplemental reports, such
  as the NMB's list of emergency boards. That list is located but not acquired.

**What would disprove the "rule applies" premise:** held evidence that a board filed a later or supplemental report, or
reconvened after its report. A report whose board number or parties do not match its order would also do it. None was
found, but none was searched for systematically.

## 5. The shortest path from held sources to reviewable findings (existing machinery)

1. **Zero-token step:**
   - Extract each report's cover and transmittal dates from the held text extracts (`jobs/source-ladder/output/texts/queue_EO_*`).
   - Flag OCR-damaged dates, shared-report groups, extra clauses and orders with no standstill sentence.
   - Split the standstill clause and compute its 30-day end by script.
   - Run the actual checker offline (`kit.py overlay-check`'s new pre-review check, PR #305).
2. **Replacement proposals** for the clean cases (a script or a narrow producer pass under `board_rule.txt`).
3. **Blind review in batches:** two arms with planted controls, as for Cujas's recheck of already-reviewed claims (Kean
   F-20261108-cujas-photius-recheck: worker cost about $0.41 per filed claim).
4. **Completion.**
5. **Owner adoption by named decision,** per D-20261110-papinian-board-bytes.

| | Removed | Still required | First use | Recurring |
|---|---|---|---|---|
| Legal analysis of the ending mechanism | Yes: the rule is decided once | Checking each order's text against the rule | the done rule | per order |
| Source acquisition | Yes: bytes stored | Index of supplemental reports | that index (unpriced) | none |
| Drafting | Mostly, by script | Judgment on the exceptions (OCR dates, follow-on orders, extra clauses) | script, about 1 session | per exception |
| Blind review | No | Every changed claim, two arms, controls | none | about $0.4-1 per claim [proj, from Cujas] |
| Owner work | No | One named adoption decision per batch | none | minutes |

**Projection,** not measured: about $0.5-1 per order brought to ready on the clean cases, or about $60-120 for about
100 orders, plus coordination. That buys a correct ending step for orders already decided NO. It does not buy new life
histories.

## 6. Recommendation

**Do not call the board cohort "the best lever" for complete histories.** It is the cheapest known route to correct,
completion-ready ending steps on about 100 orders. It also illustrates the owner's point: sources already bought that
have not yet produced their value. But it advances the full-life-history goal only on its ending question.

**If funded, start with a hard-case sample, not easy confirmations.** Six orders:
- **EO 10926:** the unreadable transmittal date.
- **EO 11169:** a follow-on order sharing PEB-161.
- **EO 10015:** several clauses.
- **EO 14077:** congressional intervention, outside the contract; record it, do not force it.
- **EO 12495:** no whole-order end.
- **One plain order with the standstill sentence folded in,** as the reference case.

The zero-token extraction for all 117 comes first.

- **Cap:** $15 all-in, including fresh-context coordination.
- **Stop if:**
  - fewer than 4 of the 6 reach eligible;
  - or review dollars per eligible order exceed $2;
  - or the zero-token step finds supplemental-report evidence for any board, which means the rule premise needs the
    owner.
- **What it establishes:** the exception rate and per-order cost on the hardest board cases. It does not establish
  collection-wide savings.
