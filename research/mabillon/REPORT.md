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
2. **The largest bulk source available today is already in the repository: official printings for 1,771 orders,
   762 of them in the frame, proved by machine.** `jobs/hathi-gpo-orders` saved government-printed pages for orders
   5076-8027: GPO bound *Executive Orders* slip volumes from Wikimedia Commons, the 1974 GPO Hoover compilation and
   1936 Federal Register issues. It OCRed the Commons volumes whole but cut out passages only for orders with no
   text at all, and the tracker files everything it holds as transcriptions. The new zero-token job
   `jobs/mabillon-held-printings` reads both the saved passages and the committed page dumps. It proves 1,771 orders
   strong. Each passage carries the order's own closing number, its own printed segment scores at least 0.5 against
   the American Presidency Project's independent transcription, and it beats every order numbered within 3 by at
   least 0.15. Planted controls: 86 of 88 true pairs confirmed and 0 of 6,834 false pairs accepted, a 95% upper
   bound of 0.04% on the false-accept rate. Of the 1,771, 762 are frame orders and 1,009 are orders whose working
   text is a transcription that must be replaced by the official original (Herschel's replace step). 393 of them are
   among Selden's 1,386 acting orders without an official text, and those act on 517 orders. Another 244 passages
   are leads. Grade: `machine_read_government_printed_copy`, the grade Tischendorf uses. They count only once the
   job is registered with the tracker, in the separate count-changing PR #164 (Kean ask
   A-20261106-mabillon-register).
