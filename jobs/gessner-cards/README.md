# Gessner cards: one card per executive order

Named for Conrad Gessner (1516–1565), the Zurich bibliographer whose 1548 *Pandectae* explained how to
build an index on separate strips of paper, one entry each, so the entries could be re-sorted at will.
This job does the same for the project's unit of analysis: one card per executive order.

**Output:** `output/CARDS.html`, a self-contained page (data embedded, no network calls except Google Fonts)
with a card for each of the 14,972 orders in the working census, and `output/SUMMARY.json`.

Each card shows the order's number, date, president, title, provisional YES/NO status, a segmented bar of
the readiness steps that apply to it (done, provisional working text, or open), and whether its dossier is
ready for human review. Clicking a card opens the steps, the blockers in plain English, the best document
held, the text-evidence tier and any obligation to replace a transcription with an original. The page also
shows the pipeline counts and a mosaic with one square per order, grouped by president, which the filters dim.

## Inputs (read only)

- `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv` and `STATUS.json`: status, steps, readiness,
  blockers. Every readiness figure on the page is tallied from these rows; nothing is re-measured.
- `jobs/domesday-register/output/REGISTER.csv` and `SUMMARY.json`: number, date, title, president, era,
  best document held.

The tracker's generation is named on the page (run time, run link, commit). The register can be older than
the tracker; the page names both dates. Census candidates not yet admitted are not shown.

## President names derived from dates

The register leaves the president blank for about a third of the orders. For those, the page derives the
name from the order's date using the dates each president took office, and the detail panel says so. An
order dated on a term's first day is left as uncertain, as is a year-only or month-only date that spans a
change of president. Where the register names a president, the register wins. Checked against the 9,889
register rows that name a president and have a full date: the date rule agrees on all but two, both of which
look like register errors (EO 8969 dated 1946-12-11 but credited to Franklin D. Roosevelt; EO 10276 dated
1961-07-31 but credited to Harry S. Truman).

## What this page does not do

It assigns no status, grades no source and changes no count. "Ready for human review" means the machines
have finished every step; human certification is a separate count and the page shows it as the tracker
reports it (0).

## Running

Runs daily (`DAILY`) and after `readiness-tracker` and `domesday-register` when they run together
(`after.txt`). Tests in `test_build_cards.py` run first; the page is not built if they fail. Locally:
`OUTPUT_DIR=/tmp/cards python3 -I jobs/gessner-cards/build_cards.py`.
