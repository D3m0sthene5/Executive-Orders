# APP ingest: what it moved, and the cheapest next unlocks (2026-10-18)

Branch `claude/app-ingest-2959a8` (PR into `app-executive-orders`). Source: the American Presidency Project
(APP) order pages harvested by `jobs/app-executive-orders/` (live lane and the Common Crawl / Wayback
archive lane). Every APP record is grade `mirror_transcription`, `secondary_compilation_transcription`,
`acceptable_as_original=false`: historical-document discovery, not identity authentication, original custody
or a legal finding. Nothing in this work changes a census, ledger, codebook or certified count. The certified
whole-lifecycle count stays **0**; the tracker's "ready for human review" count stays **130**.

## 1. What changed in the pipeline

| Stage | Before | After | How |
| --- | --- | --- | --- |
| claim-kit loader (`load_corpus`): census orders with an APP text | 522 | 9,812 | `jobs/app-transcriptions/` converts the archive lane's `MIRROR_FRAGMENTS.jsonl` (invisible to claim-kit's `FRAGMENTS*.jsonl` glob) into `output/FRAGMENTS.jsonl`; text paths only, records not marked lead-only are refused |
| ...of which had no text of any kind before | 522 | 3,068 (784 decided) | census orders with any held text: 8,735 -> 11,281 |
| ...with no held text acceptable as an original | 522 | 3,348 (803 decided) | |
| loader warnings caused by APP records | 0 | 0 | (1,312 pre-existing warnings, none from APP) |
| clause-drafts: orders with a draft inventory | 4,747 | 9,715 (+4,968, all APP-based) | APP is a fallback input; no existing draft was displaced or changed |
| ...decided orders with a draft | 1,806 | 3,153 (+1,347; 1,302 good, 45 partial) | |
| ...orders not segmentable / identity-quarantined | 1,672 / 144 | 150 / 10 | 1,557 previously unsegmentable and 142 previously quarantined orders now draft from their own APP heading |
| claim-drafts: decided drafts whose only gaps are judgment fields | 780 | 1,114 | same code and inputs with and without APP (local runs); APP original candidates (3,195) are all `compiled_transcription_lead`, never acceptable |
| claim-drafts readiness: clause_inventory / ending_or_current_basis at "confirm" | 887 / 763 | 1,271 / 1,115 | machine evidence present, agent must check it |
| claim-drafts mechanical check: pass / pass_with_unverified | 2,792 / 557 | 1,445 / 1,904 | APP clause quotes are exact but their source is custody-record-only, so they stay unverified |
| later-events text corpus | fr-originals + Stage 21 + Opus | + 9,843 APP order texts | `app-transcriptions/output/SOURCES.jsonl`; APP "in part" wording can flag but never withhold an OFR whole-order end |
| footnote leads | none | 2,664 sentence rows | `jobs/app-footnote-leads/` |

### Segmentation outcome per candidate copy (clause-drafts, every copy of every order segmented)

| Input | Copies | good | partial | failed (unusable, not located, identity doubt) |
| --- | ---: | ---: | ---: | ---: |
| APP texts from app-executive-orders | 9,812 | 9,089 (92.6%) | 563 (5.7%) | 160 (1.6%) |
| APP pages inside the Opus zip | 1,773 | 1,004 (56.6%) | 88 (5.0%) | 681 (38.4%) |
| Federal Register, born-digital (PDF text layer, HTML) | 1,785 | 961 (53.8%) | 789 (44.2%) | 35 (2.0%) |
| Federal Register, scanned issues (OCR) | 5,818 | 393 (6.8%) | 2,896 (49.8%) | 2,529 (43.5%) |
| All Federal Register texts | 7,603 | 1,354 (17.8%) | 3,685 (48.5%) | 2,564 (33.7%) |

The populations differ (APP spans 1789-2026; scanned FR is 1936-1993), and "good" means only that no
structural warning fired. APP's clean HTML-derived text splits far better than OCR, but every APP clause is a
transcription and must be checked against the official original before it enters a claim.

