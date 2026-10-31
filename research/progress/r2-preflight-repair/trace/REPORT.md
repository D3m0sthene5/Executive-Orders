# R2 locator and exact-span tracing

Read-only implementation examination at base `88cef0253ed735b2a6e612770f25f9148641ce93`. No implementation, corpus, evidence, claim, status or register edits were made by this worker. This report is the sole owned deliverable. Independent source examination and coordinator integration are separate.

## Recommendation

Reuse the clause-drafts locator and its paragraph/recital helpers on the unchanged, hash-verified original representation. Diagnose missing command text by interval subtraction against exact original-bound inventory spans. Do not treat a clean machine screen as an approved inventory.

1. Keep `evidence_preflight.inspect()`'s existing confined loading, 32 MB limit, UTF-8 decoding, SHA-256 and quoted-span checks. Start this diagnostic only from its verified selected `original_source_id`. An explicit different `Instrument:` marker is a boundary/identity exception, not permission to scan for the requested order elsewhere.
2. Load the existing module with `locator = excavate._clause_locator()` (`excavate.py:121`). Call `loc = locator.locate_order(body, iid[3:])`, leaving `hint_unnumbered=False`. `Located` supplies absolute `doc_start`, `body_start`, `body_end`, `doc_end`, `heading_style`, `signature_found` and warnings. The number argument is `8220`, not `EO:8220`.
3. Accept the positive numbered/trailing-number route only after checking identity/boundary ambiguity. In particular, for `trailing_number`, reject an intervening valid numbered heading in `[loc.doc_start,loc.doc_end)` exactly as `_trailing_extent()` does: iterate `locator.GENERIC_HEADING.finditer(body, loc.doc_start, loc.doc_end)` and require no `locator._valid_generic(body, match)`. Repeated own headings also deserve an ambiguity warning; the locator chooses one matching document and can prefer a later signature-bearing match. Preserve the existing multiple-unnumbered-heading boundary task until explicit source examination resolves it.
4. Bound ordinary command candidates to `[loc.body_start,loc.body_end)`. `locator.segment(body,loc,iid)` returns clauses with keys `start/end/clause_kind`, separate `recitals`, and warnings. These are distinct from claim-kit `segment(iid,body,source)`, whose clauses use `char_start/char_end/text/kind`. Never mix the two field layouts or argument orders.
5. For paragraph command candidates, use `locator.paragraphs(body,start,end)` followed by `locator.split_recital(body,a,b)` and keep only the returned operative span. This splits a fused authority-and-command sentence at an absolute offset, excludes a whole WHEREAS paragraph, and treats an empty “ordered as follows:” formula as recital/enacting words. A raw uncovered-paragraph scan or the mere presence of `shall` is too broad. Numbered units can contain unnumbered trailing command paragraphs; inspect paragraph residuals within those units as needed, rather than restricting attention to clause kinds labelled unnumbered.
6. Merge valid original-representation inventory intervals and subtract them from candidate operative intervals. Require a bounded directive phrase in uncovered operative text, and return its actual `[a,b)` plus `body[a:b]`, source text path/hash and diagnostic reason. Do not call a whole candidate missing just because authority words, punctuation or whitespace are outside the inventory. Conversely, a covered candidate/heading start must not mask later uncovered command words. Multiple adjacent inventory clauses may jointly cover one candidate.
7. Keep findings diagnostic (`research_required`/possible omitted command), with no inventory replacement or adjudication. If no trustworthy extent is available, report/retain boundary uncertainty and do not invent identity. A narrowly described false negative is preferable to promoting a guessed neighboring command to this order.

The locator is not a substitute for the independent examiner. In particular, a missing signature, interleaved columns, malformed/unbalanced quotation warnings, uncertain heading identity or unexpectedly large residual should remain visible. Do not add automatic OCR repair, punctuation normalization or paragraph reconstruction to satisfy coverage.

## Exact-offset contract

- All offsets are Python Unicode code-point offsets into the exact decoded held text, not bytes, PDF coordinates or normalized text.
- `paragraphs()`, `split_recital()` and the clause-drafts `segment()` preserve absolute offsets when passed the full body string and absolute bounds. If a substring is passed instead, every returned offset becomes relative to it and must be translated; the safer call is always the full string.
- Never use `reading_text()` for coverage or evidence quotes: it removes furniture lines and changes the representation. Whitespace flattening may aid a regex decision but cannot supply evidence offsets.
- The new coverage union must be tied to the selected original representation. Current preflight's `ranges = [(char_start,char_end), ...]` accepts naked offsets from every proposed clause. Another source's offsets or malformed quotes can therefore mask missing text. Prefer a clause's resolved evidence reference or source path and text hash matching the original, validate integer bounds (`bool` is not an integer offset), and verify its quoted text equals `body[a:b]`. If a supported dossier schema does not expose enough information, document that exception; do not silently assume cross-representation coordinate identity.
- A task should identify candidate scope and residual span separately if both are supplied. Its quote must always equal the specified residual slice. Deterministic task de-duplication must not collapse two distinct uncovered commands on the same source into an unexplained single offset.

