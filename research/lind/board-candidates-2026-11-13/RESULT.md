# Board cohort: candidate ending corrections, extraction and classification (2026-11-13)

This folder holds **isolated candidates, not claims.**
- **Artifacts:** `extract.py` (zero model tokens; re-runnable), `CANDIDATES.json` and `CANDIDATES.csv` (126 orders),
  and `nmb-inventory/` (the public NMB list of emergency boards, with retrieval time and sha256 in `SOURCE.json`).
- **Inputs:**
  - `jobs/eumenes-nmb-reports/output/SOURCES.jsonl`: report bytes in the Pergamon store, with locators;
  - `jobs/source-ladder/output/texts/` and `SOURCES.jsonl`: report text extracts;
  - the current effective claims in `research/readiness/claims/`;
  - `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`;
  - the census.


## 0. Corrections (2026-11-13, targeted pass)

1. **"Closed" is undefined.** The NMB does not define its "closed" column, either on the list page or on the overview
   page (fetched 2026-11-13). Board 187's row shows closed 10/10/1975, yet the board reconvened and reported again on
   1975-11-26. So "closed" is not proven to mean report submission or the end of the board.
2. **Agreement is not independence.** The NMB both publishes the reports and keeps the inventory, so it may have
   compiled the inventory from them. A match therefore checks the **transcription** of the date. It is not independent
   historical evidence that the report was submitted that day. The status `CORROBORATED` is renamed `INVENTORY_AGREES`
   throughout. The submission evidence is still the held report's own transmittal letter or cover.
3. **The page images are readable; the extraction failed.** Every image viewed (11) was readable by a human. The
   "damaged" and "absent" labels describe failed OCR or extraction, not unreadable sources.
4. **The owner rule does not require blocking a readable image.** The owner's text (D-20261108-board-rule;
   `research/readiness/owner_rulings/2026-11-08-haloander-decisions.md` item 2) ends the board command "on the
   transmittal-letter date of the held report". The held report is the PDF. The instruction to block when the date
   is "unreadable in the held text" comes from the coordinator's producer brief (`board_rule.txt`), not the owner's
   ruling. A date read from the held report's page image therefore does not need an owner rule change. It needs a
   recorded page reading, which existing page-check routes provide, and an update to the brief. The earlier statement
   that "changing that is an owner decision" was wrong.
5. **The 67 are not proven clean.** They are **candidate inputs under the documented checks**: the inventory agrees, the
   order creates a board, and no flagged exception was found. Exceptions not visible to these checks (for example
   unlisted reconvenings, or a statute affecting the standstill) are not ruled out.

**Still unresolved:**
- the meaning of "closed";
- whether other boards reconvened without an inventory note;
- the 33 orders whose dates have not been read from the image;
- case-specific questions for the 23 exceptions.

**Not done:** the proposed 10-order pilot. It would estimate clean-repair performance, not comparative savings.

## 1. What each date field means

- **Transmittal reading:** each reading carries its text offset and raw characters.

  | Label | Meaning |
  |---|---|
  | `OBSERVED_DATELINE` | the letter's date line, between the "Letter of transmittal" heading and the address to the President |
  | `OBSERVED_DATELINE_OCR_CORRECTED` | a misread digit corrected only because the result equals the independent NMB date |
  | `OBSERVED_NO_HEADING` | a letter found by its address, without the heading |
  | `OBSERVED_BODY_ONLY` | a date in the letter body. Weak, and never used |
  | `DAMAGED` | month or year present, but not readable |
  | `ABSENT` or `NO_TRANSMITTAL_MARKER` | nothing found |

- **Cover report date:** the date printed above "(No. NN)" on the report cover.
- **NMB inventory "closed" date:** an independent value, recorded but never substituted.
- **`report_date_status`:**

  | Status | Meaning |
  |---|---|
  | **INVENTORY_AGREES** | a held-report reading equals the NMB date |
  | **CONFLICT_IMAGE_CHECK_NEEDED** | the readings disagree |
  | **UNREAD_IMAGE_CHECK_NEEDED** | no reading |

  One machine reading is never enough: in every disagreement checked against the page image, the NMB date was right
  and the extraction was wrong (section 3).

