# Lightweight repairs and handoffs

Follow-up to the owner's October 29 request: which existing tools could become more useful through small repairs or better wiring, excluding heavy research and new frameworks?

Inspected main `73d99f666573ee10f5b1ff2ada60f7d9331c3952`. These are concrete recommendations, not implemented changes. Three bounded delegated code inspections, a deterministic queue/result join, and one isolated Cotton test reproduction support the findings. No production/acquisition job ran; no source grades, claims, scientific counts or review thresholds changed. Model/token/cash telemetry was unavailable.

## Priority 1: Cotton test environment, then checker ordering

**Very small; highest confidence.** The current failure is a test-environment leak. The runner sets `JOB_PRIOR_OUTPUT_DIR`; Cotton intentionally honors it, but the ordinary committed-bytes test puts its fixture under a different temporary job/output directory without clearing the inherited variable.

Using the exact main Git blobs, the same test fails `0 != 1` when the variable points at an empty temporary directory, and passes when it is removed. Its stub getter makes no network requests. See [the reproduction receipt](COTTON_TEST_REPRODUCTION.json).

Smallest repair: pass a copied environment with only `JOB_PRIOR_OUTPUT_DIR` removed to the test subprocess in `jobs/cotton-capture-custody/job.py`, or isolate it in the test fixture. Preserve the variable for the actual Cotton run and keep the dedicated runner-prior-output test.

Then add `cotton-capture-custody` to `jobs/claim-checker/after.txt`. The checker already reads Cotton's source manifest through its generic loader. Ordering Cotton before checker, then tracker, makes newly saved custody available in the same selected run. An `after.txt` entry orders jobs selected together; it does not mean every output change schedules the whole chain. Current push scheduling ignores ordinary output-only changes.

This restores the ability to run custody acquisition/reuse, not changed live-page hashes or automatic readiness. Daily digest currently also depends on a failing portfolio-repair check (`prior research context missing; prepare a new version`), so Cotton alone cannot clear the entire daily run.

**Correction to the tier assessment:** the observed Cotton stop is now traced to inherited test environment. It did not demonstrate defective runtime reuse.

Primary evidence: [Cotton runtime](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/cotton-capture-custody/cotton.py), [test fixture](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/cotton-capture-custody/test_cotton.py), [test launcher](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/cotton-capture-custody/job.py), [checker ordering](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/claim-checker/after.txt), [blocked digest](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/_attempts/daily-digest/40829686426-1/STATUS.json).

## Priority 2: X1 reads retained event sources and exposes them in its sheets

**Small reader and display patch; no new acquisition.** X1's `events.py::held_sources()` reads only Panizzi's source manifest. Astra retention already holds seven exact registered event-source URLs; five texts satisfy X1's existing phrase screens.

Read the two existing manifests with each producer's own relative paths, retaining URL, raw hash, text hash and representation provenance. Keep the existing checks. Do not overwrite Panizzi's passing Schechter text with the retained narrower excerpt: the two share the same raw-PDF hash, but only Panizzi's selected representation passes the registered phrase screen. The 1921 resolution's retained text also fails its existing phrase screen and must stay visibly unresolved.

Add the retention dependency and show source state plus exact source-record pointers in X1's existing sheets. The sheet builder currently retains only event IDs and discards source state. Merely improving the hidden event table would not make the research handoff useful.

Expected source-state improvement: five previously pending source references become passing, supporting NIRA (496 candidate links), Philippine independence (74) and FLPMA (3,016). These are overlapping candidate links, not unique orders, ready cases or legal conclusions. FLPMA remains explicitly `not_an_end_authority_repeal`.

Claim-kit, case-bundles and checker already discover source manifests generically. No new generic importer is needed. Supporting statutes deliberately have no EO-original `instrument_ids`; never populate them with the requesting EO IDs to force ingestion. A further automatic event-to-dossier integration would be a larger change; use existing sheets and explicit source supplements first.

Primary evidence: [X1 event reader](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/x1-class-engine/events.py), [sheet consumer](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/x1-class-engine/sheets.py), [retained source records](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/astra-source-retention/output/SOURCES.jsonl), [current source states](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/x1-class-engine/output/EVENT_SOURCES_STATE.json).

## Priority 3: Lewis consumes Panizzi's existing queue/result state

**Small status join; zero downloads.** Lewis still generates `fetch_request_proposed` with next action `Enqueue PROPOSED_FETCH_REQUESTS.jsonl`. All 265 current proposals already have matching instrument/step/citation entries in the actual queue.

An exact join to the published Panizzi results finds **115 matching found records and 22 matching not-attempted-budget records**. The remaining 128 lack an exact match in this result generation; do not label them unattempted or exhausted by inference. See [the deterministic join and pins](LEWIS_HANDOFF_AUDIT.json).

