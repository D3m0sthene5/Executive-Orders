# Cujas c03 producer report

Start 2026-11-08T18:12:46Z; end 2026-11-08T18:18:13Z. Final applied directory: `applied-v1`.

## Method
Read the 2026-10-21 transcription ruling and the AGENT_PROTOCOL "Provisional working texts" section. For each member I compared the held APP working text (and the derived clause-drafts copy, which is the APP text plus a heading) word by word against the Photius GPO printing `jobs/photius-gpo-volumes/output/texts/EO_<n>.txt`. The comparison checked identity (number, title, date, signature), completeness (start to signature) and the quoted spans. OCR noise (broken hyphens, spaced punctuation, truncated signature or year at the end of the OCR run, stray `[No. N]` tags) was ignored. I did the same for every other order whose APP text is a cited working source (earlier or later exemption orders): 7413, 7635, 7945, 8058, 8489, 8552, 8554, 8562, 8710, 8747 and 8810.

APP page rule: for each APP text, the `DOCUMENTS.jsonl` or `MIRROR_DOCUMENTS.jsonl` row with the fragment's sha256 names the order's number and subject in its heading, has a date that agrees with the held text's dateline, and has a `text_sha256` equal to the held text's. This held for all of them. `pages_confirmed` is true for the APP and clause-drafts copies on that basis, and I also compared them with the official printing. For the GPO printing entries, `pages_confirmed` is true only where `PAGE_CHECKS.csv` records a pass (8204, 8207, 8218, 8345, 8368, plus cited 7413, 7945, 8552, 8554, 8562, 8810). The other GPO fragments declare `needs_page_check: false`, and I did not view page renders, so theirs stay false. The checker accepted this.

## Per order
- **Submitted (24)**: EO 8105, 8132, 8204, 8207, 8209, 8213, 8218, 8228, 8231, 8253, 8260, 8263, 8268, 8270, 8274, 8275, 8282, 8286, 8287, 8345, 8368, 8369, 8414, 8421.
  - Comparison result: agreement. The only differences were OCR noise, a trailing OCR truncation of year or signature, and APP's missing `[No. N]` tag. Number, title, date, signatory and operative wording agree. Every claimed end date matches "ending <date>" in the printing.
  - Change: identity, complete-text and page confirmations set as above and `approved` set to true. I changed no clause rows, rationales or standing note.
  - Legal recheck:
    - Each order is a time-limited personal exemption under section 204 of the act of June 30, 1932, so the stated end is the order's own term. The stated end dates are inclusive, with the exclusive reading disclosed in the claims.
    - Federal Register notes: no "Revoked by" note exists for any member. The notes "Amended by: EO 8554 / 8562 / 8747" on 8228, 8260 and 8369, and the "See" notes on 8368 and 8413, point to later further-exemption orders. I read those later texts, and each grants a new period without revoking or shortening the earlier term.
    - The claims address these notes as later events, not ends. The "Amends:" notes carried by 8207, 8287, 8345, 8414, 8369 and others are the same orders acting on their own predecessors.
    - Savings: personal grants with no continuing obligation. No error found.
- **Blocked (1): EO 8413.**
  - The APP text reads "for a period of one year ending June 30, **1041**." in the operative sentence, near the end of the held text (about offsets 628-684). It also reads "title 5, **see.** 715a".
  - The GPO printing (hvd.hl272k, PDF pp. 63-64) reads "ending June 30, **1941** ." and "sec. 715a".
  - The carried claim quotes the APP misprint "1041" and reads it as 1941. The date is material, so the quoted span does not match the official printing and the working text is not confirmed.
  - The claim needs rebuilding on the printing's reading with a fresh quote. The end date June 30, 1941 is supported by the printing. Identity otherwise agrees: No. 8413, May 18, 1940, FRANKLIN D ROOSEVELT.
  - Recorded in `unresolved_material_gaps`; outcome is blocked and `approved` is false.

## Checks
`kit.py apply` wrote `applied-v1`. `batch-check` reported 25 members, 24 claims checked, strict pass 24 and fail 0. The actual claim checker reported all_checks_passed for 24 of 24. Blocked: 1. No actionable failures.

Geddes lint: 0 defect flags and 30 coverage gaps across 12 claims (advisory). `GEDDES_RESOLUTIONS.json` is empty because no flags were raised.

Tool defects: none. No "changed prior research" or "changed Valla review context" message appeared.
