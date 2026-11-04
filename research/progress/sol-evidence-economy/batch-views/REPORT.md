# Repeated ordinary dossier views

The additive `geddes.py views` command renders an assigned list from one frozen
packet in one process. `view_many(packet_path, eos, write_dir=None, repo=None,
full_claim=False)` uses the existing renderer and returns an ordered list.
No new evidence codec, deduplication store, acquisition route or review rule is introduced.

Packet decoding, latest current-claim selection, lookup JSON, draft CSV/rationales
and shared memo parsing occur once per invocation. Claims keep the exact last
filename/physical-line rule and remain qualified as prior drafts. The shared
context is discarded after the call. Native envelopes are self-hash/shape checked
before decoding, including native-sized 64-hex fingerprints whose schema was
stripped. Schema-less legacy exports without such a fingerprint retain the
original dossier/source checks and do not receive native envelope verification.
These rendering checks do not replace full current preparation gates. Each order's held sources are still read and
SHA-256 checked on every source comparison, including same-size mutations between
members. Existing source access, legal qualifications, full-claim option and
explicit overflow bounds are preserved. No extra truncation is introduced. For newly optional MAITLAND contexts, the
view live-validates `reviewed_histories` once and displays only relevant queries,
including unknowns and no-approval notices. Typed factual occurrence intervals
retain full source markers and live source/review revalidation; they are shown
separately from citable legal actor records and never converted into endings.
Legacy packets without these contexts retain exact prior output.

## Ordinary consumer

A producer assigned EO6258A and EO6308 from retained n01 can use:

```sh
python3 -I jobs/geddes/geddes.py views research/excavator/claude-apollo-2026-10-31/n01/packet/PACKET.json EO:6258A EO:6308 --write-dir /tmp/n01-assigned-views
```

Each file has the ordinary view content, named `EO_6258A.view.json` and
`EO_6308.view.json`; stdout contains summaries. Without `--write-dir`, stdout is
an ordered JSON list. Existing batch destination files or symlinks cause a refusal before output. The lossless packet, source paths and indicated physical
claim line remain the access route for material beyond existing view caps.
This read-only rendering step does not prepare, apply, review, certify or file.
The coordinator owns the normal `kit.py view/views` integration.

## Retained evidence and measurement

Inputs are the exact n01 packet and 23 members retained at
`c733e69dbd0fa1e57a1f2614a33d77bdd600f122`, not generated lookalikes. The
376,232-byte packet's Git blob is `92b4b337a3862ecebff12decca122664346260c1`.
All 28 declared source files were fetched and SHA-256 checked against the packet;
no unavailable or bad source was silently substituted. `INPUTS.json` records 33
exact Git-blob inputs, including the actual draft sheets, shared analysis and
319,809-character retained n01 claims file. Git promisor hydration failed first;
the connector fetched the exact ref instead. No active output path was used.

The fixture includes one retained claims file, rather than the full current
104-file claims tree. The APP publisher INDEX could not be materialized: its
connector response contained an empty string with a different expected Git blob.
Consequently all 23 whole-order-body verifications remain explicitly unresolved
in both outputs. There are zero text-file integrity/unavailability failures.
This measures preparation/rendering parity, not a new substantive source review.

The baseline loads the exact pre-change Geddes code and competently calls its
per-order `view` in one process: imports are not repeated per order. Five
alternating baseline/batch runs preserve complete output equality, including
full-claim mode. Output is 704,268 UTF-8 JSON bytes for either route.

| Observation | Existing per-order loop | Shared invocation |
|---|---:|---:|
| Median rendering seconds, five runs | 0.304922 | 0.057337 |
| Path byte/text read calls | 219 | 108 |
| Distinct Path byte/text reads | 27 | 27 |
| Fresh-process wall seconds | 0.585283 | 0.251591 |
| One-order warm seconds, one observation | 0.011423 | 0.013004 |

Median rendering was 5.32 times faster (81.20% less rendering time)
for this bounded 23-member fixture. A separate shared-setup probe took
0.020454s, followed by 0.047900s
for all member rendering. These independently timed observations should not be
subtracted from other runs. The single-order observation is slower on the shared
route; the optimization is intended for repeated members. Fresh-process numbers
include Python startup, but operating-system caches were not flushed. CSV `open`
reads are not in the Path counters. Raw final-code run variance appears in `BENCHMARK-final.json`; the earlier full run remains in `BENCHMARK.json`;
`INITIAL_TIMING.json` preserves the initial run's summary before adding overhead
probes. The figures do not establish end-to-end production/research savings.

Replay after materializing exact `INPUTS.json` members into an isolated fixture:

```sh
git show c733e69dbd0fa1e57a1f2614a33d77bdd600f122:jobs/geddes/geddes.py > /tmp/geddes-baseline.py
python3 -I research/progress/sol-evidence-economy/batch-views/benchmark.py --fixture-root /tmp/n01-fixture --baseline-code /tmp/geddes-baseline.py --write /tmp/batch-views-benchmark.json
python3 -I -m unittest discover -s jobs/geddes -p 'test_*.py'
```

Validation: 96 Geddes tests pass, including native envelope/schema tamper and fixed-cutoff refusal, multi-member ordinary/full-claim
parity, one shared scan, invalid members before writes, CLI file summaries,
overflow/unknown coverage preservation and actual source mutation between
members/invocations. An initial new read-count expectation was 12; the measured
fixture performs 11 reads (six source reads), and the assertion was corrected.
Existing 89 tests passed before adding seven new regressions. Additional optional-history/factual source tests exercise live stale refusal, unknown-state preservation and unrelated-member exclusion.

## Cost and boundaries

Worker: actual configured OpenAI `gpt-6.1-sol`. Model token counts, cash and active
implementation time are unavailable; no retrospective labor clock is invented.
All measured rendering/setup times are recorded above. No benchmark model was
invoked. Ordinary outputs are identical in size, so no prompt-token reduction is
claimed. Reusing the shell process does not prove a model/cache/cash saving.
No claim/status, review verdict, production output, register, shared handoff,
canonical source, Git ref, commit or publication was changed by this worker.
