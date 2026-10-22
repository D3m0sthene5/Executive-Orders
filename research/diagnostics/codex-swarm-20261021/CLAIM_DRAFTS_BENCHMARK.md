# Claim-drafts verification and performance

Measured on 2026-10-21 against base `cd5dba93874a04e014b0167293fd2a95dffca63b`
with the swarm's imported inputs. Python 3.12.14, pypdf 6.10.0, macOS;
every run used cProfile. All four runs drafted the same 3,359 decided orders
and indexed 88,425 held-copy records.

| Version | Cold extraction cache | Warm extraction cache |
|---|---:|---:|
| Baseline, downloads disabled | 169.794 s | 23.759 s |
| Patched, enforced offline | 169.204 s | 24.080 s |

`DRAFT_CLAIMS.jsonl`, `TODO_BY_ORDER.csv` and `CONFLICTS.csv` are byte-identical
across all four runs. `SUMMARY.json` is identical after removing only
`elapsed_seconds`. No URL calls occurred; the benchmark forbids them and
asserts zero calls. Hashes and exact measurements are in
[CLAIM_DRAFTS_BENCHMARK.json](CLAIM_DRAFTS_BENCHMARK.json).

There is no demonstrated whole-corpus CPU speedup from this patch. The
baseline's cold profile spent 145.930 seconds extracting 995 pages from nine
PDFs. The roughly sevenfold cold-to-warm improvement uses the checker's
existing persistent PDF extraction cache. Draft construction did not justify
adding a second persistent cache with new legal/provenance invalidation risk.

The repair removes the embedded checker's unintended network allowance:
claim-drafts promised no downloads but inherited up to 400 GovInfo requests,
each with a 120-second request timeout. Missing bytes now remain unverified.
The historical 86-minute run was not repeated online, so its avoided latency
is not quantified. The standalone checker and source ladder remain the
acquisition tools.

Existing byte receipts are reused read-only from both draft and standalone
checker stores, with SHA-256 validation. Repeated hashes are memoized only
within a POSIX run and file version; Windows rehashes each reference. Changed,
replaced, deleted or unreadable receipts are not promoted, including files
replaced/removed during hashing. No legal verdict, gate result or whole draft
is persisted. Gates and quotation checks still run for every draft.

The fresh corpus cache had no download receipts: all 4,119 missing-receipt
references stayed unverified. Therefore receipt-memo savings are not claimed
for these runs. A separate synthetic 8,388,600-byte receipt referenced 200
times took 0.770510 seconds with repeated hashing versus 0.012960 seconds with
one hash and 199 reuses, with identical verification results. That experiment
measures only the digest loop, not project, model-token or human-review savings.

## Regression coverage

All 68 claim-drafts tests pass on Python 3.13 without pypdf and Python 3.12
with pypdf. New regressions cover the embedded checker with networking
forbidden despite a standalone allowance of 400; missing receipts remaining
unverified; standalone-only receipt reuse without copying; corrupt bytes;
same-size/restored-mtime edits; replacements/deletions; changes during hashing;
cold/warm and fresh-run behavior; and Windows's no-memo fallback.

The corpus checker results remained 53 fail, 1,211 pass and 2,095
pass-with-unverified. These are mechanical checks on incomplete machine
drafts, not reviewed claims or human certifications.

## Reproduce

Run `python -B -m unittest -v test_drafts` from `jobs/claim-drafts/` first.
Save the base revision's `jobs/claim-drafts/drafts.py` to a scratch file using
`git show`, then invoke the supplied worker separately for baseline and
patched source:

```sh
python -B research/diagnostics/codex-swarm-20261021/benchmark_claim_drafts.py \
  /path/to/drafts.py /path/to/repo /path/to/scratch/output /path/to/scratch/cache
```

Use a fresh cache for each cold run, then reuse that version's cache with a
new output folder for its warm run. Do not use canonical job output folders.
The worker writes a profile and a normalized summary for equality comparison.
It forces the old implementation's download allowance to zero and forbids
URL calls. Full declared inputs in `jobs/claim-drafts/needs.txt` must be
materialized; missing optional inputs would make the benchmark incomparable.
