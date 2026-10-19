# X1 type rules: independent AI review, round 2

Reviewer: `x1_type_rule_reviewer_r2` (an independent agent). **This is not human certification.** It decides no order, changes no status, and leaves the human-certified whole-lifecycle count at **0**.
Reviewed 2026-10-19T16:52:05Z to 2026-10-19T16:58:38Z. Previous round: `TYPE_RULES_REVIEW_R1.json`. Rules: 22 (20 revised; 2 carried from round 1 unchanged). Withdrawn: TR-STOCK-DRIVEWAY.

**Result: 17 approved (lead only), 5 approved with required changes, 0 rejected.**

All 21 quote and text-hash checks passed (exact, single occurrence, at the recorded spans; SHA-256 of the text equals `text_sha256`).

| Rule | Decision | R1 changes addressed | Required changes now | File sha256 (12) |
|---|---|---|---|---|
| TR-ALIEN-PROPERTY-SALE | approve (lead only) | yes | - | `cdb05f4c8281` |
| TR-BIRD-REFUGE | approve (lead only) | yes | - | `2f3979ca7188` |
| TR-CANAL-ZONE | approve with required changes | yes | Replace 'with Prohibition's repeal in 1933' with: the statutory proviso was repealed by the Act of June 19, 1934 (ch. 657, s.3, 48 Stat. 1116). That date is ... | `e5de56881598` |
| TR-CLOSING-MOURNING | approve (lead only) | carried (unchanged) | - | `c825b13728c4` |
| TR-CS-WAIVER | approve (lead only) | yes | - | `c64f4416a934` |
| TR-EIGHT-HOUR-SUSPENSION | approve (lead only) | yes | - | `fec45cfa7461` |
| TR-FUND-ALLOTMENT | approve (lead only) | yes | - | `5da95f938c9a` |
| TR-INDIAN-RESERVATION | approve (lead only) | yes | - | `b54edfc971a4` |
| TR-LAND-WITHDRAWAL | approve (lead only) | yes | - | `a4ac9bd6aff4` |
| TR-LIGHTHOUSE | approve (lead only) | yes | - | `1639b681f7c6` |
| TR-MILITARY-RESERVATION | approve (lead only) | yes | - | `27766fb580a0` |
| TR-MINERAL-WITHDRAWAL | approve (lead only) | yes | - | `f3ea8d79908d` |
| TR-NATIONAL-FOREST | approve (lead only) | yes | - | `e17032017fe2` |
| TR-NRA-CODE | approve (lead only) | yes | - | `fc05b20b26a7` |
| TR-OWN-TERMS-EXPIRY | approve with required changes | yes | Replace 'or the date of the next extension if earlier' with: 'if a later order extended the date before expiry, the extended date (computed the same way); if... | `daeb17446dac` |
| TR-PHILIPPINES | approve (lead only) | yes | - | `93b87c55f3a1` |
| TR-POWER-SITE | approve with required changes | no | Rewrite the FPA s.24 sentences in ending_pattern and exceptions_savings as follows. Lands within a filed project application are reserved from the filing dat... | `25ae059a3149` |
| TR-PROPERTY-TRANSFER | approve with required changes | yes | Extend the quote through 'by the Librarian of Congress.', and add the transfer-date sentence as a second quoted part.; Add an outlier: a stated transfer date... | `255b666d094c` |
| TR-RETIREMENT-EXEMPTION | approve (lead only) | yes | - | `e0168a290024` |
| TR-TAX-RETURN-INSPECTION | approve (lead only) | yes | - | `9a56293122d4` |
| TR-WATER-RESERVE | approve (lead only) | carried (unchanged) | - | `85083f86d4f4` |
| TR-WWI-EMERGENCY | approve with required changes | no | Delete 'Orders under statutes not named in the resolution.' and add 'Orders whose authority is not war- or emergency-contingent by its terms (the 1921 resolu... | `885fa83f9afa` |

Full text of every required change, unaddressed item and recommendation is in `TYPE_RULES_REVIEW.json`.

## Main remaining problems

- **TR-CANAL-ZONE**: EO 5888's authority (NPA s.20 proviso, 47 Stat. 579) was repealed on **June 19, 1934** (48 Stat. 1116, s.3), not by 'Prohibition's repeal in 1933'.
- **TR-POWER-SITE**: the FPA s.24 'until otherwise directed by the Commission or by Congress' clause covers lands in filed project applications. Power-site reserves can be opened only on a Commission determination, with a reserved right of re-entry. Round 1's wording was itself too broad. The new exemplar is a *reservoir* site reserve, not the numbered Power Site Reserve that round 1 asked for.
- **TR-PROPERTY-TRANSFER**: the new EO 206 quote stops before the receiving agency (the Library of Congress) and leaves out the order's own transfer-date sentence.
- **TR-OWN-TERMS-EXPIRY**: effective_date_basis ('the date of the next extension if earlier') contradicts the revised ending_pattern.
- **TR-WWI-EMERGENCY**: the outlier 'Orders under statutes not named in the resolution' keeps the 'Acts it names' error; the round-1 outlier on authority that is not war-contingent is missing. Hungary's peace treaty was proclaimed Dec. 20, 1921, not in November.
- Across rules: `exceptions_savings.reviewed` is false everywhere. There are duplicate outliers (OWN-TERMS, PHILIPPINES, POWER-SITE, WWI). Some quotes open or close mid-sentence (MILITARY, MINERAL, FUND, OWN-TERMS; recommended fixes only).

## Sources consulted

- Held exemplar texts at each rule's `source.text_path`, and `jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv` (EO 2456 dated Sept 19, 1916).
- 27 U.S.C. 63 and the note on 63a-63d (govinfo, https://www.govinfo.gov/link/uscode/27/63): repealed by the Act of June 19, 1934, ch. 657, s.3, 48 Stat. 1116.
- 16 U.S.C. 818 (FPA s.24), https://www.law.cornell.edu/uscode/text/16/818.
- Proclamation 2416, July 25, 1940, 54 Stat. 2717 (https://www.govinfo.gov/link/statute/54/2717); FWS release of Aug. 1, 1940 (https://www.fws.gov/sites/default/files/documents/historic-news-releases/1940/19400801.PDF).
- 25 CFR ch. I appendix, on the Act of June 15, 1935, 49 Stat. 378 (https://www.law.cornell.edu/cfr/text/25/appendix-to_chapter_I).
- U.S.-Hungarian Peace Treaty, proclaimed Dec. 20, 1921 (https://en.wikipedia.org/wiki/U.S.%E2%80%93Hungarian_Peace_Treaty).
- Round 1's verified sources (41 Stat. 1359-1360 and others) were relied on where unchanged. Points marked 'verify' in the JSON were checked from memory only.
