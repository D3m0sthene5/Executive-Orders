# Producer report y13 (producer-y13)

Start 2026-11-10T05:24:02Z; end 2026-11-10T05:58:52Z.

Final applied directory: applied-v3. Submitted 7, blocked 18. batch-check v3: 7 claims, strict pass 7, actual checker all checks passed 7, 0 failures. Geddes: 0 flags (13 coverage gaps), so no resolutions needed (GEDDES_RESOLUTIONS.json empty).

## Submitted (YES, operative)
EO:10347 (item 4 ended 1970-03-19 by EO 11517; inventory corrected so clause c1 = authorizing sentence plus item 1, too short otherwise), EO:10641, EO:12101, EO:12260, EO:12436, EO:12548, EO:12641.

## Blocked (exact missing source in decisions.csv gaps and ASSESSMENT.jsonl)
- EO:11079, 11965, 12312: only an APP mirror record of EO 13286 is in the packet; the official copy (jobs/fr-originals/output/texts/EO_13286.txt) is held but not a packet record, so working_text official_copy_available_recheck_required rejects it.
- EO:10111: packet inventory is EO 10110's text; 50 U.S.C. 3507 not held; no current-law mention.
- EO:9998: 22 U.S.C. 132 and FAA 1948 sec. 109(a) not held; no current-law mention.
- EO:12250: unidentified 2026-07-23 rescission; inventory wrong.
- EO:12458, 13118: current text of amended parent orders not held.
- EO:12564: 55 overlapping scopes; dated duties.
- EO:12567: Panama Canal Commission status; IOIA/IAIC Act text not held.
- EO:12058: no citable end for sec. 5(a)/(b).
- EO:13823: sec. 2(d) performance not shown.
- EO:12978, 13466, 13620, 13850, 13846, 13857: NEA continuation notices not citable records.

## Time
Most time went to identifying inventory/identity defects (10111), reading amendment chains, and verifying authority statutes in jobs/theophilus-sources. apply ~1 min; batch-check ~8 min.

## Files opened beyond views
PACKET.json (via batch.load_packet, decoded), LOOKUPS.md/jobs/current-law outputs, decisions.csv, clauses.csv; cruden.py searches (noisy); held texts under jobs/fr-originals, jobs/app-executive-orders, jobs/theophilus-sources, jobs/later-events EDGES.csv.

## Tool defects
cruden.py search output unbounded; the packet cannot attach an official copy where only an APP mirror ACT record exists.
