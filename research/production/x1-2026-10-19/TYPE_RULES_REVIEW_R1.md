# X1 type rules: independent agent review

Reviewer: x1_type_rule_reviewer (independent AI agent; **not human certification**). Reviewed 2026-10-19T16:47:37+00:00. Full record: `TYPE_RULES_REVIEW.json` (with each rule's file SHA-256).

**Counts:** approve_pattern_lead_only 2; approve_with_required_changes 19; reject 2. No rule decides an order. The human-certified whole-lifecycle count stays at 0.

Mechanical checks: all 21 rules with a source passed the exact-quote and UTF-8 text-hash checks. The 2 no_quote rules were rejected.

| Rule | Decision | Exemplar shows type | Main issue |
|---|---|---|---|
| TR-ALIEN-PROPERTY-SALE | approve_with_required_changes | yes | Settlement of War Claims Act proceeds wrongly called independent; reject/resale sub-patterns missing |
| TR-BIRD-REFUGE | approve_with_required_changes | yes | Quote starts mid-citation; outlier copied from land type; acquired-land and bureau-transfer continuity missing |
| TR-CANAL-ZONE | approve_with_required_changes | yes | Missing lapse of statutory authority (exemplar rests on Prohibition); Code-as-end overstated; 30-month treaty transition |
| TR-CLOSING-MOURNING | approve_pattern_lead_only | yes | Sound; event-relative mourning periods recommended |
| TR-CS-WAIVER | approve_with_required_changes | yes | Quote omits the person's name and includes the next order's date; 'lapses if never used' unsupported |
| TR-EIGHT-HOUR-SUSPENSION | reject | no | No exemplar, quote or source (no_quote) |
| TR-FUND-ALLOTMENT | approve_with_required_changes | yes | Exemplar is an amending order; availability end is only a not-later-than bound |
| TR-INDIAN-RESERVATION | approve_with_required_changes | yes | IRA s.2 overstated (s.13 Oklahoma, s.18 opt-outs, 1935 Act); two types merged; quote truncated |
| TR-LAND-WITHDRAWAL | approve_with_required_changes | no | Exemplar is a modification of a mineral (oil-shale) withdrawal, the rule's own outlier; FLPMA s.701 savings missing |
| TR-LIGHTHOUSE | approve_with_required_changes | yes | Exemplar is an amending order; cite Reorg. Plan II 1939 |
| TR-MILITARY-RESERVATION | approve_with_required_changes | yes | Quote is a secondary water-right clause with page furniture; retained reversions/rights missing |
| TR-MINERAL-WITHDRAWAL | approve_with_required_changes | yes | Exemplar is a modification order; reserved mineral estate on restoration missing |
| TR-NATIONAL-FOREST | approve_with_required_changes | yes | Quote runs into the next order's text; exemplar is a two-lifecycle outlier |
| TR-NRA-CODE | approve_with_required_changes | yes | Facts correct; add S.J.Res.113 citation, Panama Refining, PRA agreements |
| TR-OWN-TERMS-EXPIRY | approve_with_required_changes | yes | Exemplar's date is event-relative; deferral and deferred measure conflated |
| TR-PHILIPPINES | approve_with_required_changes | yes | Quote is mostly recited statute and truncated; date 16 vs 19 Sept 1916; 1947 bases claim overstated |
| TR-POWER-SITE | approve_with_required_changes | no | Exemplar is an administrative-site withdrawal, not a power-site reserve; FPA s.24 missing |
| TR-PROPERTY-TRANSFER | approve_with_required_changes | no | Exemplar is an office-abolition (organization) order, the rule's own outlier |
| TR-RETIREMENT-EXEMPTION | approve_with_required_changes | yes | 'usually until a stated date' contradicted by the open-ended exemplar; page furniture in quote |
| TR-STOCK-DRIVEWAY | reject | no | No exemplar, quote or source (no_quote) |
| TR-TAX-RETURN-INSPECTION | approve_with_required_changes | no | Exemplar is a standing state-officer class order, not a committee grant; 1976 s.6103 rewrite missing |
| TR-WATER-RESERVE | approve_pattern_lead_only | yes | Sound; reserved water rights as residual recommended |
| TR-WWI-EMERGENCY | approve_with_required_changes | yes | 1921 resolution misdescribed as 'Acts it names' (it is a general rule with exceptions); Knox-Porter missing; quote truncated |

## Sources consulted

- Joint Resolution of March 3, 1921, Pub. Res. 64, 41 Stat. 1359-1360 (govinfo: https://www.govinfo.gov/link/statute/41/1359). Text read: general rule, with exceptions including the Trading with the Enemy Act.
- Indian Reorganization Act ss.2, 13, 18 and the Act of June 15, 1935 s.3 (https://thorpe.law.ou.edu/IRA/IRAbook/acts.htm; 25 U.S.C. 5102, https://www.govinfo.gov/link/uscode/25/5102).
- NIRA s.2(c) and the 1935 extension (S.J. Res. 113, June 14, 1935): Monthly Catalog https://mocat.library.unt.edu/catalog/485-ch745; FDR statement https://www.presidency.ucsb.edu/documents/statement-conference-with-congressional-leaders-after-supreme-court-decision-nra; EO 7076 https://presidency.ucsb.edu/documents/executive-order-7076-extending-the-activities-the-nra.
- Trading with the Enemy Act excepted from the 1921 resolution: 50 U.S.C. ch. 53 notes (https://www.law.cornell.edu/uscode/text/50/chapter-53); Michigan Law Review (https://repository.law.umich.edu/cgi/viewcontent.cgi?article=9642&context=mlr).
- FLPMA s.704(a) prospective repeal; pre-1976 withdrawals continue: IBLA, Grant L. Hacking (1980) (https://www.arlis.org/docs/vol1/L/AlaskaWaterRights/Day3/H-3-Land-use-authorizations/Reference-material/11-IBLA-Grant-Hacking-decision.pdf); 43 U.S.C. 148 notes (https://www.law.cornell.edu/uscode/text/43/148).
- Panama Canal Treaty entry into force Oct. 1, 1979 and the 30-month transition: Panama Canal Act of 1979, 93 Stat. 452 (https://www.govinfo.gov/content/pkg/STATUTE-93/pdf/STATUTE-93-Pg452.pdf); DOJ opinion (https://www.justice.gov/file/148096/dl); https://countrystudies.us/panama/19.htm.
- From reviewer knowledge, not separately fetched (verify): Schechter, 295 U.S. 495 (May 27, 1935); Panama Refining v. Ryan, 293 U.S. 388 (1935); Reorganization Plan No. II of 1939; Proclamation 2695 (July 4, 1946) and the 1947 Military Bases Agreement; Acts of March 4, 1907, June 30, 1919 and March 3, 1927; FPA s.24; Tax Reform Act of 1976 s.6103; Knox-Porter Resolution, 42 Stat. 105.
