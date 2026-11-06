# Selden: official texts of the later instruments that act on an order

Named for John Selden (1584-1654), who went back to the records for the actual texts of statutes and precedents.
This is the work of the night of 2026-11-05/06, in lane `research/selden/` and `jobs/selden-*`. No status, census,
codebook or certified count changed. Eight lifecycle claims were filed through the ordinary claim-kit route
(`research/readiness/claims/claude-2026-11-06-selden-*.jsonl`); they enter the ready count only when the owner merges.
Certified: 0.

## Conclusions

**Most of Herschel's later-law blocker needs a source showing the order is still operative, or a search, rather
than a named instrument the project lacks.** Herschel projected that 1,814 open orders are blocked only by "later
law, notice or instrument needed for the ending or current basis". That projection rests on 21 sampled orders. Read
one by one (`HERSCHEL_21.csv`), they need, by projection weight:

| Need | Share of the 1,814 |
|---|---:|
| A source showing the order is still operative on 2026-10-14 (current CFR, agency program text) | 44% |
| An unspecified ending source | 14% |
| An unnamed later instrument | 13% |
| The text of the statute the order rests on | 12% |
| A fact date (a report submitted, a board dissolved) | 8% |
| A claim-kit own-terms record | 7% |
| National Emergencies Act continuation notices | 2% |
| A named later order the project lacks | 1% |

None of the 36 Herschel orders blocked on later law has a named acting instrument that the project merely lacks. For
30 of them, no acting instrument is named anywhere in the finding jobs. Twenty-one orders is a small sample, so these
shares are wide.

**Selden now holds official text for four routes**, all from verified runs on GitHub Actions (each job's
`output/STATUS.json`):

| Route (job) | Held | Custody | Orders reached |
|---|---|---|---|
| Federal Register full text, 1994 on (`selden-fr-citers`) | A bounded search for every one of the 13,138 orders with an open ending or counterevidence step; 4,820 later documents kept | Bytes kept and re-hashable; federalregister.gov full text built from GPO's XML | 1,769 orders have a later document that prints their number; 1,086 have a sentence printing an ending, amending or continuing word |
| Federal Register pages, 1936-1993 (`selden-fr-acting`) | 826 of 827 pages printing a named Public Land Order or other non-EO instrument | 803 daily issues byte-identical to the SHA-256 GPO publishes (PREMIS); page extracts committed | Acting sentence located for 652 order-instrument pairs, 447 orders |
| Statutes at Large, govinfo, 1789 on (`selden-statutes`) | 2,179 of 2,210 statutes named as acting, or cited by an open order's own text | sha256 of each granule PDF; text layer kept; 85 whole PDFs committed (the proof orders and those under 400 KB) | 4,394 orders whose own text cites a held statute |
| Census of acting instruments (`census.py`) | 16,322 leads, 5,579 acting instruments | none (no download) | 2,401 named instruments not held as official text |

Together, 1,513 orders now have a held later-instrument text with a located sentence that prints an act on them. For
382 of those, no acting instrument had been named anywhere before.

Of the 1,015 named non-EO instruments the project did not hold, 818 are now held (782 Public Land Orders, 23
statutes, 13 others). The 1,386 executive orders that act on other orders without an official text of their own
belong to the order-originals lane and are ranked for it in `ACTING_EO_TEXTS_NEEDED.csv`.

**The 30-order proof: 8 of 30 orders filed, 3 of them because of Selden texts.** Thirty orders were drawn at random
(seed 1584) from the 1,531 decided, unclaimed orders among the 1,814 later-law-only orders. They went through the ordinary claim kit,
with Selden's texts bound into the packets as exact excerpts (`SOURCE_SUPPLEMENT.json`). Each batch was then reviewed
by two independent blind Opus reviewers, with one planted control per batch: every end date moved back three years.
A claim files only if both reviewers upheld its exact hash.