## Phrase-detector limits and lower-false-positive reuse

Eight additional in-memory phrase probes confirmed the following limits:

| Text | Existing splitter/phrase behavior |
|---|---|
| `By virtue of authority vested in me, the Secretary shall submit a report.` | Entire paragraph classified as recital; no operative phrase |
| `Now, therefore, the Secretary shall report annually.` | Entire paragraph classified as recital; no operative phrase |
| `I hereby find that the board has completed its work.` | Operative span returned; `OPERATIVE_PHRASE` matches only `I hereby` |
| `The Secretary shall submit a report.` | Operative span returned; no `OPERATIVE_PHRASE` match |
| `This order shall become effective immediately.` | Operative span returned; no `OPERATIVE_PHRASE` match |
| `It must be recognized that these conditions exist.` | Operative span returned; no `OPERATIVE_PHRASE` match |
| `The prior statute provides that the Secretary shall report.` | Operative span returned; no `OPERATIVE_PHRASE` match |
| `Under authority vested in me, the board is hereby abolished.` | Recital `[0,30)`, operative `[30,60)`; phrase matches `is hereby` |

Accordingly, apply recital splitting to the full original paragraph/candidate before subtracting covered intervals, not to an arbitrary residual fragment. Treat its recital classification as a heuristic with the authority-led `shall` false negatives above disclosed. Silently treating every returned recital span as legally non-operative would be wrong.

`OPERATIVE_PHRASE` is a useful boundary helper but not a complete command detector: it both misses ordinary `shall` commands and accepts incomplete phrases such as `I hereby` or `is hereby`. For a low-false-positive diagnostic, pair it with an actual bounded directive verb (including necessary inflected/passive forms), or a separate explicit duty/effectiveness pattern. Do not use bare `must`, a historical/quoted `shall`, or unqualified `VERBISH` as positive proof. `VERBISH` (`segment.py:873`) is a heading heuristic and includes `is/was/may/must`.

One narrower existing reusable signal is `locator.classify(residual_text, '', '', iid[3:])[0] == 'effective_date'`: `classify()` already recognizes “this order/the provisions of this order/this amendment shall become effective/take effect/be effective”. Its normalized working string is suitable only for the decision; return the quote from the unchanged body slice. Its default `operative` result is **not** a positive command test. General-provisions/definitions/policy classifications likewise do not establish absence of legal effect, and should not become blanket exemption rules.

## Why `_extent()` alone is unsafe for this added check

`evidence_preflight.py:113` currently calls `excavate._extent()` for numbered heading coverage. That helper returns a broad research extent, not a clean ordinary-command body.

1. `_body_end()` deliberately ignores a signature/White House end anchor when a later `SCHEDULE` occurs. A synthetic numbered order with a post-signature schedule produced `_extent == (0,491)` while `loc.body_end == 59`; the schedule contains command-looking `shall` language. Clause-drafts emits it separately as `annex_after_signature`. Exclude this candidate kind and anything beyond `loc.body_end` from the ordinary-body omission diagnostic. This does not declare an annex non-operative; annex completeness is separate research.
2. `_trailing_extent()` rejects a bare-heading/closing-number binding when a valid numbered neighbor intervenes, but `_extent()` then falls back to its other parser. When that fallback has no matching own numbered heading, it starts at zero and can retain both documents. An inline fixture `EXECUTIVE ORDER ... first command ... Executive Order 8221 ... second command ... [No. 8220]` produced `locate_order(...,'8220')` in trailing-number style spanning both commands; `_trailing_extent()` rejected it, yet `_extent()` still returned `(0,123)`. A positive locator call therefore also needs the explicit intervening-numbered-heading guard.
3. `locate_order(...,hint_unnumbered=True)` picks an unnumbered heading with an explicit identity-from-filename-only warning; `locate_body_only()` similarly warns that identity comes from source URL. Neither is positive printed identity. Do not use either to silence the existing neighboring-document warning or infer target identity from metadata alone.

## Observed bounded probes

Five synthetic in-memory probes imported the existing modules without writing implementation or fixtures. These establish parser behavior, not historical facts.

