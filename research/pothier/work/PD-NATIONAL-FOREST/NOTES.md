# PD-NATIONAL-FOREST working notes (2026-11-05)

## What I read

- `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`, `jobs/pothier/pothier.py`
  (condition and date-rule semantics), `research/readiness/owner_rulings/2026-11-05-empty-status-history.md`.
- `research/readiness/type-rules/TR-NATIONAL-FOREST.json` (mechanism `boundary_change_merged`, outlier list; exemplar
  EO 1260, which this doctrine decides on B06).
- `research/excavator/jacquard-2026-10-31/LOT_RULES.md` (question framing: does the order's own command still operate;
  accrued effects do not count). The Jacquard lot files have no forest lot.
- `jobs/x1-class-engine/data/EVENTS.json`: the only relevant event is X1-E5-FLPMA-1976, already classed there as
  `not_an_end_authority_repeal`, which agrees with this doctrine.
- Member records: `research/pothier/work/PD-NATIONAL-FOREST/MEMBERS.csv` and the 708 `national_forest_boundary` records
  in `jobs/pothier/output/MEMBERS.jsonl`. I read all 708 titles and the operative text of about 120 members: every B02
  revoking order, all B03 and B05 members, the questionable B04 and B06 members, and samples from each open branch.
- Held FLPMA text: `jobs/astra-source-retention/output/pages/3949c2ad…/08af9986…/selected-pages.txt` (secs. 701-704,
  90 Stat. 2786-2792).
- Web, read only and not held: the 30 Stat. 11 PDF (pages 34-36) and 36 Stat. 847 PDF on govinfo; the 90 Stat. 2949
  PDF (sec. 9 at p. 2957); the 34 Stat. 1256 PDF (proviso at p. 1271); 16 U.S.C. 1609 at law.cornell.edu (the
  uscode.house.gov fetch failed); the Forest Service 1997 chronological record at foresthistory.org (through a
  summarizing fetch, so only sample entries were seen); search results for the FY2024 Land Areas Report.

## What I tried and rejected

- **Held later-event edges as an ending branch.** Only five members have edges. Three of the revocation edges are
  partial (EO 2242 by EOs 7053 and 7448; EO 4889 by EO 5048), and the engine cannot test an edge's qualifier. The two
  full ones (EO 3102 by EO 7078; EO 3626 by EO 5422) are covered by the explicit B02 pairs instead.
- **FLPMA sec. 702 (repeal of the homestead laws, 1976; Alaska 1986) as an outer bound for opening schedules.** I
  rejected it because it repeals the laws under which land was opened, not the orders, so it does not meet the owner
  rule.
- **NFMA sec. 9 / 16 U.S.C. 1609(a) as a CURRENT predicate for additions.** I rejected it because it protects land
  that was still in a forest in 1976 but cannot show that a given member's land or designation survived to 1976 or to
  2026.
- **Treating all boundary modifications, including additions and transfers, as amendments spent on issue.** This is
  defensible under the owner's rule and the type rule's "merged" framing. The persistence reading is also defensible,
  so I left those members open and framed the choice as an owner question.
- **Consolidation-based endings** (for example EO 3317 merging the Sopris into the Holy Cross, which would end EO 1069
  under the persistence reading). I did not encode them, because they depend on the unresolved owner question and
  need forest-name matching that the held fields do not support reliably.
- **Coordinator lead "NFMA sec. 11".** The provision is in the 1974 Act's sec. 11(a) as redesignated, but NFMA amended
  it by its sec. 9 (90 Stat. 2957). The JSON cites sec. 9.
- **Coordinator lead "Chronologic Record 1891-2012".** I could not locate it. I used the 1997 edition (1891-1996);
  a 1985 edition is at Biodiversity Heritage Library item 252736.
- **Identity scan** for "[No. NNNN]" tags that disagree with the member number. Most hits were OCR noise. The real
  mismatches are EO 4613 (the scan is EO 4614) and EO 3537 (a postal reinstatement), both routed to B01. EO 4675's
  scan carries the tag "[No. 4676]" but its text matches EO 4675's title and date, so I kept it on B04.

## Method

Branch regular expressions were tuned against the held texts with a scratch script outside the repository
(`/tmp/pnf/scripts/build.py` generates the JSON; it is not a deliverable). The B02 pairs were found by machine from
number, date and site-name references in revoking members, then verified one by one against the revoking text. Rejected
candidates: the matches from ten texts (EOs 637, 802, 898, 970, 1069, 1257, 1354, 1934, 2223 and the EO 1555 match
inside EO 4712's neighbour text) were only mentions in neighbouring orders or navigation text; EO 4421 revokes EO 1555
and EO 3098 revokes EO 2964 only in part; and EO 1883 partly revokes EO 1324½ (Alaska medicinal springs), not EO
1324.

## Effort

About three hours of wall time in one session, with a large token spend: many full-text reads and about 25 iterations
of `pothier.py try`. Model: Claude Opus 5.5.
