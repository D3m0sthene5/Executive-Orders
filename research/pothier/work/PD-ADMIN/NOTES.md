# PD-ADMIN working notes (2026-11-05)

## What I read

- Brief and schema: `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`; owner ruling
  `research/readiness/owner_rulings/2026-11-05-empty-status-history.md`; engine `jobs/pothier/pothier.py` (date rules
  have no regex extraction of an "until" date, so per-member fixed dates are separate branches keyed on instrument id
  plus a text regex that requires the stated date phrase).
- Type rules: `research/readiness/type-rules/TR-FUND-ALLOTMENT.json`, `TR-PROPERTY-TRANSFER.json`,
  `TR-OWN-TERMS-EXPIRY.json`, `TR-TAX-RETURN-INSPECTION.json`, `TR-CLOSING-MOURNING.json`.
- Jacquard: `research/excavator/jacquard-2026-10-31/LOT_RULES.md` (L3 closings) and its `INDIVIDUAL_REVIEW.csv` (29 L3
  failures: undated Labor Day orders, funeral-day orders, misclassified Civil Service amendments, unreadable scans);
  the w2 `INDIVIDUAL_REVIEW.csv` has no closing rows.
- Member texts: all 801 summaries; held texts in full or in their operative part for all closings, own-terms, tax,
  the territory reserves, single-day pay orders, fiscal-year allowance orders, and about 120 revoke/amend candidates;
  the acting orders for every held ending edge (EO 5376, 5207, 6005-A, 6612, 6562, 5952, 5605, 6913, 6776, 8714, 6550,
  9461, 6724, 6777, 6858, 7005, 7044) and the in-family revoking orders (EO 1706, 3583, 4158, 3261, 4021).
- Held statute: Tax Reform Act of 1976, `jobs/source-ladder/output/texts/queue_EO_10906_..._64c0b4c21d.txt`, lines
  8640-9916 (sec. 1202; 6103(a) at 90 Stat. 1667, 6103(g) at 1672, sec. 1202(i) at 1688, located by the page headers).
- Web: Cornell LII 43 U.S.C. 1618 (ANCSA sec. 19(a), source credit 85 Stat. 710); uscode.house.gov 31 U.S.C. 1502
  (derivation 63 Stat. 407, 68 Stat. 831); usc-cdn.house.gov Pub. L. 85-56 (truncated before titles XXII-XXIII; table
  of contents shows sec. 2307 "Outstanding rules, regulations, and orders"); a search for Rev. Stat. 3690 text (no
  primary result); a search for the 73d Congress second-session date (secondary only). uscode.house.gov failed for
  43 U.S.C. 1618 and 31 U.S.C. 1301.
- Kean was not run (the shell search of held sources with `jobs/pothier/held.py` covered the statutes needed).

## Tried and rejected

- Statehood, Philippine independence and Puerto Rico Constitution as class events: no member found that these reach
  by their terms (no Philippine member here; Alaska reserves are land withdrawals; PR orders are acting-judge
  designations).
- Fund-allotment lapse rule: rejected because availability depends on each appropriation item; act titles such as
  "Fourth Deficiency Act, fiscal year 1933" name a fiscal year but the funds ran longer. Only EO 2968A, whose own
  text limits use to "said fiscal year", is decided.
- Property transfers spent on issue: rejected to stay consistent with TR-PROPERTY-TRANSFER (end = delivery record).
- Land-office discontinuances as single acts: left open; the receiving district's extent continues to rest on them.
- Veterans' Benefits Act of 1957 as a repeal of the Veterans Regulations: not usable until sec. 2307 is read.
- Committee-life ends for tax inspection grants: each committee's resolution would be needed; the 1976 rewrite gives
  a sound outer bound instead.
- Held-edge revocations taken as given: EO 2525 (EO 5207 revokes only "as to the tract described"), EO 6126 (partial,
  "in so far as ... in conflict"), EO 6098 (amendment), EO 6514 (partial rescission), EO 1, 4, 13 (edges point to
  unrelated orders) were not used.
- EO 6221: event-relative date and the further deferral by EO 6624; left open.
- Encampment leave: the year-end bound is an inference and labelled so in the lead.

## Things noticed for other workstreams

- EO 3878, 4075, 4571 (typed fund_allotment) are Indian trust-period extensions (PD-INDIAN).
- EO 3885 (typed closing_mourning) is a military land withdrawal on Oahu; EO 1183's held text is EO 1182½.
- EO 5471, 6352, 7209 (typed closing_mourning) amend Schedule A of the Civil Service Rules; decided here as amend-only.
- EO 267's WPA summary says "until Feb. 2, 1904" for an order of July 30, 1904; the text is illegible.

## Effort

About three hours of agent time: roughly one hour reading member texts, one hour on sources and the web, one hour
building and testing the doctrine (generator kept outside the repository at `/tmp/pd/gen.py`; the JSON in the
repository is its output).