### Footnote leads (`jobs/app-footnote-leads/output/SUMMARY.json`)

| note_type | rows | notes |
| --- | ---: | --- |
| fr_citation | 1,199 | 1,071 publication-date notes, 87 announced future publication, 40 attachment notes, 1 bare `3 FR 547`; 1,184 publication dates inferred |
| not_published | 48 | 47 empty archive captures (reported as APP "[Not Published.]"), 1 note (EO 4601) |
| amended_by | 3 | 4 edges: EO 4601 <- 7962; EO 8533 <- 9543, 9774; EO 9265 <- 9706 |
| revoked_by / superseded_by | 0 / 0 | APP footnotes almost never carry disposition notes |
| other | 1,414 | press release 444, source citation (Kappler) 158, cross-reference 105, list items 103, release place 51, Weekly Compilation timing 37, APP note 26, unclassified 490 |

The footnotes are a weak lead source: APP does not reproduce the OFR disposition notes. The APP order *texts*
are the stronger later-event source (revocation sentences of later orders), now scanned by later-events.

### Categories and attributes (`jobs/app-transcriptions/output/CATEGORIES.csv`)

Every page carries the same categories (Presidential / Written Presidential Orders / Executive Orders). The
attribute is "Executive Orders" on archive captures and "Executive Order" on today's live pages, a capture-era
label change, not information about the order. Three pages carry a subject attribute (2 "National Parks &
Monuments", 1 "Memorial Day"). Nothing maps onto the family rules (which key on an acting instrument and a
mechanism) or the codebook; no rule was changed.

## 2. Readiness tracker, before and after (decided orders, n = 3,359; GitHub run 39181833471)

| Step | Done before | Done after | Change | Why |
| --- | ---: | ---: | ---: | --- |
| provisional_status | 3,359 | 3,359 | 0 | |
| original_text | 2,312 | 2,312 | 0 | APP is lead-only by design; `ONLY_COMPILED_TRANSCRIPTION_FOUND` rises from 2 to 892 decided orders (68 -> 3,172 of all orders) |
| clause_inventory | 178 | 178 | 0 | counts only checked claims; the 1,347 new draft inventories are agent inputs |
| ending_or_current_basis | 134 | 134 | 0 | claims only |
| savings_residuals | 166 | 166 | 0 | claims only |
| counterevidence | 2,470 | 2,470 | 0 | later-events now scans 17,462 texts (7,619 before; +3,843 APP-text edges); the guard kept 27 OFR whole-order ends that APP "in part" wording would otherwise have withheld, so no contrary lead was lost |
| shared_sources | 209 / 236 | 209 / 236 | 0 | |
| opus_media | 82 / 844 | 82 / 844 | 0 | |
| **ready for human review** | **130** | **130** | 0 | |

## 3. Cheapest remaining machine unlock per step, ranked by orders per machine-hour

Estimates of yield are marked as such; nothing below has been measured unless it says so.

