# Independent reviewer brief: NIRA code-approval claims (reusable)

You review proposed lifecycle claims blind. You did not produce them, and some are deliberately wrong
(planted controls). Review every claim line in the file you are given; do not assume any is correct. Open only the files your
assignment names and the repository sources they cite; never list or open other files in the review-set folder,
the packet's `completion/` folder, or the producer's sheets and reports.

For each claim:

1. Identity and text. Re-hash the cited text file and check every quoted span against its bytes. Do the page
   check on the cited page record (APP `MIRROR_DOCUMENTS.jsonl` row with the same sha256, or the printed copy).
   Confirm number, date and subject against the census register and the WPA 1944 list.
2. Inventory. Read the order in full. Every operative command must be a clause; nothing operative omitted.
3. Ending. Check the order's own terms, earlier government action on the same code (search held order texts
   under `jobs/*/output/texts` for the code's name and the order's number), and independent commands. For a
   code-dependent command with no earlier end, the shared analysis (`SHARED_ANALYSIS.md` and its independent
   review in `review-shared/`) sets the end at 1935-06-14 by S.J. Res. 113 section 2, with Schechter
   (1935-05-27) and void-from-issuance as stated alternatives. Check that the claim applies it correctly and
   that its stated facts match the sources; reject a claim whose dates, mechanism, quotes or reasons are wrong
   or internally inconsistent, even when the date is right.
4. Savings. Accrued acts, liabilities and the section 5 exemption for completed action; nothing continues the
   approval unless a held source says so.
5. Searches. The claim's searches must be adequate for the order and honestly described.

Write one JSON object per claim line to the output file you are given, with fields: `review_id`,
`instrument_id`, `claim_sha256` (canonical: sorted keys, UTF-8, no spaces, ensure_ascii=False, of the claim
object), `reviewer`, `model_family`, `independent: true`, `separate_context: true`,
`review_kind: "independent_ai_source_review"`, `scope: "whole_case"`, `verdict` (`upheld` or `rejected`),
`defects` (list of `{field, claim_says, source_says}`), `evidence_checked` (list), `reasoning`, and
`started_utc` / `ended_utc`.
