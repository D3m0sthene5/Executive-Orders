# Nihil obstat: the human certifier page

Named for the censor's certificate that nothing stands in the way. The project files machine-checked claims about each
executive order's legal lifecycle; blind AI reviewers must uphold each claim's exact hash; independent humans certify
last. This folder is the human step: a static page, an exporter that builds the cards it reads, a reliability
calculator, and a recruiting plan. **It changes no count.** The certified count stays 0 until the owner's importer
records reviews (`research/stage19/CLAIM_SCHEMA.md`).

## Run it locally

1. Export cards from a repository checkout (Python 3, standard library only):

   ```
   py -I export_cards.py PATH_TO_REPO --ids EO:10863 EO:12598 --out my_cards
   py -I export_cards.py PATH_TO_REPO --git-ref origin/main --ids EO:8123 --out my_cards   # no checkout needed
   py -I export_cards.py PATH_TO_REPO --git-ref origin/main --list-ready 20                 # ready orders with review counts
   ```

   Add `--copy-originals` to copy committed original PDFs into `my_cards/sources/<sha256>.pdf` for the page's folder
   picker (they are too big to embed). Without `--allow-not-ready` the exporter refuses orders the tracker has not
   marked `ready_for_human_review=yes`, and it refuses a claim whose recomputed SHA-256 differs from the one the
   claim checker recorded.
2. Open `index.html` in a browser (double-click it; no server, no network). Choose the export folder, enter your name,
   and work through the cards. To verify an original, attach the PDF (or drop the whole folder including `sources/`);
   the page hashes it and matches it by SHA-256.
3. Press **Export decisions (JSONL)** and send the file back. **Resume from decisions file** reloads one.

The five example cards in `example_cards/` can be opened right away (`Choose export folder` and pick `example_cards`).
They are real filed claims (EO 8123, 10104, 10863, 11219, 12598), public government text only, 813,527 bytes in all.

## What the page shows for each claim

* The claim's SHA-256, recomputed in the browser (canonical JSON identical to `claim_gate.claim_sha`); a red box if the
  card's claim does not hash to the hash it is filed under.
* Checker results: the claim checker's per-step results, check counts and every row that did not pass.
* Every AI review record that names the exact claim hash: reviewer, model family, phase (blind / after reveal /
  correction), verdict, defects, reasoning and evidence checked, plus an information-only line against the campaign
  rule "two blind AI reviewers must uphold the exact claim hash".
* Sources: for each cited source its URL, page, grade, the claimed SHA-256 of the original file, and two separate
  hash checks (below).
* For each part of the claim (original text and identity, each operative clause, whole-order status and end, savings,
  later-source search) the claim's own fields, every quoted span next to the source bytes it was checked against with
  the span highlighted **by UTF-8 byte offsets** into the hash-verified text, and a certify / reject / needs-more
  choice with a reason. "Open whole source text" shows the full text with every span marked.
* An overall decision. Certify is only possible when every part is certified, no hash is red, the reviewer declared
  independence and attested to reading the cited pages of the originals.

## What "verified" means here (read this)

A source has two hashes and they are different things:

| Check | Meaning | Where a red or amber state comes from |
|---|---|---|
| **Text layer** | SHA-256 of the saved text embedded in the card, recomputed in the browser, equals the `text_sha256` the claim recorded for it. The quoted spans are located in this text; their bytes are compared to the quotation. | **Red** if the text differs from the claim's hash (or from the export manifest), or a span's bytes differ from its quotation. **Amber** if the claim recorded no hash and only the export manifest vouches for the text. |
| **Original** | SHA-256 of the original file (usually a Federal Register PDF) equals the claim's `sha256`. The card cannot carry multi-megabyte PDFs, so you attach the file. | **Red** if an attached file has a different hash. **Amber** while no file is attached. |

The text layer is what the checker matched quotations against (OCR or an extraction of the PDF). A matching text hash
shows the text is the text the checker used and that nothing was altered since; it does not show that the extraction is
a faithful transcription of the page. Reading the original page is the certifier's job, which is why certify requires
that attestation. Hashing uses `crypto.subtle` (SHA-256) and falls back to a pure-JavaScript SHA-256 where that is
unavailable; the engine is named on the page and in every decision record.

## Decision records

`eo-nihil-obstat-decision/v1`, one JSON object per line: reviewer name and independence declaration, UTC time,
`claim_sha256`, `card_file_sha256`, `page_version`, hash engine, overall decision, per-element decision and reason,
notes, the read-the-originals attestation, each source's text-layer and original status at that moment, the AI
review ids the reviewer saw, `active_seconds`, and `record_sha256` (hash of the rest of the record). A certify with
independence declared also carries `lifecycle_review_draft`, shaped like the `eo-lifecycle-review/v1` object in
`research/stage19/CLAIM_SCHEMA.md`, for the owner's importer to validate. It is a draft; the page imports nothing.

## Reliability

`alpha.py` computes Krippendorff's alpha (nominal) for two or more certifiers over the exported decisions, overall or
per element, with missing data, a bootstrap interval and page-time statistics:

```
py -I alpha.py alice.jsonl bob.jsonl --bootstrap 2000 --seed 1
```

## Tests

| Command | What | Count |
|---|---|---|
| `py -I tests/test_export_cards.py` | exporter on a synthetic repository (filesystem and git modes), offset mapping, refusals, and the five committed cards | 11 |
| `py -I tests/test_alpha.py` | alpha against two published worked examples, hand derivations, and the decision-file reader | 13 |
| `py -I tests/run_js_tests.py` | the page's `core.js` in headless Edge or Chrome: SHA-256 vectors, fallback equals SubtleCrypto, canonical JSON equals Python, byte spans, tamper detection, decision rules (or open `tests/test_core.html` over http) | 36 |

The page itself was also driven in the built-in browser: all five cards load, all 131 quoted spans verify by byte
offset, a real 7.4 MB Federal Register PDF attached from the repository verified as the claim's original, a one-byte
change to it turned the source red, and a certify decision recorded and sealed.

## What it deliberately does not do

* It changes **no count**, no claim, no status, no review file. It never writes to the repository (it cannot: it is a
  static page that only offers downloads).
* It does not import its own decisions. The certified count remains 0 until the owner's importer records reviews.
* It does not decide anything for the certifier: the AI review gate is displayed, not enforced, and AI verdicts are
  shown as AI verdicts.
* It does not fetch sources from the network, and it does not call any model.
* It does not prove a transcription faithful to its page, and it does not establish that a source is authentic
  (distinguishing document discovery from identity authentication stays a human, source-by-source judgment).
* It stores nothing off the machine; in-progress work is kept in the browser's local storage as a convenience and
  exported only when the certifier chooses.

## Files

| File | Purpose |
|---|---|
| `index.html`, `style.css`, `app.js`, `core.js` | the page (no build step, no external scripts, fonts or CDNs) |
| `export_cards.py` | builds card JSON from filed claims, sources and review records |
| `alpha.py` | Krippendorff's alpha (nominal) |
| `RECRUITING.md` | plan and budget for recruiting human coders through NYU |
| `example_cards/` | five real example cards and their manifest |
| `tests/` | the tests above |