Read the existing queue/results before emitting the next action. Distinguish not queued, queued/pending, retrieval recorded awaiting target-page/identity verification, and failed/deferred with reason. Keep stale/mismatched records explicit and preserve source pointers. For found records, route the worker to the existing source receipt/text and the required page/custody checks rather than telling them to enqueue again. A historical found receipt does not guarantee that its raw PDF remains held in the present execution environment.

This turns a misleading route inventory into a more useful work queue. A `found` receipt alone does not prove the excerpt contains the right EO or establish an original grade. Do not automatically reenqueue all proposals or mark 115 orders ready.

Primary evidence: [Lewis routing function](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/lewis-originals/lewis.py), [proposals](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/lewis-originals/output/PROPOSED_FETCH_REQUESTS.jsonl), [actual queue](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/research/readiness/FETCH_QUEUE.jsonl), [Panizzi results](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/source-ladder/output/RESULTS.csv).

## Priority 4: Shepard / FR pages into existing source supplements

**Small bounded handoff using held pages; more involved than a dependency line.** The FR-page service already holds 28 PDF extracts across 30 source rows. Nine high-confidence location rows cover six target EOs; five targets already have provisional statuses.

Begin with three already-held high-confidence extracts: PLO570 and PLO4079 for EO7373, and PLO1249 for EO7510. Use the existing source-supplement interface to attach the PLO acting instrument and exact text to a small ordinary research packet. Preserve the PLO-versus-target-EO distinction, page/hash provenance, and independent review. Both targets are decided, but still have several substantive lifecycle obligations; this handoff does not establish immediate readiness.

The gap is real: source rows may list both a PLO actor and target EOs, while claim-kit correctly refuses to treat such a multi-instrument record as the target EO's original text. Adding `after.txt` or recompiling cannot fix that semantic handoff. A naive dependency from claim-kit to Shepard also creates the existing claim-kit → X1 → Shepard → claim-kit cycle. Use the existing separate discovery/acquisition and fresh-prepare phases.

The bounded Shepard auto-acquisition feature is already implemented but disabled, with a cap of 25. Turning it on is optional later acquisition, not the first fix: useful pages are already held and need to reach a packet. Source-ladder ordering already reaches claim-kit through claim-drafts, so another duplicate dependency adds no benefit.

Primary evidence: [FR-page service](https://github.com/D3m0sthene5/Executive-Orders/tree/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/fr-pages), [claim-kit source supplements](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/claim-kit/source_supplement.py), [claim-kit inputs](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/claim-kit/inputs.py), [prior handoff audit](https://github.com/D3m0sthene5/Executive-Orders/blob/85ff7a5414b0da9394d2e357a5e0cf78a2fe97c3/research/excavator/production-line-audit-2026-10-29/REPORT.md).

## Priority 5: Early Ranger fails visibly instead of publishing an empty success

**Small defensive repair, not historical-research acceleration.** The current metadata run planned 21 items, failed four requests, skipped 17, retrieved zero, and still wrote its empty/current inventory as a successful result. Transcriptions then found zero XML links.

Add an explicit all-provider-failure guard and preserve the last good generation through the runner's existing failure behavior. Distinguish a legitimately empty plan from a nonempty plan whose requests all failed. A zero-metadata downstream run should be visibly blocked, not replace good transcription output with an empty success. Restore prior held artifacts only from their exact published versions, with provenance intact.

This protects earlier useful work and makes failures actionable. It does not solve LOC access, handwriting, issuer identity or historical EO admission.

Primary evidence: [metadata job](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/early-ranger-original-items/job.py), [actual zero-yield metrics](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/early-ranger-original-items/output/METRICS.json), [transcription job](https://github.com/D3m0sthene5/Executive-Orders/blob/73d99f666573ee10f5b1ff2ada60f7d9331c3952/jobs/early-ranger-transcriptions/job.py).

## Keep outside the tiny-fix budget

- **Poggio:** useful 456 saved captures already exist, but branch Cotton lacks main's runner-prior-output support. It needs reconciliation, append-only APP publication and post-backfill verification. Its zero-successor Cotton run predates the backfill, so that zero does not prove failure. Re-citing a changed live source still requires exact new claim review. Small-to-moderate integration, not a one-line merge.
- **Portfolio repair:** a missing qualified prior-research context blocks the latest check. Diagnose the specific fixture/version contract; do not weaken or rebase historical review attestations merely to get a green run.
- **Mansfield, Craigellachie, family certificates:** input selection can improve, but missing legal/source evidence remains substantive work.
- **NORTON, NEYMAN, Junto:** no missing dependency has been demonstrated that supplies absent reusable answers, complete effort observations or a valid savings experiment. Keep existing useful components; a general revival exceeds this scope.

The first three recommendations have the cleanest ratio of small change to demonstrated obstruction. The fourth uses existing held evidence; the fifth prevents regressions. None supports an automatic increase in readiness or a promised campaign-wide savings percentage.
