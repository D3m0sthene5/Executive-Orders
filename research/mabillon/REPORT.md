# Mabillon: bulk sources of official originals for orders that lack one

Named for Jean Mabillon (1632-1707), whose *De re diplomatica* founded the science of authenticating original
documents. Session of 2026-11-05/06, branch `claude/mabillon-originals`.

## Conclusions

1. **The National Archives has not put the signed originals online, so RG 11 cannot be the bulk source.** The
   Archives' own public bulk export of its Catalog (AWS Open Data bucket `nara-national-archives-catalog`, keyless)
   was read in full for Record Group 11: 400 chunks, 231 MB, 14,622 descriptions. The series "Executive Orders"
   (NAID 299999, 1862-2020) has 41 item descriptions, 27 of them imaged (105 images), naming 29 orders between
   EO 3669 and EO 13125, a showcase of famous orders (9066, 9981, 10340 and so on). Only 3 of the 5,943 frame orders
   are imaged (EO 3669, 6101, 7037). The other RG 11 executive-order series (drafts, numeric and subject registers,
   card indexes, "Executive Orders Files") are described only at series level, with no images. A Catalog API key
   would not change this: the API serves the same descriptions. The signed originals can be had only as ProQuest's
   replica scans or a paid NARA reproduction; the owner chose ProQuest and no paid reproductions
   (Kean D-20261105-proquest-not-nara).
2. **The largest bulk source available today is already in the repository: 492 frame orders' official printings,
   proved by machine.** `jobs/hathi-gpo-orders` saved government-printed pages (GPO bound *Executive Orders* volumes
   from Wikimedia Commons, the 1974 GPO Hoover compilation, 1936 Federal Register issues) for orders 5076-8027, and
   the tracker files them as transcriptions. The new zero-token job `jobs/mabillon-held-printings` proves 492 of
   them strong (each passage is that order: its own closing number, its own printed segment scoring at least 0.5
   against the American Presidency Project's independent transcription, and beating every order numbered within 3
   by at least 0.15). Planted controls: 75 of 77 true pairs confirmed and 0 of 4,382 false pairs accepted, a 95%
   upper bound of 0.07% on the false-accept rate. Grade: `machine_read_government_printed_copy`, the grade
   Tischendorf uses; they count only if the owner registers the job (Kean ask A-20261106-mabillon-register).
   Another 59 are leads.
3. **No public set of slip prints or bound volumes covers orders below EO 5076.** The only GPO-bound numbered
   volumes found are the FDR-era Commons scans already read (6071-8027). The 1944 WPA list (Lord) is an index,
   not texts. HathiTrust's catalogue refuses automated requests; Google Books and loc.gov searches could not be
   read by the discovery tools. `jobs/mabillon-scan-inventory` lists the Commons category and Internet Archive
   holdings by number range so the gap is measured, not assumed (results below).
4. **Serials reprint only small subject groups, and reprints are leads, never originals.** The *Official U.S.
   Bulletin* (1917-19) and the *Panama Canal Record* (1907-41) printed some orders in full (an estimated few hundred
   at most); the Statutes at Large print proclamations, not executive orders; Treasury Decisions is unconfirmed. They
   are on the Internet Archive, which Tischendorf's full-text route already searches, so no new job was built for
   them.
