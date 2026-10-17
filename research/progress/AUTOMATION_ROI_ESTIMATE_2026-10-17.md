# Executive Orders — eight-job automation return-on-investment estimate

Date: 2026-10-17. **This is a scenario estimate, not an observed automated throughput claim.** Legal cutoff 2026-10-14; human-certified whole-lifecycle count is unaffected.

## Grounded baseline and implementation status

The project owner reports **21 million agent tokens** for the Stage 11 work yielding **844 accepted AI-reviewed classifications**. The [Stage 11 complete README](../../releases/opus_stage11_complete/README.md) identifies 1,155 reviewed cases, of which 844 were accepted and 311 held (six additional assigned cases excluded). This is **24,882 token-equivalents per accepted result**, including tokens consumed investigating eventual holds, or 18,182 tokens per reviewed case. These figures describe Stage 11 classifications; they do **not** establish the cost of source-backed whole-lifecycle legal histories.

As of this snapshot, the [readiness tracker](../../jobs/readiness-tracker/output/TRACKER.md) reports 3,359 provisional classified cases, **174 with saved original text**, zero clause inventories and zero fully machine-ready cases. The Stage 21 source overlay covers **402 direct official document URL candidates** (386 PDF candidates) for provisional cases, and the bounded fetcher recorded **160 PDF responses** downloaded, without treating downloaded bytes as legal-source authentication. The GitHub Actions run [39055917466](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39055917466) fetched 120 additional PDF candidates and completed in about 75 seconds of end-to-end Actions elapsed time. That is machine acquisition telemetry, not legal analysis time.

## Forecast, after completing and integrating jobs 1–8

**Conservative 35%, central 60%, optimistic 75%** future Stage 11-like token reduction. These are judgemental planning scenarios, pending a representative measured pilot. Source ladders, primary text capture, clause drafting, change graphs, current law indexing, image matching, claim checking and draft assembly must be de-duplicated so a claimed saving is not counted twice. The central **illustrative** 21-million-token cost allocation is:

| Job/step | Hypothetical old tokens | Fraction removed | Tokens saved |
|---|---:|---:|---:|
| Access ladder | 4.20M | 80% | 3.36M |
| Original source locating | 2.52M | 80% | 2.02M |
| Clause inventories | 2.10M | 65% | 1.37M |
| Later change graph | 3.15M | 65% | 2.05M |
| Current-law references | 2.73M | 55% | 1.50M |
| Image matching | 0.84M | 75% | 0.63M |
| Mechanical claim checks | 1.47M | 75% | 1.10M |
| Draft assembly | 1.05M | 70% | 0.74M |
| Irreducible case-specific legal judgment | 2.94M | 0% | 0M |
| **Total** | **21.00M** | **60.75% overall** | **12.76M** |

The category allocation is explicitly *not* derived from instrumented Stage 11 traces; Stage 11's 7.7-million-token continuity lane contains multiple categories of work and must not be equated entirely with current-law scanning. Exact time and token decomposition requires workflow instrumentation.

Using a rounded 60% savings scenario and 2.5-million-token one-time build:

| Future comparable accepted-result equivalents | Prior tokens | Gross savings | Net savings after build |
|---|---:|---:|---:|
| 844 | 21.0M | 12.6M | 10.1M |
| 3,359 | 83.58M | 50.15M | 47.65M |
| 14,972 | 372.53M | 223.52M | 221.02M |

**Break-even ≈168 future comparable accepted results** after 2.5M build tokens. Costs already spent on the 3,359 provisional cases are sunk, and the 14,972 entries include heterogeneous/missing historical originals. The 14,972-row extrapolation is a mathematical *what-if*, not a forecast of complete lifecycle certification or nationwide issuance coverage.

## Time model (illustrative)

The repository has no recorded Stage 11 aggregate agent-minutes per accepted result. Assume **40 aggregate agent-minutes** previously and **16 minutes** after integrated jobs (60% saved). Savings: **338 agent-hours per 844**, **1,344 per 3,359**, **5,989 per 14,972 comparable future results**. Six fully concurrent agents would realize the middle saved work as ~224 elapsed processing hours if parallelizable, or ~28 six-agent days at eight productive hours per agent. These are not measured elapsed times.

Engineering/real-data integration allowance: **5–12 calendar days** with six cooperating agents, plus machine indexing time from hours to several days depending on data volume, site limits and OCR. Reserve **2–4 million implementation tokens**, with 2.5M central. Independent human legal review is separately necessary: illustrative 10–30 minutes per already source-prepared dossier equals **560–1,680 reviewer-hours for 3,359**, often higher for archival and complex savings questions.

## Specific failure modes / controls

- Do not let automatic source-ladder network failures silently populate `EXHAUSTED.jsonl` as a certified exhausted investigation: distinguish a bounded attempted route from a genuine reviewed search-limit determination. The readiness tracker currently treats exhausted steps as done.
- Merely downloading a candidate PDF does not establish its pages contain the exact EO, the complete original operative footprint, or later legal effect.
- A section parser may not identify all operative clauses; later formal revocation can be later than first cessation; a current Code/CFR cross-reference may be only contextual; Opus media are stored in shared shards and cannot be assigned to all 844 cases by directory.
- Continue to preserve the **zero** independently human-certified lifecycle numerator until the legal claim and reviewer gates pass.
- To calibrate these forecasts, pilot 40–80 varied cases across 1937+ and early/unpublished orders. Instrument LLM input/output tokens, wall-clock elapsed time, source attempts, court/primary authority links, retrieval successes, corrected machine clause inventories, effective-ending errors, savings errors and human-review time. Report median and p90 by family; sample before scaling.
