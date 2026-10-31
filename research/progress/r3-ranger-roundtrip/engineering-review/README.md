# Independent bounded engineering review

Verdict: **PASS for the exact code hashes in REVIEW.json**. Thirty-nine focused tests passed; the final subprocess took 1.712 seconds, with identical code hashes before and after. This is a separate-context OpenAI Codex engineering review, not human certification, different-family review, or source-content/legal adjudication. Exact inherited model variant and complete worker/token/cash telemetry are unavailable.

The tests execute the actual generated workbench script in Node with a minimal DOM, drive its real import/export handlers, compare all six Python/JavaScript validation classes, and exercise the actual census adapter on isolated fixtures. Current notes survive intact. Stale, missing-source, conflicting, unknown-version and v1 notes cannot become current proposals through re-export, repeated import, a fabricated historical validation label, or restoration of previously changed source bytes. Source changes include transcript/XML/page/facsimile bytes and declarations, metadata, prior Stage22 records, and transcription/page inventory provenance. Census candidates retain `NOT_ADMITTED`, `HOLD`, `human_certified: false` and zero admission/certification counts even with hostile imported note fields.

Three issues were reported to the coordinator and fixed there:

1. Browser `JSON.parse` silently dropped duplicate worksheet keys. The strict parser now rejects repeated keys, including escaped equivalents.
2. Displayed manuscript images loaded mutable GitHub `main`, while bindings referred to local bytes. Generated HTML now embeds exact, rehashed JPEG/PNG bytes; tests decode the image URI and compare its digest to custody.
3. Transcript hashing and display read could race. A deterministic mutation after hashing reproduced the mismatch; display bytes are now rechecked and the regression passes.

Retained facsimile derivative grades remain explicit; display data is not smuggled into source fingerprints. Missing and wrong-identity retained snapshots remain blocked. HTML source/note script delimiters are escaped and preserved exactly.

The harness does not test browser layout, accessibility, actual JPEG decoding, network links, production source truth, or a full repository rollout. No network, crawl, full repository suite or Git mutation was performed by this worker. These fixtures establish engineering behavior only.

One initial harness failure came from waiting only two event-loop turns for asynchronous WebCrypto; the harness now waits for actual initialization with a bounded timeout. A later intentionally stricter candidate binding made a mismatched census fixture stale; setup was corrected to use the same prior record. That failure is retained in `pre-final-provenance-fixture-failure.log`; final results are in `focused-tests.log`. Review/timing/hashes are in `REVIEW.json`. Complete worker effort is additional to the recorded final subprocess duration.

No owner question or decision arose. Coordinator owns Kean and shared HANDOFF integration; no register or shared-note mutation was made from this disjoint review workspace.
