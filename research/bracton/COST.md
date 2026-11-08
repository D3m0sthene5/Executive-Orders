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

**Measured worker total: $0.00.** No Bracton producer or blind reviewer has run. Coordinator model usage in this Codex chat is not exposed as per-call token telemetry, so its API-equivalent cost remains unmeasured; the measured total is not the campaign's all-in cost. Each subsequent producer/review batch will append its model, tokens, list-price calculation, and running measured total here. Machine-only acquisitions are recorded after their result batch even when USD remains zero.

Bentham's `usage --wave bracton-2026-11-08 --phase staging` command was run, but its default scan included unrelated Claude Code transcripts, so those figures are excluded. The sanitized `research/bentham/usage/bracton-2026-11-08/` record is explicitly filtered to a Bracton session prefix and currently has zero Claude Code calls. It says nothing about this Codex coordinator's token count.
