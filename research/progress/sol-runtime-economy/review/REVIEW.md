# Independent engineering review: source-index memory adapter

Configured reviewer: `gpt-6.1-sol`, high reasoning, independent context in the OpenAI family. Actual token and cash telemetry are unavailable. This is engineering review, not different-family, human, legal or source approval.

Baseline: `2c85459cf38b08dc1eea6d7c84a74268fa45c28e`, loaded directly through `git show` by the retained differential harness. Reviewed candidate source SHA-256: `7bb63fdb6f154ee67a568bc690a3d3c081f3d6d39137ec7bb55b7d551695679b`. Runtime regression test SHA-256: `d38cef189fa6ccd2d2d7d451a7c82d55d92f2745e35ce6d5c7666778e327594f`.

## Result

No outstanding engineering blocker found for the compact-field deque adapter at the exact reviewed bytes. The coordinator confirmed these final implementation hashes, which were rehashed before issuing `REVIEW_SEAL.json`. Complete raw probe results are in `ADVERSARIAL_RESULTS.json`; the reproducible harness is `adversarial_probe.py`.

The first HeldCopy-staging candidate (`51408a5723f83fc749a5f263c59914f15a5b79fc8ecf269144b62147b2b97943`) was rejected. A deterministic file-close callback creating or removing cache bytes changed its `local_path`, custody and saved-byte note versus the real baseline. It resolved filesystem paths during the read, whereas the baseline did so after the whole read and close. The reviewer reported these create/remove discrepancies during this session. Original rejected-candidate bytes and raw replay results are unavailable. `REJECTED_HELDCOPY_RESULTS.json` now contains only an explicitly attributed observation; it is not reconstructed exact replay evidence. An earlier version of this report incorrectly claimed raw results were retained at that path, which was empty. The prior seal is retained as `REVIEW_SEAL_SUPERSEDED.json` solely to document that corrected evidence error. The corrected adapter stages only the eight consumed values, completes reading and closing, and then executes the old path/custody/index operations in order. Both counterexamples now match the baseline.

## Verification

The retained independent harness passes 29 checks, including one seeded corpus with 1,200 varied records and complete `HeldCopy` slot values, SHA/URL lookup ordering, origin counts, notes and propagated exception parity. Inputs vary malformed hashes, duplicate sources and URLs, paths, unsupported shapes, integer coercions, instrument IDs, notes and arbitrary field types. Real invalid UTF-8 bytes retain replacement decoding and line counting. Index-add failures after partial mutation match the baseline for four caught exception types. Open/read/close interruption probes cover `OSError`, `UnicodeError`, `ValueError`, `KeyboardInterrupt`, `SystemExit`, `MemoryError` and `RecursionError`. These compare exception type/message and the entire index, preserving all-or-nothing file behavior for failures before processing. Cache creation and removal at close now preserve exact custody and notes. The six implementation regression tests also pass.

Code inspection confirms that missing fields and explicit null values remain equivalent because every consumed access uses `rec.get`; no unconsumed field affected the old adapter. Per-record processing and index-add exception handling retain their old scope and order. `_read_jsonl` remains a list-returning wrapper and malformed counts are appended only after successful complete read and close. No persistent index, new cache, restart checkpoint or source-registration policy is introduced.

## Limits

The memory bound remains proportional to all consumed fields for one manifest plus the accumulated index; this is not a constant-space parser or an out-of-memory guarantee. Unknown fields are discarded before staging, and deque entries are removed while index entries are constructed, removing the old parsed-dictionary/list overlap. RSS and speed gains require separate measurement. There is no general concurrent-file snapshot or locking guarantee: the preserved baseline can already observe mutations between its read and later filesystem checks. No new snapshot claim follows from the matched close-interleaving tests.

The review did not hydrate the corpus, dispatch jobs, modify implementation or Git state, publish, assess primary source authenticity, approve claims, or measure total production/model costs. Coordinator-owned native retained-input replay and full-suite checks remain separate evidence. End-to-end legal/source judgment and any adoption decision remain with the coordinator and applicable review rules. No owner question arose.