| | Orders |
|---|---:|
| Filed (both reviewers upheld) | 8 |
| Rejected on review or at completion | 3 |
| Blocked by the producer, with the reason recorded | 16 |
| Refused at screening (the order's own text lacks custody) | 3 |

All five planted controls (one per reviewed batch) were caught by both reviewers. Four genuine controls were then upheld after reveal by both; for the fifth (EO 8116) one reviewer found a separate defect. No planted
claim filed. Per-order outcomes are in `proof/OUTCOMES.csv`.

- **Selden made the difference for 3 orders.** EO 7951 and 8480 end by Public Land Orders whose official Federal
  Register pages Selden fetched and verified against GPO's published SHA-256 (PLO 3277, 571, 686 and 835).
  EO 13934 needed the amendment, revocation and reinstatement chain (EO 13978, 14029 and 14189). Selden's Federal
  Register search found and kept those texts, and the claim binds them whole. A fourth, EO 8116 (ended by PLO 2292, also held by Selden), failed review on a
  different point: it says Proclamation 2416 is not held, but the project holds it (it renames the refuge), so the
  renaming is missing as a later event. That fix is one sentence and one event; it was not attempted tonight.
- **The other five filed orders (EO 9260, 10367, 10451, 10991 and 11196) needed no Selden text.** Their ending sources
  were already held. The proof population counts orders whose remaining step is later law, and that step was sometimes
  already met by texts the project held.
- **Review earned its cost.** Both blind reviewers rejected two producer claims on reasoning, not dates.
  - EO 8480's first version called the order's own authority (30 Stat. 11) a neighbouring artifact. It also read PLO
    571's date from OCR as March 6, 1949; the page image prints March 9.
  - EO 8116's first version claimed patents were residual effects of the reservation, which PLO 2292 does not say.

  Both were corrected and reviewed again blind (batch b4r). EO 9644 was rejected on the merits: EO 9691 ended its
  section 2 basis in early 1946, earlier than claimed. EO 8080 failed completion mechanically: a quotation was not
  found in the recheck text.

At this yield, about 1 order in 4 files (8 of 30), and Selden's texts decided 1 in 10 (3 of 30). Projected to the 1,531
decided orders, that is about 150 orders where a Selden text is what files the claim. Thirty is a small sample: the
95% interval runs from about 30 to 400.

## How the sentences are located

The locator (`jobs/selden-common/selden_common.py`) reuses Shepard's citation, relation-word and sentence code
(`jobs/shepard-citations/cites.py`). It adds:
- readings for OCR-split headings and printed lists of orders;
- readings for OFR revocation tables;
- the instrument's own text spans on a page that also prints neighbouring documents.

It was measured on 5,574 pairs in which OFR's editorial notes say a later order acted on an earlier one. For 77% of
them it found a sentence citing the target in the later order's own held text, and it located none of 21,940
planted negatives. By hand, 28 of 30 sentences it classed as acting on the order were right. Both errors came from
neighbouring documents, and such sentences are now written as cross-references. Every job run also carries planted
controls:

| Job | Recall on planted true pairs | False locations |
|---|---|---|
| `selden-fr-citers` | 79 of 80 | 0 of 312 |
| `selden-fr-acting` | 552 of 638 | 0 of 2,517 |

`census/LOCATOR_ADJUDICATION.md` has the samples. A located sentence is a lead to what the instrument says, never a
finding about its effect.

## Herschel's 21 later-law-only orders

Selden holds a plausible source for 6 of the 21, which carry 472 of the 1,814 projected orders (26%). These are
leads for a producer, not reviewed claims:
- the 2026 continuation notices for the North Korea (EO 13466) and Iran-related (EO 13553) emergencies;
- 2024 to 2026 Federal Register documents in which agencies act under EO 13879, 13953 and 13843, evidence that
  those orders still operate;
- the National Industrial Recovery Act text (48 Stat. 195) for EO 6595.

For the rest, the search found no later Federal Register document, or the need is a fact date or a kit record,
which no text supplies.

## What still blocks, ranked

`REMAINING.csv` ranks the 1,583 named instruments still without an official text by the orders they act on. The
executive orders lead (EO 12692, 12319, 11490, 11846) and belong to the originals lane. The rest are:
- 120 Public Land Orders with no 1936-1993 FR citation in BLM's table;
- 46 proclamations (govinfo's link service has no proclamation-number route);
- presidential notices before 1994;
- the 1972 Okinawa reversion treaty.

The proof's blocks show what the claims need beyond texts. Of the 16 blocked orders and 3 screen refusals, none is blocked for want of a non-order instrument's text that
Selden could fetch. EO 10685 lacks an accepted-grade text of the ending order EO 10827, which belongs to the originals
lane. The rest need something no acting-instrument text supplies:

| What the claim still needs | Orders |
|---|---|
| A held current source showing the order still operates on 2026-10-14, of an accepted grade (current CFR or USC note held only as a lead, or a conflict with the provisional status) | EO 10457, 11851, 12021 |
| A fact date: a report submitted, a conference concluded, a parent commission's end, persons appointed | EO 12091, 12545, 13205, 6028 |
| The end of a national emergency or a body created by statute, from a statute that does not name the order | EO 11270, 11599, 12304 |
| No instrument names the order as revoked or superseded; an amendment is not an end | EO 8734, 9709, 10907 |
| Custody: the order's own page image or text is not held (originals lane) | EO 11146, 12055, 13876, 14349 |
| An ending source held, but not at an accepted grade | EO 10685 |
| A mechanical source-binding defect: the dossier's hash for EO 9557 points to EO 9556's text | EO 9557 |

The statute rows show where an owner ruling is needed, not more downloads. Selden holds PL 92-255 and PL 94-412, but
under the evidence ruling a statute that does not name an order does not end it. A ruling on when a statute that
abolishes a body, or ends an emergency, ends an order resting on it would decide EO 11270, 11599 and 12304. The same
pattern recurs across the 1,814. This is ask A-20261106-1.

## Problems and their cost

- **Invalid search field.** The first full Federal Register search returned HTTP 400 for every order. One
  requested field name is not a valid API field, and the offline tests' fake server accepted it. About 45
  runner-minutes were lost. The job now fails when most requests fail (Kean F-20261106-selden-fr-api-400). The
  lesson was already in Kean (F-20261105-tischendorf-2) and was not applied.
- **Wrong pages kept.** The first Federal Register page run read only a window of pages around govinfo's page hint.
  The hint is often wrong, so about 750 of 825 pages kept were not the instrument's own. The job now reads the whole
  issue when the heading is missing, keeps only pages where the instrument's heading was found, and reads every own
  span on a page. Those three fixes took sentence location from 113 to 652 pairs.
- **Stale packets.** Merging `main` after the proof packets were sealed changed
  `jobs/claim-kit/source_supplement.py`. Every packet was refused at apply and had to be prepared again. Merge before
  sealing packets, never after.
- **Unbound statutes.** Statutes named as acting on an order but not printing its number were held but not bound
  into packets, so producers could not cite them. Fixed in `proof/tools/supplement.py`.
- **Worker processes.** `claude -p` workers cannot authenticate in this container, so the proof's producers and
  reviewers ran as subagents of this session. `jobs/bentham/sessions.py` found no transcripts on this machine, so
  `proof/telemetry/WORKERS.csv` records each worker's model and the total tokens the Agent tool reported.
- **Serial runs.** Jobs on one branch run in series. At the owner's request, downloads ran on parallel runner
  branches (`claude/selden-shard-*`) at the shared fetch pool's ceiling: 6 requests in flight per host, 0.1 s apart,
  robots.txt obeyed. Their outputs are united on this branch through each job's `data/shards/`.

## Registration and counts

`jobs/claim-kit/inputs.py` discovers every `jobs/*/output/FRAGMENTS*.jsonl` and `SOURCES.jsonl`. Merging this branch
therefore registers these sources with the claim kit and, through it, the readiness tracker. Together with the eight
filed claims, that can change counts, so it waits for the owner's merge.

`jobs/claim-kit/source_supplement.py` adds held excerpts only to decided dossiers (Kean
F-20261106-selden-supplement-decided-only). The coordinator has since extended it to the overlay route (`main`
48da66f755), which lets these texts reach undecided orders.
