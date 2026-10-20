# NORTON

NORTON pools exact unresolved factual questions, locates function-succession provisions using
source-bound institution/function aliases, and finds candidate completion receipts in held primary
material. It reuses Panizzi's date parsing and the validated FETCH_QUEUE reader. It never fetches,
decides legal status, writes a claim, certifies a person, or creates a source store.

Run `python -B jobs/norton/job.py` from the repository root. The shared GitHub runner sets
`OUTPUT_DIR`; all generated results go there. Bounds: 250 MB of held text, 5 MB per text,
20 candidate spans per registered question, 1,000 possible-duplicate pairs. Every omitted item
and inaccessible source remains in HOLDS, with possible-pair overflow counted in CENSUS.
There is no daily marker and no expansion beyond the first pilot.

The durable registry lives in `research/readiness/factual/<owner>/`:

| File | Unit and review boundary |
|---|---|
| `questions.jsonl` | Exact entity ID, object/function, scope, interval, proposition and event kind. `question_key` hashes all seven. No fuzzy merge. Preserve `origin: owner_seeded`. |
| `applications.jsonl` | One question's applicability to one exact EO clause; pins the original source span. Sharing an answer never reviews an application. |
| `evidence.jsonl` | Candidate factual evidence with source bytes/hash, text/hash, page/item, exact span, edition, event date/meaning and custody provenance. |
| `answers.jsonl` | Producer factual answer, exact question key and evidence IDs. |
| `reviews.jsonl` | Separate factual reviews pinned to the exact answer or application hash, reviewer identity/type, date, rationale and D6 later-event check. Never a human lifecycle review. |

Each record's `id` is unique within its file type. Replacement proposals receive a new ID;
retain rejected versions and their reviews. Never replace another owner's records. Human acceptance
requires an independent human factual review; an independent AI review is labeled `ai_reviewed`.
For each reviewed application, write substantive separate `checks` for scope, applicability,
earlier cessation, independent commands, and savings. Its `legal_effect` remains `unresolved`.
Missing interpretation proceeds through the established claim-kit decision/review process.

`aliases` on a question are typed institution/function/object strings bound to its entity ID and
an exact held source span (`evidence`). The scanner matches both institution and function/object;
similar agency names alone cannot locate a duty. These are search aids requiring answer review.
An agency's survival or abolition proves no duty's survival or abolition. A function transfer may
be partial; candidate spans preserve exceptions and dates without selecting their legal meaning.
Publication, transmittal, delivery, recurring performance, appointments and transfers have separate
event types. A deadline or report landing page supplies no receipt. Silence proves no nonperformance.

`QUESTION_LEADS` retains machine-extracted obligations from own-term, claim and reviewer records.
Entity-unknown leads remain bound to their original order and clause, so wording cannot join them
across orders. Repeated representations of one clause are not separate investigations.
`POSSIBLE_DUPLICATES` is a bounded review queue; it never changes keys.

`CANDIDATE_EVIDENCE`, `REVIEWED_ANSWERS`, `APPLICATIONS`, `REJECTIONS`, `HOLDS` and `CENSUS`
are separate outputs. Source text and bytes remain at existing producer paths. Sources lacking
original bytes, a correct edition or complete performance coverage remain held. The job emits
`FETCH_QUEUE_PROPOSED`, validates it through source-ladder, and never appends it to the durable queue.
A coordinator must append requests within the existing research workflow; acquisition failures
remain source holds, never exhaustion declarations.

`FRAGMENTS` uses the shared fragment envelope and the new minimal kind
`shared_factual_obligations`. Claim-kit exposes it under the dossier's same-named field and pins
it in the dossier fingerprint. It is excluded from legal events, current predicates, original
representations and automatic assembly. Changed inputs or failed runs refuse ingestion. Existing
case-bundles retain the attributed generic fragments. Claim-checker/tracker continue their own
rules. Run consumers explicitly; output-only result commits do not trigger them.

The own-term census reads claim-kit's previous generation. Its exact hashes stay in
`lagged_census_sha256`; claim-kit necessarily clears those files before rebuilding. The consumer
validates `consumer_sha256` instead: the live registry, source manifests, primary text and compiler
must still match. This removes the circular live-file dependency without relaxing factual evidence
or review checks. The census snapshot remains attributable to its input commit.

The Junto finder accepts `NORTON_CENSUS.json` in the existing external `--data` directory and runs
through `junto.py run --finder norton`. It registers observed intersections under
`norton_shared_factual_obligations`, retaining owner-seeded origin and unverified status. Use
`add-test` only with actual full-arm session bills and independently reviewed integrated units.
No candidate count, hypothetical reuse, text bytes or extraction timing counts as savings.

The focused verification branch is `sol/norton-20261020-verified` (PR #45). The earlier branch
keeps its independent shared source-acquisition run and frozen pilot history. This run selects
NORTON and its existing consumers without enlarging the seven-order factual pilot.
