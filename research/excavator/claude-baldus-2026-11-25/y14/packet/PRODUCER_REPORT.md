# Producer report, y14 (baldus)

Start 2026-11-25T16:47:17Z. End 2026-11-25T17:04Z. Final applied directory: applied-v4.

## Outcomes
All nine orders submitted as YES: EO 13536 (Somalia), 13551, 13570 (North Korea), 13553, 13599, 13606 (Iran), 13566 (Libya), 13581 (transnational criminal organizations), 13611 (Yemen). Each rests on its own held Federal Register original (no own-terms end) and the held 2026 National Emergencies Act continuation notice (Somalia Apr 8, North Korea Jun 22, Iran Mar 2, Libya Feb 13, TCO Jul 13, Yemen May 7), plus the three bounded searches. No order was found not in force on 2026-10-14.
- Later events recorded: EO 13620 (EO 13536 sec 1(a), five clauses, before/after text); EO 13863 (EO 13581 sec 3(e)); EO 13726 (EO 13566 lead, scope expansion); EO 14312 sec 4(b) (EO 13606 preamble, held official text, merged sec 1 clause).
- Conflicts resolved in decisions.csv: PARTIAL_END_CANDIDATE_ON_YES_ORDER on EO 13553, 13599 (continuation notices reciting revocations of other orders), 13566 (OFAC general licenses superseded), 13606 (word Suspending in the title).
- Residual risks disclosed in rationales: CISADA 104/105 and NDAA 1245(d) delegations (EO 13553 secs 5-8, EO 13599 secs 10-11) rest on statute text not held; EO 13611 OFR See note "Proc. 11026, May 5, 2026" text not held (the May 7, 2026 notice post-dates it).

## What took the time (one line each)
EO 13536: amendment by EO 13620 before/after text. 13551/13570: shared NK notice, short lead clauses. 13553/13599: Iran machine conflicts and statutory delegations. 13566: OFAC supersession candidates. 13581: EO 13863 effective date (no clause, signing date used). 13606: EO 14312 partial amendment; switched to its held FR original. 13611: Proc. 11026 note.

## Batch-check and Geddes
applied-v1 rejected 9 (savings source was an FR capture; conflicts unresolved). v2 assembled 9, batch-check exit 1 (4 claims unverified: lead clauses of 13551/13581/13606 and sec1-a of 13553 too short to verify). v3 merged those into adjoining clauses by inventory override: 9/9 pass, 0 failures. v4 (final): strict_claim_pass 9, fail 0, actual checker 9 all-checks-passed, 0 unverified. Geddes on v3 flagged fr_citation_mismatch (OFAC notice pages in rationales, EO 13551 and 13581): fixed in v4, lint shows 0 defect flags, 9 advisory coverage gaps (citing_corpus_incomplete) recorded as disputed in GEDDES_RESOLUTIONS.json.

## Files beyond the views
LOOKUPS.md (full, read once); PACKET.json via batch.load_packet (conflicts, machine searches); no READ.md or LOOKUPS.details.json. Also read held texts outside the packet: jobs/fr-originals EO_13620/13863/13726/14312/14382/13611/13606, jobs/selden-fr-citers notices, jobs/later-events EDGES.csv, status-history FRAGMENTS, selden-fr-citers FRAGMENTS.

## Tool defects
Early prints of PACKET views and own_original_text (a string iterated as a list) wasted context; batch-check exit 1 on unverified short quotes is reported as actionable though gate passes.
