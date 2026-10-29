# Dossier original selection: wrong documents chosen as ORIGINAL (fix of 2026-10-28)

The 2026-10-28 land probe (`research/excavator/claude-land-probe-2026-10-28/decided/packet/supp/LAND_PROBE_REPORT.md`, "Tool defects hit", item 1) found that 4 of 18 dossiers carried another document as `ORIGINAL:<order>`. After this fix, EOs 7435, 7509 and 7510 carry their APP transcriptions, and EO 4872 has no original. Its only held text is a 1928 statute page, and the dossier records why that text was refused.

## Cause

The only place where an original is chosen is the scan loop in `build.py`. That loop processes held texts in `rank_text` order, and the first readable text for an order becomes `selected[iid]`. `selected` supplies the dossier's `ORIGINAL:` evidence, its clause inventory (`segments`), `ACTOR_TEXT` contexts, families and `OVERLAY_INPUTS`. No other job or module chooses an original. `excavate.py` only segments the text it receives.

Two faults combined:

1. **Ranking.** `rank_text` sorted by `(not acceptable_as_original, needs_page_check, "mirror"/"transcription" in grade, ...)`. Every grade that is neither acceptable nor a mirror therefore tied: `held_text_lead`, `derivative_lead` and the ungraded text layers. The `"mirror"` flag then pushed registered APP and Wikisource transcriptions behind those leads. Among the tied leads, the file path decided the order. For EOs 7435 and 7510 this alone explains the defect. The source-ladder FR issue text (`held_text_lead`) ranked ahead of the APP `mirror_transcription`, which is registered under the 2026-10-21 ruling. In the current corpus, ranking explains all eight wrong originals among the decided dossiers. An earlier simulation found that ranking did not explain 7435 and 7510; on this corpus it does.
2. **No identity test.** `inputs.py` treats a `SOURCES.jsonl` record that has a single `instrument_ids` entry as that order's own text. However, `opus-media-match/output/SOURCES.jsonl` lists every Opus evidence file under the orders whose cases cite it, including statutes (STATUTE-45-Pg729, PLAW-106publ541, CFR pages, Reorganization Plan No. II). `source-ladder/output/SOURCES.jsonl` does the same for `ending_or_current_basis` documents, U.S. Code notes and partial FR issues (pages 1–6 of 66). These texts are declared for the order but never print it, and nothing checked them.

## Fix (`build.py`, `inputs.py`; no pinned file touched)

- **Tiered ranking** (`text_tier`, `rank_text`). Texts rank in three tiers: 0, declared original candidates (`acceptable_as_original`); 1, registered working texts, meaning a grade in `working_text.GRADES` that the producer registered as an `original_representation` fragment for this order, path and grade; 2, every other text, which is an unverified lead. The registration comes from the existing `inputs` registry lookup. `load_corpus` now also returns `registered_working_texts`. A grade label that inputs inferred without a producer registration ranks as a lead, because the assembler would reject it (`working_text_fragment_identity_or_grade_mismatch`). The secondary keys within a tier are unchanged.
- **Identity gate** (`identity_conflict`). The gate tests only for contradictions and never confirms identity. A held text is refused as this order's text in three cases:
  - **It prints no order.** The text is empty, a lone date line (three CSC extractions), or APP's "(this executive order was not published)" placeholder (31 texts).
  - **It is a statute, public law, U.S. Code or court-report printing of an EO.** The test matches the govinfo package or file name (`STATUTE-`, `STAT_`/`stat67_`, `PLAW-`, `USCODE-`, `USREPORTS-`) or a first line that heads the text as a public law or session law. The file-name test applies at every tier.
  - **It is an unverified Federal Register lead (tier 2) that never prints or names the order.** The test tolerates OCR: it accepts a located heading, letter-spaced "E xecutive O rder N", a `[No. N]` closing line with an OCR-damaged bracket, or a standalone four- or five-digit number such as a contents entry. Producer header lines (`Wanted:`, `Instrument:` and similar) do not count as printing the order.

  Tier 0 and tier 1 texts are not subject to the "prints the order" test. Many correct fr-originals pages fail it only because of OCR (for example "[No. 78571", or a "1236è" heading), so applying it there would refuse correct official texts.
