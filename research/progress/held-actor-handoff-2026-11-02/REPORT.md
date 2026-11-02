# Held actor source handoff, 2026-11-02

The existing native source-supplement route closes two of the four Erasmus
packet source-ID gaps without a shared runtime change. A fresh four-order packet
now carries exact held PLO 1704 excerpts for EO 8129 and EO 8163, and the held
Proclamation 2416 excerpt for EO 8163. All four members remain unresolved;
ordinary apply emits no claims or statuses. This is engineering preparation,
not legal research, independent review, readiness, or scientific adoption.

| Target | Added evidence ID | Remaining source handoff gap |
| --- | --- | --- |
| EO:8129 | `SUPPLEMENT:plo1704-fr1958-p14` | None for this exact held excerpt; research/review remain |
| EO:8163 | `SUPPLEMENT:plo1704-fr1958-p14`, `SUPPLEMENT:proc2416-stat54` | None for these exact held excerpts; research/review remain |
| EO:9949 | None | EO 10804 raw PDF unavailable in this checkout |
| EO:11026 | None | EO 11029 raw PDF unavailable in this checkout |

## Existing routes and bounded change

Kean searches for `actor`, `supplement`, and `handoff` found the printed-reference,
Namier, prior supplement, and lightweight handoff work, including F-20261028-12,
F-20261028-8 and F-20261029-4. The original combined search found no match and
disclosed the sparse checkout's unsearched reports; it was not treated as proof
that the route did not exist.

`build.package` already attaches `ACTOR_TEXT:` evidence for located or known
actor pairs. `excavate.acting_provision` locates bounded named change provisions;
neither route licenses a new pair, source identity or date from a researcher's
unreviewed assertion. `source_supplement.py` already supplies the needed exact
held-excerpt route, with immutable lineage, raw/text hash and span checks and
ordinary packet routing. Its existing CSV fields support producer-selected
`later_events` with explicit legal/date judgments, or qualified `source_notes`
without inventing an event date. No new source-selection or grading system was
added.

The recovered `replay.py` declares four exact source candidates. Its two absent
FR raw paths now name the existing retention job's canonical
`output/pdf/<sha256>.pdf` destination, rather than guessed paths inside
`fr-originals/data/full_run/blobs/`. FR source metadata records those as external
cache paths, not committed files under `data/full_run`. `native_replay.py` is a
bounded reusable engineering replay: it prepares new ordinary packets, calls the
existing supplement, verifies exact source reference round trips and inherited
dossiers, exercises refusal controls, and leaves producer decisions blank.

## Native evidence and checks

Base: `f07b023133640f288fd44c10c5176888c49f23e2`, fetched from GitHub main during
this recovery. Branch: `codex/held-actor-handoff-20261102`. No historical packet
was renewed or re-fingerprinted. The exact native receipts and packet artifacts
are under `native-v2/`; `native-v2/RESULT.json` identifies every added quote's source,
raw/text hashes, Unicode offsets and quote hash.

The fresh parent has four orders and 16 held text pins. The supplement has 18
held text pins and verifies exact lineage/source bytes. Each added evidence ID
round-trips through the native assembler's source-reference encoder with the
exact quote. Removing only supplement metadata, its added evidence and the new
fingerprint reproduces every inherited dossier field exactly. No mechanism,
effective date, identity approval or grade was added. Existing missing-items
lists, including the PLO census-identity warning, remain unchanged.

Eight negative controls are refused: changed raw hash, changed text hash,
injected grade, boolean span offset, foreign member, stale dossier fingerprint,
already-supplemented parent, and an outer-rehashed packet with stale dependency
pins. Native apply retains `unresolved: 4`, zero proposed claim lines, zero
published claims and zero published statuses. Shared tests: **17 source
supplement + 17 batch tests passed**, recorded in `VALIDATION.json`. The corrected
source handoff and artifact assertions are recorded in `CORRECTION_VALIDATION.json`. An initial
batch-test attempt had two sparse-checkout errors because Valla source files
were absent; materializing unchanged Valla code fixed those fixture errors.
The final native parent includes Valla context.

This is a bounded sparse-checkout replay. Valla and prior research explicitly
report unmaterialized context; this packet is not an exhaustive scientific
briefing. A production researcher must prepare a new version with the relevant
complete research/review material and perform all ordinary source, scope,
date, inventory, savings, independent whole-case review and adoption checks.
The replay establishes the source-ID handoff, not any order's ending theory.

## Preexisting dirty PDF and missing raw sources

