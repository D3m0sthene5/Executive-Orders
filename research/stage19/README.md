# Stage 19 — lifecycle and early-source excavators

The [design funnel](FUNNEL.md) records ten definitionally different approaches to each task and the selected features **before** the tools were built. These are research accelerators, not autonomous legal adjudicators. All outputs use the Stage 17 working bibliography and the complete Opus reconciliation as frozen inputs.

## Lifecycle excavator

[`code/lifecycle_excavator.py`](code/lifecycle_excavator.py) reads the restored Stage 17 SQLite and [`DECIDED_CASE_COMPLETENESS_RECONCILED.csv`](../progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv), then writes:

| Output | Use |
|---|---|
| [`CAUSAL_QUEUE.csv`](output/CAUSAL_QUEUE.csv) | All 3,359 provisionally decided identities; blocker codes, evidence counts, transparent opportunity ranking, and five triage lanes. Score is **not** legal confidence. |
| [`REVIEW_PACKETS.jsonl`](output/REVIEW_PACKETS.jsonl) | 80 stratified packets containing existing scoped claims, legal events, relationship leads, source observations, raw Stage 11 material where present, and source entry points where available. |
| [`REVIEW_WORKBENCH.html`](output/REVIEW_WORKBENCH.html) | Searchable local packet browser and exportable researcher worksheet. Export is a proposal, not a certification. |
| [`PROGRESS.json`](output/PROGRESS.json) | Reproducible headline, secondary provisional-label count, source hashes, and unassessed remainder. |

The default packet mix spans early historical (15), contradiction (16), relationship-rich (20), existing scoped pilot (13), and unmapped (16). Seventy-three packets have at least one source entry point (which may be an editorial catalog or relationship lead); seven explicitly need source acquisition. Fourteen Stage 18 cases have locally preserved official printed pages linked from packets. A provision sunset, graph edge, raw AI assessment, or Opus YES/NO label is insufficient for a whole-order result.

Run from the repository root, replacing the database path with the independently restored Stage 17 canonical SQLite:

```sh
python research/stage19/code/lifecycle_excavator.py --db PATH_TO_STAGE17_CANONICAL.sqlite --out research/stage19/output --max-packets 80
```

Optionally pass `--claims PATH_TO_CLAIMS.jsonl --reviews PATH_TO_REVIEWS.jsonl`. [`CLAIM_SCHEMA.md`](CLAIM_SCHEMA.md) explains the two gates. The published release contains no qualifying whole-lifecycle claims or independent whole-order reviews, so the documented complete numerator is **0/14,972**. This is a lower bound on *documented, reviewed work*, not a claim that all other orders are legally unresolved. To reach 25% of this working denominator requires **3,743** qualifying dossiers. The 3,359/14,972 (22.435212%) provisional YES/NO bar remains secondary. The national historical denominator is still unknown.

## Early-source ranger

[`code/early_ranger.py`](code/early_ranger.py) reads 1,023 Lord OCR leads and six curated, still uncounted Stage 18 candidate documents. Only nine inherited leads are dated to the 18th century, so it also creates 12 systematic **survey cells** for 1789–1800 that assert no document identity. It produces 1,041 lead/survey rows, 3,403 different date/topic, recipient/subject, presidential papers, military, land/treaty, printed-ephemera, and congressional-reprint search routes; a [candidate-match file](ranger_output/CANDIDATE_MATCHES.csv); and a [searchable workbench](ranger_output/RANGER_WORKBENCH.html). The six curated entries have located primary historical representations, but none has been admitted to the EO bibliography. Lord dates and excerpts are explicitly unverified and may be paired with a neighboring scan line. Presidential names are used as query hints only when a curated source supplies one; the tool does not infer the signer from the year.

Default operation creates routes without network access:

```sh
python research/stage19/code/early_ranger.py --out research/stage19/ranger_output
```

An optional, bounded LOC Catalog search preserves exact response bytes by SHA-256 and marks every returned row `search_hit_not_authenticated`:

```sh
python research/stage19/code/early_ranger.py --out research/stage19/ranger_output --fetch --max-requests 10 --delay-seconds 1.5
```

The first two live LOC requests in this environment timed out; [the trial record](LOC_LIVE_TRIAL.json) has 2 attempts, 0 successes. Thus the published ranger demonstrates route generation and the six already located representations, **not** new live catalog retrieval. The [LOC JSON search documentation](https://www.loc.gov/apis/json-and-yaml/requests/parameters/) specifies the query parameters. The [NARA Catalog API documentation](https://github.com/usnationalarchives/Catalog-API/blob/master/README.md) requires an API key, so the ranger supplies NARA search links for a person instead of pretending to run that API.

The next scientific test is a stratified human inspection of candidate *hits and misses*, including same-day document splits, autograph versus “by command” attribution, and whether a catalog item is a contemporary representation or a later transcription. No search route or hit changes the 14,972 denominator automatically. An offline archival scan may eventually be needed for some cases, but these online routes should be exhausted and logged before concluding a document is unavailable online.

## Checks and limits

`python research/stage19/code/test_excavators.py` covers claim and review gates, stale fingerprints, noncertifying worksheet export, lead isolation, and a mocked/cached LOC response. Structural checks only ensure specified fields and provenance references are present. They do **not** independently verify source content, completeness of clause inventory, or the legal conclusion; those remain human research and review tasks. The planning windows and remaining effort are in the [moving tracker](../progress/README.md).
