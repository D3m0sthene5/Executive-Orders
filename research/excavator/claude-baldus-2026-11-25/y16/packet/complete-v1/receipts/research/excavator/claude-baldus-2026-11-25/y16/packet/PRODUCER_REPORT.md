# Producer report, packet y16 (agent baldus)

Start: 2026-11-25T16:50:24Z. End: 2026-11-25T17:09:30Z.

Final applied directory: `research/excavator/claude-baldus-2026-11-25/y16/packet/applied-v2`. Applied-v1 is kept unchanged; its 13755 claim passed the strict gate but the actual checker marked two quotations too short to verify (all_checks_passed false), so 13755 was rebuilt with an inventory correction in v2.

## Outcome per order

| Order | Outcome | Why |
|---|---|---|
| EO:13823 | submit, YES | No own-terms end; no later instrument revokes or amends it; scan of held executive orders 13824 to 14435 finds no citation (the digits 13823 occur only as section 13823 of the 2017 tax act). Section 2(d)'s 90-day date is a deadline, not an end; no held source shows performance, so it is recorded as continuing with that disclosure. |
| EO:13755 | submit, YES | Order of succession under the Federal Vacancies Reform Act; no end, no later citation. The machine conflict (a 2017-01-19 "revocation") is the Department of Labor notice superseding Secretary's Order 4-2008, not this order. Items (a) with (b) and (j) with (k) are merged by inventory override because (a) and (j) alone were too short for the checker's quotation test. |
| EO:13757 | submit, YES | Amending order for EO 13694. Emergency continuation notices 2017 to 2026 recorded as later events on section 1. Section 1 and paragraphs (i) to (iii) carry later events EO 14144 section 9 (2025-01-16, full restatement of 1(a)) and EO 14306 section 3 (2025-06-06, "any person" to "any foreign person"), recorded as amended, continuing under the strike-and-insert ruling, with a reviewer note that the substance changed. |
| EO:13808 | submit, YES | Venezuela emergency notices 2018 to 2026 and EO 14245's statement that the sanctions remain in effect are later events on section 1. EO 13857 amended section 3(d) (later event, before and after recorded). EO 14373 (2026-01-09, Foreign Government Deposit Funds) is explained in the claim as not reaching any clause; it is not a citable packet source, so it is not a later event. |
| EO:13827 | submit, YES | Same structure as 13808 (notices 2019 to 2026; EO 13857 amends 3(d)). |
| EO:13835 | submit, YES | Same structure as 13827. |
| EO:13848 | submit, YES | Emergency notices 2019 to 2026 (last signed 2026-08-31, after the 2026-09-12 anniversary) recorded as later events on the opening clause and section 2. Recurring election duties are not ended by any cycle; the 30-day framework in 1(f) is a deadline with no held evidence of performance. 54 clauses. |
| EO:13726 | blocked | The Libya continuation notices of 2022 to 2026 are held as texts and declared in HELD_SUPPLEMENT.json (HELD13726_2 to _6) but are not registered, citable evidence in the packet. Needed: a source supplement registering them. Best reading: in force on 2026-10-14, unrevoked. |
| EO:13846 | blocked | The Iran continuation notices of 2020 to 2026 (HELD13846_3 to _10) are held but not registered; only the 2019 notice is. Needed: a source supplement. The 113-clause inventory would also need clause decisions. Best reading: in force on 2026-10-14, unrevoked; EO 14382 (2026-02-06) does not revoke or amend it. |

No order was found not in force on 2026-10-14; the ledger is untouched.

## What took the time (one line each)

- 13823: reading the 18 clauses and confirming no later citation; first order, used to learn the sheet format.
- 13755: resolving the machine conflict and the short-quotation inventory correction.
- 13757: reading EO 14144 section 9 and EO 14306 section 3 against the order's restated section 1(a).
- 13808, 13827, 13835: one shared builder; reading EO 13857 and EO 14373 for any reach into these clauses.
- 13848: 54 clause texts, 8 continuation notices, Proclamation 8693 search for section 6.
- 13726, 13846: finding that the continuation notices are not packet evidence; no clause work done.

