# Formulario: a checked library of lifecycle lemmas, and the documents that prove them

Named for Giuseppe Peano's *Formulario mathematico* (1895–1908), the first attempt to write every known theorem in
one formal notation, each with its source. It is the ancestor of Lean's mathlib.

**The idea.** A dossier is a theorem about one order: what it did, what ended it or keeps it in force, and what
was saved. Today each producer re-reads whole documents to prove every step. That is part of why an attempted
order costs about 751,000 tokens of context (Bentham, 2026-11-06). Formulario breaks lifecycle facts into small,
named, reusable **lemmas**, each with a proof term. A producer then imports one checked span instead of reading a
document.

| Lean | Formulario |
|---|---|
| axiom | a source document (statute, proclamation, reorganization plan, treaty, court decision, Attorney General or OLC opinion, official finding aid), retained as bytes in `output/raw/` |
| lemma | one atomic statement: subject instrument, relation (`revokes`, `terminates`, `abolishes_agency`, `continues`, `interprets`, …), the orders it names, date |
| proof term | source URL + SHA-256 of retained bytes + text path and its SHA-256 + the exact character span of the words that state it |
| kernel | a small mechanical checker (see below); nothing else can mark a lemma `proved` |
| `sorry` | an unproved lemma, with the reason (no retained bytes, quote not found, other instrument not named, …) |
| general theorem | a **class lemma**: one instrument that ends or confirms a whole class in its own words (e.g. the 1947 joint resolution terminating war powers) |
| `exact?` | `formulario.py exact EO:N --goal end`: the lemmas that close that goal for that order |
| `import` / `.olean` cache | sharded, gzipped, pre-built lemma files; a query loads one shard (a few hundred KB), never the library |
| tactic | when an axiom's own URL fails, the shared web-search engines look for another official copy, and the kernel runs again |

## The kernel (what `proved` means, exactly)

A lemma is `proved` only when all of these hold:

1. **The bytes are retained.** The source's bytes are committed in this repository, either Formulario's own
   `output/raw/` (listed in `output/SOURCES.jsonl`) or another job's retained text, with their SHA-256.
2. **The quote is in the text.** The quoted words are found in the text of those bytes by a
   normalization-tolerant exact match:
   - tier `spaced` ignores case, quote-mark and dash styles, and whitespace, and joins words broken across lines;
   - tier `alnum` compares letters and digits only, which covers OCR spacing.
3. **The quote is in the right record.** For a Federal Register disposition note, the quote must fall inside the
   record of the order the note is attached to, not merely somewhere on the 1,000-record page.
4. **The other instrument is named.** The quote must name the other instrument by its number(s): `EO 7234`,
   `PLO 936`, `Pub. L. 95-495`, `51 FR 2353`. For an agent-found instance axiom, every named target must appear
   within 1,500 characters of the quote.

**A `proved` lemma is a checked quotation, and that is all.** It is not a legal finding, an identity
authentication, a readiness step or a human certification. The certified count stays 0. Whether a class lemma
reaches a particular order is legal judgment, so `exact` lists class lemmas as *candidates* next to the order's
Pothier family, never as proved for that order.

## What it holds (sources of lemmas)

