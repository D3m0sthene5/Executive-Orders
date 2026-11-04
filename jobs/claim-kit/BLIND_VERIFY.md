# Explicit blinded-card byte verification

`blind_verify.py` replaces repeated reviewer hash/span scripts. It verifies only
explicit reviewer input files and source files those inputs actually cite, inside
explicit allowed source directories. It does not select cases, compare genuine
counterparts, inspect control keys, discover sources, load canonical dossiers or
registries, score controls, or supply a scientific verdict.

```sh
python3 -I jobs/claim-kit/blind_verify.py \
  --card /review/blind/items/opaque-card.json \
  --expected-card-sha256 EXACT_REVIEWER_MANIFEST_FILE_HASH \
  --source-root /review/retained-sources \
  --allow-source-root jobs/fr-originals/data/full_run/texts \
  --allow-source-root jobs/fr-originals/data/full_run/pdfs \
  > /review/MECHANICAL.json
```

`kit.py blind-verify` exposes the same arguments. `--card` accepts one JSON or
JSONL file per argument; repeat it for several files. Direct lifecycle claims,
Mountweazel Track C `{item_id, track, claim}` cards, arrays, and a blinded
`{records: [...]}` envelope are supported. A source-free Track S card fails with
`no_source_references`; the verifier never supplies missing sources from a pool.
No directory scanning, glob expansion, manifest loading or network operation is
performed. Shell-expanded paths remain the operator's explicit inputs.

`--source-root` provides the coordinate base for the paths already in the cards.
Every `--allow-source-root` is an explicit directory underneath it; relative
values are relative to that base. Use narrowly retained source trees rather than
a general repository containing claims, controls or keys. Only text/raw paths
inside source references are read; metadata links such as `source_file`, fixity
records and review ledgers are inert. The operator remains responsible for
supplying actual blinded cards and keeping controls/counterparts outside the
allowed source trees. Filename heuristics cannot prove blinding.

When supplied, repeat `--expected-card-sha256` in `--card` order for every file.
This is the exact **file byte** hash obtained from the blinded input's manifest,
not a canonical claim hash. A mismatch stops that file before parsing or source
reads. No expected pin is inferred or fetched; `input_pin_checked: false` makes
an unpinned invocation explicit. Current canonical card/payload hashes are also
reported, retaining every supplied field. They do not establish an earlier freeze.
Changing an interval date with unchanged source bytes is caught by an expected
card pin; byte checking alone cannot judge what the interval establishes.

The verifier walks nested source references, including NORTON interval witnesses
inside a factual source marker. References may carry `quote` and character offsets
inside the source, or NORTON's surrounding `{source, text, char_start, char_end}`
record. Conflicting versions of those spans fail. Offsets are nonempty Unicode
code-point slices of UTF-8 decoded exact stored bytes. CRLF is preserved; byte
offsets and newline-normalized quotes are not substituted. Missing offsets are
never reconstructed by searching for the quote.

Every declared `local_path`, `local_file`, `download_path` and `raw_path` must be
inside the allowlist and hash to the declared source SHA-256. All aliases are
checked, so a good alias cannot conceal a bad one. Archival sources may use the
existing `local_file_sha256` convention. Traversal (even traversal resolving back
inside a root), absolute/Windows-drive paths, symlinks, missing/nonregular files,
malformed hashes/offsets, duplicate JSON keys, nonfinite JSON and invalid UTF-8
fail closed. Source bytes are rehashed after computation to refuse changes during
the check. POSIX descriptor-relative reads additionally prevent parent symlink
replacement from redirecting a read; on platforms without that API, before/after
path and file checks apply. This is not an adversarial filesystem sandbox.

A lifecycle claim requires an explicit raw path and valid source hash for each
reference. A generic textual research record may omit raw custody: its exact
text/span checks can pass while `raw_path_missing` remains **unresolved**. This is
an incomplete verification, never fabricated raw custody. A declared missing or
incorrect raw file is always an error. No implicit LFS/download/materialization
step runs.

The deterministic report uses input/card indices and field loci. It contains
source file hashes, lengths, declared source paths, source errors and separate
`text_verified` / `raw_verified` flags. It contains no plant classification,
claim quote, scientific accept/reject recommendation or reviewer attestation.
`ok` means all present source references passed text and raw checks; it is not
claim-schema validation, original authentication, source identity, provenance
registration, legal-effect approval or control sensitivity. Those ordinary
review obligations remain with the reviewer and native workflow.

Exit codes: **0** complete mechanical pass; **1** refusal or unresolved custody;
**2** invalid CLI arguments. Stdout is the machine report for exit 0 or 1. The
command itself writes nothing. Save stdout in the assigned review destination;
never overwrite a sealed review or treat this output as a completion receipt.

The Python API is `verify_files(cards, source_root, allowed_source_roots,
expected_card_sha256=None)`. It reuses `assemble._source_errors` with its optional
`source_reader` callback over already confined/pinned bytes. The assembler's
ordinary default reader is unchanged. The verifier does not call `check_claim`,
which can perform canonical lookup. `add_arguments(parser)` and `run(args)` are
the CLI integration points.

Run `python3 -I jobs/claim-kit/test_blind_verify.py` and
`python3 -I jobs/claim-kit/test_assemble.py`. The retained actual-input replay and
limitations are in `research/progress/sol-evidence-economy/blind-verifier/REPORT.md`.
