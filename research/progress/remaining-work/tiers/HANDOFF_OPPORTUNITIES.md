# Small dossier-production handoffs — November 2, 2026

Read-only assessment at main `b3fc50647cfc6f153ac2497ad2e172de69213295`, requested after the Job tiers dashboard update. No implementation, acquisition, scientific production, status adoption, grade change or readiness increment was performed. A bounded configured gpt-6-sol reader checked the claim-kit handoffs; complete elapsed time, tokens and cash are unavailable. Root retained recommendations and interpretation.

## Strongest scalable repair: Lachmann confirmations into fresh claim-kit packets

PR120 is merged. `jobs/lachmann/output/SUMMARY.json` reports 1,674 confirmed working texts (188 ProQuest replica scans, 576 machine-read government printings and 910 APP mirror transcriptions). The owner ruling `research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md` explicitly permits later claims to reuse confirmations while preserving the grade and replace-and-recheck note.

The tracker consumes machine confirmations and agent overrides, matching instrument, grade, raw hash, text hash and text path and rechecking page requirements and held bytes (`jobs/readiness-tracker/tracker.py`, confirmation_rejection/counting_confirmations). Claim-kit materializes the output through its broad input glob, but its semantic input/build/blank-sheet route does not consume Lachmann confirmations. `working_text.py::blank` sets identity, completeness and pages false; `assemble.py::blank_sheet` uses that blank; `batch.py::prepare` freezes it into decision CSVs. No corresponding Lachmann reader was found in inputs/build/batch/working_text/assemble/kit.

Smallest repair: carry a validated exact confirmation for the selected original representation into the frozen dossier and working-text sheet. Share the existing exact-record validation rather than introduce another registry. Pin the record, method and source version. Missing/changed bytes, conflicting grade, a different selected representation or a negative agent override must refuse reuse. Preserve the standing original replacement/quotation-recheck debt, producer approval, clause/ending/savings/counterevidence analysis and independent whole-claim review. No `acceptable_as_original` promotion.

1,674 is the candidate ceiling, not a measured packet intersection or completed-dossier count. The historical combined Jacquard/Lachmann simulation recorded 513 confirmed texts on decided orders and readiness unchanged at498. First refresh current production inputs and measure exact matching packets; then test a small fresh native cohort and refusal cases.

## Strongest direct pilot: already-held later instruments into source supplements

`research/excavator/claude-erasmus-2026-11-02/REPORT.md` identifies four unfiled target claims with later evidence lacking packet IDs: EO8129/PLO1704, EO8163/Proclamation2416, EO9949/EO10804 and EO11026/EO11029. It also names eight further actor-ID gaps; those are a follow-up fixture set, not eight additional promised completions.

`build.py` creates ACTOR_TEXT records only for located or known actors and puts contexts over50KB behind overflow pointers. `assemble.py` requires explicit dossier evidence IDs for events. Existing `source_supplement.py` already hashes held bytes/text, pins excerpt spans, assigns SUPPLEMENT IDs and preserves parent/replacement routing. Pilot that interface on the four actual blocked packets; if the omission recurs, add a narrow deterministic held-actor handoff to normal preparation. This repairs source access, not source identity, event occurrence, date, scope or legal effect; fresh source examination, blind review, checker and completion still apply.

## Other bounded opportunities

- **Two board-report packets:** EO11343/12095 are blocked because held reports are graded held_text_lead. Use the existing source-ladder/NORTON factual-event route after exact page, board-identity and occurrence review. A label change alone cannot create admissible evidence or prove report delivery. The earlier institutional-series pilot concerned different orders (EO10029/10117/10130) and must not be recredited here.
- **Cruden bare-number tables:** the ordinary by-number search misses EO12553's table of bare order numbers because it requires an Executive Order/E.O. prefix. Add a bounded table-aware lead extraction mode with exact page/hash, suffix and column guards; preserve ordinary conservative behavior and independent acting-provision judgment. One demonstrated pattern, no inferred ready count.
- **Lachmann Wikisource page checks:** the audit reports456 texts passing identity but lacking a supported page rule. A source-specific page/provenance adapter plus a fresh blinded audit is a bounded extension candidate. It could satisfy text prerequisites only; no automatic complete history follows.

## Operational prerequisite and already-completed work

PR119 adopted888 individually reviewed provisional NO statuses, taking the authoritative population from3,403 to4,291; PR120 merged1,674 provisional text confirmations; PR121/123 filed Apollo/Erasmus claims. The published tracker/compiler generation still predates those merges. Run the existing dependency-ordered production refresh before selecting/scoring another cohort. This is execution/freshness work, not a missing new framework or a justified arithmetic readiness increment.

The older Cotton, Lewis, X1, runner, Cruden cache, NEYMAN bridge and source-supplement replacement-routing repairs are already integrated. Do not propose them again. NORTON/Junto/NEYMAN/Valla do not become production accelerators merely by adding dependency lines where substantive source evidence or useful examined work is absent.

The dashboard's prior79-node map, expanded to82 for Apollo/Erasmus/Geddes, omitted separate Jacquard/Lachmann entries. They should be represented in a subsequent catalog correction. Its498-ready headline correctly describes the last published tracker generation; it does not incorporate the new adopted population or confirmations.
