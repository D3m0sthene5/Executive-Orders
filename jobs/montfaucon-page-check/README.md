# Montfaucon page-check interface

Code-only consumer. No research checks or generated outputs are supplied here.
`job.py` reads only `research/montfaucon/CHECKS.jsonl` and
`research/montfaucon/checks/*.jsonl`; batch and worklist files are never inputs.
The first two reviewed batches and their control, cost and source receipts
are under `research/montfaucon/` (`REPORT_M001.md` and `REPORT_M002.md`).
The runner publishes derived output on the merge target; a research branch
must not carry its own generated `jobs/*/output/` files into main.
It emits separate official and ProQuest replica fragment files, `OUTCOMES.json`
for all valid pass/fail/unsure outcomes, and a rejection receipt. Only validated final
passes count in the readiness tracker, which revalidates against current inputs.
Source records remain unchanged; model page review never authenticates an
original, verifies its location or confers human review.

Each record has schema `montfaucon-page-check/v1`, `instrument_id`, `lane`
(`official` or `replica`), `final`, `target`, and exactly two `reviews`.
The target contains repository-relative `fragment_path`, `fragment_sha256`
(SHA-256 of canonical JSON: sorted keys, compact separators, UTF-8, no ASCII
escaping), and exact source-data `sha256`, `url`, `page_or_item`, `text_path`,
`text_sha256`. The held text path uses the source fragment directory as its
base, must stay inside the repository and must hash to the pinned value.
`target.page_images` is a nonempty array for passes. Include every page from
the start through the closing, each with held `path` (repository relative),
`sha256`, image `url`, `source_url`, unique `page_or_item`, `cited_scope`, and
`provenance` (`official_government_printing`
or `proquest_replica` for the corresponding lane). Source `sha256` can name a
text layer and is never treated as the scan hash. Both reviews hash this image
pin as part of their exact target. Non-government publications are rejected.
Every image's `source_url` equals the target source URL; `cited_scope` equals
the target's complete `page_or_item` scope. Each image's `page_or_item` identifies
its own page within that scope. Both reviewers explicitly affirm
`image_source_and_page_confirmed=true`: the image URLs identify the cited source
and pages. `cited_pages_confirmed` and `complete_start_and_closing` affirm that
the array covers every required page, with no missing intervening pages. The
target hash covers the full array; every held file is hashed separately. These
coverage and provenance findings require examination, not URL-string inference.

Each review has a distinct nonempty `context_id`, `reviewer`, `evidence`,
`number_seen`, `date_seen`, `signature_seen`, `first_words`, `last_words`,
`verdict=pass`, and `target_sha256` (the same canonical hash over `target`).
Each pass explicitly sets `identity_confirmed`, `complete_start_and_closing`,
`cited_pages_confirmed`, and `wording_compared` to true, and supplies
`substantive_differences=[]`. These are separate recorded examination findings,
not findings inferred from nonempty observation strings.
Two distinct contexts are a required recorded independence boundary; the code
does not claim it can establish how a model context was actually operated.
Use `final=fail` or `unsure` to retain negative outcomes without credit.
Both reviews still pin the held source and text; negative records may omit a
page-image pin where missing images are the reason they cannot pass. Explicitly
record unobserved identity/boundary details as such. Agreeing reviews determine
the final verdict. Any disagreement requires an `adjudicator` object with the
same review fields, exact target hash, and a third distinct context. The final
verdict must equal the adjudicator's verdict. Passing adjudication must affirm
every pass check and no substantive differences. Both original opinions remain
in the record and derived fragment. Without the third review, disagreement is
rejected and earns no credit. An adjudicator is not accepted for an agreeing pair.

Duplicate exact-source records all lose credit, even a pass paired with a
negative: the key pins instrument, lane, fragment path, source SHA, URL and cited
page scope. Separate source witnesses for the same order can coexist, including
a failed witness alongside an independently passing witness. Malformed JSON
blocks the entire assembly. Missing source/text bytes,
changed page/URL/hash, changed reviews and unsafe paths reject the record.
Source fragments are copied only into derived output. Replica credit retains `REPLICA_CHECKED_PROQUEST_BYTES` through the
tracker's existing checked-replica lane. No legal grade or human certification
is inferred from model review. Add code changes before any research results.
Matching top-level/data grades `official_printing` (official lane) and
`archival_replica_checked` (replica lane) are admitted. Other missing grades and lead
grades are rejected; their source identity must first be established through a
separate approved process. An explicit exception admits ungraded legacy FR,
OFR 1974, Isthmian 1911 and Indian Reservations 1912 fragments only from their
exact known official route strings. With both reviews and held image provenance
they emit `official_printing` in the derived output. Existing grades are never
changed in source records. Ungraded FR text SHA pins are checked directly against held text bytes.
The FR exception admits `official/govinfo_fr_issue_pdf`,
`official/govinfo_link_fr`, and `official/ofr_index_pdf_url` only.
Tischendorf `official/ia_fulltext` rows qualify for a new derived
`official_printing` only when their exact source kind is
`government-printed compilation of executive orders` and the source grade
is `machine_read_government_printed_copy` (the legacy data grade may be absent,
but cannot conflict); both page examinations and full held
image provenance are still mandatory. Generic IA fulltext and non-government
publications remain excluded. The source grade and codebook remain unchanged.
One explicit replica recheck exception accepts the existing Photius
`archival_replica_check_failed_or_pending` source grade when the new record sets
`adjudication=new_independent_page_check`, pins a held ProQuest image, and both
independent reviews pass every check. The new derived witness is then graded
`archival_replica_checked`; the earlier failed/pending source record and the
codebook remain unchanged. This never upgrades a government-publication lead.
Rejected records appear in the tracker's `input_problems`. Negative outcomes
are valid job results, not runner failures. The helper `validated_output` is
intended for individual checks; the tracker assembles once per load.
Source fragment files are parsed and indexed once per assembly; the cache is
discarded afterwards so subsequent tracker runs reread current bytes.

This interface gives no Lachmann working-text confirmation, provisional-text
credit or claim/lifecycle approval. Those remain governed by their own gates.

Run focused tests with `python -m unittest discover -s jobs/montfaucon-page-check`.