| Probe | Observed behavior | Consequence |
|---|---|---|
| Fused authority + unnumbered revocation before Sec. 1; effective-date paragraph after Sec. 1 | Locator body `[28,200)`; separate preamble operative `[69,106)`; Sec. 1 candidate `[108,198)` includes effective-date paragraph | Preserve fused-command offsets; inspect residuals inside numbered candidates |
| Two bare-heading orders with their own closing numbers | Target 8220 bound `[23,60)`; only its first command candidate returned | Positive trailing-number route can isolate a neighbor when properly anchored |
| WHEREAS with `shall`; authority-only “ordered as follows”; actual revocation | Two recital spans `[28,70)`, `[72,141)`; only operative `[143,180)` | Reuse recital splitter, not raw `shall` search |
| Numbered order + long post-signature SCHEDULE containing `shall` | Body ends at 59; annex candidate `[113,489)`; broad `_extent` ends at 491 | Ordinary command diagnostic must exclude the annex |
| Bare heading, intervening numbered 8221, target closing number 8220 | Locator and `_extent` both potentially span neighbor despite legacy-route rejection | Explicit boundary rejection is essential |

Existing preflight regression command: `python3 -B -m unittest discover -s jobs/claim-kit -p test_evidence_preflight.py -v`. Result: **12 tests passed in 0.028 s**. No new repair implementation or tests were written by this worker.

## Bounded repair acceptance tests

Use short local fixtures only, with exact source/text pins and asserted `body[a:b] == task_quote`:

- Omitted separate unnumbered command before sections; omitted command in fused authority sentence; omitted effective-date command after a section; omitted command in a wholly unnumbered two-command order.
- Existing inventory starts at the candidate/section heading and stops before the second command: still flag the second command. Two adjacent valid inventory spans jointly covering the candidate: no flag. Overlapping coverage: stable result.
- WHEREAS paragraph mentioning a duty, authority-only enactment formula, title/heading, furniture, recognized signature/date/filing block: no command-coverage finding.
- Neighboring numbered order before and after the target; bare neighboring orders with closing numbers; intervening numbered neighbor before a purported target closing number; explicit wrong `Instrument:`: no target command finding from the neighbor, and boundary/identity exception stays visible.
- Post-signature schedule/annex containing `shall`: no ordinary-body command finding, without suppressing any existing annex research warning.
- Wrong source representation with coincident offsets, invalid bounds, boolean offsets, wrong exact quote, same source bytes but differently normalized representation: none may count as covering the selected original.
- Non-ASCII punctuation, letter-spaced printed EO number, CRLF representation, line-wrapped fused command: offsets remain into the unchanged input. Missing/ambiguous locator and quotation/interleave warnings: documented bounded behavior, no guessed reconstruction.
- Read-only repeatability: deep-copy dossier before `inspect`, assert unchanged afterwards; stable repeated task ordering; held file loaded once through existing cache; no source acquisition.

## Provenance and costs

Read `AGENTS.md`, `HANDOFF/KEAN.md`, `HANDOFF/README.md`, newest checked-out handoff entries and the assigned parsers. Kean search `unnumbered inventory preflight locator` found no earlier work, with 993 tracked notes/reports unavailable in this sparse checkout; this is not a corpus-wide negative. Coordinator owns required shared Kean/handoff integration; worker ownership forbids changes outside this report.

Final inspected parser hashes match the supplied base exactly:

| File | SHA-256 |
|---|---|
| `jobs/claim-kit/evidence_preflight.py` | `0698661c59f5384fae99dac7586bbbc572793283abac5803f12482f4ae546242` |
| `jobs/claim-kit/excavate.py` | `d869e4086c121e33da551ebbe17e678d945d1424d223c1cd1d891d0f2ca5347d` |
| `jobs/clause-drafts/segment.py` | `0ea7afd1bfd6e5776068d32bda1b58efcc367db3055740ee64709da0caef6573` |

An earlier shared-workspace read showed one extra terminal LF in each parser; these disappeared before final hash verification. The worker did not change them. The tree is sparse and shared; a broad `git status --short` unexpectedly emitted a very large absent-file list. This was an inefficient inspection, not source fetching or a change to those files.

Model: inherited GPT-6 Codex/OpenAI context; exact runtime variant is not exposed to this worker and is **unknown**, not inferred from a requested routing label. Token/cache/cash telemetry: **unknown**. Total worker elapsed time was not captured from assignment start and is **unknown**; the actual recorded clock interval from first explicit timestamp `2026-10-31T04:14:36Z` through `2026-10-31T04:15:44Z` is **68 seconds**, only a lower bound on work through report preparation. Existing test execution time is separately measured above. No savings or independent-source-review credit is claimed.
