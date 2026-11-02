# Fresh held-actor handoff after retained raw custody

All four assigned targets now have exact source-excerpt evidence IDs in a new
native packet. The unchanged source-supplement route accepts all four declared
raw/text pairs, verifies exact lineage, and preserves every inherited dossier
field. Blank ordinary apply retains **four unresolved orders, zero claim lines,
zero published claims and zero statuses**. This is engineering source access;
source identity/application, operative scope, dates and legal outcomes remain
unreviewed.

| Target | Added source-excerpt ID |
| --- | --- |
| EO:8129 | `SUPPLEMENT:plo1704-fr1958-p14` |
| EO:8163 | `SUPPLEMENT:plo1704-fr1958-p14`, `SUPPLEMENT:proc2416-stat54` |
| EO:9949 | `SUPPLEMENT:eo10804-fr1959` |
| EO:11026 | `SUPPLEMENT:eo11029-fr1962` |

The earlier engineering raw-custody blockers for the last two rows are absent
in this replay. That does not establish their source roles or legal effect.
In particular, the held EO 11029 heading and amendment language name EO 11025;
its application to EO 11026 must be examined rather than inferred from this
attachment. Both FR texts explicitly disclose machine extraction, OCR risks and
neighboring material. The selected contexts preserve that material and require
page/extent examination before substantive use. No source identity, grade,
complete-text, page-review, event-date or legal approval was supplied here.

## Exact inputs and fresh preparation

Runtime: final PR128 head
`43d1fef165d2a65f2e4e6e851bb0848823815b24` (implementation `a923a9e2` plus the
test-only LF fix). Retained sources: PR127 acquisition head
`a3fbcbfe960c417e006a821b1a053a0bb3e482e7`. A separate worktree/branch at the exact
runtime head materialized only the two new raw PDF blobs from that source
commit; their hashes and sizes match both its Git blobs and retention catalogue:

| Held actor | Raw SHA-256 | Bytes |
| --- | --- | ---: |
| EO:10804 | `f337a3b16522261cc147d92721a7fdea67ee17bfb1d9d155d45667455b09adaa` | 8,975,954 |
| EO:11029 | `7dfadd0c42279cf10b8e842c13ebdcd9a860d90b37da0862d2e5b421d33bab1f` | 35,388,126 |

`SOURCE_CUSTODY.json` preserves exact catalogue rows, raw/text hashes, existing
text paths, selected Unicode offsets and acquisition/runtime commits for all
four declared sources. The two FR extraction headers themselves name the same
source URL, raw SHA-256 and actor label; this is a checked recorded linkage,
not independent authentication. No network source request, redownload,
re-extraction or source-byte edit occurred in this follow-up.

The existing `native_replay.py` prepared new `parent/`, derived dossiers and
`supplement/` here. It did not modify or renew `native/`, `native-v2/`, or their
seals. `FOLLOWUP_VALIDATION.json` records their unchanged artifact hashes and
pins the exact runtime modules. The source-supplement module is byte-identical
to the earlier actor recovery version.

## Verification and remaining gates

`RESULT.json` records no blocked declarations, 20 held text pins, exact native
source-reference round trips, unchanged inherited dossier fields, and eight
refused controls: changed raw hash, changed text hash, invented grade, boolean
offset, foreign member, stale dossier fingerprint, already-supplemented parent,
and outer-rehashed stale dependency pins. Native supplement verification passes.
`TESTS.json` records **17 supplement tests and 24 final-runtime batch tests
passing**. The empty `CLAIMS.proposed.jsonl` and native apply receipts remain
inside `supplement/applied-unreviewed/`.

The sparse checkout's Valla and prior-research context limitations remain
explicit in the frozen packet. This engineering packet is not a complete
scientific briefing. Production requires fresh ordinary preparation with the
relevant full context and all applicable producer, source, clause, date,
independent whole-case review and owner-adoption gates. Existing missing-items
lists and holds remain intact. No readiness, scientific throughput, cost saving
or human certification is claimed.

To reproduce after the retained source commit and final runtime are available
with their ordinary dependencies and named source files materialized:

```sh
python3 research/progress/held-actor-handoff-2026-11-02/native_replay.py \
  --write research/progress/held-actor-handoff-next-fresh
python3 jobs/claim-kit/source_supplement.py --repo . verify \
  research/progress/held-actor-handoff-next-fresh/supplement
```

Use a new destination. Old sealed packets remain historical. This commit adds
only this new evidence/report directory; shared runtime, outputs, retained raw
sources, canonical claims/statuses, Kean and HANDOFF are not changed. Root owns
metadata integration and independent review. Model family is OpenAI; exact
worker model/token/cash and complete labor telemetry were not exposed.