## Batch-check counts (applied-v2)

Packet members 9; submitted claims 7; blocked 2; strict claim pass 7, fail 0; actual claim checker: 7 of 7 all checks passed, 0 mechanical unverified, 0 mechanical fail, 7 gate passed. v1 for comparison: 6 of 7 (13755 unverified).

## Geddes

Lint of applied-v2 (`GEDDES_LINT.json`): 27 defect flags (EO:13757 two, EO:13808 eleven, EO:13827 six, EO:13835 eight), all code `later_instrument_named_without_event_source`, and coverage gaps (corpus incomplete for all seven; unclassified mention of EO 14306 on 13757 sections 2 and 3; EO 13757 on 13848 section 2(b)). All 27 flags are recorded as `disputed` in `applied-v2/GEDDES_RESOLUTIONS.json`: 25 name EO 13692 or EO 13694 only as the earlier parent emergency order (not a later actor), and one names EO 13984, which amended section 9 of EO 13694, a provision this order did not insert. The coverage gaps were read: EO 14306 amends EO 13694 paragraphs 1(a)(ii) and (iii), not 13757's Annex or delisting section; EO 13848 section 2(b) only recites EO 13694 as amended by EO 13757. Geddes did not crash.

## Full-packet files opened beyond the views

- `LOOKUPS.md` (read as instructed; the long citation lists were truncated by the tool).
- `HELD_SOURCES.json` and `HELD_SUPPLEMENT.json`: read by script (counts, aliases, custody states).
- `PACKET.json`: grep and `load_packet(..., check_sources=False)` only, to read dossier `conflicts`.
- `LOOKUPS.details.json`: keys only. `READ.md`: not opened.
- Repository sources: held later executive-order texts (jobs/fr-originals/output/texts), continuation notices (jobs/selden-fr-citers/output/texts), jobs/later-events/output/EDGES.csv and COUNTEREVIDENCE_LEADS.csv, jobs/current-law/output MENTIONS, EVENT_CANDIDATES and POSSIBLE_CONFLICTS (grepped for the nine orders), jobs/claim-kit/assemble.py and batch.py (to learn field semantics), and the prior unfiled papinian claim record for EO 13755 that the view carries.

## Facts for the coordinator

- Source custody: the U.S. Code release-point zip (xml_uscAll@119-121.zip) is held as a hash only (custody_record_only, state bytes_not_held for 7 members), so no claim uses a CURRENT U.S. Code record. Operative clauses rest on the order's own held clause text plus the bounded searches; continuation notices and later orders are cited as later events (federalregister.gov full-text captures are accepted only in the later-event role).
- Source supplement: HELD_SUPPLEMENT.json declares 63 held excerpts that are not registered as packet evidence. Applying a supplement for EO:13726 (HELD13726_2 to _6) and EO:13846 (HELD13846_3 to _10) would unblock those two orders for a later producer.
- `first_cause` in ASSESSMENT.jsonl has no enumerated value for an order still in force; "unresolved" is entered for all nine and each basis sentence says no ending event exists.
- Held executive-order texts run through EO 14435 (signed 2026-10-05); orders signed 2026-10-06 to 2026-10-14 are covered only by the OFR catalog search, and each claim says so.
- `apply` and `batch-check` each ran in under 30 seconds, not 10 to 30 minutes.

## Tool defects

- `batch.load_packet` requires a `Path`, not a string, for the folder argument (TypeError otherwise).
- The Geddes lint labels a parent emergency order as a "later actor" whenever a clause's reasoning names it; this produced the 27 disputed flags.
- The checker's minimum quotation length (6 words or 30 characters) makes one-line list items such as "(a) Solicitor of Labor;" unverifiable unless merged by an inventory override.
