# Family rules: offline research proofs

Agents maintain one source-grounded JSON rule per acting instrument in
`research/readiness/rules/`. The five largest decided families were measured
from pinned main da952e0: EO 12553 (335), EO 14148 (66), EO 9830 (53), EO 12379
(30), EO 11490 (21). These are candidate family sizes, never accepted endings.

`job.py` writes a certificate for every matching ending edge target, a hashed
saved-text sweep manifest, `FRAGMENTS.jsonl`, `SUMMARY.json`, and measured
cl100k input-payload token comparisons in `METRICS.json`. No model is called.
`discover.py` is an offline evidence-packet helper; it is not the job entry point.

Rules specify mechanism, effective date and its basis, exact quoted clause,
source URL/hash/page and saved text hash, explicit scope, exceptions/savings,
and a list of targets whose independent clauses have actually been reviewed.
Missing original custody, source, scope, date, original target text, independent
clause review or current-law inputs blocks a proof. Any qualified edge, earlier
ending, revival, savings lead, current-law mention, or later/undated reference in
saved text also blocks it. Mirror transcriptions retain their authenticity gaps.
A rule's signing date never silently substitutes for a stated effective date.

All certificates, including blocked ones, merge into `_draft.family_rule_certificates`
through claim-drafts. Only a certificate passing the bounded checks additionally
creates a whole-order-end **candidate**. Neither output fills an asserted claim,
changes a status, accepts a readiness step, or proves that unsaved sources contain
no counterexample. Source-hash and corpus-manifest changes regenerate proofs.

Run offline tests: `python -m unittest discover -s jobs/family-rules -v`.
