# Notes for the coordinator: Lowande-Poznansky prior-art stream

Date: 2026-11-06. Branch `enc/prior-art-lp`. Tier: lead. Nothing here changes a status, count, codebook or claim.

## Results worth recording (for Kean)

1. L&P's deposited `revoked_next_term` can be reproduced from Thrower's order list with the rule "revoked by the last
   year of the next four-year block": per-year shares correlate 0.991 with L&P's (README.md). In the 1937-2013 data
   the L&P `ceremonial` counts equal Thrower's in every calendar year. Both suggest L&P's order-level file is Thrower's
   corrected and extended, which makes the requested file valuable and the 20 + 65 corrections the only new
   revocation information.
2. The deposit rows can be linked to EO numbers by the ASC-within-year hypothesis in 21 of 70 testable years, not in
   the others (`output/aligned_orders.csv`, `output/alignment_by_year.csv`). Do not use the link outside those years.
3. The article's own text (SI-3) supports the project's thesis for EO 12553 as an assertion without a count. Thrower's
   list gives 377 orders with revocation year 1986, median gap 25 years (BASELINE.md).
4. Source inconsistencies: sample end date (article p. 351 versus SI-2 versus data); Chiou-Rothenberg year (2014 versus
   2013); the Thrower column name `revokedbyotherthaneo` versus the PDF codebook `revokedbyeo12553`.
5. Tooling: the one-line CRLF converter in WORKER_RULES.md truncated every file I had written (it opens for writing
   before reading); I rebuilt them. The coordinator has since supplied `tools/lf.py`.

## Owner questions

- Send `REQUEST_EMAIL.md` to lowande@umich.edu? (Draft only; fill the email and project link first.) Is "we will credit
  your data in anything we publish" acceptable, and should the offer to share corrections stay in?
- Where did the Thrower archive (zipB) come from? I could not cite a DOI for it; record the source before it is cited
  in the article.
- Whether `output/aligned_orders.csv` should be fed to any other stream. I recommend not until the order-level file
  arrives; it is a hypothesis for 28% of rows.

## Not done

- No contact with Lowande. SI replication materials not obtained.
- The within-year ordering in 38 years was not recovered.
- Figure C.1 values (Chiou-Rothenberg) were not read from the image.

## Bytes

No PDF, archive or raw text is committed; the article and SI PDFs stay in `C:/Users/danie/eo-venvs/lp-dl/`. The push
size is in the stream's final message.
