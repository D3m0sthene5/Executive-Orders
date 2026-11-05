# Daily research digest

New York date: 2026-11-04. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 1,331 of 14,972 orders (8.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 4,291. The other 10,681 have not been researched yet.

Ready by text evidence: {'original_supported': 804, 'transcription_dependent': 527}. Provisional working texts do not authenticate originals.
Outstanding original replacement obligations: 1,886; quotation rechecks: 1,886. These remain work after readiness.

Text step provisional on a confirmed working text (separate from `done`, never an original; owner ruling 2026-10-31): 1,357. Confirmations rejected: {'grade_not_a_working_text_grade': 4, 'not_confirmed': 5856}.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |

## Changes since the previous day

Comparison snapshot: 2026-10-28; intervening runs may be absent.
- astra-source-retention: attempted: 18 → 7; download_bytes: 17475798 → 0; extractions_completed: 18 → 7; http_requests: 7 → 0
- cassiodorus: legal_conclusions: unavailable → 0; pages_kept_total: unavailable → 10; statuses_changed: unavailable → 0
- census-candidates: items_with_LOC_XML_transcript: 10 → 0; research_note_records: unavailable → 0; source_bound_AI_research_proposals: unavailable → 0
- claim-checker: claim_lines_found: 510 → 1466; claims_all_checks_passed: 410 → 1369; claims_checked: 510 → 1466; claims_gate_passed: 420 → 1376
- claim-drafts: decided_orders_with_draft: 3403 → 4291; orders_with_draft: 3403 → 4291
- cotton-capture-custody: archive_successors: unavailable → 0; failed: 2 → 1; not_web_sources: 575 → 1095; published: 526 → 756
- fr-pages: bytes_committed_this_run: 15402202 → 0; bytes_downloaded: 612727745 → 0; carried_forward: 0 → 30; requests: 23 → 0
- jacquard: full_review_max: unavailable → 80; sample_size: unavailable → 59
- kean: decisions: 11 → 21; findings: 44 → 136; open_owner_questions: 10 → 2
- lachmann: assessed: unavailable → 7534; complete_text_confirmed: unavailable → 3278; confirmed: unavailable → 1674; identity_confirmed: unavailable → 3517
- lambertini: counterevidence_records: 672 → 1248; decided_orders_with_draft: 3403 → 4291; packet_targets: 835 → 840; packets: 109 → 114
- namier: legal_conclusions: unavailable → 0; network_requests: unavailable → 0; orders_with_held_text: unavailable → 14913; statuses_changed: unavailable → 0
- pinakes-htr: either_passes_screen: unavailable → 89; errors: unavailable → 0; orders: unavailable → 310; pages: unavailable → 555
- readiness-tracker: orders_with_provisional_status: 3403 → 4291; original_replacement_obligations: 103 → 1886; quotation_recheck_obligations: 103 → 1886; ready_for_human_review: 395 → 1331
- shepard-citations: land_targets: 3516 → 3547; land_targets_with_any_edge: 1048 → 1054; land_targets_with_ending_candidate: 616 → 617
- valla: active_claims: 421 → 1445; shared_rationale_references: 525 → 783; textual_leads: 11 → 24
- x1-class-engine: modern_families_5_plus: 195 → 193

## Top shared unlocks

- orders_unblocked: 3667; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 2558; kind: agent_check; action: Compare the ProQuest replica scan's pages with the order (pinakes-proquest-ingest ORDERS.csv, texts/) and use the scan as provisional working text under the 2026-10-21 owner rulings (proquest-request, transcription-as-text), disclosed and rechecked against an original when one is held; blocker: ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 285; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)

## Open asks from the newest handoff entries

- notes-astra.md: - **Asks:** @Owner: none.
- notes-boundary-review.md: No open ask recorded in newest entry.
- notes-ce-review-pair1.md: No open ask recorded in newest entry.
- notes-ce-review-pair2.md: No open ask recorded in newest entry.
- notes-ce-review-pair3.md: - **Asks:** none.
- notes-claude.md: No open ask recorded in newest entry.
- notes-codex.md: - **Asks:** @Owner: none.
- notes-corpus-evidence-retrieval.md: - **Asks:** @Owner: none.
- notes-inventory-a.md: No open ask recorded in newest entry.
- notes-inventory-b.md: No open ask recorded in newest entry.
- notes-lifecycle-assurance.md: - **Asks:** @Owner: none.
- notes-nmb-series-independent-review.md: No open ask recorded in newest entry.
- notes-production-batch1.md: No open ask recorded in newest entry.
- notes-production-review1.md: No open ask recorded in newest entry.
- notes-r1-materializer-followthrough.md: - **Asks:** @Owner: none. @Root: leave PR112 unmerged and preserve exact scientific holds and evidence qualifications.
- notes-r2-preflight-repair.md: - **Asks:** @Owner: none. @Root: integrate the dependency receipt and exact-version review proposals through existing routes; register R2 findings.
- notes-r3-ranger-roundtrip.md: - **Asks:** @Owner: none.
- notes-r4-production-diagnosis.md: No open ask recorded in newest entry.
- notes-shared-research-production.md: - **Asks:** @Owner: none.
- notes-sol-readiness-economy.md: - **Asks:** @Owner: none. @Integrator: leave draft unmerged until combined A+B review and checks.
- notes-sol-runtime-economy.md: - **Asks:** @Owner: none.
- notes-sol.md: - **Asks:** None while validation is running.
- notes-source-first-control-preparer.md: No open ask recorded in newest entry.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/41955554786)