5. **What remains.** Of the 5,943 frame orders, 2,558 have a ProQuest archival replica (pending a page check, as
   the codebook requires), 774 rest on a Civil Service Commission reprint, 82 on a Tischendorf lead, and **1,972 have
   no route to any official image** (2,443 of Herschel's projected 5,313; 738 of the 1,234 for which the original is
   the only blocker). For these the only known witness is the signed original in RG 11, so by the owner's decision their route is more
   ProQuest replica downloads (found by phrase search, since 1,957 are not on the owner's link list), each still
   needing the codebook's page check.

## Coverage against the orders lacking an official original

The frame is every order whose tracker blockers include NO_OFFICIAL_SOURCE_LOCATED (5,943 on 2026-11-05;
`frame.py`). Herschel's 5,313 and 1,234 are projections from 110 sampled orders; `frame.py` reproduces both exactly
from Herschel's outcomes, and the projected columns below apply Herschel's stratum weights to the same orders.
Each order is counted once, under its best route. Regenerate with `python3 -I research/mabillon/coverage.py`.

COVERAGE_TABLE

The projected columns rest on 110 sampled orders (94 of them in the census frame), so their uncertainty is wide;
the census column is exact. The held printings are all 1929-38 orders (numbers 5076-8027), which Herschel's sample
under-weights relative to the census.

## Sources examined

| Source | Orders it could cover | Grade | Access, robots and terms | Outcome |
|---|---:|---|---|---|
| NARA RG 11 "Executive Orders" (NAID 299999), Catalog bulk export | 3 frame orders imaged | image of the signed original; codebook grade not yet assigned | AWS Open Data bucket, anonymous HTTPS, no key; the dataset is published for bulk use. The Catalog API needs a key and asks users not to cache returned content; not used | job `mabillon-nara`, verified run |
| Other NARA record groups (State RG 59, Interior RG 48, Forest Service RG 95, White House Office RG 130) | NARA_OTHER_RGS | as above | same bucket | job `mabillon-nara`, second run |
| GPO bound volumes, 1974 GPO Hoover compilation, 1936 FR, already held | 492 strong, 59 leads | official printing, machine-located | already in the repository; no network | job `mabillon-held-printings`, verified run |
| Commons and Internet Archive volumes of numbered orders | SCAN_SUMMARY | official printing if GPO | Commons category HTML and IA advanced search, robots obeyed, 1 request a second | job `mabillon-scan-inventory` |
| HathiTrust bound sets | not measurable | official printing | catalogue and full-text answer automated requests with a challenge; not bypassed | none |
| ProQuest "Replica of Original" (owner's NYU access) | 2,558 held; the rest by phrase search | archival replica, pending page check | owner downloads by hand under NYU's terms | existing `pinakes-proquest-ingest` |
| *Official U.S. Bulletin*, *Panama Canal Record* | a few hundred at most (estimate) | reprint, lead only | Internet Archive, open | covered by Tischendorf's IA route |
| Statutes at Large 1907-36 | about 0 | | govinfo | vol. 35 prints proclamations, not executive orders |

Discovery notes with URLs: `discovery/NARA_RG11.md`, `discovery/GPO_SLIP_SETS.md`, `discovery/REPRINT_SERIALS.md`.

## How the held-printings match was made safe

Tischendorf's rule was first applied unchanged, and the planted controls failed in two instructive ways. First, the
saved passages are whole printed pages, so a passage often prints the next order too; 11 "false" pairs were in fact
true (the neighbour really is on the page). The negative was corrected to keep the passage's own number and swap only
the text, and the score is taken on the order's own segment, between the previous closing number tag and its own.
Second, orders issued as families (codes of fair competition, veterans regulations, land withdrawals for resurvey)
share rare wording, and 49 neighbour negatives still passed; the neighbour margin rule removed all 49 while keeping
75 of 77 positives. Both additions are local to the Mabillon job; Tischendorf was not edited. Its own routes also read
whole pages, so the same neighbour risk may apply there (recorded in Kean, and raised in `QUESTIONS.md`).

A ProQuest replica pre-check by the same method was considered and not built: only 68 of the 2,558 frame replicas
have an independent transcription to compare.

## Costs

Three discovery workers (Sonnet tier) used 97,085, 112,312 and 113,908 tokens and 4.2, 7.1 and 7.3 minutes
(`telemetry/WORKERS.csv`). The coordinator was Opus; its usage is in `telemetry/` from `jobs/bentham/sessions.py`.
The jobs spend no tokens: the RG 11 census read 231 MB in 63 seconds on a GitHub runner; the held-printings match
runs offline in about 15 seconds.

## What this does not do

No status, codebook, census, identity or certified count changed. Machine locations are not authentication; the
tracker reads none of these jobs until the owner registers them. Certified: 0.