- **Consequences of a refusal.** The declaration stays in `TEXT_REPRESENTATIONS` and the text's inventory stays in `TEXT_CLAUSES`. The text is not selected as the original. Its own-terms, generic-reference counts and discovered acting provisions are not attributed to the order, because a statute or a neighbouring document is not that order's text. When no acceptable text remains, the original is left absent, and `missing` gains "No held text accepted as this order's original; refused: <path>: <reason>". `SUMMARY.counts.texts_refused_as_order_text` reports the number of refused texts.

## Tests added (`test_original_identity.py`, 7 tests)

- **Ranking.** A registered working text outranks `held_text_lead`, `derivative_lead`, `official_fr_pdf_text_layer` and `mirror_transcription_app`, whatever the paths. An acceptable original outranks a working text. An unregistered working-text label falls to tier 2.
- **Refusals.** Statute, public-law, Code and Opus `STAT_` and `stat67_` printings are refused at every tier. A first-line `PUBLIC LAW` or `... CONGRESS. Sess` heading is refused. A citation of a public law inside an order's body is not refused.
- **FR leads.** A partial FR issue that does not print the order is refused (the EO 7510 case). The OCR forms `[No. 73731` and `Execu tive O rder 12415` are accepted.
- **No-order texts.** A date line, the APP placeholder and an empty text are refused.
- **No refusal outside the gate's scope.** Official and working texts are not refused for an unread number. A non-FR Richardson lead for an unnumbered early order is not refused, and neither is an unnumbered census id.
- **End to end.** A build fixture reproduces 7510, 7509, 4872 and 7373. It checks that the registered mirrors win, that 4872 has no original or clauses and records the refusal, that refused texts contribute no terms or acting provisions, and that every declaration is preserved.

The full suite passes: `python3 -m unittest discover -s jobs/claim-kit -p "test_*.py"` ran 417 tests, all OK.

## Impact on the current corpus

The fixed build of the current inputs was written to a scratch folder inside the repository and then deleted. It was compared with `jobs/claim-kit/output`. That output was confirmed to match the current `load_corpus` exactly (142,532 declarations).

**Originals.** 69 of 14,886 orders with held text change originals. 8 of these are among the 3,403 decided dossiers.

| Change | Orders |
|---|---|
| Richardson `derivative_lead` → registered APP or Wikisource `mirror_transcription` | 56 |
| `held_text_lead` → registered `mirror_transcription` | 11 (decided: EOs 6694, 7034, 7435, 7509, 7510, 11633) |
| `held_text_lead` → no original (the only held text is a statute page) | 2 (EO 2834: 41 Stat. 1359; EO 4872: 45 Stat. 729) |

**Clause inventories of the decided orders:**

| EO | Clauses before | Clauses after |
|---|---|---|
| 7509 | 1,987 | 1 |
| 7510 | 99 | 1 |
| 11633 | 136 | 4 |
| 7034 | 31 | 9 |
| 7435 | 7 | 1 |
| 6694 | 4 | 8 |
| 4872 | 5 | 0 |
| 2834 | 1 | 0 |

**Refused texts.** 280 held texts are refused as order text:

| Reason | Texts |
|---|---|
| Statute, public-law or Code printings | 176 |
| FR leads that do not print the order | 70 |
| APP "not published" placeholders | 31 |
| CSC date-only extractions | 3 |

**Downstream records:**

| Record | Before | After |
|---|---|---|
| OWN_TERMS | 52,832 | 46,448 |
| Located actor pairs | 11,004 | 10,916 |
| Known pairs | 16,626 | 16,539 |

In detail, 89 located (target, actor) pairs disappear and 1 appears (EO 11051 > EO 11490). The pairs that disappear came from refused texts. Examples are U.S. Code notes filed under EO 13743, 13883, 14054 or 13697; Public Law 90-53 filed under EO 11362; and EO 10827's FR text filed under EOs 10708, 10746 and 10799. Parent-as-amended links built from those texts disappear with them. 131 dossiers keep their original but lose terms or acting provisions drawn from such texts.

