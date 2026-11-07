# Producer report: u01 undecided packet (claude)

Start 2026-11-07T21:16:29Z; end 2026-11-07T21:25:03Z. Final applied directory: `applied-v1`.

## Outcomes (assigned members)

| Order | Outcome | Why / exact missing source |
|---|---|---|
| EO:10955 | submit (awaiting_status_review) | Status **no**. Superseded by EO 10973 sec. 605(c), effective as of 1961-09-30 (sec. 607). Dossier inventory held only sec. 2; corrected to sec. 1 and sec. 2 by inventory override. STATUS_DECISION.json filled and passes `_decision_errors`. |
| EO:12082 | submit (awaiting_status_review) | Status **no**. Periods end 1979-09-30 under own terms (inclusive; exclusive reading 1979-10-01). EO 12239 (1980-09-21) revoked it afterwards, as formal disposition. Inventory corrected to sec. 1-101, 1-102 and 1-103 (the dossier split items and duplicated 1-102, and omitted the 1-103 revocation). STATUS_DECISION.json passes `_decision_errors`. |
| EO:2738 | blocked | Original held only as a transcription (acceptable_as_original=False) and needing a page check; no page image held. No ACT/TERM/ACTOR_TEXT record in the dossier. Missing: an acceptable original or page image of EO 2738 (Official Bulletin No. 148 p. 5) and a dossier-registered acceptable text of EO 3377 (held only as a model transcription outside the dossier). |
| EO:3761 | blocked | Original is the ProQuest replica (archival_replica_checked, not acceptable). Missing: an acceptable original or official printing of EO 3761. EO 7234 sec. 7 revokes it on 1935-11-25 (APP mirror and printings held), but no ACT provision is located. |
| EO:5739 | blocked | Dossier holds no ACT/TERM/ACTOR_TEXT ending and no CURRENT record. Missing: an ending or performance record, namely the GLO or PLO record of the restoration (PLO:2097 has no census identity or held text). |
| EO:8109 | blocked | Page check cannot be done and the held official text is page 1 only (recitals, no operative paragraphs or signature). The dossier clause text is EO 8107's, not 8109's. EO 10664 and 10688 are partial restorations; no instrument for the remaining tracts. Missing: FR page images of 4 FR 1903-1904 and the operative text of EO 8109. |
| EO:13820, 2225, 4770, 9025 | dispatch-blocked (not researched) | Assessment rows written from the views only; decisions rows left as prepared (`unresolved`). |

## What took the time
- EO:10955: finding that the dossier clause covered only sec. 2; reading EO 10973 secs. 101, 605-607.
- EO:12082: reconciling the eight dossier rows (duplicate 1-102 items), the missing 1-103 clause, and EO 12239's overlapping periods.
- EO:2738, 3761, 5739, 8109: reading the working text and later instruments; `cruden.py number` run once each. EO:8109 needed the most time because the dossier's clause and ACT records belong to EO 8107.

## Batch-check
apply: blocked 4, unresolved 4, awaiting_status_review 2. batch-check: packet_members 10, claims_checked 0 (undecided members are not assembled), strict pass 0, fail 0, actionable_failures none.
Before handback, I assembled both submit sheets in scratch with a temporarily forced status `no` (harness under /tmp/claude-0/haloander-work/u01/). Both assembled with no errors and no check_claim errors.

## Geddes
`GEDDES_LINT.json`: 0 claims, 0 defect flags, 0 coverage gaps. `GEDDES_RESOLUTIONS.json` is empty. The lint covered no claim because undecided members assemble none.

## Full-packet files opened beyond views
EVIDENCE.json and STATUS_DECISION.json for the two submitted members, plus EVIDENCE.json for EO:3761, 5739 and 8109 (read through a summary script). No READ.md, PACKET.json or LOOKUPS.details.json. The harness loaded PACKET.json once via `batch.load_packet(check_sources=False)`. Repository sources read: held texts of EO 10955, 10973, 12082, 12239, 5739, 3761 (dossier text), 6608, 7234, 2738 (Wikisource), 3377 (pinakes-htr), 8109 (APP mirror) and 10664/10688 (fr-originals), plus the kit's `assemble.py`, `batch.py` and `status_overlay.py` for formats.

## Tool defects
- EO:8109's dossier mixes EO 8107 text into its clause and ACT records (the FR page carries three orders).
- EO:12082's inventory repeats 1-102 as `a-dup2` through `c-dup2`.
- `cruden.py number` output is about 10 MB per call. A regex with a trailing comma missed the EO 7234 citation of EO 3761 ("No. 3761, of ..."); I found it through the dossier's ACTOR_TEXT record instead.
- `apply` does not assemble undecided members, so sheet errors are not reported; I used a scratch harness.
