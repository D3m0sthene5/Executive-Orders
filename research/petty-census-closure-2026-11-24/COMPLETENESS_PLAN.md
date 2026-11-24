# What it would take to say the census is complete

Owner question, 2026-11-24: what remains before the project can say it has found every executive order that any
online source mentions? This file records the answer so later sessions can carry the work forward. Every figure
comes from this wave's results (`CENSUS.md`) or from the sources cited.

## Where the census stands

The census is not complete. ProQuest's collection of unnumbered presidential documents for 1789 to 1936 was read
record by record on 2026-11-24 (19,918 of 20,028 catalog entries). It holds about 3,900 documents signed by the
President that are land orders or other operative orders and that no census list holds: about 1,700 land orders,
including about 900 in the numbered coal, petroleum, phosphate, potash and public-water series, and about 2,200
other orders and directives by their titles (`proquest-scan/REPORT.md`, `proquest-scan/CANDIDATES_MISSING.csv`).
Reading the documents behind a random 50 of them puts the executive orders among them at about 2,100: nearly all the
land orders, but only about a fifth of the other orders (`scan-check/REPORT.md`).

The literal claim, that the project holds every executive order mentioned anywhere online, cannot be shown,
because no one can enumerate every web page. A defensible claim can be made: **every major digitized corpus that
could record an executive order was searched systematically. Each search is logged. Successive independent
sources stopped adding new orders. The parts of the record that are not online are named, and their likely size
is estimated.**

## Already done, and not to be repeated

- **National Archives Record Group 11.** Its AWS catalog export was read in full on 2026-11-06
  (Kean F-20261106-mabillon-nara).
- **HathiTrust GPO slip volumes.** The 12 bound volumes for EO 4306 to 9284 were downloaded by the owner and read.
  HathiTrust holds no slip series before EO 4306, and its full-text search was refused by its robots/access gate
  (F-20261018-5, F-20261106-photius-gpo-volumes).
- **ProQuest TDM Studio.** The 2026-11-06 audit session found that it carries only Congressional Hearings from the
  Congressional product, so it is not a route.
- **ProQuest numbered orders.** The owner retrieved 2,797 PDFs of numbered orders (`ProQuest Pre-1937 Orders/`).
- **ProQuest's unnumbered collection, 1789 to 1936.** Every result page was read on 2026-11-24 and every record
  saved, classified by title and matched against the census (`proquest-scan/`). About 110 records were missed
  because records that share a date change order between page loads. The candidates are listed but not admitted.
- **The map of pre-1900 sources.** `jobs/census-completeness/data/SOURCE_UNIVERSE.csv` lists 40 series and the
  search status of each. Its open rows are the work list for pre-1900 orders.

## Work, in order of yield per cost

The early steps match bulk data the project can download for free, using scripts and no model tokens. They follow
the owner's standing rule to use tools before spending tokens.

1. **Match the whole CIS universe.** The Kaufman and Rogowski deposit (Harvard Dataverse doi:10.7910/DVN/6SGSTI,
   already held) lists 101,186 CIS accession numbers for 1789 to 2020, by record group. The pilot matched only four
   executive-order groups before 1937. Matching every group, by date, subject words and number, produces a
   candidate list.
2. **Match the GPO's Monthly Catalog.** GPO has digitized the *Monthly Catalog of U.S. Government Publications* for
   1895 to 2004 on govinfo and released about 1.2 million historic catalog records. Every executive order the GPO
   printed as a slip appears there with its number and date. Matching the records against the census tests the
   numbered series against a second contemporary listing, outside the WPA-to-OFR overlap.
3. **Match the National Archives catalog.** The catalog's descriptions can be downloaded in bulk from the AWS Open
   Data registry. Record group 11 was read on 2026-11-06. Pull record groups 49 (General Land Office), 48 (Interior), 75
   (Indian Affairs), 77 and 94 (War Department) and 185 (Panama Canal), and match file and item descriptions that
   name executive orders.
4. **Search the founding era.** The Founders Online API provides transcriptions for the papers of Washington, Adams,
   Jefferson and Madison. A keyword sweep finds directives from before 1820 that Lord missed.
5. **Run full-text sweeps through the runner.** Internet Archive full text,
   Chronicling America newspapers (1770 to 1963) and govinfo's Serial Set and Statutes at Large all refused this
   session's fetch tool. HathiTrust's full-text search is gated against robots (F-20261018-5) and is left out. A GitHub runner job can query them with logged parameters. The targets are the phrases
   "Executive Order", "by direction of the President" and "approved:" combined with reservation and withdrawal
   terms. Measure 5 to 10 queries before any full run.
6. **Recover the about 110 ProQuest records the reading missed,** by re-reading the busiest dates of 1912, 1918
   and 1933 to 1935 with narrow date ranges, and check the land-order series against the General Land Office annual
   reports and Interior's withdrawal schedules.
7. **Read the candidates.** Every machine candidate from steps 1 to 6 needs a person, or a two-reader machine
   check, to look at the document and decide whether it is presidential, distinct and an executive order. The CIS
   pilot showed that catalog data alone cannot settle this.
8. **Measure saturation.** For each new source, record what share of its executive orders the census already
   holds. When successive sources that do not copy each other add almost nothing, report that curve. Use
   capture-recapture only between sources that were compiled independently, such as CIS and the Monthly Catalog.
9. **Name what is not online.** About 0.49% of National Archives Record Group 11 is scanned (NARA Record Group
   Explorer). Departmental files and some presidential library holdings are not digitized either. The census paper
   should say so and estimate the size of the offline remainder from a sample, through a NARA reference request or
   visit.

## What the finished claim looks like

The finished census would come with a search ledger: every source, query, date, hit count and new find. A reader
could then check that the project searched each corpus, see where new finds ran out, and see the estimated size
of what exists only on paper.
