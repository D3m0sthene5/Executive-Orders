# Owner rulings: sampled class adoption (Jacquard), reviewer family, and confirmed working texts (2026-10-31)

Given by the owner, Danny, on 2026-10-31 in a Claude session, answering three questions put to him directly.

## 1. Jacquard: sampled review may adopt provisional NO statuses for a class (answers A-20261021-3)

For X1's "spent" and "swept" classes, a class's provisional NO statuses may be adopted from a sampled independent
review instead of order-by-order review, under a strict test:

- Per class (a "lot" defined in advance by deterministic criteria), a random sample with planted errors.
- **Zero misses allowed.** The sample is sized so the 95% upper confidence bound on the class error rate is 5%:
  59 orders, or every order when the class is small.
- Flagged outliers go to individual review.
- Adoption is still by a pull request the owner merges; statuses stay provisional AI status hypotheses; the
  human-certified count stays 0.

## 2. Reviewer family (answers A-20261028-4 for sampled class review)

Separate-context Claude reviewers, with planted controls, **may decide** a class sample and its adoption. A
different-family (GPT/Codex) review is not required for this route.

## 3. Confirmed working texts may close the text step provisionally (extends D-20261021-transcriptions)

When a standalone check confirms an order's working text (the text is the right order, the text is complete, and
the pages are checked) before any claim exists, the readiness tracker may mark the text step done provisionally
for that order. It is counted separately, never as an original; the grade label and the standing
replace-and-recheck note carry over, and later claims reuse the confirmation.

No codebook change. Certified: 0.
