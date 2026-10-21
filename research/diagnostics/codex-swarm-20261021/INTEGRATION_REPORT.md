# EO workflow swarm: integration and execution

Base: `cd5dba93874a04e014b0167293fd2a95dffca63b` (main, rechecked 2026-10-21).
Four working roles: orchestration/integration, runner wiring, draft performance,
claim production, with separate independent review (roles used available slots in sequence).

## Results

- Connected the Pinakes/ProQuest and CSC source collections and their readers. The
  local tracker recognizes 2,750 archival replica fragments and 798 CSC compiled
  transcriptions. Their existing custody limits remain; they are not authenticated originals.
- Repaired producer/consumer order, transitive shared-library triggers, root
  ProQuest/research/release workflow filters, and the ranger-to-census chain.
  Removed references to a nonexistent executable WPA job where the job uses vendored data.
  Dependency cycles now fail with an actionable path. Bot output commits still do not loop.
- Enqueued all 266 valid Lewis source requests through the existing contract,
  preserving the entire historical queue prefix. These are queued, not newly acquired.
- Draft checks now enforce their documented offline behavior and reuse standalone
  checker receipts read-only after byte verification. In-run receipt hashing is
  safely reused on supported filesystems; changes during hashing fail closed.
- An unavailable web search engine is probed once per run. The remainder is recorded
  as deferred, separately from real engine attempts; the next run may retry. No
  search deferral is treated as source absence or legal exhaustion.
- Repaired LOC XML ingestion when the metadata grew from nine to eleven links.
  Its validated plan is deduplicated and capped at fifty links, with distinct
  filenames for multiple resources from one item. The bounded local run saved all
  eleven transcriptions (10,857 words). `loc-success/` retains exact XML/text and
  receipts. The first local CA-configuration failure is preserved in `loc-attempt1/`;
  the successful retry used the system CA bundle with TLS verification intact.
- Produced five case attempts, independently reviewed two exact claims (EO11087,
  EO11089), and committed only those two to a new claims file. EO11088, EO11090
  and EO11092 remain blocked on transfer/savings analysis. The archived frozen
  codebook2.0.0 was recovered by range reads and verified against nested manifests;
  its bytes and retrieval evidence accompany the pilot. No methodology changed.

## Measured validation

The expanded road entry point passed 190 offline tests. Two final ranger-chain
regressions then passed with the entire 14-test scheduler suite (192 distinct tests
across the final suites). Independent code review found three issues; each was
repaired and independently rechecked. `CODE_REVIEW.md`, `ROAD_TESTS.log` and
`SCHEDULER_FINAL.log` retain the detail.

All 3,359 drafts, CSVs and semantic summaries are identical in four profiled runs:

| Drafting run | Cold cache | Warm cache |
|---|---:|---:|
| Baseline, downloads forbidden by the harness | 169.794 s | 23.759 s |
| Patched, intrinsically offline | 169.204 s | 24.080 s |

There is no demonstrated new CPU speedup. Existing PDF extraction caching explains
warm performance. The patch removes unintended online work and safely connects
receipt reuse; the old unbounded online run was not repeated to manufacture a speedup.
No token or dollar savings are claimed. Full methodology and repeatable worker:
`CLAIM_DRAFTS_BENCHMARK.md` and `CLAIM_DRAFTS_BENCHMARK.json`.

The two final committed claim hashes pass the actual checker: 2/2 all checks passed,
0 failures, 36 GPO source-hash references, 17 identity checks and 51 exact quotations.
Source pages were independently visually reviewed. The checker alone is mechanical.

Local tracker replay: **278 → 280 ready for human review**, with no input problems.
It merged just the two exact new checker results into a scratch map and retained
other published job outputs. This is a reproducible local integration observation,
not a newly published full GitHub pipeline generation. The baseline and replay
receipts are saved here. No canonical job output was replaced by the replay.

## Imported generations

Selected authored paths and existing source outputs came from:

- Pinakes/Lewis/Clark: `2019758cebe8f8802e66d393ef46800fc3874a23`.
- CSC: `bd7e78c8cc47ffe21393b27407d0a3a97c575919`.

These are path-level integrations, not whole-branch merges. Other agents' HANDOFF
notes and unrelated branch changes are not included. Existing output STATUS files
retain their original execution provenance; imported outputs are not represented
as fresh executions of this integration commit.

## Remaining boundaries

- The 266 source requests await the bounded source-ladder run.
- External search credentials/access permissions are not invented. Manual import
  routes for restricted repositories remain intentional; no crawler was added to bypass them.
- ProQuest replica grading/page checks and the three held claims require substantive
  research. Existing six source-audit holds and pending owner rulings remain.
- This change adds no new model or tool marketplace dependency and makes no verified
  end-to-end token saving claim. It uses existing artifacts and closes their connections.
- Accepted claims are AI-reviewed research, not human certification. Status/census,
  immutable methodological inputs, other claims and human-review records are preserved.

The pull request and its GitHub checks are the publication boundary. Local evidence
above is complete; fresh remote execution results, if any, must be read from their
own run receipts rather than inferred from these tests.
