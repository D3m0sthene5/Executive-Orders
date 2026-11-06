# Freshness scopes: what each job reads, and what discarded two finished runs

Justinian, 2026-11-06 (task A2). Main at `454a70716` when measured.

## What discarded the runs

| Run | Started | Checkout | Tip at publish | Outcome |
|---|---|---|---|---|
| [42146445914](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42146445914) (schedule) | 02:41 UTC | `4b32e7db` | about `ae6d7584` | 27 jobs ran (24 succeeded); "records-only", nothing published |
| [42146887458](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42146887458) (#156 push, 4 h 17 min) | 01:54 UTC | `833233dd` | about `6daac0ed` | bentham and kean ran; nothing published |

Before Arsenale (#166, merged 07:53 UTC), one stale job made the whole run records-only. Arsenale now publishes
each job whose inputs are still fresh. That fixes most of the waste by itself.

For the scheduled run, every job was stale for two reasons:

1. `jobs/_lib/eo_websearch.py` changed under the run (paid-search caps, `70dfd463`). Each job's scope held all of
   `jobs/_lib`, so this one file invalidated all 27 jobs, including the 20 that never import it.
2. Claim-checker's scope was `research/**`, `releases/**` and `jobs/*/output/**`: 111,801 files. 16,046 of them changed
   during the run.

## What claim-checker actually reads

I ran `checker.main([])` on main under a Python audit hook (`freshness/trace_sitecustomize.py`), with no fetching. It
took 888 s and 25,335 quotations were checked. The trace is in `freshness/claim-checker-trace-20261106.tsv.gz`:
4,865 files read and 188 directory listings.

- Under `research/` and `releases/` it read 83 files besides the claims: Stage 21 custody and acquisition logs, the
  Stage 14/15/18/20 indexes, the decided-case table, 7 source-book PDFs and 2 Opus zips. It read nothing under
  `research/excavator`, `research/herschel` or `research/progress` except the decided-case CSV.
- Under `jobs/*/output` and `jobs/*/data` it read 4,606 files. 4,558 of them are files the code globs (`*.csv`,
  `SOURCES*.jsonl`, `FRAGMENTS*.jsonl`, `data/**`) or paths named inside provider records. The other 48 are read under
  names built from provider fields: `texts/<id>.txt` and `raw/<sha256>.html`.

## The change (PR for A2)

1. **Library by imports.** The scope keeps only the `jobs/_lib` modules the job imports: directly, transitively, or
   through a literal `.py` input it declares. It also keeps the non-Python library files and `cache_cap.py`, which
   the runner itself executes. If any source fails to parse, the whole library stays in scope. Valla is unchanged,
   because its certificate binds the whole library.
2. **Runner tests excluded.** `.github/scripts/test_*.py` cannot change a job's output, so it leaves every scope
   except Valla's.
3. **`references.txt`.** A job may list its provider files. Every `research/`, `releases/` or `jobs/` path named
   inside them becomes a root. A name that does not exist keeps its nearest existing ancestor. The job's
   `needs.txt` then declares only the checkout, no longer the read scope. Claim-checker declares its claims,
   factual records, SOURCES/FRAGMENTS and provenance files. Its `inputs.txt` lists the code-level reads in place
   of the three whole trees. Scanning the providers takes 5 to 7 s (404 MB, 46,109 references).
4. **Digest asks from Kean.** The digest's "open asks" section now reads `jobs/kean/register/asks.jsonl`.
   Notes are no longer an input, so a HANDOFF note edit no longer discards it.
5. `select` and `literal_prefixes` look up ancestors in a set. The result is identical; this keeps 17k roots fast.

**Coverage check.** Every one of the 4,851 tracked files the traced run read falls inside the new claim-checker
scope; 0 are missing. The scoped file count falls from 111,801 to 70,547.

## Dry run against the two discarded runs (`freshness/dryrun.py`)

Paths changed between each run's checkout and the tip it published against:

| Job | Stale paths, old scope | New scope | Would publish? |
|---|---:|---:|---|
| claim-checker | 16,046 | 3,777 | no: Mabillon's 2,018 and Ptolemy's 1,397 new SOURCES/texts landed mid-run, and the checker reads them |
| fr-pages, shepard-citations, theophilus-sources | 2 each (`_lib`) | 0 | **yes** |
| clark-discovery, domesday-register, gessner-cards | 6 to 7 | 5 to 6 | no: `tracker.py` and tracker outputs changed |
| readiness-tracker, claim-kit, bentham, cassiodorus | 2,250 to 6,100 | about the same | no: `research/excavator` salvage (#158) and new SOURCES |
| corpus-excavator, polya, neyman, lambertini, x1-class-engine | about 8,630 | about 8,630 | no: claim-kit published 8,611 output files mid-run |
| second run: bentham, kean | 2,070; 12 | 2,068; 10 | no: genuine new inputs (excavator waves, Kean register) |

**The acceptance check in the prompt does not hold, and saying it does would be false.** With the narrower scopes,
three jobs of the first run would have published. Claim-checker's stale set shrinks by 76%. But during both runs,
inputs each job really reads changed, so their discards were correct. What prevents the rest of the waste is
fewer concurrent writers during a run, not a looser guard: hence the A5 merge-freeze ask. Narrowing
`research/**` for the tracker, claim-kit and Bentham in the same way is the next step (B3); it needs a trace of
each job.

## Reproduce

```bash
cd jobs/claim-checker && PYTHONPATH=../../research/justinian/freshness TRACE_FILE=/tmp/cc REPO_ROOT=$PWD/../.. OUTPUT_DIR=/tmp/out python3 -c "import sys;sys.path.insert(0,'.');import checker;checker.main([])"
```

(rename `trace_sitecustomize.py` to `sitecustomize.py` in a scratch folder on `PYTHONPATH`.) Then run
`python3 research/justinian/freshness/dryrun.py ARTIFACT_DIR BASE TIP`. The artifact directory comes from each
run's `oversized-outputs-<run>` artifact.