3. **No public set of slip prints or bound volumes covers orders below EO 5800.** `jobs/mabillon-scan-inventory`
   read every U.S. presidential category on Wikimedia Commons (Lincoln to F. D. Roosevelt, the national category and
   the National Archives' own upload series; 10 category pages, 67 files) and the Internet Archive's catalogue of
   texts titled "executive orders" (152 U.S. items after dropping Philippine and state-governor series). The only
   numbered GPO volumes are 5800-6070, 6071-8027 (already read by `hathi-gpo-orders`) and 8032-9003, outside the
   frame. The per-president categories hold single showcase files. The 1944 WPA list (Lord) is an index, not texts.
   HathiTrust's catalogue answers automated requests with a challenge and was not bypassed, so bound sets held only
   there remain unmeasured; the Commons GPO volumes were themselves uploaded from HathiTrust, which suggests
   HathiTrust's full-view holdings begin around the same point, but that is an inference.
4. **Serials reprint only small subject groups, and reprints are leads, never originals.** The *Official U.S.
   Bulletin* (1917-19) and the *Panama Canal Record* (1907-41) printed some orders in full (an estimated few hundred
   at most); the Statutes at Large print proclamations, not executive orders; Treasury Decisions is unconfirmed. They
   are on the Internet Archive, which Tischendorf's full-text route already searches, so no new job was built for
   them.
5. **What remains.** Besides the 762 held printings proved (and 108 held-printing leads), of the 5,943 frame orders 2,558 have a ProQuest archival replica (pending a page check, as
   the codebook requires), 774 rest on a Civil Service Commission reprint, 82 on a Tischendorf lead, 120 lie inside a
   held or listed GPO volume's range without a located passage, and **1,535 have no route to any official image**
   (1,672 of Herschel's projected 5,313; 473 of the 1,234 for which the original is the only blocker). For these the only known witness is the
   signed original in RG 11, so by the owner's decision their route is more ProQuest replica downloads, found by
   phrase search because 1,520 of them are not on the owner's link list, each still needing the codebook's page
   check.

## Coverage against the orders lacking an official original

The frame is every order whose tracker blockers include NO_OFFICIAL_SOURCE_LOCATED (5,943 on 2026-11-05;
`frame.py`). Herschel's 5,313 and 1,234 are projections from 110 sampled orders; `frame.py` reproduces both exactly
from Herschel's outcomes, and the projected columns below apply Herschel's stratum weights to the same orders.
Each order is counted once, under its best route. Regenerate with `python3 -I research/mabillon/coverage.py`.

| Best route | Grade | Frame orders (census) | Of Herschel's 5,313 (projected) | Of the 1,234 sole-blocked (projected) |
|---|---|---:|---:|---:|
| `held_printing_strong` | official printing, machine-located (Tischendorf rule plus segment and margin); counts only after the owner registers the job | 762 | 572 | 152 |
| `tischendorf_strong` | official printing, machine-located (Tischendorf); counts only after registration | 3 | 0 | 0 |
| `nara_signed_original_image` | image of the signed original in RG 11; codebook grade pending; page check | 1 | 0 | 0 |
| `proquest_archival_replica` | archival replica of the signed original; stays pending a page check | 2,558 | 1,613 | 319 |
| `held_printing_lead` | official printing held, lead (a check failed or no independent text) | 108 | 54 | 0 |
| `tischendorf_lead` | official-printing or reprint lead; page check | 82 | 221 | 123 |
| `csc_report_reprint` | reprint in a Civil Service Commission annual report; lead only, never the original | 774 | 661 | 0 |
| `official_find_page_check_pending` | official find already on file (fr-originals, ofr-compilations), flagged for a page check; Tischendorf corroborates | 0 | 127 | 0 |
| `listed_volume_range` | a digitized volume's title range includes the number; ceiling only | 120 | 395 | 167 |
| `none` | no route found; signed original at NARA (RG 11, not digitized) is the only known witness | 1,535 | 1,672 | 473 |
| **Total** | | **5,943** | **5,313** | **1,234** |

Orders outside the frame whose working text is a transcription that must be replaced by the official original (1,911; Herschel's replace step):

| Best route | Orders |
|---|---:|
| `held_printing_strong` | 1,009 |
| `tischendorf_strong` | 33 |
| `proquest_archival_replica` | 192 |
| `held_printing_lead` | 135 |
| `tischendorf_lead` | 21 |
| `listed_volume_range` | 295 |
| `none` | 226 |

Selden's acting orders without an official text (1,386; `research/selden/ACTING_EO_TEXTS_NEEDED.csv`, copied to `frame/`):

| Best route | Acting orders | Orders they act on (leads, as Selden counts them) |
|---|---:|---:|
| `held_printing_strong` | 393 | 517 |
| `tischendorf_strong` | 21 | 29 |
| `proquest_archival_replica` | 277 | 317 |
| `held_printing_lead` | 22 | 28 |
| `tischendorf_lead` | 69 | 114 |
| `csc_report_reprint` | 47 | 56 |
| `official_find_page_check_pending` | 48 | 111 |
| `listed_volume_range` | 64 | 89 |
| `none` | 445 | 517 |

By era (census):

| Era | held_printing_strong | tischendorf_strong | nara_signed_original_image | proquest_archival_replica | held_printing_lead | tischendorf_lead | csc_report_reprint | official_find_page_check_pending | listed_volume_range | none |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1862–1906 | 0 | 0 | 0 | 101 | 0 | 8 | 11 | 0 | 0 | 454 |
| 1907–1936 | 671 | 3 | 1 | 2,426 | 106 | 74 | 762 | 0 | 97 | 1,010 |
| 1937–1989 | 87 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 23 | 14 |
| Unknown date | 4 | 0 | 0 | 27 | 2 | 0 | 1 | 0 | 0 | 57 |

The projected columns rest on 110 sampled orders (94 of them in the census frame), so their uncertainty is wide;
the census column is exact. The held printings are all 1929-38 orders (numbers 5076-8027), which Herschel's sample
under-weights relative to the census.

## Sources examined

| Source | Orders it could cover | Grade | Access, robots and terms | Outcome |
|---|---:|---|---|---|
| NARA RG 11 "Executive Orders" (NAID 299999), Catalog bulk export | 3 frame orders imaged | image of the signed original; codebook grade not yet assigned | AWS Open Data bucket, anonymous HTTPS, no key; the dataset is published for bulk use. The Catalog API needs a key and asks users not to cache returned content; not used | job `mabillon-nara`, verified run |
| Other NARA record groups (State RG 59, Interior RG 48, Forest Service RG 95, White House Office RG 130) | 0 imaged; RG 48, 95 and 130 have executive-order series described at series level only, and RG 59 (18 GB) was skipped whole by the cap rule | as above | same bucket | job `mabillon-nara`, second run |
| GPO bound volumes, 1974 GPO Hoover compilation, 1936 FR, already held | 762 frame orders strong (1,771 in all), 108 frame leads | official printing, machine-located | already in the repository; no network | job `mabillon-held-printings`, verified run |
| Commons and Internet Archive volumes of numbered orders | 0 below EO 5800: Commons holds GPO volumes 5800-6070, 6071-8027 (all already read) and 8032-9003; IA holds the Hoover and Indian-reservation compilations already used | official printing if GPO | Commons category HTML and IA advanced search, robots obeyed, 1 request a second | job `mabillon-scan-inventory` |
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
(`telemetry/WORKERS.csv`). The coordinator was Opus 5.5; `jobs/bentham/sessions.py` found no usage records in this environment's local transcript, so its tokens are unmeasured (`telemetry/AGENT_USAGE.csv` records the gap rather than a zero).
The jobs spend no tokens. Bytes and time were estimated before each read: the RG 11 census read 231 MB in 63 seconds; the second census planned 1.85 GB over RG 11, 48, 95 and 130 (RG 59's 18 GB skipped) and read it in 181 seconds; the held-printings match
runs offline in about a minute.

## What this does not do

No status, codebook, census, identity or certified count changed. Machine locations are not authentication; the
tracker reads none of these jobs until the owner registers them. Certified: 0.
