# Source boundaries: a demonstrated repair opportunity

We identified and repaired a repeatable input-assembly defect. This is stronger
evidence than the earlier sequencing experiment: it identifies an actual wrong
operation, affected selected inputs and an existing component that fixes it.
It still does not establish a large reduction in total remaining campaign hours.

## What went wrong

The Federal Register locator found the correct pages, often labeled high
confidence. Those pages contain several documents. `clause-drafts` already
locates early orders by their bare EXECUTIVE ORDER heading and closing
`[No. NNNN]` line, and its four corresponding draft inventories contain better
target text, with explicit OCR warnings.

Claim-kit chooses a held text representation and independently segments it;
it does not simply inherit that clause inventory. Its extent finder understood
numbered headings but not this early closing-number format. With no numbered
heading, it started at offset zero and could stop at a preceding document's
signature. The resulting source hash was genuine while the selected command
belonged to a different document. EO8123 received Florence Lake/EO8119 text,
EO8126 Lake Oliver/EO8124 text, and EO8992 EO8991 weather commands.

EO8083 had a second problem: a rule meant to skip an authority preamble before
numbered sections instead skipped the retirement extension before a wrapped
internal `(d)` reference. Fixing the document boundary alone did not fix that
omission. The independently tested failed minimal alternative is preserved.

## How far this reaches

The frozen read-only screen covered 6,497 available FR order texts. The existing
locator recognizes closing-number extents in 894 of them (EO7532–9097). Compared
with those extents, old inventories are disjoint in 517 cases, extend outside in
75, and lie inside in 302. These are mechanical discrepancy strata, not 592
independently verified errors. An inside span can still omit commands or contain
page furniture.

The current readiness snapshot marks 503 disjoint and 75 outside cases unfinished.
Replaying the actual recorded representation-ranking rule confirms that **501 of
those disjoint cases use this exact FR text as their selected representation**;
90 have provisional statuses and 411 are undecided. Another 74 selected unfinished
representations extend outside. These counts are not unowned assignments or new
ready orders, and the published tracker predates PR64's five new proposals.

Eight fixed random discrepancy cases, excluding the four known cases, were all
confirmed against primary page images to contain the wrong document in the old
inventory. The patched inventory reaches the target commands in all eight.
Eight fixed inside-span cases were also inspected; no newly missing target
command was observed. Their OCR and segmentation are not thereby certified.
EO8930 still includes quoted convention material and publication furniture.
The discrepancy sample is stratified and small: it cannot establish a precise
error prevalence or justify multiplying the sample's defect rate across the corpus.

## The modular repair

Claim-kit now reuses `clause-drafts`' existing locator for the early closing-number
format. Numbered modern behavior remains unchanged. Intervening numbered headings,
including OCR-spaced, No.-prefixed and split-line variants, refuse the new binding.
For this early format only, the preamble-skipping formula must immediately precede
the apparent clause marker; it cannot erase an intervening command.

The same corrected extent bounds the existing own-terms and change-mention
excavators. No new downloader, source store, legal classifier or scheduler is
introduced. Exact raw Unicode offsets, source bytes and explicit inventory/page
confirmation requirements remain. Legacy-parser cautions reach the dossier's
existing missing-items list and readable packet. The external locator participates
in persistent-cache invalidation, compiler fingerprints and runner dependencies.

The bounded replay changes 598 of 894 inventories and leaves 296 unchanged. All
581 changed selected unfinished representations remain within the matched target
extent (501 disjoint, 74 outside, six inside/truncated leads). This is not 581
completed or certified inventories. The replay also retains changed own-term and
mention leads; those are research leads, not newly accepted legal findings.

Two source problems remain explicit: EO8220 has an interposed EO8219 footnote;
EO8729 retains contents/publication text across a page break. The repair does not
solve OCR transcription, operative-clause interpretation, legal endings, source
discovery, review or early/unnumbered census recovery.

## Actual task comparison

Two fresh independent OpenAI producer contexts each completed the same two
original-inventory tasks, with counterbalanced old/patched starting drafts and
the same primary sources. The cases were the first two frozen discrepancy-sample
entries, not selected after observing task costs. Each worker had a 300-second
budget. A separate same-family source reviewer evaluated four exact cards with
arm and worker labels/timing withheld; the reviewer reused prior source familiarity.
All four covered both printed commands. EO8220's disclosed footnote limit remains.
No substantive correction was requested. There were no planted controls in this
focused task comparison; engineering refusal probes are separate.

Recorded case production was 103.286 seconds with old drafts and 63.821 seconds
with patched drafts: a 39.465-second difference across two paired orders. One pair
was slightly slower with the patch. These are small, descriptive observations,
not a reliable causal or population estimate. Producer occupancy totaled 276.866
seconds including shared work. Independent review added 109.433 seconds. Shared
setup/finalization is not cleanly assigned by arm; one review interval also contains
cross-card report/seal drafting. Consequently **no end-to-end hours or token saving
is established**, even for this small inventory task. Full lifecycle research was
not repeated or completed by this test.

## Validation, sources and costs

The final claim-kit suite passes all 391 tests, including real-source regressions,
exact offsets, preceding-signature isolation and intervening-heading refusal.
Independent engineering review pins the exact code; a final metadata-only recheck
is separate from the original sealed verdict. The old screen reproduces byte-exactly
from pinned base899671f. Existing generated outputs, claims, statuses, census,
reservations, codebook and source-audit holds were not rewritten. The current full
compiled corpus remains the old generation: the patch applies on recompilation,
and undecided compiler freshness checks require that rebuild. This PR is unmerged.

All 16 sample primary PDFs were obtained through the unchanged queued retention
job and exact expected hashes: 17 HTTP requests, 82,490,962 downloaded bytes,
193.027 machine seconds. One exact raw version was already published. The 15 new
versions and 16 selected-page text artifacts use the existing retention store;
16 empty-identity source records append after the preserved 203-row prefix.
This does not grant identity approval or change source grades. Native default
REQUESTS/SUMMARY remain unchanged. Acquisition execution metadata and a restoration
map preserve the separate bounded run. PNGs/cache files are intermediate; raw PDFs
and page references permit inspection. No redundant remote acquisition was launched.

Machine timers overlap worker intervals and are not added again as agent labor.
EFFORT.json records observed coordinator, producer and reviewer occupancy and its
coverage limits. Initial setup before the prospective root marker is unmeasured;
active labor, complete tokens/cache/cash and campaign payback are unavailable.
The publication extension brings observed worker occupancy to **45.7 minutes**,
with those coverage limits and the last small receipt/PR operations excluded.
Failures are retained in FAILURES.json and earlier test logs: an initially overbroad
preamble change, incomplete sparse test hydration, failed proxy clone, the locator-only
8083 omission, a synthetic boundary expectation, and a post-write reporting exception.

## Judgment

This is a concrete repair worth integrating because it prevents known wrong-document
research inputs across a substantial, enumerated early-FR group. It does not yet
qualify as the project's major hours-saving change. Keep the distinction: automated
removal of a demonstrated reconstruction task is supported; a large campaign saving
is not. On later normal production, record remaining reconstruction and downstream
corrections before deciding whether to expand this intervention. Do not commission
another general reconciliation system from these counts alone.

Reproduce with a checkout holding the recorded inputs:

```sh
python -B research/excavator/source-boundary-audit-2026-10-26/screen.py /tmp/eo-boundary-screen
python -B research/excavator/source-boundary-audit-2026-10-26/replay.py
python -B research/excavator/source-boundary-audit-2026-10-26/verify.py
python -B -m unittest discover -s jobs/claim-kit -p 'test_*.py'
```
