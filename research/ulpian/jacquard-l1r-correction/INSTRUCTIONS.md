# Reading instructions: Jacquard L1R correction (one arm)

You are one of two independent readers. You will not see the other reader's answers. Read
the one packet file named in your task only (about 96 items: `item`, `order_date`, `text`; `order_date` may be "(no exact date)"). Do not open any
other file in `research/ulpian/` or `research/excavator/jacquard-*`, and do not search the repository for the orders.
Decide each item from its `text` alone.

## The question for each item

Each item is an executive order that lets one named person be appointed, reinstated, transferred or similar,
usually "without regard to the civil-service rules". It is presently recorded as "not in force today" on the
argument that the person must be dead by now. That argument holds only if the **order's own text** shows the person
was **born no later than 1904-05-02** (then even the longest documented human life, 44,724 days, ends before
2026-10-14).

Answer **KEEP** only when both hold:

1. **One beneficiary, one command.** The order's command reaches only one named person (other people may be named
   as background: a husband, a recommending official). No second command of another kind (a suspension, a
   reduction), no condition (a later test, a future vacancy), no class or list, no "similar cases". If the command
   reaches several persons, answer KEEP only if the text bounds the birth of every one of them as below.
2. **A quoted fact about that person** places the person's birth no later than 1904-05-02. Only these count:
   - the person was alive, working, employed, serving or appointed on a date on or before 1904-05-02 (for example
     "appointed a clerk on June 1, 1900", "employed since 1898", "served from 1892 to 1899");
   - a stated number of years of the person's service or experience ending on a stated date, or ending no later than
     the order date when no end is stated, that reaches back to 1904-05-02 or earlier (start = end minus the years;
     for "about", "approximately" or "nearly", count five years fewer than stated);
   - a stated age with its number ("is 58 years of age"): born no later than the order date minus that age;
   - an age limit with its number that the person is said to exceed ("beyond the age limit of 45").

When `order_date` is "(no exact date)", only a fact with its own date counts (a stated age or a period ending
"now" needs the order date, so it is not enough unless the text itself dates the order).

Everything else is **not** a sufficient fact: "Mrs.", "widow of", "wife of", a job title, being reinstated or
"formerly employed" without a date, children, a fact about a husband, father or other relative, a date after
1904-05-02, an age limit without its number, or anything you infer about likely age.

Otherwise answer **RETURN**. Also answer RETURN, with reason `not_the_order`, if the text is not this kind of order
or seems to be another order's text.

## Output

Write one JSON object per item, in item order, to your output file (path given in your task), one per line:

```json
{"item": "B1-01", "verdict": "KEEP", "quote": "exact words copied from the text", "born_no_later_than": "1893-06-15", "reason": "appointed in the Pension Office on 1893-06-15, before 1904-05-02; one beneficiary, one command"}
```

- `quote`: for KEEP, the exact words of the fact, copied character for character from `text` (OCR errors and all);
  for RETURN, the words that decided it if any, else "".
- `born_no_later_than`: for KEEP, the date the fact gives (for a year only, December 31 of that year; for a month,
  its last day); for RETURN, "" or the date if a fact was found but is too late.
- `reason`: one sentence. For RETURN start with one of `no_dated_fact`, `fact_too_late`, `fact_about_another_person`,
  `several_persons`, `second_command`, `condition`, `not_the_order`.