**Spot-check of 10 changed orders (texts read):**

- **EO 7509.** Before: the Water Resources Development Act of 2000. After: the APP text of Fort Peck Game Range. Correct.
- **EO 7510.** Before: Treasury Regulations 94 (FR of 1936-11-14, pages 1–6). After: the APP text of Lenore Lake refuge. Correct.
- **EO 7435.** Before: the FR issue of 1936-08-07, which does not contain Winnemucca. After: the APP text of Winnemucca refuge. Correct.
- **EO 4872.** Before: a 1928 statute page (45 Stat. 729). After: no original, with the refusal recorded. Correct.
- **EO 2834.** Before: a 1921 statute page (41 Stat. 1359). After: no original. Correct.
- **EO 7034.** Before: Reorganization Plan No. II (53 Stat. 1431). After: the APP text "Establishing the Division of Applications and Information". Correct.
- **EO 11633.** Before: 32 CFR part 155. After: the APP text on the security clearance program for citizens employed by NATO and other treaty organizations. Correct.
- **EO 6694.** Before: the FR issue of 1942-03-13 printing EO 9095. After: the APP text abolishing the Office of Alien Property Custodian (1934). Correct.
- **EO 1.** Before: Richardson's "provisional court in Louisiana", which is a different document. After: the APP text "Executive Order No. 1—Relating to Political Prisoners", which matches `domesday-register` (1862-02-14). Correct.
- **EO 11.** Before: a Richardson lead. After: the Wikisource text of EO 11 (1873), which is the same document. The Wikisource text carries page chrome ("Jump to content").

**EO 7373 is unchanged.** It keeps the Opus FR issue of 1936-05-22 (`held_text_lead`), which does print `[No. 7373]`. The clause-drafts mirror of the same order carries a working-text label with no producer registration, so it ranks as a lead and loses to the FR printing. The assembler still cannot cite either text until a registered working text or an official copy is held.

## Not fixed

- **Page-neighbour later events (probe item 2).** The pairs such as EOs 8858–8860 attached to EO 4109 come from `jobs/later-events`. Their records carry the flag `acting_order_heading_not_found_in_text(whole text scanned)`. They reach claim-kit as known pairs through `claim-drafts` `proposals.later_events`. Claim-kit's own scanner does not locate those provisions, and lists them only as "target provision not located" plus the actor's context. The fix belongs in later-events (or in a filter of flagged pairs in `inputs.add_pair`) and needs an owner decision. Claim-kit's own neighbour attributions from FR leads that do not print their order are removed by this fix; EO 8861's FR issue of 6 FR 4289 is an example.
- **Neighbour text inside a correctly located extent.** `excavate.discover_mentions` falls back to the whole text when the order's own heading is not found. Changing that requires editing `excavate.py`, which is pinned, so this fix leaves it alone.
- **fr-originals tier-0 pages that may be the wrong page.** Among selected fr-originals originals, 106 at low or medium location confidence and 17 at high confidence do not print their number even under the OCR-tolerant test (5 hathi-gpo printed copies also fail it). The high-confidence cases inspected earlier were OCR damage. The low-confidence ones already carry `requires_page_check`. Correcting them needs page images, not this gate.
- **Ambiguous registrations (probe item 5)** and the official-copy gate conflict (probe item 4) are untouched.
- **OCR misses in refused FR leads.** A few refused FR leads probably do contain their order behind OCR damage. In EO 9774 the heading reads "EXECUTIVE ORDER $774", and in EO 11836 it reads "11036". This affects leads only, never an official or working text.
- **`inputs.py` still attributes singleton `instrument_ids` SOURCES records** (opus-media-match, source-ladder `ending_or_current_basis`) to the cited order as representations. The gate now stops the observed contradictions. Refusing those records at input would require producer-specific role fields, which the producers do not yet publish uniformly.
