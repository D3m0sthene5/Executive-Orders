# Linnaeus: the no-lead undecided orders, by type, matched to a bulk status source

Named for Carl Linnaeus, whose *Systema Naturae* (1735) sorted every living thing into a few ranks so each could be
looked up by its kind. Zero model tokens, offline: every input is a committed job output.

**What it does.** Takes the undecided orders that have no ending or current-law lead (Respondendi's S5 stratum: the
claim kit's `STATUS_LEADS.jsonl` record has no `lead_actor_ids`, no `own_terms` and no `current_law_leads`; 4,174 on
2026-11-10), gives each a type and a family, and says where it stands:

- `pothier_decided_lead`: a Pothier family doctrine already proposes a status the claim kit does not read;
- `held_ending_lead_unrouted`: a held finding aid already names the order with an ending word about it but
  `STATUS_LEADS` does not carry it: a Shepard or later-events edge whose mechanism is an ending (revocation,
  supersession, replacement, termination, abolition, rescission, restoration, vacation, nullification), a Selden FR
  citer in the ending class, or a 1989 OFR table row in its `ended_by_1989` group;
- `unsourced`: neither. These need a new source. Rows that name the order without an ending word (amendments,
  cross references, the 1989 table's in-force, merged or excluded rows) are listed in
  `held_mentions_without_ending` and do not move an order out of `unsourced`.

The M1118 column counts residual orders whose only route is the LC/NARA film (`microfilm_pending` in
`research/photius/RESIDUAL.csv`); rows whose ProQuest replica check failed are counted apart
(`residual_replica_gap`).

Each family is matched to the bulk source that could record its later events or current status (`SOURCES` in
`linnaeus.py`; the measurements behind each are in `research/linnaeus/REPORT.md`).

Type precedence: X1 `TYPES.csv`, then the X1 taxonomy on the APP title (orders from 1937 on), then Linnaeus title
patterns, then the Pothier doctrine, then the title's form (amends or revokes another order), else unknown.

| Output | Contents |
|---|---|
| `NO_LEAD_TYPES.csv` | One row per no-lead order: type, family, era, M1118-gap flag, Pothier lead, held ending leads, stratum, matched source |
| `TYPE_TABLE.md` | Families by stratum and era, with the matched source |
| `SUMMARY.json` | The same counts, the inputs and the source table |
| `CRUDEN_TARGETS.csv` | Unsourced numbered orders, one-person civil-service waivers excluded (Ulpian's track), for `jobs/cruden-fr-concordance` |

**Limits.** Types are leads from titles, WPA summaries and machine patterns; a family is a routing hint, not a legal
category. A source's silence about an order is never evidence about it. No status, census, codebook or count
changes. Human-certified: 0.

Tests: `python -I jobs/linnaeus-types/test_linnaeus.py`.