1. **Axioms** (`axioms/*.jsonl`). These are definitive non-order documents found by the 2026-11-06 axiom sweep:
   eight sonnet researchers, one per family, plus an opus completeness critic. That is 41 axioms after the
   critic's corrections (18 were dropped and 13 recoded or annotated; see each `critic_note`). The families:
   - war and emergency termination (1921 resolutions, 1947 war-powers resolution, Proclamation 2974, NEA §101);
   - territorial transfer (Philippine independence, Panama Canal Act 1979, Hawaii and Guam acts);
   - agency abolition and reorganization (Reorganization Plans of 1939, 1953, 1970 and 1978; the NIRA's end);
   - civil-service supersession (CSRA 1978 §902, Classification Act 1949);
   - public-land withdrawals (FLPMA §§ 701(c), 704(a));
   - judicial holdings (Youngstown, Dames & Moore, Panama Refining, Schechter, Endo, and others);
   - interpretive authorities (Attorney General and OLC opinions);
   - official finding aids.

   An agent's word is never trusted: each axiom is `sorry` until the kernel finds its quote in bytes the job
   fetched and kept.
2. **Later-events edges.** The 23,858 edges of `jobs/later-events` become lemmas, proved from the order texts
   other jobs retain (FR originals, APP and Opus texts). For disposition notes, they are proved from Formulario's
   own retained copy of the seven Federal Register API pages the notes came from: about 4 MB, now checkable
   offline by any session.
3. **Open goals** (`catalog/WANTED.jsonl`). 15 instruments the critic named as missing, such as the Indian
   Reorganization Act, the Engle Act, Proclamation 4417, Ludecke v. Watkins and the 1946 Philippine treaty. They
   become lemmas when someone adds an exact quote to `axioms/`.
4. **Bulk catalog** (`catalog/BULK_SOURCES.jsonl`). 27 bulk collections, each noting whether an existing job
   already harvests it, for future zero-token adapters.

## Use it

```bash
python3 -I jobs/peano-formulario/formulario.py exact EO:2040 --goal end
```

```bash
python3 -I jobs/peano-formulario/formulario.py supplement F-1a2b3c4d5e6f
```

- `exact` prints the instance lemmas that name the order, proved first, then the class candidates for its
  families. `--json` gives full records. `--goal basis` asks what keeps an order in force.
- `supplement` prints claim-kit source-excerpt entries (`jobs/claim-kit/source_supplement.py`) for proved lemmas:
  source, text path and SHA-256, and char span. Add `alias` and `actor_id`, then declare as usual. The excerpt
  then goes through the claim kit's ordinary source checks and independent review.

**Wiring.** Retained bytes are listed in `output/SOURCES.jsonl`, the shared record format the claim checker
already reads (`jobs/claim-checker/sources.py` globs `jobs/*/output/SOURCES.jsonl`). A claim that cites one of
these documents is checkable with `job_cache` custody and no code change. Nothing is pushed into dossiers:
producers pull what they need, so packets do not grow.

## Outputs (`output/`)

| File | What |
|---|---|
| `lemmas/EO_<band>.jsonl.gz` | Instance lemmas whose objects fall in the band of 500 order numbers; sorted, proved first |
| `lemmas/CLASS.jsonl.gz` | Class lemmas (general theorems) |
| `FAMILIES.json` | Order → Pothier families (the doctrines' `x1_type` membership rules over `jobs/x1-class-engine`) |
| `INDEX.json` | Counts by status, kind, relation and origin; `sorry` reasons; orders with a proved end lemma; tactic results |
| `SORRY.csv` | Unproved axiom lemmas and why: the work list |
| `SOURCES.jsonl`, `raw/`, `texts/` | Retained documents (only those that prove at least one lemma), their texts and hashes |
| `TACTICS.jsonl`, `PAID_SEARCH.json` | Every search-tactic query, and the paid-query ledger |

## Cost

Zero model tokens per run. It runs daily, and after later-events and x1-class-engine.

**Fetching.** Retained documents carry forward from `JOB_PRIOR_OUTPUT_DIR`, so a document is fetched once. New
fetches are bounded by `FORMULARIO_MAX_FETCHES` (400) and `FORMULARIO_MAX_MB` (600). They go through
`jobs/_lib/fetch_pool.py`, which follows robots.txt and paces 0.5 s per host, two per host at a time.

**The search tactic.** It tries at most `FORMULARIO_TACTIC_LEMMAS` (40) lemmas and `FORMULARIO_TACTIC_REQUESTS`
(160) requests per run, using whatever engines `jobs/_lib/eo_websearch.py` finds ready. Free engines go first.
Paid engines, Brave's API among them, are asked only when the free ones found no official-host candidate. Paid
use stays within `FORMULARIO_PAID_PER_RUN` (20) and the project's shared lifetime caps.

## Adding to it

Add one line to an `axioms/<family>.jsonl` file. Required fields:
- `axiom_id` and `instrument`;
- `instrument_kind`, `date` and a direct `url` to the official or public-domain copy;
- a verbatim `quote` of at most 400 characters;
- a `relation`;
- `targets_named` (only the orders the document names) and `class_scope` (the class in the document's own words);
- `census_families_hint`.

The next run fetches, retains and checks it. To add a bulk source, write an adapter that emits the same lemma
records; the kernel and the index are shared.

## Not yet

- **Sources from other jobs:** Selden, current-law, Theophilus and Shepard edges. Their formats differ; each needs
  a small adapter like `build_later_events`.
- **Brave:** on GitHub's runner, `brave_api` is ready (the project's `BRAVE_SEARCH_KEY` is set). The first run
  sent one paid Brave query, within the caps, and that search proved one more axiom. In this container and in
  Lewis's earlier run, Brave was refused under robots.txt; the shared library defers a refused engine for the run.
