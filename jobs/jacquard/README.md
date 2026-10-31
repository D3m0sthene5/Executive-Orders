# Jacquard: sampled class review with planted errors

Named for the loom that applies one punched-card pattern to every thread. One rule, written in advance,
is checked against a random sample of a class of orders; if the sample passes, the rule is applied to every
order in the class.

## What it is for

Owner ruling 2026-10-31 (`research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md`): the
provisional NO statuses of a pre-defined lot of orders may be adopted from a random sample reviewed with
planted errors, with zero misses allowed. Statuses stay provisional AI status hypotheses, the human-certified
count stays 0, flagged outliers go to individual review, and adoption is by a pull request the owner merges.
Separate-context Claude reviewers may decide the sample.

The sample size of 59 comes from the zero-failure bound: with 0 failures in n draws the exact one-sided 95%
upper confidence bound on the error rate is 1 - 0.05^(1/n); for n = 59 it is 4.95%, below 5%. Lots of at most
80 orders (`full_review_max`) are reviewed in full instead.

## Lots (`lots.json`)

A lot is the TYPES.csv rows (from `jobs/x1-class-engine/output/TYPES.csv`) with a given `type` and `rule_id`,
a confidence in the listed set, a year at or below `max_year` where given, no row yet in
`research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`, and a held text that exists on disk.
`CALIBRATION.csv` lists, for each lot's type, how many orders are already in the register and with what
status. It is evidence for the reader, not a gate.

## Steps

All commands run from the repo root. `--out` defaults to `jobs/jacquard/output`.

| Step | Command | Writes |
|---|---|---|
| select | `python3 jobs/jacquard/jacquard.py select --out DIR` | `LOTS.csv`, `CALIBRATION.csv`, `SELECT.json` |
| sample | `... sample --out DIR` | `SAMPLES.json` (seed, lot size, mode, sampled ids) |
| packets | `... packets --out DIR --packets-dir P --key-file K` | blinded packets under P, answer key at K |
| verify | `... verify --out DIR --reviews R --key-file K --packets-dir P` | `VERIFICATION.json` |
| accept | `... accept --out DIR` | `ACCEPTANCE.json`, `INDIVIDUAL_REVIEW.csv` |
| propose | `... propose --out DIR` | `PROPOSED_STATUS_ROWS.csv` |

The GitHub job (`job.py`) runs select and sample only and writes them to `OUTPUT_DIR` with `SUMMARY.json`.
Put the packets directory and the key file outside the repo and outside each other: reviewers must never see
the key. `packets` refuses a key file inside the packets directory. `propose` never touches the register.

### Sampling

If the lot has at most `full_review_max` members the whole lot is the sample (mode `full`). Otherwise
`random.Random(sha256(seed + ":" + lot).hexdigest()).sample(members sorted by instrument_id, 59)`. The same
inputs give the same sample.

### Planted controls

Each lot gets max(2, round(0.08 x sample count)) controls, alternating intruder, text swap, intruder, ...

- **Intruder**: an order of one of the lot's `control_types`, not in the register, with a held text, presented
  as a member of the lot with its own honest header. Caught when the reviewer answers `type_fits` false or
  `status_no_supported` false.
- **Text swap**: sampled member A's number, date and title with a different member B's text (in a sampled lot
  B is taken from the members outside the sample when there are any). Caught when `identity` is `mismatch`.
  A and B keep their genuine items. When a lot has several batches, the swap, A's genuine item and B's genuine
  item (if B is in the sample) go to different batches so a reviewer never sees the same header or text twice.
  In a lot that fits in one batch this is impossible; the key records `twins_in_other_batches: false`.

### Packets

`PACKETS/<lot>/batch-NN/items.jsonl` (`item_id`, `claimed_number`, `claimed_date`, `claimed_title`,
`text_file`) and `texts/<item_id>.txt`. Item ids look like `L1-B03-07` and say nothing about kind or order.
Genuine items and controls are shuffled together; batches hold at most 20 items, sizes as even as possible.
A text over 12,000 characters is cut there and ends with `[TRUNCATED: original N characters]`.
The provenance preamble that some held texts carry (`# order: EO:n ...` lines, the `Copy/Source/Location` lines
of the hathi texts, and the `----- EXACT ... -----` marker) is removed because it names the order; the order
text that follows is unchanged. `claimed_date` is the TYPES year. `claimed_title` is `app_title`, else
`wpa_summary`, and is empty when TYPES holds neither.

Blinding check run by `packets`: an error if a listed word (control, intruder, swap, planted) appears in a
path or in any `items.jsonl` field other than the title, or if any answer-key instrument_id appears anywhere.
Listed words that occur as ordinary English inside a historical text or title are counted as warnings; they
cannot be removed without altering the text.

### Review format and grading

Reviewers write `R/<lot>/batch-NN.jsonl`, one object per packet item: `item_id`, `identity`
(`match|mismatch|cannot_tell`), `identity_evidence`, `type_fits` (bool), `outliers_found` (list of strings),
`status_no_supported` (bool), `basis`, `end_or_bound`, `operative_quote`, `notes`.

- A batch is `incomplete` if a review is missing, duplicated, unparseable or for an unknown item, or the file
  is absent. It is `invalid` if any planted control was missed (a control whose review fails the schema counts
  as missed). Either way all its genuine reviews are discarded and the batch is listed for re-review.
- In a valid batch a genuine review is **upheld** only if identity is `match`, `type_fits` and
  `status_no_supported` are true, `outliers_found` is empty, and `operative_quote` is non-empty and an exact
  substring of the packet text after runs of whitespace are collapsed to one space on both sides. Anything
  else is a **failure** with its reasons recorded. The quote check is skipped only when `status_no_supported`
  is false and identity is `mismatch`.

### Acceptance

- Any batch not valid: the lot is `pending_rereview` and nothing is adoptable.
- Sampled lot, zero failures among the 59: `accepted`; every lot member is adoptable except any member whose
  own review failed.
- Sampled lot, one or more failures: `rejected`; nothing is adopted from the sampling. Sampled members whose
  own review was upheld are still adoptable individually; failures go to `INDIVIDUAL_REVIEW.csv`.
- Full lot: `full_review_complete`; each upheld order is adoptable individually, failures go to
  `INDIVIDUAL_REVIEW.csv`.

`ACCEPTANCE.json` gives each lot's Clopper-Pearson 95% upper bound on the error rate (k failures in n reviewed;
for a full lot it is shown for comparison only, because no sampling took place).

### Proposal rows

`PROPOSED_STATUS_ROWS.csv` uses the register's own header, read from the register file, with one row per
adoptable order: status `no`, `decision_origin` =
`jacquard-<lot>-2026-10-31:ai_class_status (<sampled|full|individual> review research/excavator/jacquard-2026-10-31/<lot>; ruling 2026-10-31-jacquard-and-working-texts)`,
and the fixed template values for the other columns (counts 0, `human_certified_by_this_release` = no).
Orders already in the register are skipped.

## Files

`job.py` (select + sample), `jacquard.py` (library and CLI), `lots.json`, `needs.txt`, `test_jacquard.py`
(`python3 -I jobs/jacquard/test_jacquard.py`).
