# Explicit blinded byte checks

The reusable verifier consumes actual reviewer cards and only their cited text/raw
paths under explicit source roots. It emits a deterministic mechanical report;
it does not read a genuine counterpart, a control key, a canonical claim registry
or a canonical dossier. This work supplies no scientific verdict or reviewer
attestation. The current source registration, source examination, control
adjudication and ordinary scientific review requirements remain in place.

Implementation: `jobs/claim-kit/blind_verify.py`, tests
`jobs/claim-kit/test_blind_verify.py`, usage `jobs/claim-kit/BLIND_VERIFY.md`.
The only owned assembler change is an additive optional `source_reader` callback
in `_source_errors`; its ordinary default and exact-byte algorithm are unchanged.
The verifier supplies already confined/pinned bytes through that callback.
Source discovery, dossier lookup and `_check_claim` are never invoked.

Actual-input results (exact pins and timings in `REPLAY.json`):

| Actual blinded input | Cards | Source occurrences | Text hash/span pass | Raw verified | Outcome |
|---|---:|---:|---:|---:|---|
| Retained MAITLAND `blind-review-input/RECORDS.json` | 23 | 26 | 26 | 0 | 26 explicit raw-custody unresolved; exit 1 |
| Earlier retained opaque historical blinded card | 1 | 41 | 0 | 0 | Missing source paths/raw declarations; 82 errors; exit 1 |

The MAITLAND input file hash matches its existing blinded `FREEZE.json`
`input_file_sha256`, supplied explicitly to the verifier. Its ten declared text
files were fetched by exact paths at PR133 `c733e69` into the external retained
source directory. Their actual byte hashes and Git blobs are retained in
`SOURCE_ACQUISITION.json`. All 26 quotes were re-sliced from those exact UTF-8
bytes. The input does not declare raw-source custody; the verifier reports the
text success while refusing a complete mechanical pass. It does not consult
later independent reviews to fill that gap.

The historical card is the actual existing blinded file at
`research/excavator/astra-cumulative-2026-10-24/review/blind/A.json` on main
`600ae301`, fetched alone through the connector. It remains outside the
repository. Its fetched raw-file SHA-256 is pinned in `replay.py`; that pin is an
observed retrieval pin, not a claim to reconstruct an earlier blind freeze. The
card references older text/raw material absent from the narrow retained source
tree; it also uses historical quoted-parts presentation without current exact
span fields. The verifier preserves the missing-source refusal. It neither
searches for a matching quote nor opens the old canonical claim to manufacture
offsets or custody. No control identity is known or disclosed here.

The replay command is:

```sh
python3 -I research/progress/sol-evidence-economy/blind-verifier/replay.py \
  --sources /tmp/sol-blind-verifier/retained-sources \
  --historical-card /tmp/sol-blind-verifier/actual-blind-A.json
```

The replay harness only writes its assigned report files. The consumer itself
writes nothing; its stdout is saved by the harness. There was no production
prepare/apply/complete execution, source grading, status/adoption/census change,
job dispatch, push or Git-reference edit under this assignment. Source/card
retrieval is explicit preparation outside the verifier and does not weaken its
read boundary.

Twenty-five focused tests pass, plus 50 ordinary assembler tests (logs retained).
They cover valid native C cards, generic records, exact CRLF/Unicode spans,
boolean and malformed offsets, missing and corrupt text/raw pins/files, all raw
aliases, LFS pointers, traversal/absolute/Windows paths, symlink escapes/loops,
duplicate/nonfinite JSON, bad UTF-8, frozen-card changes, interval witness
recursion, source mutation, CLI machine output/exit codes, and absence of
canonical lookup. The source boundary test instruments reads and proves that
metadata links and sibling files are not opened.

The independent engineering review found two substantive engineering defects
in an earlier candidate: recursion initially stopped at source metadata (missing
NORTON's nested interval bound witnesses), and symlink loops raised a runtime
exception. Both are corrected and directly covered. A changed nested NORTON
quote or raw path now fails, conflicting surrounding/source span fields fail,
and expected card pins catch even semantic-only interval edits before source
reads. The engineering review, source-boundary tests and fixture passes do not
substitute for different-family or human scientific review.

Observed setup failures are retained as limitations: one Git promisor lookup of
an absent historical blinded blob failed (`not our ref`), then the connector
retrieved that same explicit blinded file; one initial batched text materialization
exceeded the shell argument limit and was retried as ten bounded writes. Neither
failure read a key/counterpart or changed a scientific artifact. Two tests that
spied on the source reader needed their spy to allow the newly secured card read;
the corrected tests still assert no source read on pin/path refusal. No failed
scientific trial was discarded.

Configured worker: `gpt-6.1-sol`, provider OpenAI. Replay UTC clock and bounded
subprocess times are recorded in `REPLAY.json`. Tokens, cash cost, active labor
and full session timing are unavailable and recorded as null. These are local
machine timings, not measured end-to-end research savings. Root owns shared
register/brief/protocol integration and the final combined review.
