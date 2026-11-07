# Notes for the coordinator: Lowande-Poznansky prior-art stream

Date: 2026-11-06. Branch `enc/prior-art-lp`. Tier: lead. Nothing here changes a status, count, codebook or claim.

## Results worth recording (for Kean)

1. L&P's deposited `revoked_next_term` can be reproduced from Thrower's order list with the rule "revoked by the last
   year of the next four-year block": per-year shares correlate 0.991 with L&P's (README.md). In the 1937-2013 data
   the L&P `ceremonial` counts equal Thrower's in every calendar year. Both suggest L&P's order-level file is Thrower's
   corrected and extended. The SI's new revocation information is counts only: 20 missing revocations, 30 revocations
   after 2013, 8 supersessions, 37 nullifications, 1 false revocation and 65 wrong revoking presidents, none listed.
2. The deposit rows can be linked to EO numbers by the ASC-within-year hypothesis in 22 of 73 testable years, not in
   the others (`output/aligned_orders.csv`, `output/alignment_by_year.csv`). Do not use the link outside those years.
   Among rows with any positive signal, 246 of 284 agree (86.6%); the 98% figure over all rows is inflated by rows
   with no signal.
3. The article's own text (SI-3) gives prior art for the concern behind the project's thesis, for EO 12553, as an
   assertion without a count. Thrower's list gives 377 orders with revocation year 1986 and a 372-order EO 12553 flag
   (main `.dta`); the project has EO 12553 edges for 383 orders in range.
4. Source inconsistencies: sample end date (article p. 351 versus SI-2 versus data); Chiou-Rothenberg year (2014 versus
   2013). The `revokedbyotherthaneo` (CSV) versus `revokedbyeo12553` (main .dta) question is answered: two different flags.
5. Register defects found by the coordinator's check: `EO:7700A` is a duplicate and `EO:10276` has a date typo; they
   explain the 1937, 1951 and 1961 count differences.
6. Tooling: the one-line CRLF converter in WORKER_RULES.md truncated every file I had written (it opens for writing
   before reading); I rebuilt them. The coordinator has since supplied `tools/lf.py`.
7. An independent check on 2026-11-07 produced corrections; see `CHECK_2026-11-07.md`.

## Owner questions

- Send `REQUEST_EMAIL.md` to lowande@umich.edu? (Draft only; fill the email and project link first.)
- Where did the Thrower archive (zipB) come from? I could not cite a DOI for it; record the source before it is cited
  in the article.
- Confirm the identity line and the offer of corrections in `REQUEST_EMAIL.md` (both bracketed for you).
- Whether `output/aligned_orders.csv` should be fed to any other stream. I recommend not until the order-level file
  arrives; it is a hypothesis for 30% of rows.

## Not done

- No contact with Lowande. SI replication materials not obtained.
- The within-year ordering in 38 years was not recovered.
- Figure C.1 values (Chiou-Rothenberg) were not read from the image.

## Bytes

No PDF, archive or raw text is committed; the article and SI PDFs stay in `C:/Users/danie/eo-venvs/lp-dl/`. The push
size is in the stream's final message.
