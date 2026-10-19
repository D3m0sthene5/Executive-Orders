# Corpus excavation profiler and bounded acquisition planner

Run `python -B jobs/corpus-excavator/job.py` to profile all census orders against
the committed tracker and existing claim-kit families. It writes per-order
remaining tasks, overlapping era/source/mechanism bottlenecks, acquisition
opportunities, historical witnesses/gaps, upstream failures and a fingerprinted
source plan. It never fetches or establishes a lifecycle conclusion.

Execute a plan with the existing source ladder:

```sh
JOB_PLAN_FILE=jobs/corpus-excavator/output/SOURCE_PLAN.json python jobs/source-ladder/job.py
```

Use the runner's `OUTPUT_DIR` and `REPO_ROOT` environment variables. Plans select
at most 50 distinct existing requests with a finite 1–300 HTTP-request budget;
the default pass is 12 requests and an 80-request budget. Changed queue metadata,
URLs, expected hashes, membership or ordering invalidate an explicit plan.
Readiness ceilings describe machine steps only; they are not accepted outcomes.

`measure.py --receipts <SOURCES.jsonl> --out research/excavator/<pilot>/<arm>`
replays the actual tracker with additive frozen receipts and reports differences
without mutating production inputs. The preserved pilot shows why source retrieval
and queue ranking cannot substitute for legal review.

The larger repeated-research extension is `jobs/status-history/`, consumed directly
by claim-kit. See `research/excavator/2026-10-18/REPORT.md` for the component choice,
measurements, costs, rejected readiness claim and next work. Neither profiler
families nor historical gap records are admitted census identities.

