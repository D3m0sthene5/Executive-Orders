# Linnaeus: the no-lead undecided orders, by type, matched to a bulk status source

Named for Carl Linnaeus, whose *Systema Naturae* (1735) sorted every living thing into a few ranks so each could be
looked up by its kind. Zero model tokens, offline: every input is a committed job output.

**What it does.** Takes the undecided orders that have no ending or current-law lead (Respondendi's S5 stratum: the
claim kit's `STATUS_LEADS.jsonl` record has no `lead_actor_ids`, no `own_terms` and no `current_law_leads`; 4,174 on
2026-11-10), gives each a type and a family, and says where it stands:

- `pothier_decided_lead`: a Pothier family doctrine already proposes a status the claim kit does not read;
- `held_ending_lead_unrouted`: a held finding aid (Shepard, later-events, Selden FR citers, the 1989 OFR table)
  already names the order with an ending word but `STATUS_LEADS` does not carry it;
- `unsourced`: neither. These need a new source.

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
