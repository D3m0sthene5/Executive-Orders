# Pothier: family doctrines applied to the orders with no dated status history

Named for Robert-Joseph Pothier (1699-1772), who reduced French law to treatises by subject so that one treatise
settled what had been argued case by case. Report and doctrines: `research/pothier/REPORT.md`,
`research/pothier/doctrines/`.

**Members.** The undecided orders (no provisional status in the readiness tracker) for which `jobs/status-history`
located no dated history: 5,918 on main of 2026-11-05, almost all from 1862-1936. The owner ruled on 2026-11-05 that
the claim kit may start them with an explicit, noted empty history (D-20261105-empty-history); their status must then
rest on the order's own terms and on law that applies to its whole class. A doctrine states that law once for a family.

**What it writes (zero tokens, standard library plus pypdf for the fetch step).**

| File | One line per | What it is |
|---|---|---|
| `output/MEMBERS.jsonl` | member | the fields a doctrine may read: dates, WPA 1944 summary, X1 type, held texts, literal text features, named persons, held later-event edges, current-law mentions (`members.py`) |
| `output/LEADS.jsonl` | member and doctrine | a **status lead** (`no`, `yes`, `open`), the deciding branch, basis kind (`TERM`, `ACT`, `CURRENT`), date or interval, sources (held or not), evidence gaps, contradictions with held evidence |
| `output/COVERAGE.json` | run | per doctrine and per WPA family hint: members, decided, not decided, contradicted |
| `output/DOCTRINE_PINS.json` | doctrine | path and sha256 of the doctrine applied |
| `output/SOURCES.jsonl`, `output/sources/` | fetched source | custody copies of the doctrine sources the project did not hold (`fetch.py`, GitHub Actions only) |

**What a lead is not.** A lead is never a provisional status, a claim or a finding. It changes no status, codebook,
census row or certified count (0). Leads are proposals for owner adoption, one decision per family (Kean asks). Every
order still goes through the claim kit on its own terms; a lead tells the producer which mechanism and sources to
check first and which evidence is missing.

```
python3 -I jobs/pothier/pothier.py members                      # rebuild MEMBERS.jsonl (about 8 s)
python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-LAND-WITHDRAWAL.json --hints
python3 -I jobs/pothier/pothier.py apply                        # all doctrines
python3 -I jobs/pothier/pothier.py sample --doctrine PD-INDIAN --n 30 --seed pilot1
python3 -I jobs/pothier/held.py 90 Stat 2743                     # is a source held?
python3 -I jobs/pothier/test_pothier.py
```

Doctrine format and condition language: `research/pothier/DOCTRINE_SCHEMA.md`.
