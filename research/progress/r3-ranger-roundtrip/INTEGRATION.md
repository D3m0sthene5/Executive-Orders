# R3 integration contract

Branch `sol/r3-ranger-roundtrip`, base `88cef0253ed735b2a6e612770f25f9148641ce93`. Leave unmerged for Root. The implementation changes only the existing Early-Ranger workbench and census-candidates interfaces. No authoritative census, denominator, status, claim, certification, Clark, acquisition implementation, runner or dependency declaration is changed.

## Versioned export/import contracts

- Export: `eo-early-source-worksheet/v2`, `review_state=research_only_never_certification`; `per_case` is keyed by exact LOC item ID. Each entry contains `candidate_id=LOC:<id>`, `source_binding`, and attributed notes/proposal. The source binding is `eo-early-case-sources/v1`.
- A candidate version hashes its exact metadata record and prior Stage22 candidate record. The binding includes item ID/URL, actual retained artifact SHA256, declared custody SHA256, paths, original resource URL/page sequence, canonical inventory-row hashes, and explicitly selected older workbench representation. The binding fingerprint is SHA256 of canonical, recursively key-sorted UTF-8 JSON, excluding the fingerprint itself.
- Import checks both identities, the complete binding and current bytes. `unchanged_source` permits restoring current research notes. `changed_source`, `missing_source`, `conflicting_representation` and `unknown_version` retain notes in the unverified history and cannot produce a validated proposal. An unchanged binding means the source snapshot matches; it does not authenticate a document, prove source completeness, verify a legal conclusion or authorize adoption.
- V1 worksheets restore as `legacy_unverified`. Unknown/wrong item IDs remain conflicting exceptions. Historical notes remain quarantined on later exports/imports, including when source bytes are restored. Neither nested self-declared validation labels nor human/admission fields inside a note can promote it. Python and browser reject duplicate JSON keys, including escaped duplicate keys.
- Exact JPEG/PNG source bytes are embedded in the existing display; transcript and preview rereads must match captured hashes. TIFFs and reduced IIIF images retain their representation labels. Data URI previews are not new originals. Stored image order is not presumed to be manuscript reading order.
- Browser validation is relative to the frozen HTML case snapshot. Regenerate from current source files to check freshness; `census-candidates` rebuilds the current cases and revalidates rather than trusting a UI receipt. The worksheet is a research record, not a cryptographic signature or protection against deliberately falsified notes.

## Existing tool usage

Run from a checkout containing the exact source inputs listed in the replay receipt and both optional custody manifests:

```sh
python3 -m unittest discover -s jobs/early-ranger-workbench -p 'test_*.py'
python3 -m unittest discover -s jobs/census-candidates -p 'test_*.py'
python3 research/progress/r3-ranger-roundtrip/replay.py
```

`replay.py` calls the existing `make_case`/`build_cases`, repaired exporter, generated HTML import/export event handlers, workbench CLI and census-candidates CLI. It writes only R3 outputs. The Node VM uses a minimal DOM; it verifies the actual import/export code, not browser layout or image decoding.

The workbench accepts `--import-worksheet <file>`, `--retained-workbench <older HTML>` and `--include-retained-facsimiles`. `--facsimile-custody <file>` reuses the existing facsimile custody format for explicitly supplied acquired source packets; stored paths are relative to that custody file. There is no new candidate registry. Census uses corresponding source options with `--research-worksheet <file>`; it attaches validated proposals and retains exceptions beside the exact candidate. Multiple worksheets can be retained. It never changes `NOT_ADMITTED`, `HOLD` or `human_certified=false`.

These source options are explicit. Default runs do not silently consume a historical HTML snapshot, R3 findings, or additional acquired images. No runner/dependency changes are supplied within this ownership. Root must materialize the existing workbench helper files and selected optional source inputs before invoking the adapter through a selective-checkout runner. Do not remove a runner fallback or infer dependency closure from this local replay.

## Exact pins and native results

`REPLAY_RECEIPT.json` pins the four implementation files, exact exported worksheets, both additional source inventories and final candidate output. `engineering-review/REVIEW.json` pins the five tested code/test files before and after its 39 focused tests. `independent-source-review/INITIAL_SEAL.json` pins the pre-comparison independent source examination. `crosswalk/CROSSWALK.json` pins current/older source availability; per-case packets contain full exact source bindings.

The current transcription inventory is empty. Nine transcripts are explicitly recovered only as older retained HTML representations, not missing original XML. The isolated workbench has 21 cases. The native census replay has 67 exact LOC item candidates and 8 source-bound AI proposals, with zero admissions and zero certifications. Its current XML transcript count remains zero; the older embedding does not alter that metric. Canonical job outputs were not overwritten.

Bounded acquisition added 8 exact Madison-copy master JPEGs and 16 Polk page representations (one master TIFF, 15 reduced LOC IIIF derivatives). Existing held sources were used for the other cases. The independent examiner viewed 42 media files across the selected 8 item IDs; file count differs from manuscript-side count. No broad crawl or exhaustive historical census is claimed.

## Recommendations and adoption requirements

| LOC item | Current research disposition | Evidence and remaining adoption work |
|---|---|---|
| mjm017450 | Recommend exclusion of asserted instruction text | Actual page is a `Wanted` checklist requesting prior instructions; it is not those underlying instruments. Whether this request was separately issued official direction remains open. |
| mjm018302 | Hold | Revised Navy instructions; approximate/ambiguous date, no final issued version established. Resolve presidential approval/transmission, final clauses and historical naval-class inclusion. |
| mtjbib011110 | Hold | Printed presidential/by-command instructions, with blank execution/addressee fields. Resolve issued-copy status and military-class inclusion. |
| mtjbib012509 | Hold | Signed June20 expedition instruction; older ante-June20 editorial label concerns drafting. Resolve version/transmission, historical expedition/military/letter class and existing-census crosswalk. |
| mtjbib016595 | Hold | Revised Wilkinson/convention bundle, alternate articles and envelope to President. Resolve contributors, boundaries, final wording/issuance and class. |
| mss365090092 | Hold; correct document identity | Rough message drafts about withholding prior Slidell instructions. Do not admit a new Jan12 1848 Slidell instruction based on this grouping; reconcile the message and the older instructions separately. |
| mjm017456 | Recommend administrative-instruction candidate | Signed Aug13 rules for War Department reporting; distinguish oversight from field command. Resolve final sent/retained-copy role, historical inclusion and existing-census/Lord crosswalk. |
| mjm022917 | Duplicate-witness proposal | Explicit `Copy` and corresponding substantive sequence support same-instruction witnesses; no second issuance demonstrated. Preserve distinct documentary versions; do not merge rows or count two instruments. |

All dispositions are attributed AI research. The initial producers and independent examiner are separate OpenAI contexts; this is not different-family or human review. Final notes preserve producer artifacts by hash and incorporate independently identified date, page-order and clause corrections. Formal admission requires the existing historical inclusion/identity procedure, scientific review and authorization. Whole-lifecycle research remains separate. The pending June1932 admission question is untouched.

## Integration order

Adopt the two workbench helpers and both job interfaces together; keep the focused tests. Preserve R3 research, seals, failed experiments and both source custody manifests. Union the R3 append-only Kean findings with other sessions' findings and regenerate the brief rather than replacing concurrent entries. Recheck code/source pins, run the focused suites and native replay in the combined tree. A changed source or candidate version requires a new worksheet/source examination; do not relabel an old review as approval of a new version.