| Rank | Step | Machine unlock | Orders it can move | Machine time | Orders / hour | What stays human |
| ---: | --- | --- | ---: | --- | ---: | --- |
| 1 | clause_inventory, ending_or_current_basis | Already done here: 1,347 more decided orders carry a draft inventory and claim-drafts now leaves 1,114 decided drafts with judgment-only gaps (780 before). The next machine step is claim-checker on agent-filled claims; it reruns on every claims commit (minutes). | up to 1,114 drafts whose gate passes once an agent decides | ~5 min per claim-drafts + claim-checker run | >10,000 (drafts); the bottleneck is agent judgment | every clause's state, first end or current basis; checking APP clause text against the official original |
| 2 | original_text | Search FR volume 1 (1936) issues by APP date and title for the 49 decided orders fr-originals could not route (`fr_volume_1_1936_not_in_ofr_index`); fr-originals already has the issue-PDF fetcher. | <= 49 decided (estimate 30-45) | ~0.5 h runner | ~60-90 | page check of each find (`needs_page_check`) |
| 3 | original_text | Feed the APP publication dates to fr-originals for undecided orders with an APP lead (12 1936-1993, 1 1994+); tiny, but it is the only footnote field that maps to a route. | 13 (undecided) | minutes | high but tiny | page check |
| 4 | opus_media | Queue the 472 `OPUS_MEDIA_REFETCH_NEEDED` URLs in `FETCH_QUEUE.jsonl` (source-ladder already does this). APP does not help. | <= 472 decided | ~1-2 h runner | ~250-450 | ambiguous matches (1), media never cited (217) |
| 5 | counterevidence | Nothing APP can do for the 693 pre-1937 orders blocked by `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE`: the tracker rightly requires the OFR catalog, and APP texts are not an official later-source corpus. A documented, bounded search per era (Lord, Richardson, WPA, APP, Statutes at Large) recorded in `EXHAUSTED.jsonl` is the route. | 693 decided | agent-written search records; little machine time | n/a | adequacy of each era's search; the 159 contrary leads and 36 quarantined conflicts |
| 6 | original_text | The 294 decided 1936-1993 orders the OFR index lists as "not received for publication" have no FR printing to fetch; their originals are at NARA (RG 11). APP gives title and date for a scan request. | 294 decided | none (scan requests) | n/a | archival request, custody, identity |
| 7 | original_text | 456 decided pre-1936 orders with only a transcription lead: official compilations already read (ofr-compilations, 1911/1912 GPO volumes) found none; next are NARA/State Department originals. | 456 decided | none (scan requests) | n/a | archival request, custody, identity |
| 8 | savings_residuals | No machine unlock from APP: savings are a reading of the order and its revoking order. claim-drafts already proposes savings sentences (regex) for agents. | 912 research | n/a | n/a | the savings judgment itself |
| 9 | shared_sources | 27 decided orders wait on specific shared sources (EO::4314 alone blocks 10): one source-ladder queue line each. APP does not help. | 27 | minutes | high | none beyond custody |

**Steps APP can never satisfy.** Original text custody (an APP page is a secondary transcription of a page,
possibly older than the live page, and its capture bytes are not the signed or printed original); identity
authentication (APP's heading, number and date are an editor's, and the census identities stay as they are);
provisional status; and independent human certification, which no machine output, including these, can
supply. APP can supply discovery (title, date, president, text to read), draft clause boundaries, and leads
to later events and publication dates.

## 4. GitHub verification

Run jobs [39181833471](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39181833471) on commit `8c341127`, results commit `1d376590`: `STATUS.json` succeeded (exit 0) for app-transcriptions, app-footnote-leads, clause-drafts, later-events, claim-drafts, readiness-tracker, claim-kit, family-rules, case-bundles, ofr-codification-1989 and daily-digest. clause-drafts on GitHub: 9,715 drafts, 4,968 from APP, 150 not segmented, 10 quarantined (identical to the local run); claim-drafts: 1,114 judgment-only drafts, 3,153 clause inventories. claim-kit moved `ACTING_PROVISIONS.jsonl`, `TEXT_CLAUSES.jsonl` and `ACTING_REPRESENTATIONS.jsonl` (over 95 MB) to the run download; they were already absent from the branch before this work and no other job reads them.

## 5. Follow-ups worth a decision

- 31 APP numbered orders are not census identities (for example EO 5853-5873, EO 5151A, 5605A, 5638A):
  candidates for `census-candidates`, never auto-admitted.
- later-events' Opus APP pages (`order_text_opus_mirror`) still withhold OFR whole-order ends on "in part"
  wording; whether the new transcription guard should cover them too is a change to existing outputs and
  needs the owner's or Astra's call.
- family-rules indexes every `.txt` under `jobs/`, so its sweep now includes about 10,700 APP texts and 4,968
  APP-based clause-draft texts; its owner should confirm its runtime and that mirror texts keep their
  authenticity gap there.
