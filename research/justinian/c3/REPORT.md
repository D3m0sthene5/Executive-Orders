# C3: claims filed under the 2026-10-21 reading, re-tagged as schema v2 (COUNT-CHANGING)

Justinian, 2026-11-06. Owner ruling R3 (Kean D-20261106-justinian-r3). This pull request depends on the schema v2
pull request (C1/C2) and waits for the owner to merge it.

## What R3 requires

The 2026-10-28 ruling, point 3: "a later general rule, rewrite or revocation ends a command only where something
shows it extinguished that command; its date is not a default end". It governs wherever it conflicts with three
2026-10-21 rulings:

- **Report deadlines:** emergency boards end "on express revocation (for most of these, EO 12553)", with the report
  date recorded as functionally spent.
- **Unnamed instruments:** "the end is the instrument that names it", and any earlier unnamed instrument is disclosed
  as a candidate.
- **EO 10449:** the board was never constituted but stayed on the books until revoked.

Claims filed under that reading are not researched again. Each is re-tagged: `first_cause: unresolved`,
`date_kind: not_later_than`, and the recorded end instrument moves to `formal_disposition`. The v1 line stays,
because claim files are append-only and the later file wins.

## Which claims (my legal judgment)

A claim is "filed under the 10-21 reading" when its own text applies one of those rulings:

- it calls a report-relative provision "functionally spent";
- it discloses an "earlier candidate" end under the unnamed-instruments ruling;
- it records a board "never constituted";
- or it cites one of the three ruling files.

All 184 matching claims were read for context. Every marker is a genuine application of a 10-21 ruling, not an
incidental phrase. Of the 184, 176 are ready today and 8 are not.

| Marker | Claims |
|---|---:|
| functionally spent | 140 |
| disclosed earlier candidate / earlier candidate end | 42 |
| cites 2026-10-21-report-deadline | 16 |
| cites 2026-10-21-unnamed-instruments | 2 |
| never constituted | 2 |

Recorded end instruments, now the formal disposition: EO 12553 145; EO 12379 7; S.J. Res. 113 (1935) 3; EO 9830 3;
EO 12319, 12692, 13062, 13225 3 each; and others.

**Not re-tagged (`NOT_RETAGGED.csv`, 192 ready claims).** The prompt listed every ready NO claim whose end actor is
a mass cleanup instrument (EO 12553, 14148, 11490, 12379, 12076, 11708, 9830). 192 of those ready claims apply no
10-21 reading. Their end is an express revocation that names the order, and the producer found no earlier
cessation. Examples:

- EO 13988 was revoked by EO 14148 sec. 2(d) while it was in force.
- EO 10997 was revoked by EO 11490 when emergency-preparedness assignments were consolidated.
- EO 11338's level V position fell out when EO 11708 revoked and replaced EO 11248.

A named revocation of an order in force is the evidenced first end; point 3 is about *general* rules. R3 does not
reach these claims, so re-tagging them would assert an uncertainty the evidence does not show.

Counts: EO 12553 81, EO 14148 42, EO 9830 18, EO 11490 17, EO 11708 12, EO 12076 12, EO 12379 10. They are listed so
the owner can widen the selection if he reads R3 more broadly (Kean A-20261106-justinian-r3-scope).

## How each claim is re-tagged (`retag.py`, deterministic)

- **Clauses ending at the whole-order end:** when a clause's recorded first end is the whole-order end's instrument
  and date, it becomes `not_later_than` that date with `first_cause: unresolved`. The original mechanism text is
  kept verbatim in `mechanism_note`, and an enum `mechanism` is read from it.
- **Clauses with their own earlier end:** a clause whose recorded end differs keeps it as `exact`, with a
  `first_cause` read from its mechanism. This happens twice: EO 6530 and EO 6743 each have an own-terms clause end
  in 1934 (`under_original_terms`). A clause whose mechanism maps to no cause would also be bounded, conservatively;
  none occurred.
- **Whole order:** `whole_order_end` becomes `not_later_than` the latest bound. `formal_disposition` is
  `{instrument, date, source}` taken from the v1 whole-order end.
- **Provenance:** each line carries `retag.v1_claim_sha256` and `researched_again: false`.

All 184 v2 lines pass the v2 gate. None of them hand-fills the derived field.

## Effect on the headline

With this file added, a tracker run on main's data (v2 tracker and gate) gives:

- **ready for human review: 1,384 → 1,208** (−176);
- claims by schema: v1 1,321, v2 184;
- whole-order end kinds: exact 1,214, not_later_than 184.

The 176 leave because a `not_later_than` end does not establish the first end (blocker `FIRST_END_UNRESOLVED`), and
because each new claim version needs a fresh claim-checker pass. Each of the 176 still shows the order without
operative force at the 2026-10-14 cutoff, since it was formally revoked no later than the bound. They stay in the
operative-force estimate (ESTIMAND.md) as "no, first end unresolved". They are not ready whole-lifecycle dossiers.

What re-research would recover: a held, dated report, or an earlier dated statute, turns a claim back into
`exact` or `interval` with cause `completion_of_task` or `legislative`. Bentham can value that as one action per
family.

## Files

- `research/readiness/claims/justinian-2026-11-06-r3-retag.jsonl`: 184 v2 claims (14.8 MB, mostly the v1 claims'
  embedded claim-kit evidence, which is copied unchanged).
- `research/justinian/c3/RETAGGED.csv`: per claim, the markers, bounded and exact clause counts, both claim sha256s and
  the gate result.
- `research/justinian/c3/NOT_RETAGGED.csv`: the 192 cleanup-actor claims left as v1, with the reason.
- Reproduce: `python3 -I research/justinian/c3/retag.py . jobs/readiness-tracker/output/READINESS_BY_ORDER.csv OUT`.

Certified: 0. No codebook, census or provisional-status change. Ready count change: −176 once merged and checked.
