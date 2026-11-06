# ending_or_current_basis, worker H6-w27 (start 2026-11-06T00:10:46Z, end 2026-11-06T00:14:30Z)

Edited: clauses.csv (state..reason), decisions.csv (earlier_end_check, scope_check, independent_command_check). No earlier worker value changed. Blocked states are written as `blocked:<source>` in the state column. later_events are JSON objects (event, effective_date, actor, mechanism, source_id, quote).

- **EO:4309**: done. Express revocation by held EO 4643 (1927-05-05), end terminated; own resurvey end has no held event.
- **EO:5615**: done. One-time transfer effective 1931-07-01 by the order's own terms, terminated; no later reversal held.
- **EO:2491**: blocked. Clause b terminated on signing 1916-11-21; clause a only partly revoked by held EO 3141 (a revoker the earlier worker had read as a recital) and has no current source.
- **EO:6798**: blocked. Open-ended withdrawal, 0 later orders, no current source held.
- **EO:2280**: blocked. Withdrawal with no own end; only 1916 recitals held; no current source.
- **EO:660**: blocked. Own cruden number run found only the Wikisource copy; classification has no held end or current predicate and the retention permission's use is not shown.
- **EO:3804**: blocked. Four delegation clauses with no held ending order or current statute; broad Alien Property Custodian search not resolvable.
- **EO:4155**: blocked. No clause row exists to fill; blocked for the missing inventory and for lack of evidence of reinstatement.

Sources opened: the held texts of each order (ProQuest EO_4309, EO_4643, EO_2491, EO_3141, EO_3804; APP mirror 5615; Wikisource EO_660), the HAND bundles, status proposals, and the owner rulings listed in the brief.

Correction to an earlier lead: status/EO_2491.json called EO 3141 a recital only; EO 3141 also revokes "the order of withdrawal of November 21, 1916" in part (T. 11 N., R. 37 E. secs. 12, 13, 23, 24). EO 3141's day of signing is illegible in the OCR (1919).
EO:4155 has no clause row (inventory blocked), so no clause fields were set; decisions.csv check columns say so.
Limits: searches were by order number (cruden), plus one failed broad literal search ("Alien Property Custodian": 1557 matches, too broad to review); searches by date-only references (e.g. "order of December 1, 1915") were not run for 2280, 6798, 660, 3804. 2491#b and 5615 rest on self-executing wording, an inference a reviewer may test.
Tool defects: none; the cruden JSON for the literal search keeps hits under an 'offsets' key, not 'hits'.
