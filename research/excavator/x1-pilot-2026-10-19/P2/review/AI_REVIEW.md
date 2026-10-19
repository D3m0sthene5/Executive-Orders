# P2 independent AI review (claude-x1-reviewer-P2)

This is an AI review by an independent agent. It is **not human certification** and not an `eo-lifecycle-review/v1` record. The certified whole-lifecycle count stays at 0. The structured record is `AI_REVIEW.json`, which pins each claim by the SHA-256 of its exact line in `applied-v1/CLAIMS.proposed.jsonl`.

## Counts
- Members: 32. Submitted: 3 (2 upheld, 1 rejected). Blocked: 29 (all 29 justified, none unjustified).
- Clock times: start 2026-10-19T16:51:13Z, end 2026-10-19T16:55:35Z, 4.4 wall-clock minutes as `date -u` reported them.

## Submitted claims
| Order | Decision | Basis |
|---|---|---|
| EO 5614 | uphold | The inventory covers paragraphs 1-3. EO 8512 sec. 9 revokes the order by number. EO 8512 has no effective-date sentence and no savings clause, so the end date is its signing date, 1940-08-13. The related 1933-35 orders were revoked in the same sentence, which shows they coexisted with EO 5614. No title from 1931-1940 amends EO 5614. |
| EO 5707 | uphold | The inventory covers (a) and both parts of (b). EO 8189 revokes EO 5624 and EO 5707 by number. The "effective July 1, 1939" sentences on that page belong to EOs 8190 and 8191, so the end date is 1939-07-05. In 1938, EO 7968 still cited "EO 5624, as amended" as in force, and EO 8297/8298 removed that cross-reference after the revocation. |
| EO 5825 | **reject** | The earlier-end test was not finished. Held EO 7845 (annual leave regulations, effective 1938-01-01, issued under the Annual Leave Act of 1936) contains no Foreign Service exception. Its sec. 9 and sec. 13 cover leave without pay and leave at the turn of the calendar year, and sec. 20 revokes inconsistent leave regulations. Together these may have ended paragraph (d), in whole or in part, before EO 8189. EO 7013 (1935), which amended the Instructions and Consular Regulations and was revoked in the same EO 8189 list, is not held, and neither are other amendments from 1934-37. The OFR catalog starts in 1937. The producer named the 1936 leave acts as an open question but recorded `unresolved_material_gaps: []`. |

Caveat for all three: `original_pages_confirmed` is false. A human still has to check the page images.

## Blocked rows
All 29 blocks are justified, and the missing items listed are the right ones. They match the dossier's evidence grades (APP `derivative_lead`, page-check-required, and lead originals), the unlocated target provisions, and the conflicts. I checked these points directly:
- The EO 7968 "Executive Orders superseded" list names EOs 5737, 5812, 5837, 5848 and 5910. It is held, but the dossier has no evidence record for it, so none of those ends can be cited.
- EO 5624: held EO 5707 rewrote section 20 on 1931-09-04. That end has no evidence record, so blocking was required.
- EO 5621 and EO 5973: the earlier-end question raised by the Nationality Act of 1940 (effective 1941-01-13) is real.
- EO 7373: the chain events are `whole_via_parent` events on EO 6910, not events on EO 7373.
