# Cruden: the 1936-1993 Federal Register and the Statutes at Large, searched by executive-order number

Named for Alexander Cruden, whose *Complete Concordance* (1737) listed every place each word of the Bible appears.
This job does the same for an order's number. Zero model tokens.

**Why.** Of the 4,174 undecided orders with no ending or current-law lead, 2,818 are named by no held finding aid
with an ending word about them (`jobs/linnaeus-types`; 388 of those are named without one, by an amendment or a cross
reference). `selden-fr-citers` searches the Federal Register's full text only from 1994
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
3. **Identity** (`cruden-locate-3`, after two passes of the 2026-11-10 hostile review). A sentence is tied to the target by the
   printed number. It is published with its printed relation only when some citation of the target in it prints an
   attached date (`of`, `dated`, `approved`, `signed`, or the contents form `, Oct. 30, 1929`; a later `effective`
   date, an FR citation's date or an act's date is not read as the order's) equal to the target's own date (domesday-register, OFR catalog, then the Lord 1944 WPA list's month-day for numbered orders they lack). The scan's
   OCR often interleaves the page's three columns ('of February [other column] 24, 1913'): such a split date counts only
   when it reassembles into exactly the target's date, never as a disagreement. With no known target date the
   sentence is a pointer only
   **Refused** (kept in `LOCATED.csv`, never published): the printed dates all
   disagree; the number runs on into digits (`1085 6`, `1,885`), sits inside a longer number (`10,885`; a list such
   as `Nos. 1884, 1885` is not) or carries an attached letter or fraction the target lacks (`2656A`, `2656-A`,
   `2656½`); another issuer is printed with it, before or after,
   without a matching date (Governor's, Canal Zone, Philippine, `of the State of ...`, `of the Military Governor`);
   the citation lies inside the order's own printing (its heading or `[No. N]` tag, or a line starting with its
   number, with no relation word governing it, in an issue within 45 days of it); the bytes are neither committed
   nor a GPO PREMIS match. **Pointer only** (`cross_reference`): no matching printed date; a
   contents or index entry (leader dots to a page number); an exception or savings sentence (`except`, `but not so
   as to affect`, `does not revoke`, `nothing in this`); a capital letter after a space (`2656 A`); `by his` or `its`
   with no issuer named earlier in the sentence. The FR search starts the
   day after the order's date.
4. **Acting instrument.** Named only when the citation lies inside that instrument's own printed span: the nearest
   standalone heading line before it (`[Public Land Order 945]`, `PUBLIC LAND ORDER 2100`, `EXECUTIVE ORDER 10524`,
   `PROCLAMATION 2600`, or the 1936-37 `[No. 7500]` tag), at most 6,000 characters before, with no filing line
   (strict, or damaged but carrying `Filed, <date>` or a filing time) and no new document's agency header
   (`BUREAU OF RECLAMATION`, `DEPARTMENT OF AGRICULTURE`, `Forest Service`, `TITLE 43`) between, whose previous line
   does not run on into it (`... AND`, `Prior orders:`), and which is not the target itself. The previous page is read for the
   heading. Otherwise the page is the actor, as `NOTICE:<package>/p<page>`, flagged `acting_instrument_not_identified`.
5. **Custody.** For a Federal Register issue the whole PDF is hashed and compared with the SHA-256 GPO publishes in
   the package's PREMIS record (`gpo_premis_match`); a pypdf extract of the cited page is committed
   (`captures/<sha256>.pdf`, at most 1.5 MB each and 80 MB a run). A Statutes page granule is committed whole. The
   OCR text of the cited page (with its neighbours) is in `texts/`, named by and recorded with its own sha256
   (`text_sha256`, written with LF line ends), so each `quote_span` points into pinned bytes; the text tool and its
   version are recorded. A citation whose bytes are neither committed nor a GPO PREMIS match is refused. Each issue's records are published together at the end of its processing, so a failure leaves none.

**Silence.** An order with no hit, or with hits but no acting sentence, gets a `SEARCHES.jsonl` record and nothing
else. A concordance's silence is never evidence that nothing acted on an order (D-20261028-evidence-decides).

**Planted controls, every run.** Positives: 30 pre-1937 orders that BLM's PLO table (independent of the OCR) names
by number with an ending word in a PLO printed by 1993, outside the target set; a positive counts as found only with
its matching printed date, their units are read again every run, and their fragments are never published. Negatives:
near-miss numbers and another positive's target in each control text (Selden's `run_controls`), and 12 fixed identity
negatives (other issuers, split and suffixed numbers, a disagreeing date, an exception sentence, an order's own
printing). The run passes only with recall of at least 0.6 (dated location), at least 0.4 of the positives
published as acting (so over-broad pointer rules show), no false location and no identity negative published as
acting. A failed run writes every fragment as `cross_reference`, and the next run carries none of its pages or
fragments forward: it reads every hit again.

| Output | Contents |
|---|---|
| `FRAGMENTS.jsonl` | `later_event_candidates` (claim-kit shape): acting id, target, printed relation, qualifier, exact `quote` and `quote_span` into `texts/`, `date_matches_target`, flags; `date_candidate` is the issue's publication date, flagged `publication_date_not_instrument_date` |
| `SOURCES.jsonl` | Shared source records; `instrument_ids` lists the page id first, so a page never reads as an order's own text |
| `SEARCHES.jsonl` | One record per (order, collection): query, count, hits, response sha256, `complete` |
| `LOCATED.csv` | Every citation found, including refused ones and the reason |
| `CONTROLS.json`, `SUMMARY.json`, `FAILURES.jsonl` | Controls; yields by collection and by family (`queried` means govinfo was asked, not that the order is covered); failures |

**Running.** By hand only (`gh workflow run run-jobs.yml --ref <branch> -f job=cruden-fr-concordance -f only=true`),
after `linnaeus-types` has run; its inputs are declared in `inputs.txt`, not `after.txt`, so an upstream change
does not start a multi-hour search by itself. Each run carries forward earlier searches whose query is unchanged.
It carries pages, fragments and sources only when the earlier run used the same locator and passed its controls,
and only after re-hashing every text and committed PDF; anything that fails is read again. A query with more hits
than the cap (40 FR issues, 20 Statutes pages) keeps the earliest and the latest halves and is marked
`complete: false`; such queries are not asked again. Lists such as `Executive Orders Nos. 1884 and 1885` are not
queried. Budgets: `JOB_MAX_SEARCHES` (6,000; 25 with DEMO_KEY; govinfo reports 36,000 an hour), `CRUDEN_SEARCH_INTERVAL` (0.25 s),
`JOB_MAX_PACKAGES` (1,500), `JOB_MAX_DOWNLOAD_GB` (25), `JOB_TIME_BUDGET_MIN` (280), `CRUDEN_COLLECTIONS` (`FR,STATUTE`).

**Limits.** Leads only. govinfo's index and the scan's OCR decide what is found. A located sentence says what a later
document prints, not that it ended or changed the order, in whole, or on that date. Merging registers the output with
the claim kit (it reads every `FRAGMENTS*.jsonl`); that waits for the owner. No status, census, codebook or count
changes. Human-certified: 0.

Tests: `python -I jobs/cruden-fr-concordance/test_cruden.py` (offline, fake govinfo).