- **Candidate ending:** computed only for INVENTORY_AGREES, board-creating orders.
  - The board clause ends on the corroborated report date. The transmittal evidences submission; receipt by the
    President may be later.
  - The standstill clause, only where the claim's quoted order text has the "thirty days after … report" sentence, is
    **INFERRED_UNDER_RULE** (D-20261108-board-rule). Both counting readings are given: report date plus 30 days, and
    plus 29 days.
  - No uncertain reading is turned into a computed end.

## 2. Counts (126 distinct orders; categories are exclusive except where noted)

| Category | Orders | Meaning |
|---|---:|---|
| Already ready (6/6) | 3 | EO 10015, 10286, 12159 |
| **Usable inputs for a candidate correction** | **67** | report date corroborated, the order creates a board, no demonstrated exception, not ready. All 67 are tracker one-blocker orders. 57 have the 30-day sentence in their claim text; 10 have only the board clause |
| **Demonstrated exception** | **23** | follow-on orders sharing a report (11); no current claim (5); congressional action listed by the NMB (5: EO 11101 with PL 88-108; EO 11324 with PL 90-10, 90-13 and 90-54; EO 12370 with PL 97-262; EO 14077 with PL 117-216; EO 12095's board created by PL 95-504); a reconvened board (EO 11876, below); a second board (EO 12495); more than two clauses (3). One order can carry several |
| **Unknown report date** | **33** | 25 unread and 8 conflicting readings. A page-image check is needed; every one checked so far was readable by a human |
| Overlap | 2 | of the 23 exceptions, 2 also have an unknown date (counted once, under exceptions) |

**The reconvened board** (EO 11876, Emergency Board No. 187):
- Its report is dated 1975-10-10. The NMB lists a supplement, `PEB-187-Report-Supplement.pdf`, sha256 438ccb9d…, fetched
  for this audit.
- The supplement's transmittal letter, dated **1975-11-26**, says the President approved on 1975-11-19 a request to
  **reconvene** the board to interpret one of its recommendations.
- This raises a question about the original board's authority and its clauses after 1975-10-10. It is not an automatic
  date substitution, and it stays an exception for judgment.

**What the inventory search does and does not establish:**
- The NMB list has 254 boards. It notes exactly one "Supplement Published" and one "Second PEB".
- Its silence elsewhere is **not** proof that no other board reconvened or reported again.
- The NMB annual reports (only fiscal 1949-1951 are held, in `jobs/source-ladder/data/nmb-series-20261025/`) were not
  searched systematically.

## 3. Cross-check against page images

These 11 cases are a check on the extraction and classification, not a yield estimate. They were deliberately varied:
headed and unheaded letters, damaged, absent, missing, OCR-year, supplement and modern cases. Each PDF was downloaded
from the Pergamon store and its hash matched the stored record.

| Order (board) | Script's reading | The image shows | NMB | Lesson |
|---|---|---|---|---|
| EO 9702 (33) | date line 1946-04-18 | (not viewed) | 4/18/1946 | control; agrees |
| EO 9922 (55) | body date 1948-01-14 | letter **February 14, 1948**; cover 1948-02-14 | 2/14/1948 | the body date was the appointment date; flagged and not used |
| EO 9923 (56) | unheaded 1948-01-29 | (not viewed) | 1/29/1948 | agrees |
| EO 10114 (82) | damaged ("1960") | letter **April 1, 1950** | 4/1/1950 | OCR year error; a human can read it |
| EO 9929 (57) | damaged | letter **March 27, 1948**; cover 1948-03-27 | 3/27/1948 | OCR failure; readable |
| EO 9918 (54) | no letter found | cover **January 28, 1948** | 1/28/1948 | the cover date is readable |
| EO 10919 (135) | damaged | letter **June 20, 1961** | 6/20/1961 | the rule says block if unreadable, yet a human reads it; the rule is not changed here |
| EO 11876 (187) | date line, OCR-corrected, 1975-10-10 | letter **October 10, 1975** | 10/10/1975 | correct, but the board reconvened (supplement dated 1975-11-26) |
| EO 10511 | date line 1954-01-15 | letter **May 15, 1954** | 5/15/1954 | the script took the body date; the address to the President was missed |
| EO 11852 (186) | date line 1975-05-28 | letter **May 23, 1975** | 5/23/1975 | OCR read 3 as 8 |
| EO 14077 (250) | unheaded 2022-08-16 | (not viewed) | 8/16/2022 | agrees; congressional action PL 117-216 |

- The extraction alone was wrong in 4 of the 6 disagreements checked (EO 9922, 10511, 11852, 10114). That is why
  corroboration is required.
- Every viewed date was readable by a human. "Damaged" describes failed OCR or extraction, not the evidence (see
  section 0, item 4, on the rule).

## 4. Which reasoning is established, and which is case-specific

- **Established and reusable** (owner rule D-20261108-board-rule and its analysis in
  `research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt`):
  - a board-creating order's board clause is performed when the board reports;
  - the order's own standstill sentence is a separate clause, ending 30 days after the report;
  - the cleanup revocation (EO 12553 or EO 12379) stays as the formal disposition.
- **Case-specific, judgment still needed:**
  - Follow-on extension and amendment orders: what each one commanded and when it was spent.
  - Reconvened or second boards: whether the original board's authority and clauses continued (EO 11876, 12495).
  - Congressional action: whether a statute ended or changed the standstill or the board's role (5 orders).
  - Orders with extra clauses (compensation, other officers).
  - Unreadable dates: the production rule says block, though a human can read them. Changing that is an owner
    decision.
  - Verifying, per order, that the claim's quoted standstill sentence is the order's own text and counts from the
    report.

## 5. What this corrects, and what it leaves out

- **Corrects:** the ending step of claims that currently end these orders at the 1986 cleanup revocation. That is an
  upper bound the tracker no longer accepts as a first end. For the 67 orders it supplies, as candidates:
  - when each board's task was done;
  - when its standstill ran out.
- **Leaves out** (full-life-history questions outside the completion contract):
  - board membership and appointments;
  - the report's findings and recommendations;
  - whether the dispute settled, struck, or went to a further board;
  - presidential or congressional follow-up (5 statutes listed by the NMB);
  - the parties' later agreements;
  - reconvenings.
- **Some of that is already in the held reports:** for example, EO 10045's report records the parties announcing a
  written agreement ending the strike.
- **Scope reconciliation warning** (Sol's EO 9482 finding, in a different family: a common termination source covered
  18 of 19 mines, and the 19th ended earlier): a shared rule's coverage must be reconciled order by order. Here that
  means follow-on orders and boards whose reports cover several orders.

## 6. Work and cost incurred (list-price allowance; cash $0)

- **Coordinator, this extraction round:**
  - script development (four corrections after checks exposed errors);
  - inventory retrieval;
  - 12 page renders and image reads;
  - classification and this write-up.

  About $6.3 through 01:07 UTC, plus the remaining write-up, measured from the transcript.
- **The preceding board check** (premises, the 94-of-117 test): about $5.0.
- **Script execution:** seconds; no model calls.
- **Network:** the NMB list page and 12 PDFs (about 20 MB).
- **Owner time:** reading only.

Execution being token-free does not make the activity free.

## 7. Is a paid experiment still worth doing?

**The decision it answers:** whether correcting the 67 usable-input orders is cheap and reliable enough to fund. That
means per-order production plus blind-review cost, and the review acceptance rate. It does not decide any exception;
those need owner rulings or case work.

**Selection:**
- A simple random sample of 10 from the 67, stratified by era (before 1960, 1960-1979, 1980 on) in proportion to their
  counts.
- No deliberately blocked or stress cases, and no eligibility quota for exceptions.

**Method:**
1. Replacement claims built from the candidate inputs (a script or a narrow producer pass).
2. `overlay-check` with the offline checker.
3. One blind review set with two fresh arms and planted controls.
4. Completion.

**Cap:** $12 all-in, including fresh-context coordination.

**Stopping rule:** stop after the first 5 if either holds:
- reviewers reject 2 or more for a defect in the candidate inputs (date, standstill, clause split);
- cost per eligible claim is running above $1.50.

Otherwise finish the 10 and report cost per eligible claim with its range, and the defects found.

**Worth it?** Only if correct ending steps on already-decided orders are worth about $40-80 for the 67 (a projection,
not measured). That is real accuracy work on existing claims, not new life histories. If the owner's priority is
broader histories, spend nothing here yet. The 33 unknown dates can be resolved by image checks first, a human task of
about 1-2 minutes per order, unmeasured.
