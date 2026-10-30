# Three ProQuest custody holds: diagnosis and verified correction

EO254, EO2171 and EO4354 all become ready for human review in the bounded native
checker-to-tracker replay. Each remains **transcription-dependent**, requires an
original replacement and quotation recheck, and has no human certification.
No claim, source grade, page confirmation, legal review or certification gate was
edited. The three canonical claim files remain byte-identical.

## Why the standard workflow held them

The investigation is pinned to main `f9c6d806ad059dcad7875ab3708715f20ea386df`.
PR88's 395-ready dashboard was accurate for its generation. The repository already
contained the three exact PDFs as ordinary Git blobs, but `.github/workflows/run-jobs.yml`
initially checks out `.github`, `jobs` and `HANDOFF`. The checker adds its `needs.txt`
directories; neither selection includes `ProQuest Pre-1937 Orders`.

`sources.load_replica_fragments()` indexes Pinakes's explicit PDF association but
uses `raw.is_file()` to distinguish a local copy from metadata. With the source
outside the sparse checkout it creates `custody="record_only"`. A saved hash and
OCR text permit quotation checks but cannot establish byte custody. The generic
`custody_record_only` explanation saying the bytes are in no committed place does
not establish that the Git object is absent: these three regular blobs do exist.

Merged PR94 (`a6faab34fa5e86f4483e18c58f76e6885f17b797`) already supplied the correct
bounded restoration mechanism: intersect cited hashes with Pinakes, fetch exact
regular Git blobs at pinned HEAD, verify SHA-256 and PDF signature, then let the
ordinary checker rehash the materialized file. No release download is needed.
However, it applied a **32,000,000-byte aggregate limit to the entire claims
directory before selecting the three identities**. Current main has 76 files,
34,221,195 bytes total; its largest file is 3,491,032 bytes. The helper therefore
returned no receipts and `claim input byte bound exceeded`.

This is reproduced locally in `baseline/PROQUEST_MATERIALIZATION.json` and independently
visible in GitHub run [40936647222](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/40936647222),
job 123668843379; the relevant log excerpt is retained in `PR94_RUN_EVIDENCE.json`.
That run also had unrelated later failures and a freshness rejection, so it did
not publish a new canonical total. Those failures are outside this repair.

## Exact source trace

`SOURCE_TRACE.json` records Pinakes inventory and fragment rows, the corresponding
production packet's source declaration/input pin/held-text receipt, and Git blob IDs.
The claims originate from the unchanged October 28 production files b1b, b1a and
b1c respectively. Each cites only its own ProQuest source hash.

| Order | Repository PDF | SHA-256 | Bytes |
|---|---|---|---:|
| EO254 | `ProQuest Pre-1937 Orders/PT1-1904-EO-254.pdf` | `63a96efb348908966e3769b300d93b2a2cefd10dacdcee9bd8bf33f1f6748732` | 78,595 |
| EO2171 | `ProQuest Pre-1937 Orders/PT1-1915-EO-2171.pdf` | `6887d2296a53d1b5bafe5a40f11399a1a7b2d87331a6349ed220129a0112a4b7` | 42,225 |
| EO4354 | `ProQuest Pre-1937 Orders/PT1-1925-EO-4354.pdf` | `98b1a107e723aa5f9fc91a3f66c08c722b3377aaf24d4339320acf99da3ea3da` | 66,513 |

All 187,333 bytes were restored from pinned regular Git blobs and independently
rehashed to those exact values. EO254 also has an inventory-listed duplicate with
identical bytes; the declared primary path is used. The scans retain
`archival_replica_scan_pending_codebook` and `acceptable_as_original=false`.

## Correction

`jobs/claim-checker/proquest_inputs.py` now streams UTF-8 JSONL and hashes the exact
raw bytes while retaining the existing 32 MB **per-file** guard. It checks actual
bytes read as well as the initial file size. All claim rows are still considered;
the growing corpus no longer shares one file-sized allowance. Total scan work
scales with the claims directory, as the ordinary checker already does. This is
not a new overall scan-time bound.

The three-identity/three-scan bounds, 8 MB per PDF/24 MB total PDF limit, permitted
roots, Pinakes grade/identity/hash intersection, pinned commit, regular-blob check,
LFS-pointer rejection, no-overwrite rule, exact SHA-256/PDF checks, and all native
source/readiness gates are unchanged. Malformed or oversized metadata still aborts
before restoring any PDF. There is no new source acquisition or broad PDF checkout.

## Validation and outcome

Final targeted regressions: **53 checker/materialization tests and 36 tracker tests
pass**. The three new tests cover corpus growth with a later target and exact
CRLF/blank-line file hashes, oversized metadata refusal, and malformed metadata
refusal. Existing tests retain wrong-hash, path/symlink, LFS, size and no-overwrite
coverage. Logs and exact commands are in `TESTS.json` and the two test logs.

`validate.py` runs unchanged native checker and tracker code against the three exact
canonical claims. It temporarily relocates only the verified PDFs for the before
case and restores them in `finally`; no source requirement is mocked. For tracker
isolation it replaces only these three receipts in an external copy of the
published receipt map. Other receipts and canonical outputs are untouched. The
local checkout carries the relevant metadata and these three texts, rather than
the complete source corpus. Consequently no global ready count is inferred.

| Order | Without bytes | With exact bytes | Remaining readiness blockers | Continuing obligations |
|---|---|---|---|---|
| EO254 | Not ready | Ready, complete claim | None | Original replacement; quotation recheck |
| EO2171 | Not ready | Ready, complete claim | None | Original replacement; quotation recheck |
| EO4354 | Not ready | Ready, complete claim | None | Original replacement; quotation recheck |

Before: all three structural gates pass and all 18 quotations match, while 15
source references remain `custody_record_only`. After: all 15 references are
`held_bytes_verified`, all 18 quotations match, all three checker claims pass,
and all six applicable readiness steps pass per order. The tracker explicitly
retains `transcription_dependent`, replacement=`yes`, and recheck=`yes`.
`replay/RESULT.json`, per-claim receipts and tracker rows retain the exact outcome.

The first replay script expected three return values from `tracker.build`, which
returns two; the script was corrected and rerun. Its failed attempt log is retained.
No repository gate failed or was changed for that harness error. Local Python uses
pypdf 6.10.0; the standard GitHub job pins its own requirements. Source quotations
were checked against the retained texts and actual PDF bytes by native code.

Independent engineering inspection is in `INDEPENDENT_REVIEW.json`. It does not
replace the existing substantive legal reviews. Worker model requested:
`gpt-6-luna`; token/billing telemetry is unavailable. No total-hours saving is
claimed. Checkout/setup and initial replay correction are additional session cost.

The correction is submitted through a separate PR, without merging or altering
main. A complete, fresh canonical checker/tracker publication is still required
before changing the project dashboard. **395 is not automatically changed to 398.**
