# Bracton cost ledger

API-equivalent USD at each recorded model's list price. A subscription charge is not inferred from this ledger. The owner set no dollar cap.

| Batch | Model | Input tokens | Cache write | Cache read | Output tokens | USD | Basis |
|---|---|---:|---:|---:|---:|---:|---|
| Source staging, 2026-11-08 | None (machine jobs) | 0 | 0 | 0 | 0 | 0.00 | Nine rank-1–6 identities in the active source-ladder run; results pending. |
| Direct-source discovery, 2026-11-08 | None (workers) | 0 | 0 | 0 | 0 | 0.00 | Twelve further direct source leads queued: four rank-6 official issues and eight rank-8 board, report, or corroborating sources. The shared CFR URL hint is staged for a later run. This is worker cost only; Codex coordinator usage is unmetered below. |
| Board b02 packet preflight, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Twenty-five orders frozen; 24 official FR issue PDFs and 20 NMB reports matched existing hashes. No producer or reviewer tokens used. |
| Board b03 packet preflight, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Twenty-five more orders frozen; 24 official FR issue PDFs and 23 NMB reports matched existing hashes. No producer or reviewer tokens used. |
| Board b04 packet preflight, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Twenty-five more orders frozen; 24 official FR issue PDFs and 17 NMB reports matched existing hashes. No producer or reviewer tokens used. |
| Board b05–b06 packet preflight, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Thirty-one remaining board cases frozen; 31 official FR issue PDFs, 10 NMB reports, and 32 archived APP captures matched existing hashes. No producer or reviewer tokens used. |
| YES y03 acquisition triage, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Twenty-five disjoint rank-9 orders prepared research-only; all source blocked, with 156 distinct source tasks. No producer or reviewer tokens used. |
| YES y04 packet preflight, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Six y03 orders acquired and reserved; nine official FR issue PDFs and two archived APP captures matched hashes; fresh dispatch passed 6/6. No producer or reviewer tokens used. |
| YES y03 source acquisition, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | All 69 official FR PDFs and 45 archived APP captures matched frozen hashes; 42 other live source routes failed exact match or returned 404. No producer or reviewer tokens used. |
| YES y03 upstream retention, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Eight GovInfo bulk XML and four OLRC release-point ZIP artifacts matched recorded raw hashes and were retained. Extraction verification and legal review remain open. |
| Photius continuation roster, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Reconciled 92 disjoint post-rank-9 orders against Cujas's 68 filed claims, current main readiness, seven low-coverage exclusions, and two rank-7 overlaps. No comparison worker or reviewer tokens used. |
| YES y03 extraction content audit, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Compared 22 held CFR/US Code text extracts with 12 raw upstream artifacts by hashes and normalized content; byte-exact extraction and legal review remain open. |
| Nonboard rank-8 n01 packet preflight, 2026-11-08 | None (machine work) | 0 | 0 | 0 | 0 | 0.00 | Twenty-five orders frozen; 79 official FR issue PDFs and 23 archived APP captures matched hashes. Fresh dispatch passed 25/25; ten optional source routes remain unverified. No producer or reviewer tokens used. |

**Measured worker total: $0.00.** No Bracton producer or blind reviewer has run. Coordinator model usage in this Codex chat is not exposed as per-call token telemetry, so its API-equivalent cost remains unmeasured; the measured total is not the campaign's all-in cost. Each subsequent producer/review batch will append its model, tokens, list-price calculation, and running measured total here. Machine-only acquisitions are recorded after their result batch even when USD remains zero.

Bentham's `usage --wave bracton-2026-11-08 --phase staging` command was run, but its default scan included unrelated Claude Code transcripts, so those figures are excluded. The sanitized `research/bentham/usage/bracton-2026-11-08/` record is explicitly filtered to a Bracton session prefix and currently has zero Claude Code calls. It says nothing about this Codex coordinator's token count.
