# Cruden: the 1936-1993 Federal Register and the Statutes at Large, searched by executive-order number

Named for Alexander Cruden, whose *Complete Concordance* (1737) listed every place each word of the Bible appears.
This job does the same for an order's number. Zero model tokens.

**Why.** Of the 4,174 undecided orders with no ending or current-law lead, 2,697 have no held finding aid that names
them at all (`jobs/linnaeus-types`). `selden-fr-citers` searches the Federal Register's full text only from 1994
(federalregister.gov), and `selden-fr-acting` fetches only pages already named by a known edge. Nothing searched the
1936-1993 Federal Register, or the Statutes at Large, by order number. govinfo's search index covers both.

**Route, per target** (`jobs/linnaeus-types/output/CRUDEN_TARGETS.csv`; one-person civil-service waivers are left to
Ulpian):

1. govinfo search (`api.govinfo.gov/search`, POST; key `API_DATA_GOV_KEY` or `GOVINFO_API_KEY` in the `X-Api-Key`
   header, never in a URL or log): `collection:FR` from the order's date (or 1936-03-14) to 1993-12-31, and
   `collection:STATUTE`, for `"Executive Order No. N"`, `"Executive Order N"`, `"E. O. N"`, `"E.O. N"`. Up to 40 FR
   issues and 20 Statutes pages per order (`complete: false` when more exist).
2. Each issue or page is downloaded once for all the orders that hit it (`jobs/_lib/fetch_pool.py`), its text read
   with pdftotext (pypdf if poppler is missing), and every sentence printing the order's number located with
   `jobs/selden-common` (citation forms, relation words, negation, the order printed as actor).
3. **Identity.** A sentence is tied to the target by the printed number. If any citation of it in the sentence
   prints a date, one must equal the target's own date (domesday-register, OFR catalog); a sentence whose printed
   dates all disagree is refused. A number followed by another issuer ("Executive Order No. 885 of the Governor
   General of the Philippine Islands", territorial governors, the High Commissioner) is refused. Refusals stay in
   `LOCATED.csv` and are never published. A number under 1000 with no printed date is a pointer only (mechanism
   `cross_reference`).
4. **Acting instrument.** The nearest heading before the sentence with no filing line between: `[Public Land Order
   945]`, `PUBLIC LAND ORDER 2100`, `EXECUTIVE ORDER 10524`, `PROCLAMATION 2600` (a title line that prints the
   target's own number is skipped). Otherwise the page is the actor, as `NOTICE:<package>/p<page>`, flagged
   `acting_instrument_not_identified`.
5. **Custody.** For a Federal Register issue the whole PDF is hashed and compared with the SHA-256 GPO publishes in
   the package's PREMIS record (`gpo_premis_match`); only a pypdf extract of the cited pages is committed
   (`captures/<sha256>.pdf`, re-hashable, at most 1.5 MB each and 80 MB a run), with the pages' OCR text in
   `texts/`. Fragments cite the extract.

**Silence.** An order with no hit, or with hits but no acting sentence, gets a `SEARCHES.jsonl` record and nothing
else. A concordance's silence is never evidence that nothing acted on an order (D-20261028-evidence-decides).

**Planted controls, every run.** Positives: 30 pre-1937 orders that BLM's PLO table (independent of the OCR) names
by number with an ending word in a PLO printed by 1993, outside the target set; recall is measured on them, and
their fragments are not published. Negatives: near-miss numbers and another positive's target in each control
text (Selden's `run_controls`). One false location writes every fragment as `cross_reference`.

| Output | Contents |
|---|---|
| `FRAGMENTS.jsonl` | `later_event_candidates` (claim-kit shape): acting id, target, printed relation, qualifier, exact `quote` and `quote_span` into `texts/`, `date_matches_target`, flags; `date_candidate` is the issue's publication date, flagged `publication_date_not_instrument_date` |
| `SOURCES.jsonl` | Shared source records; `instrument_ids` lists the page id first, so a page never reads as an order's own text |
| `SEARCHES.jsonl` | One record per (order, collection): query, count, hits, response sha256, `complete` |
| `LOCATED.csv` | Every citation found, including refused ones and the reason |
| `CONTROLS.json`, `SUMMARY.json`, `FAILURES.jsonl` | Controls; yields by collection and by family; failures |

**Running.** By hand only (`gh workflow run run-jobs.yml --ref <branch> -f job=cruden-fr-concordance -f only=true`),
after `linnaeus-types` has run; its inputs are declared in `inputs.txt`, not `after.txt`, so an upstream change
does not start a multi-hour search by itself. Each run carries forward earlier searches, fragments, texts and
extracts (re-hashed) and continues with the rest. Budgets: `JOB_MAX_SEARCHES` (2,500; 25 with DEMO_KEY),
`JOB_MAX_PACKAGES` (1,500), `JOB_MAX_DOWNLOAD_GB` (12), `JOB_TIME_BUDGET_MIN` (280), `CRUDEN_COLLECTIONS` (`FR,STATUTE`).

**Limits.** Leads only. govinfo's index and the scan's OCR decide what is found. A located sentence says what a later
document prints, not that it ended or changed the order, in whole, or on that date. Merging registers the output with
the claim kit (it reads every `FRAGMENTS*.jsonl`); that waits for the owner. No status, census, codebook or count
changes. Human-certified: 0.

Tests: `python -I jobs/cruden-fr-concordance/test_cruden.py` (offline, fake govinfo).
