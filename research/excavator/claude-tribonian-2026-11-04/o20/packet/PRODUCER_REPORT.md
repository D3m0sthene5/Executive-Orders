# Producer report, packet o20 (Tribonian, producer Claude)

Start 2026-11-04T06:29:10Z; end 2026-11-04T06:44:00Z.

## Outcomes
Final applied directory: applied-v2 (applied-v1 failed assembly for six closing/revocation orders because own-terms ends cited a clause id; kept, not overwritten).

Submitted (9): EO 12179, 12201, 12225, 12255, 12513, 12554, 12577, 12619, 12717.
- 12179, 12255, 12577, 12619: one-day closing orders; each provision names one date and ends on it (inclusive, exclusive reading stated). 12179 inventory corrected (machine scope held only the heading).
- 12201: six provisions (inventory corrected; machine scopes were OPM notices on the same pages); ended by EO 12225 stated dates (1980-07-03, 07-28, 08-11, 10-31). Provision 1-105 (definitions) end of 1980-10-31 is a disclosed reasoned dependent lapse, not an express revocation.
- 12225: five self-executing amendments/revocations, each exhausted by performance on its stated date (latest 1980-08-11).
- 12513: six paragraphs, all ended 1990-03-13 by EO 12707 (express revocation, effective immediately). Annual continuation notices are not held and not relied on.
- 12554: extension to 1987-03-10 by own terms; EO 12587 and seven later annual extension orders recorded as later events, none supersedes it.
- 12717: self-executing revocation of EO 12691, exhausted 1990-06-18.

Blocked (21):
- Emergency boards 12531, 12557, 12562, 12563, 12636, 12644, 12646, 12650, 12655, 12664, 12714: sec. 4 ends the board on report submission; no report date held, no revocation held.
- 12313 (statute and ending not held), 12604 (own-terms date July 1, 1989 vs 12692 upper bound; EO 12528 not held), 12614 (report date), 12616 (withdrawal determination; Proclamation 5748), 12634 (H.J. Res. 523 not held).
- 12258, 12271, 12534, 12663, 12736: not decided; clause-by-clause first-end work (committee lists, staggered pay dates) not completed in this run, stated as such in the gaps.

## What took the time
One line per order: closing orders (12179, 12255, 12577, 12619) and 12717 were quick; 12201/12225 needed inventory offsets and reading 12225's staggered dates; 12513 needed offsets and the 12707 savings paragraph; 12554 needed reading eight extension orders; blocked emergency boards took one shared check of held report texts; 12258/12534/12663/12736 were read, sized and deferred.

## Batch-check
applied-v2: claims checked 9, strict pass 9, fail 0, actual checker all passed 9, actionable failures 0, blocked 21.

## Geddes
Flags 0 (coverage gaps 6, not flags). GEDDES_LINT.json and GEDDES_RESOLUTIONS.json (empty resolutions) are in applied-v2.

## Full-packet files opened beyond the views
PACKET.json (evidence ids, conflicts, clauses), decisions.csv, clauses.csv. LOOKUPS.md only by head.

## Tool defects
None blocking. Own-terms ends for orders with no TERM evidence must cite the ORIGINAL evidence id; derived and plain clause ids are rejected (unknown id or missing actor). apply refuses output outside the packet, so no scratch test directory was possible.
