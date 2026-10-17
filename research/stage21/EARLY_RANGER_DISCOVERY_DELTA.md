# Early-history ranger: live discovery delta, October 17, 2026

The user requested substantive 18th- and 19th-century discovery, with minimal redundant certification work. **Preserved exploratory research is not a new executive-order census result.**

## Observed, reproducible gains

- [Live scout job](../../jobs/early-ranger-scout/output/SCOUT_SUMMARY.json): **56 query routes planned, 28 actual successful JSON responses**, including 23 Library of Congress and 5 Internet Archive responses, **4 request failures and 24 provider-unavailable skips**. Exact response bytes compressed and preserved under `jobs/early-ranger-scout/output/response_cache/`, indexed by SHA-256. Its first parser saved only 35 Internet Archive links because LOC item identifiers often used legacy `http://` links.
- [Reparse of cached LOC data](../../jobs/early-ranger-reparse/output/REPARSE_SUMMARY.json): without **any additional network requests**, recovered **65 distinct official LOC item/resource URLs** from 23 original JSON responses. Raw IDs are retained, and only verified loc.gov item/resource identifiers are rewritten to HTTPS for navigation. Of these, **46 catalog records have 1789–1861 date hints**.
- [Capacity-aware triage](../../jobs/early-ranger-triage/output/TRIAGE_SUMMARY.json): **33 manuscript metadata hits** lie in **17 years** previously marked as having no inherited specific Lord lead. These years remain unsearched exhaustively, and many records are nonpresidential. A first-pass title/date screening identifies **six presidential-term documents with directive language**, plus 14 additional in-term paper/correspondence leads. The screen also demotes 30 letters attributed to people outside their presidential service. The resulting [worklist](../../jobs/early-ranger-triage/output/CAPACITY_TRIAGE_REPORT.md) makes archival review substantially more targeted.

## Specific original-manuscript entry points

The most promising titles to inspect are:

| Indexed instrument or source | Date | Official manuscript/item page | Identity caveat |
|---|---|---|---|
| Thomas Jefferson, *Instruction for Armed Vessels* | Feb. 18, 1802 | https://www.loc.gov/item/mtjbib011110/ | Original operative author, instrument form and coverage need inspection |
| Thomas Jefferson to Meriwether Lewis, *Instructions* | June 20, 1803 | https://www.loc.gov/item/mtjbib012509/ | Presidential instruction likely; EO inclusion under project codebook not adjudicated |
| Thomas Jefferson to James Wilkinson, *Instruction* | Nov. 8, 1806 | https://www.loc.gov/item/mtjbib016595/ | Exact order, signature and delegation need inspection |
| James Madison, *List, Military Instructions* | Aug. 10, 1814 | https://www.loc.gov/item/mjm017450/ | Identify document's legal and operational form |
| James Madison to John Armstrong | Aug. 13, 1814 | https://www.loc.gov/item/mjm017456/ and https://www.loc.gov/item/mjm022917/ | Two LOC catalogue manuscript representations on same date and recipient; check whether same instruction; contemporary War Department operational rules are a strong research hypothesis, **not two orders** |
| James Madison to Benjamin W. Crowninshield, *Instructions* | Oct. 19, 1816 | https://www.loc.gov/item/mjm018302/ | Identify original text/recipient role and legally operative provisions |
| James K. Polk papers, *Instructions for John Slidell* | Jan. 12, 1848 | https://www.loc.gov/item/mss365090092/ | Item filed in speeches/messages series; title is not conclusive that Polk issued an EO |

Separate lower-priority correspondence and contemporaneous reprinted government papers include Andrew Jackson to Lewis Cass (1832), https://www.loc.gov/item/maj012871/; Andrew Jackson to John Branch (1831), https://www.loc.gov/item/maj012239/; Congressional printing of 1846 Polk / War and Navy Department communications, https://www.loc.gov/item/2022697987/; and Madison-era War Department correspondence and defense orders in the Congressional Serial Set, https://www.govinfo.gov/content/pkg/SERIALSET-00008_00_00-011-0081-0000/pdf/SERIALSET-00008_00_00-011-0081-0000.pdf.

All are currently **candidates or source corpora**. They must not be conflated with the six Stage 18 curated items or counted anew without an identity/provenance comparison and codebook inclusion decision.

## Next highest-yield actions

1. Examine and crosswalk the seven strong title leads above against the 1,023 Lord OCR records, previously identified 1789–1790 seeds, and current working bibliography before requesting more scans. Record original issuer, addressee, clause, signing capacity and same-date documents.
2. Use the LOC JSON responses we have already stored to search neighboring pages and recipient correspondence. Avoid another run of broad queries until its precision can be measured; some Archive results were irrelevant books, and historical LOC items can be from the named person's pre-presidential life.
3. Apply the same approach to **1862–1899**, where the working bibliography includes numbered/unnumbered proxy identities, rather than assuming the 1789–1861 census grid measures the entire 19th century.
4. Preserve source-custody and research-readiness counts separately from authenticated inclusion and full-lifecycle coverage.

**No newly authenticated orders or certified legal histories are claimed by these machines.** This delta records real archived source candidates and a more effective route to finding historically missing orders.
