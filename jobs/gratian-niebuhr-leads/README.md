# gratian-niebuhr-leads: Niebuhr's identifications as date leads for Lewis

Niebuhr (`research/niebuhr/`, owner-directed discovery wave of 2026-11-05) searched Clark's unknowns and reported a
signing date and subject for most of them, almost always from secondary sources. Until now no tool read those
results. This job converts them, offline and with no tokens, into two typed lead files:

| File | What it is | Who reads it |
| --- | --- | --- |
| `output/DATE_LEADS.csv` | One row per numbered order (census orders known only by number, numbered gaps, lettered citations) that Niebuhr identified with a full date at high or medium confidence, with no WPA disagreement. Grade `secondary_identification_lead`. | `jobs/_lib/eo_identity.py` `load_dates()`, last of all its sources (label `niebuhr_identification_lead`); through it Lewis's routing by date, Clark, Shepard, the Domesday register and Namier. |
| `output/RESOLVED_REFERENCES.csv` | Dated references ("the Executive order of <date>") that Niebuhr resolved to an order the census already numbers, with Niebuhr's note. | Nobody yet: a person checks each pairing before any edge is drawn (see `research/gratian/QUESTIONS.md`). |
| `output/SUMMARY.json` | Counts and the reasons rows were left out. | |

`load_dates()` reads the leads after every official and index source, so a lead only fills a missing date or refines a
bare census year that agrees with it; it never replaces another source's date. First local build: 63 date leads (33 for
orders in the census), of which 56 give an order a date it lacked or a full date for a bare year; 10 resolved references.

Nothing here admits a census entry, sets a date of record, grades a text or authenticates an identity. Niebuhr's
`ADMISSION_QUEUE.csv` stays with the owner (Kean A-20261105-niebuhr-admit). Certified: 0.
