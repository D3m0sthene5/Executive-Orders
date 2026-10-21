# Readiness tracker job

Counts orders that are **ready for human review**: the machines have done every
step the order needs. Output: [`output/TRACKER.md`](output/TRACKER.md) (read this first),
`output/SHARED_UNLOCKS.csv` (one action → many orders, largest first),
`output/READINESS_BY_ORDER.csv` (all 14,972 orders, one row each) and
`output/SUMMARY.json`.

Runs daily (the `DAILY` file), whenever this folder or `research/readiness/` changes
(`triggers.txt`), after the jobs it reads when they run together (`after.txt`), or by
hand from the Actions tab. `SUMMARY.json` → `inputs.job_outputs_used` shows which job
outputs it read. The tests in `test_tracker.py` run first; the tracker does not run if
they fail.

## Steps per order

| Step | Done when |
|---|---|
| `provisional_status` | It has a provisional YES/NO (`research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`) |
| `original_text` | Stage 19 marks a locally preserved original, Stage 21 captured the official PDF, fr-originals or an official compilation job (ofr-compilations, isthmian-canal-1911, indian-reservations-1912) found it without `needs_page_check` (otherwise `ORIGINAL_FOUND_NEEDS_PAGE_CHECK`), opus-media-match matched an Opus copy to it, or its claim's original passes the gate and claim-checker. A find only in a compiled transcription, Richardson (richardson-volumes) or the American Presidency Project (app-executive-orders, live `FRAGMENTS.jsonl` and archive-capture `MIRROR_FRAGMENTS.jsonl`), never counts; it adds the lead blocker `ONLY_COMPILED_TRANSCRIPTION_FOUND` (lead available, original still needed) |
| `clause_inventory`, `ending_or_current_basis`, `savings_residuals` | That part of its claim in `research/readiness/claims/` passes `claim_gate.py` **and** claim-checker passed that step for this exact claim (`jobs/claim-checker/output/PER_CLAIM.json`, matched by claim sha256) |
| `counterevidence` | Either the claim's later-source search passes as above, **or** the machines' bounded searches covered the order and found nothing contrary: later-events read the whole OFR catalog (the order must be in it, so 1937 on) and every saved text, current-law scanned the whole U.S. Code and eCFR, and neither `COUNTEREVIDENCE_LEADS.csv` nor `POSSIBLE_CONFLICTS.csv` names the order. Never from a sample run; never with a quarantined relationship conflict. `output/MACHINE_LATER_SEARCH.jsonl` gives the claim-shaped `later_source_search` for each such order, ready to copy into its claim. Blockers say why not: `MACHINE_SEARCH_FOUND_CONTRARY_LEAD:<job>` (an agent must resolve it) or `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE` (pre-1937) |
| `shared_sources` | Only for orders citing a Stage 20 shared source: all of them retrieved (Stage 20 records or `jobs/source-ladder/output/SOURCES.jsonl`) |
| `opus_media` | Only for Opus cases: opus-media-match resolved every medium its records cite (`all_cited_media_resolved`); otherwise a specific blocker (re-fetch needed, original not kept, ambiguous match, none cited). Falls back to the Stage 20 audit until that job has run |

**Why the printed volumes count this way.** The three official compilations are government printings of the
orders' texts (the Office of the Federal Register's 1974 Hoover volume, the GPO's 1911 Canal Commission and 1912
Indian-reservation volumes), so they play the part the Federal Register page plays for later orders. They count under
exactly the fr-originals rule (`needs_page_check` must be `false`; a missing flag does not count), because their finds
carry the same kind of uncertainty: an OCR text and a machine page location, and for the 1911 and 1912 volumes, which
print no order numbers, an identification by date and subject against the WPA list that the job grades in
`location_confidence`. Richardson's *Messages and Papers* is a compilation transcribed from department records and
newspapers, not the signed or officially printed original; no existing rule here treated a compiled printing as the
original, so it stays a lead. The American Presidency Project is the same class: an editorial web transcription (grade
`mirror_transcription`, `acceptable_as_original=false`), read live or from public web-archive captures of its pages;
it locates and dates an order but authenticates nothing.
The OFR 1989 Codification is not read here: its texts are as amended to 1989 and its
in-force snapshot cannot show anything operating on 2026-10-14 (claim-drafts proposes both as leads only).

A step recorded in `research/readiness/EXHAUSTED.jsonl` counts as done. An order is
ready when all its steps are done and either its claim passes the gate in full
(tier `complete_claim`) or the only remaining gaps are exhausted steps (tier
`machine_exhausted`). Human verification is not counted here.

To add a new source of evidence, add its file to `P` in `tracker.py`, its folder
to `needs.txt`, and a test.

## Negative source-audit holds

`research/readiness/SOURCE_AUDIT_HOLDS.jsonl` can prevent a mechanically complete
claim from being advertised as ready while a documented independent AI source
audit has an unresolved material objection. Each hold binds the exact canonical
claim SHA256 and the review file SHA256. An active hold reopens the
`counterevidence` step, removes that step's machine-search and exhaustion credit,
and withholds final readiness. Legal status and the owner's canonical claim stay
unchanged; a hold cannot confer acceptance. This prevents the row from displaying
counterevidence as complete while a material objection remains open. A changed
claim gets a stale-hold warning for explicit rereview. Missing or damaged held
review evidence fails closed.

The October 20 portfolio repair adds exact-version holds for EOs 13792, 13101,
13148, 13783 and 13807 alongside the existing EO 9789 hold. Their reviews and
unaccepted partial proposals are under
`research/excavator/astra-portfolio-repair-2026-10-20/lambertini-review/`.
Mechanical checker passes do not resolve these first-cessation and scope
questions. The existing claim owners must supply the missing evidence and
clause-specific reasoning through the normal review process.

Status-history outputs are research preparation and confer no readiness step.
The 1989 snapshot is still excluded from legal/current-status proof.

## Historical census candidate track

The separately run census-candidates job publishes an item-level register for the early rangers and Lord's index appearances. Its counts are appended in a separate section of TRACKER.md and SUMMARY.json when the job output exists. They are excluded from the 14,972 working-EO denominator. No catalog hit or scanned document is automatically admitted.