The Proc 2416 PDF was already truncated to **zero bytes** when recovery began.
Its SHA-256 was the empty-file hash `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
The Git HEAD blob is 1,698,316 bytes, begins `%PDF-1.4`, and exactly matches the
declared SHA-256 `15e01816ebc165ff00f747861704bae240f51f4f7578f1c14f53a942e5fa96de`.
No evidence explains who or what truncated the working file; it is not an LFS
pointer or a newline-only difference. With the coordinator's authorization,
the original zero-byte dirty file was copied to separate scratch storage with
a custody receipt, then the exact HEAD bytes were restored without conversion.
`CUSTODY_REPAIR.json` records paths/hashes. No modified source bytes are committed.

`MISSING_RAW_SOURCE_METADATA.json` preserves the existing FR acquisition rows:
EO 10804's issue was 8,975,954 bytes (2026-10-17), and EO 11029's was 35,388,126
bytes (2026-10-17). Their held text files match the expected hashes. The raw
PDFs are absent locally; there is no directly tracked hash-named blob or
matching Astra retention catalogue receipt. The FR README explains that its
PDFs live in an external cache and may be deleted while metadata/text remain.
Stage 21 custody and the release exclusion index have no matching raw source
entry. Release archive payloads and the owner's external cache were not
exhaustively inspected; global nonexistence is not asserted. A partial-clone
`git lfs ls-files` scan could not complete because an object was missing.

`RETENTION_REQUESTS.proposed.json` and `FETCH_QUEUE.proposed.jsonl` prepare two
exact-hash requests through the existing retention route. Neither target/URL
pair is already queued. They are proposals for integration: shared queue/input
files were not edited and no acquisition job or network source fetch was run.
Restore an exact cache/release object first if available; otherwise declare the
bounded manifest and queue the pairs before explicitly running the existing
retention job. Re-run the fresh packet path after exact raw custody is restored.

## Reproduce and integrate

From a repository checkout with the named held files and ordinary dependencies
materialized:

```sh
python3 research/progress/held-actor-handoff-2026-11-02/native_replay.py \
  --write research/progress/held-actor-handoff-replay-new
python3 jobs/claim-kit/source_supplement.py --repo . verify \
  research/progress/held-actor-handoff-replay-new/supplement
python3 -m unittest discover -s jobs/claim-kit -p test_source_supplement.py
python3 -m unittest discover -s jobs/claim-kit -p test_batch.py
```

In a sparse checkout, include this artifact directory and the two restored raw
PDF paths in the sparse definition before running the commands. Merely writing
clean bytes to an excluded tracked path does not protect it from sparse
reapplication. The Proc PDF path is recorded in `CORRECTION_VALIDATION.json`;
the PLO path is recorded in `native-v2/SOURCES.json`.

The destination must be new. Missing raw files are reported as blocked;
changed existing bytes abort, preserving the native refusal. The script never
downloads a source or repairs custody automatically. Native stale-context
refusals require fresh preparation; changing hashes to reuse an old packet is
not an allowed continuation.

## Correction after independent engineering review

Independent review of `f81eacf1fa3f09eafd31d0f7da7234188570689b` found that this
report described an earlier successful Proc 2416 preparation while the committed
`native/` replay correctly reported that PDF missing and only 17 text pins.
After the initial exact-byte restoration, adding Valla files with
`git sparse-checkout add` reapplied the sparse definition and removed the now-clean
Proc PDF, whose path had not been included in that definition. The final replay
therefore omitted Proc correctly; the report was wrong.

The original `native/` packets and receipts remain byte-for-byte unchanged as
the failed initial handoff. Recovery explicitly added both the Proc PDF and this
artifact directory to the sparse definition, materialized the exact Git blob,
and prepared entirely new `native-v2/` packets. No prior packet was edited or
renewed. The new committed result is checked directly for the Proc evidence ID,
18 held text pins, exactly two missing raw sources and four unresolved outcomes.
The original zero-byte backup remains untouched. `CORRECTION_VALIDATION.json`
records the old and corrected packet/source hashes and the exact assertions.

Root owns integration, independent engineering review, and the shared Kean and
HANDOFF updates. `KEAN_FINDING_DRAFT.json` supplies the bounded result for that
register update. No shared runtime, canonical claims/statuses/census, source
grades/holds, scientific approvals, remote branches or pull requests changed.
Model family: OpenAI; exact worker model, token/cash and complete labor telemetry
were not exposed. No cost or scientific throughput improvement is claimed.
