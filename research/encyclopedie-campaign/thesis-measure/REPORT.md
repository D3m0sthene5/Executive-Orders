# How far the held data can fill the thesis measure

Encyclopédie stream "thesis-measure", 2026-11-06 (Opus worker; committed by the coordinator because the worker's
harness refused to write report files). Kean D-20261106-encyclopedie-thesis-measure. All data are read from commit
`857313b455` of `main`. **This is a report only.** It changes no status, claim, codebook, census or tracker file, and
none of its rows is a legal finding. Human-certified whole-lifecycle dossiers remain 0.

Coordinator checks before committing: `measure.py` re-run at `857313b455` reproduces `MEASURE.csv` byte for byte;
`test_measure.py` 12 tests pass; examples 2 and 10 read in the held text (EO 12254 line 33, "1-105. The Board shall
term inate on D ecem ber 31, 1981"; EO 12258's held text contains no "12176").

## Conclusions first

1. **The measure can be filled today for 59 orders, and 34 of them rest on held, hash-verified official text on both
   sides.** These are orders formally revoked after an earlier, evidenced end of operative force. In 32 of the 34 the
   earlier end comes from a filed, gate-checked claim. The 59 prove that the pattern exists, with gaps from 31 days to
   24.8 years. They are not a rate.
2. **The held data do not yet show that formal revocation "often" only cleans up.** 2,880 orders have a formal
   revocation candidate; 810 of them have a filed claim. In those claims:
   - 475 (59%) say the revocation itself ended the order;
   - 43 (5.3%) show an evidenced earlier end;
   - 198 (24%) are open, 179 of them cleanups that the producers believe came after the order was spent but could not
     date (R3).

   Even if every open one proved to be an earlier end, the claimed set would reach at most 241 of 810 (30%). The
   claimed set is also not a sample: batches were chosen by revoking instrument. In the Stage 15 stratified sample, 1 of
   120 orders falls in this category (design-weighted share 1.1%), and only 19 sample orders have been researched, so
   that figure says little.
3. **The other half of the thesis is better supported: 1,135 orders show an earlier end and no formal revocation in
   held data.** These orders stopped operating but stayed on the books. 149 rest on held verified claims, 320 on claims
   whose bytes are recorded but not matched here, 132 on regular-expression leads in held text, and 534 on editorial
   labels (the 1989 "temporary" and "executed and obsolete" entries, and three Formulario notes).
4. **The tracker column is blank because of one code path, and a small change fills it from claims alone:** 32 `yes`,
   487 `no`, 824 blank among v1 claims (`TRACKER_FIX.md`). `tracker.py` asks `claim_gate.derived()` only about v2
   claims, and all 184 v2 claims are R3 cleanup bounds, which correctly give no answer.
5. **The largest single unlock is on the revocation side, not the cessation side.** 1,141 formal revocations are known
   only from disposition notes or the 1989 table. For 706 of them the committed official text of the revoking order
   contains the target's number. These are mostly table-form lists such as EO 12553's, which the later-events sentence
   scanner does not parse.

## What was measured, exactly

The codebook keeps formal validity and operative force apart (TC01: "formal disposition, operative effect, cessation
cause, judicial enforceability and evidence sufficiency are distinct"). The measure pairs one fact from each axis.

- **Formal revocation (F):** the earliest later instrument that expressly revokes or supersedes the *whole* order by
  name. Sources:
  - the order's filed claim: its whole-order end, its v2 `formal_disposition`, or a revocation event on every clause;
  - Formulario instance lemmas built from `jobs/later-events` (relations `revokes`, `supersedes` and
    `supersession_or_revocation`, with no qualifier and no partial evidence for the same pair);
  - the 1989 OFR disposition table (categories "revoked" and "superseded").

  A claim-cited revocation is set aside when its held text never contains the order's number and it revokes a parent
  order "as amended": TC09 says that is not a revocation of the amending order by name (53 orders). A revocation in
  part is never an F.
- **Earlier end (E):** the earliest evidenced end of operative force of the whole order before F. When the order has a
  filed claim with a whole-order end, only the claim decides. Without one, E comes from leads:
  - an own-terms clause with a stated date, found by a regular-expression scan of the order's held clause-draft text;
  - Formulario lemmas in which a later instrument terminates the order or its body by name;
  - the 1989 table's "temporary" and "executed and obsolete" labels, dated "not later than 1989-01-20".
- **Not counted as earlier ends**, under the standing rulings: a report deadline (D-20261021-report-deadline); a
  strike-and-insert amendment (D-20261021-strike-and-insert); an end bounded only by the cleanup instrument itself (R3,
  v2 `not_later_than`); a judicial holding (TC12). An order whose only candidate is one of these is **blocked**.
- **Statute without naming the order (A-20261106-1, answer provisional):** kept in its own column and its own "if
  adopted" category. It counts only when the statute's bytes are held and verified and the order's own clause text
  names the statute it rests on.
- **Evidence levels:**
  - `held_verified`: official text whose committed bytes match the recorded SHA-256, directly or through a job's
    `SOURCES.jsonl` record (the claim checker's rule); for a Formulario lemma, the kernel also found the quote.
  - `held_unverified`: a hash was recorded but the bytes were not matched here, the text is a secondary transcription
    (American Presidency Project), or the sentence was not found under the acting order's own heading.
  - `lead_only`: a disposition note or table entry.

  The tables show the weaker of the two sides.

## Counts now (14,998 orders in the tracker)

| Category | Orders | How the evidence splits |
|---|---:|---|
| Formally revoked after an evidenced earlier end | **59** | 34 verified on both sides (32 by filed claim, 2 by text scan); 3 with one side unverified; 22 with a lead on one side |
| Formally revoked, no earlier end evidenced | 2,610 | F verified 874, unverified 639, lead only 1,097; the filed claim says the revocation was the end for 475 |
| Earlier end, never formally revoked (in held data) | 1,135 | E from filed claim: verified 149, unverified 320; text scan: verified 15, unverified 117; editorial label: 534 |
| Blocked | 837 | see "What blocks the rest" |
| Neither | 10,357 | 8,609 with no record at all; 1,358 provisional ledger NO; 356 ledger YES; 34 YES claims |

If the owner adopts the provisional answer to A-20261106-1, 209 blocked orders become "earlier end, never formally
revoked" and 1 becomes category 1: 60 / 2,610 / 1,344 / 627 / 10,357.

**Share of formally revoked orders with an evidenced earlier end:**

| Formally revoked orders considered | With evidenced earlier end |
|---|---:|
| All 2,880 (any evidence) | 59 (2.0%) |
| 1,087 whose revocation rests on held verified text | 34 (3.1%) |
| 810 with a filed claim | 43 (5.3%); 32 (4.0%) verified on both sides |
| Stage 15 sample, 34 of 120 formally revoked | 1 (design-weighted 1.1% of all orders) |

These shares are floors set by the research done so far, not estimates. Most formally revoked orders have never had
their own terms read: 1,756 have only a machine clause draft and 298 have no segmented text at all.

**Routes of the earlier end:**

| Route | Category 1 (59) | Category 3 (1,135) |
|---|---:|---:|
| Own terms (sunset, fixed term, "until" date), filed claim | 38 | 442 |
| Own terms, text-scan lead | 14 | 132 |
| Implied supersession by a later order covering the same ground, filed claim | 4 | 0 |
| Exhaustion of a one-time command, filed claim | 0 | 21 |
| Termination of the order or its body by a named instrument | 2 | 171 |
| 1989 editors' "temporary" or "executed and obsolete" label | 1 | 367 |
| Statute or plan naming the order | 0 | 2 |

Own terms dominate: committees with sunsets, and one-person retirement exemptions "until" a date. None of the 59 rests
on an earlier revocation of the remaining clauses. The statutory route (A-20261106-1) supplies none of the counted
rows; it is reported separately.

**Gaps between the earlier end and the formal revocation (category 1):**

| Set | n | Median | 25th-75th percentile | Range | Under 1 year | 1-5 years | 5-10 years | 10-25 years |
|---|---:|---:|---:|---|---:|---:|---:|---:|
| All | 59 | 547 days (1.5 years) | 284-1,517 days | 31 days to 24.8 years | 23 | 24 | 2 | 10 |
| Both sides verified | 34 | 636 days (1.7 years) | 284-1,517 days | 31 days to 24.8 years | 15 | 13 | 2 | 4 |

Cleanup revokers recur: EO 11342 (1967) 9 times, EO 12534 (1985) 8, EO 12553 (1986) 7, EO 11812, 13062 and 13316 4
each. Several say on their face that they revoke orders "which established committees that have terminated".

## Ten worked examples (the worker read both sides in the held text)

Paths are committed files at `857313b455`. Examples 1-9 are verified on both sides; example 10 shows why a disposition
note is only a lead. `scripts/examples.py` prints the passages for any order.

1. **EO 7921 (1938), Quetico-Superior Committee.** Extended "for a period of four years, from June 30, 1938 to June 30,
   1942" (claim `claude-2026-10-18-codif-b3.jsonl`; `jobs/fr-originals/output/texts/EO_7921.txt`). EO 11342 sec. 6
   (April 10, 1967) lists it among orders "hereby superseded" (`jobs/fr-originals/output/texts/EO_11342.txt`). **Gap:
   24.8 years.** The same section supersedes the Committee's later extensions (EO 9213, 9741, 10134, 10541 and
   others), each long expired.
2. **EO 12254 (1980), National Advisory Community Investment Board.** "1-105. The Board shall terminate on December
   31, 1981, unless sooner extended" (`jobs/fr-originals/output/texts/EO_12254.txt`). EO 12553 (February 25, 1986)
   lists 12254 in its table of revoked orders (`jobs/fr-originals/data/full_run/texts/EO_12553.txt`). **Gap: 4.2
   years.**
3. **EO 12202 (1980), Nuclear Safety Oversight Committee.** EO 12240 moved its sunset ("The Committee shall terminate
   on September 30, 1981"). EO 12379 sec. 22 (August 17, 1982): "Executive Order No. 12202, as amended, ... is
   revoked". **Gap: 321 days.** The claim also records a second revocation by EO 12399 (December 31, 1982): a cleanup
   of a cleanup.
4. **EO 12412 (1983), Peace Corps Advisory Council.** "The Council shall terminate on December 31, 1983, unless sooner
   extended". EO 12534 sec. 3 (effective September 30, 1985) lists it among orders that "established committees that
   have terminated". **Gap: 639 days.**
5. **EO 12511 (1985), President's Child Safety Partnership.** "The Partnership shall terminate on April 29, 1987, or 60
   days after submitting its final report, whichever is earlier". EO 12610 sec. 3(d), effective September 30, 1987,
   revokes it. **Gap: at least 154 days.**
6. **EO 11414 (1968), military basic pay rates.** EO 11475 adjusted the same rates "effective on July 1, 1969" with
   complete new tables, which the claim reads as implied supersession. EO 11812 (effective October 1, 1974) expressly
   supersedes EO 11414 and 11475. **Gap: 5.3 years.**
7. **EO 13018 (1996), three members added to the National Bioethics Advisory Commission.** EO 13137 moved the parent's
   sunset to October 3, 2001. EO 13316 (September 2003) revokes "Executive Order 12975, as amended by Executive Orders
   13018, 13046, and 13137" (named, so TC09 does not set it aside). **Gap: 727 days.**
8. **EO 12785 (1991), extension of the President's Education Policy Advisory Committee to December 31, 1992.** EO
   12869 (September 30, 1993) revokes "Executive Order No. 12687, as amended by Executive Orders Nos. 12741 and 12785".
   **Gap: 273 days.**
9. **EO 13278 (2002), President's Commission on the United States Postal Service.** "The Commission shall terminate 30
   days after submitting its report and in no event later than August 30, 2003". EO 13316 item (d), September 30,
   2003, revokes it. **Gap: at least 31 days.**
10. **EO 12176 (1979). A lead, not a finding.** It revised EO 12103 so that the Coal Commission "shall terminate on
    March 15, 1980" (held verified). The OFR note and the 1989 table say "Revoked by: EO 12258", but EO 12258's held
    text revokes EO 12103 "as amended" and never mentions 12176. The row stays in category 1 with its revocation side
    `lead_only`, and its note says why.

A correction came out of reading the evidence. A first pass took EO 9278's claim, "not a revocation or supersession of
EO 9278", as a revocation by EO 9618. Negated wording is now removed before classification, with a unit test. EO 9278
is "earlier end, never formally revoked": a one-time appointment exhausted on signing.

## What blocks the rest

| Blocker | Orders | Single action that would unlock the most |
|---|---:|---|
| Formal revocation known only from a disposition note or the 1989 table | 1,141 (409 revoking instruments; EO 12553 alone 148) | Teach the Formulario kernel or later-events to prove list and table revocations (the target's number inside the revoking section of the acting order's committed official text). The number is present for 706, absent for 232, and the text is not committed for 89 (plus 114 non-EO actors) |
| No reviewed clause inventory | Of 2,821 formally revoked orders without an earlier end: 1,756 machine draft only, 298 no segmented text, 767 with a claim (475 conclude the revocation was the end). 5,207 orders overall have neither claim nor draft | Claims first for the 251 unclaimed, formally revoked orders whose revoker elsewhere cleaned up a spent order (EO 12553: 115; EO 9830: 37; EO 14148: 12; EO 12258: 10) |
| Formulario lemmas left as `sorry` | 11 orders with all whole-revocation lemmas `sorry`; 299 `sorry` revocation lemmas (149 source not retained, 141 quote not found); 10 `sorry` class lemmas | Fix the quote for class axiom F-741b0611fbf9 (Pub. Res. 26 of June 14, 1935, 49 Stat. 375), the statute behind the 209 NIRA-code claims, whose bytes `jobs/astra-source-retention` already holds; then the National Emergencies Act axiom for the 311-order war and emergency family |
| A-20261106-1 (a statute that does not name the order) | 210 qualify under the provisional answer (209 NIRA code orders, S.J. Res. 113 of 1935); 372 more (war and emergency family) have only a family-level class lemma | The owner's answer moves the 209. The 372 also need the order's own authority clause matched to the statute, which a zero-token per-order quote check can do |
| R3 cleanup bounds and the report-deadline ruling | 184 claims (145 EO 12553 emergency-board orders, 140 disclosing "functionally spent") | None by evidence about the report: under D-20261021-report-deadline a board's report is not an end, and under R3 the cleanup is only a bound. Report them as a separate "functionally spent, disclosed" line |
| Strike-and-insert amendments treated as ends | 17 claims | The re-check the 2026-10-21 ruling already orders (43 clauses in 26 claims) |
| Amendment or extension before a scanned own-terms date | 35 | Read the extension edges; each "further exempt" is its own later event (D-20261021-until-dates) |
| Judicial holdings | 19 | TC12 scope work; not counted as cessation |
| Formal revocation undated | 210 rows flagged | Date the revoking orders from the census or the order texts |
| **Tracker code path** | 0 of 14,998 filled; 1,343 v1 claims never read; 184 v2 claims all bounded | `TRACKER_FIX.md`: about 80 lines; 32 `yes` / 487 `no` from filed claims alone |

## Comparison with the published baseline

Lowande and Poznansky (*Journal of Public Policy*, 2024) report that most executive actions are never formally
revoked; the prior-art stream (branches `enc/prior-art`, `enc/prior-art-lp`) covers their data and Thrower's.

- **How the categories map.** A measure of "formally revoked or not" sits entirely on this project's formal axis:
  "never formally revoked" is categories 3 and 4 (and blocked rows without an F); "formally revoked" is categories 1
  and 2. A measure of order life that ends at formal revocation overstates operative life in category 1 and counts as
  surviving an order already ceased in category 3. Neither published measure can tell category 1 from category 2,
  which is the thesis.
- **Formal axis in held data.** 2,880 of 14,998 orders (19%) have a formal revocation candidate: 36% of orders from
  1937-1988, 26% from 1989 on, 6.8% before 1937 (a coverage floor; the OFR catalog begins in 1937). Stage 15 sample,
  design-weighted: 27.7% (34 of 120). Both are consistent in direction with "most are never formally revoked"; both
  are lower bounds.

**What the project can claim today:**
- Formal revocation sometimes comes after an order had already stopped operating: 34 orders on held, verified official
  text on both sides, gaps up to 24.8 years, and cleanup orders say so on their face.
- Many orders stop operating without ever being formally revoked: 1,135 in held data, 149 on held verified claims.
- Formal validity and operative force diverge in both directions; the TC01 separation is needed to see either.

**What it cannot claim today:**
- Any rate of formally revoked orders that were already spent. The filed claims point the other way: in 59% of the 810
  formally revoked orders with a claim, the revocation was the real end.
- Any population estimate from the convenience set of claims.
- That the 179 R3 cleanups were spent, beyond the producers' own disclosure.

## Reproduce

```
py -I research/encyclopedie-campaign/thesis-measure/scripts/test_measure.py
py -I research/encyclopedie-campaign/thesis-measure/scripts/measure.py <repo> --rev 857313b455ecc39798d75d0780778ada275259df
py -I research/encyclopedie-campaign/thesis-measure/scripts/tables.py
py -I research/encyclopedie-campaign/thesis-measure/scripts/examples.py <repo> --rev 857313b455 EO:7921 EO:12176
```

`measure.py` reads only committed files at the given commit through `git cat-file`, writes `MEASURE.csv` (6,389 rows,
every order with any record) and `SUMMARY.json`, refuses a `MEASURE.csv` over 5 MiB, and takes about 15 seconds.

## Known limits

- **The text scan only proposes.** 40 randomly chosen scan leads were read and all are genuine own-terms date clauses
  (mostly one-person retirement exemptions "until" a date); that says nothing about whether the clause was the order's
  only operative content, or about further-exemption orders that extended it. The scan misses relative dates ("two
  years from the date of this order").
- **Hash matching.** A claim citing only a PDF hash counts as `held_verified` when a job's `SOURCES.jsonl` links that
  hash to a committed text, as the claim checker does; the PDF itself may sit only in a runner cache.
- **Undated not-later-than ends.** The 1989 "temporary" label gives only "not later than 1989-01-20", so gaps built on it
  are lower bounds.
- **Early orders.** The census dates early orders by year only; for orders before 1937 without a catalog date the
  date-of-order check uses January 1.
