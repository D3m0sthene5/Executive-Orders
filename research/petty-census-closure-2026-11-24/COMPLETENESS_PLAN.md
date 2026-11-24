# What it would take to say the census is complete

Owner question, 2026-11-24: what remains before the project can say it has found every executive order that any
online source mentions? This file records the answer so later sessions can carry the work forward. Every figure
comes from this wave's results (`CENSUS.md`) or from the sources cited.

## Where the census stands

The census is not complete. Three findings show what is still missing.

- **The CIS pilot.** About 470 to 770 presidential land and canal orders in the CIS index are in no project list.
  This is an estimate from a sample of 30, and it rests on ProQuest's catalog data rather than the scans.
- **The rest of CIS.** 1,645 more CIS documents in the same record groups have not been examined.
- **ProQuest's unnumbered collection.** ProQuest describes 20,028 unnumbered orders, directives and proclamations
  for 1789 to 1936 (`research/pre-1937-sources/PROQUEST_CONGRESSIONAL.md`). The audited unnumbered series is
  1,405 to 1,816. Many of ProQuest's records are proclamations, pardons or departmental papers, but nobody has yet
  measured how many are executive orders the census lacks.

The literal claim, that the project holds every executive order mentioned anywhere online, cannot be shown,
because no one can enumerate every web page. A defensible claim can be made: **every major digitized corpus that
could record an executive order was searched systematically. Each search is logged. Successive independent
sources stopped adding new orders. The parts of the record that are not online are named, and their likely size
is estimated.**

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
   Data registry. Pull record groups 11 (presidential documents), 49 (General Land Office), 48 (Interior), 75
   (Indian Affairs), 77 and 94 (War Department) and 185 (Panama Canal), and match file and item descriptions that
   name executive orders.
4. **Search the founding era.** The Founders Online API provides transcriptions for the papers of Washington, Adams,
   Jefferson and Madison. A keyword sweep finds directives from before 1820 that Lord missed.
5. **Run full-text sweeps through the runner.** HathiTrust full-text search, Internet Archive full text,
   Chronicling America newspapers (1770 to 1963) and govinfo's Serial Set and Statutes at Large all refused this
   session's fetch tool. A GitHub runner job can query them with logged parameters. The targets are the phrases
   "Executive Order", "by direction of the President" and "approved:" combined with reservation and withdrawal
   terms. Measure 5 to 10 queries before any full run.
6. **Get ProQuest's metadata by licensed means.** NYU offers ProQuest TDM Studio, a licensed text-mining service,
   to anyone with an NYU email (guides.nyu.edu/TDMStudio). If the *Executive Orders and Presidential Proclamations*
   collection is among NYU's TDM datasets, its 53,671 pre-1937 records can be read under license. If it is not,
   ask NYU's librarians or ProQuest for a metadata export. Do not scrape ProQuest at scale: it risks NYU's license.
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
