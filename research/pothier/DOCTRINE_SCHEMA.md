# Pothier family doctrine: file format and engine contract

Each family doctrine is two files in `research/pothier/doctrines/`:

- `<ID>.md`, the doctrine in plain English for the owner: conclusions first, then (a) the mechanisms by which members
  end or persist, (b) the primary sources for each mechanism with exact citations, held or acquirable, (c) the decision
  procedure in words, branch by branch, and (d) the members the procedure cannot decide and why.
- `<ID>.json`, the same procedure in machine form (schema `pothier-family-doctrine/v1`), applied by
  `jobs/pothier/pothier.py` with no model.

A doctrine proposes **status leads**, never statuses. The question every lead answers is the project's status
question: was the order (as a whole) still in force on the cutoff, **2026-10-14**? `no` means it ended before the
cutoff; `yes` means it was in force on the cutoff; `open` means the doctrine cannot decide the member from the fields
held. The claim kit's rules bind the leads: a `no` needs an ending basis that is the order's own terms (`TERM`) or a
later instrument or statute (`ACT`); a `yes` needs a current-law predicate (`CURRENT`). A gap kept visible is never
filled by the doctrine (owner decision D-20261028-evidence-decides): a later general rule ends an order only if
something shows it extinguished that order; absence of a found revocation is not evidence of persistence or of an
end.

## The JSON

```json
{
  "schema": "pothier-family-doctrine/v1",
  "doctrine_id": "PD-EXAMPLE",
  "family": "plain name of the family",
  "version": 1,
  "members": {"field": "x1_type", "in": ["land_withdrawal_general"]},
  "mechanisms": [
    {"id": "M1", "kind": "own_terms | statute | later_instrument | review_program | class_event | life_of_person | continuity_only",
     "effect": "ends | persists | continuity_only | lead_only",
     "description": "one or two plain sentences", "effective_date_rule": "how the date is fixed",
     "source_ids": ["S1"]}
  ],
  "sources": [
    {"id": "S1", "citation": "Pub. L. 94-579, sec. 204, 90 Stat. 2743, 2751 (1976)", "title": "FLPMA",
     "url": "https://www.govinfo.gov/content/pkg/STATUTE-90/pdf/STATUTE-90-Pg2743.pdf",
     "held": true, "held_path": "jobs/astra-source-retention/output/pages/.../selected-pages.txt", "sha256": "...",
     "pin": "an exact short phrase that appears in the held text and establishes the point",
     "establishes": "what this source proves, in one sentence"}
  ],
  "procedure": [
    {"branch_id": "B1", "description": "plain words",
     "when": [ CONDITIONS, all must hold ],
     "lead": {"status_lead": "no | yes | open", "lead_kind": "short_snake_case",
              "basis_kind": "TERM | ACT | CURRENT | NONE", "basis": "plain sentence a reviewer can check",
              "date_rule": {"kind": "none"}, "mechanism_ids": ["M1"], "source_ids": ["S1"]},
     "gaps": ["evidence still missing for every member on this branch"]},
    {"branch_id": "B9", "description": "catch-all", "when": [], "lead": {"status_lead": "open", "...": "..."}}
  ],
  "undecidable": [{"reason": "...", "detected_by": "branch id or test"}]
}
```

Branches are tried in order; the first whose conditions all hold decides. The last branch must have no conditions
(the catch-all, normally `open`). Lead kinds starting with `persists` are checked against held later-event edges
(a held revocation edge flags a contradiction).

### Conditions (all read fields of `jobs/pothier/output/MEMBERS.jsonl`)

| Condition | Meaning |
|---|---|
| `{"field": "x1_type", "in": [...]}` / `"not_in"` | field value in a list |
| `{"field": "date", "gte": "1910-06-25"}` (`gt`, `lt`, `lte`) | ISO date compare; a bare year compares by year |
| `{"field": "text_features.pending", "is": true}` | exact value |
| `{"field": "named_persons", "nonempty": true}` | list or string non-empty (`empty` for the reverse) |
| `{"field": "text_features.stat_cites", "contains": "36 Stat. 847"}` | list membership or substring |
| `{"text_regex": "..."}` | case-insensitive regex on the member's primary held text (whitespace collapsed, first 12,000 characters) |
| `{"summary_regex": "..."}`, `{"title_regex": "..."}`, `{"any_regex": "..."}` | same on the WPA 1944 summary, the title, or all three |
| `{"mechanism_in": ["revocation"], "count_gte": 1, "acting_after": "1976-10-21"}` | held later-event edges on the member (`later_edges`) |
| `{"not": C}`, `{"any_of": [C...]}`, `{"all_of": [C...]}` | logic |

Member fields: `instrument_id`, `number`, `date`, `title`, `wpa_family_hint`, `wpa_summary`, `wpa_citations`,
`x1_type`, `x1_class`, `x1_rule`, `x1_confidence`, `primary_text_path`, `primary_text_grade`, `texts` (all held
texts), `text_features` and `summary_features` (`temporary`, `pending`, `until`, `for_period_years`, `trust_period`,
`revokes_other`, `amends_other`, `restores`, `waiver`, `retirement`, `emergency`, `fiscal_year`, `boundary`,
`transfer_forest`, `plss`, `stat_cites`, `act_dates`, `states`, `eo_mentions`), `named_persons`, `name_later_hits`,
`later_edges` (mechanism, acting_id, date_candidate, quote), `current_law` (U.S. Code and eCFR mention counts).

Caution: about 2,970 members' primary text is a compiled transcription or a ProQuest page scan that can run into the
neighbouring order; `eo_mentions` may include the order itself and its neighbours. Prefer patterns anchored in the
operative sentence.

### Date rules

`{"kind": "none"}`; `{"kind": "fixed", "date": "1976-10-21", "basis": "..."}`; `{"kind": "order_date"}` (spent
on issue); `{"kind": "order_date_plus_years", "regex": "period of (\\w+) years"}` (or `"years": 25`);
`{"kind": "edge_date"}` (earliest matched later edge); `{"kind": "interval", "from": "order_date", "to": "1976-10-21",
"basis": "..."}` (ended within the interval, date unknown).

## Commands

```
python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/<ID>.json --hints   # validate + branch counts
python3 -I jobs/pothier/held.py WORDS            # is a source already held? (--text also searches text heads)
python3 -I jobs/pothier/pothier.py apply         # all doctrines -> jobs/pothier/output/LEADS.jsonl, COVERAGE.json
```
