# clause_inventory H6-w11

Start 2026-11-05T23:52:35Z, end 2026-11-05T23:58:54Z. Run was interrupted once by a memory kill and resumed; sheet edits were already on disk and verified.

## EO:11929: done
Held FR text (41 FR 31159) read in full; the single "whole" scope was split into Sec. 1 (adds section 114 to EO 11157) and Sec. 2 (conforming amendment of section 105) as corrected scopes; APP page records for the two later-order transcriptions matched.
Sources opened: views/EO_11929.json, held FR text in jobs/fr-originals/data/full_run/texts, APP texts and MIRROR_DOCUMENTS.jsonl rows for working_text.

## EO:9431: done
Held FR text read in full; two items (amend IV-9, amend IV-10) confirmed unchanged; APP page record matched heading, date and text hash.
Sources opened: views/EO_9431.json, held FR text in jobs/fr-originals/data/full_run/texts, APP texts and MIRROR_DOCUMENTS.jsonl rows for working_text.

## EO:8667: done
FR OCR heading lacks the number but the trailing [No. 8667] and APP title agree (Wintering River NWR); the sole-paragraph scope was split into reservation, prohibition and naming clauses by exact offsets.
Sources opened: views/EO_8667.json, held FR text in jobs/fr-originals/data/full_run/texts, APP texts and MIRROR_DOCUMENTS.jsonl rows for working_text.

## EO:11350: done
Inventory had mislabelled dup scopes, a page-break split of item 2(c) and lead-in rows; replaced by 15 corrected scopes (items 1, 2(a)-(e), 3, 4(a)-(d), 5(a)-(d)) with exact offsets; most time went to offset mapping.
Sources opened: views/EO_11350.json, held FR text in jobs/fr-originals/data/full_run/texts, APP texts and MIRROR_DOCUMENTS.jsonl rows for working_text.

## EO:12896: done
Held FR text read in full (2 sections); sec1 revokes Civil Service Rule 4.1, sec2 sets the effective date; inventory confirmed unchanged, no working_text row exists.
Sources opened: views/EO_12896.json, held FR text in jobs/fr-originals/data/full_run/texts, APP texts and MIRROR_DOCUMENTS.jsonl rows for working_text.

Choices: original_pages_confirmed left false (FR originals do not require a page check). EO:8667 and EO:11350 and EO:11929 use inventory overrides (clause_id blank). EO:12896 sec2 (effective date) kept as a scope per the prior inventory. APP working-text confirmations set true for identity, completeness and pages; held_text_lead ones true for identity and completeness, pages false.
Tool defects: none; the first edit script crashed on an empty working_text '{}' (fixed). Offsets in some spans include page-footer text.
