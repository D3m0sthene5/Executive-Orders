# Cruden bounded table retrieval recovery — 2026-11-02

Finished the previously uncommitted `table-number` route on isolated branch
`codex/cruden-held-table-recovery`, based on current fetched main
`f07b023133640f288fd44c10c5176888c49f23e2`. The prior patch and its
831,881-byte `EXAMPLE.json` were preserved and assessed; that example remains
byte-identical (SHA256 `56db452bc4847cbfb3484e429a2efdbeb3072982cbfc0c65749dfd051130b073`).
No push, PR, merge, shared Kean-register edit or shared HANDOFF edit was made.
The coordinator owns independent review, integration and Kean/HANDOFF recording.

## Behavior and defects corrected

`table-number EO:9949` is an explicit opt-in route for same-line bare-number
cells under `No. Subject` headings associated with the held literal revocation
introduction. It returns source hashes and exact normalized number, row,
subject, heading and introduction spans, counts, truncation and page metadata.
It uses the existing content-bound snapshot and decimal candidates unchanged.

The recovered patch had three reproduced defects: an unrelated first heading
suppressed a later valid introduced table; revocation context survived a
signature into unrelated later headings; and any 7xxx digits near a PDF marker
could become a purported printed page. The finished parser starts at a valid
local introduction, expires inherited context at recognized document boundaries,
and requires explicit Federal Register page furniture. Attached and hyphenated
uppercase suffixes match exactly; parent and neighboring identifiers do not.
Invalid PDF page numbers produce no page attribution. Introduction spans make
the inherited context inspectable for every returned row.

This is a bounded layout heuristic. Unknown document boundaries, multiline
subjects, other table layouts, split-column OCR and OCR damage can still cause
misses or noisy leads. It does not infer legal effect from the word “revoked.”
The full source and actual source page still require examination. No source
authentication, identity, source grade, claim, status, census, readiness count,
codebook, review gate or human certification changes.

## Validation

- `python3 -I research/excavator/claude-nira-sweep-2026-10-29/test_cruden_table.py`:
  **10 tests pass**, including the real held APP table (no skip), exact spans,
  suffix collisions, repeated headings, nine boundary forms, later explicit
  introductions, false page furniture, valid/invalid page markers, count/limit,
  query refusal, output hash, and candidate/noncandidate/inventory mutation
  refusal before replacing an existing result.
- Existing `test_cruden_cache.py`: **11 tests pass**.
- `python3 -I research/progress/held-table-handoff-2026-11-02/verify_held.py`:
  **four matching files, four rows for EO9949**, against the four already-held
  representations pinned in the preserved example. Every source hash and every
  returned span was checked. APP pages are null; three related FR text copies
  identify PDF page 10 / printed page 7238.
- All **13 pre-existing function ASTs are identical to pinned main**, including
  `lookups`, `search`, `source_search`, `number_pattern` and source discovery.
  Matched baseline/current number and literal hit payloads and source inventories
  are equal; normal regex stdout is byte-identical. Ordinary `number EO:9949`
  remains **0** on this bounded corpus while the separate table route gives 4.
  No full packet `lookups` replay was claimed; function code is unchanged.
- `git diff --check` passes. `PINS.json` pins implementation, unchanged helper,
  tests, preserved prior example and replay artifacts. `REPLAY.json` records the
  bounded replay, source pins, results, comparisons and machine timings.

## Scope and costs

The replay covers **4 held files / 312,413 bytes**, with **33,114 tracked texts
not discovered** in this sparse checkout, zero read errors and zero directory
errors. These are four representations of one table, including related copies
of the same FR issue, not four independent legal sources. The inherited packet
path/hash in `EXAMPLE.json` is preserved as a reference only; this work did not
validate that packet. No acquisition or source-processing job was dispatched.

One warm table call took **0.1485 seconds**, including stdout serialization;
it read 312,413 bytes in each initial, candidate and final-verification pass.
Coverage inventory dominated this tiny local run. The baseline comparisons
warmed the disposable cache; this is not a cold measurement or an equivalent
research-task savings comparison. No global speed, model-token, cash or
full-session labor saving is established. Worker uses a fresh delegated OpenAI
agent context; exact configured model label and token/cash telemetry are not
exposed here. Independent engineering review remains the coordinator's next
step, and this is not scientific or human review.

## Coordinator recording text

Suggested Kean finding: “Recovered opt-in Cruden table-cell retrieval; corrected
first-header suppression, cross-document context leakage and invented printed
pages. 10 table + 11 cache tests pass; held EO9949 gives 4 exact source-bound
leads where unchanged number search gives 0, on 4-file sparse corpus with
33,114 omissions. 13 old functions unchanged. Retrieval only; no legal/source
promotion or measured overall saving. Pinned report and replay retained.”

@Owner: none. No new owner decision requested.
