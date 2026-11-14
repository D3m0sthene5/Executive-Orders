# B. What "missing" means: blocker decomposition (analyst 2 of 3, 2026-11-13)

Question tested: "missing sources, not workflow, blocks most progress" (from the Lind pilot, 22 of 30 coded ME, and a
script census). Analyses A (`A_EVIDENCE_BRIEF.md`) and C (`C_REUSE_AND_PARTIAL_UNITS.md`) are not repeated here (C
covers the NMB boards, EO 13286 mirror representation and NEA notices).

**Basis.** Repository HEAD `f89b1f976780c76b218154768d1f061eb515b1c6`. No paid agent, job, network call or git change.
Local reads only, plus 17 `cruden.py number` lookups (about 31 s each). Scratch scripts and the per-order table are in
`/tmp/claude-0/-home-user/bb339822-ebbb-5ac8-8a64-5a8ce52045fd/scratchpad/b2/` (`p2.py`..`p5.py`, `orders.csv`); they
are not committed.

**Labels:** **[obs]** observed at the path given; **[int]** interpretation; **[proj]** projection; **[unres]**
unresolved. Human-certified whole-lifecycle count: 0.

**Categories used:**
- (a) not located anywhere known.
- (b) located (a known archive, collection, URL or film) but not acquired.
- (c) acquired, but custody is hash-only.
- (d) held in the repository but not routed into the order's packet or dossier.
- (e) held, but extraction or segmentation failed.
- (f) a requirement set by our own schema, admission or gating rules.

"Workflow" here means that nothing is missing and the order has simply not been worked.

**Era assignment [int].** Year from `research/pre-1937-sources/GAP_ROUTES.csv` or
`jobs/pinakes-proquest-ingest/output/ORDERS.csv` where given. Otherwise by number: EO ≥ 7532 is modern; EO ≤ 122 is
pre-1900 (122 is the highest number dated before 1900 in those files); the rest are 1900-1936. IDs without a number
are counted as unnumbered.

---

## 1. Verdict

**The claim does not hold as stated. It holds for the ending stage of pre-1937 orders, and only if "missing" is read
as "not yet acquired".**

1. **Modern orders: the binding constraint is the work itself and our own gates, not sources [obs].**
   - Undecided modern orders: 2,693 of 4,215 (64%) pass every Larrey gate, and another 943 fail only soft gates.
   - Decided modern orders: 961 of 1,808 not-ready orders carry only claim-writing blockers.
   - [int] The Lind ME cases among modern orders were mostly (b), (e) or (f) (§4).
2. **Orders from 1900 to 1936.**
   - **Original-text stage:** dominated by (f), held machine-read government printings that our grade rule refuses
     (1,724), and by (b), mirror or compiled transcriptions where an official printing exists elsewhere (1,771) [obs].
   - **Ending stage:** dominated by (b). The ending evidence is in known collections (land-status records, Public Land
     Orders, Statutes at Large, agency reports) but not acquired [int, from sample].
   - (a) is real but a minority: personal fact dates and some 1890s-1910s endings.
3. **Pre-1900 (104 undecided):** originals are (f) or (b), and endings are mostly (a) [obs, small n].
4. **(d), held but not routed:** real but not dominant. 2 to 3 of the 18 sampled orders [obs]. Across the collection,
   at most about 4% of pre-1937 orders blocked on ending or later-act evidence have a held text that names them with
   acting words and is not linked to them (§3) [obs, upper bound with caveats].
5. **The Lind "missing evidence" count overstates unavailability.**
   - 6 of the 7 dispatch-blocked orders (EO 4658, 4475, 4621, 4788, 4861, 4968) now have ProQuest PDFs in the
     repository and no hard-gate failure in `jobs/larrey-triage/output/GATES.jsonl` [obs]. The ProQuest ingest is
     dated 2026-11-12T18:25Z (`jobs/pinakes-proquest-ingest/output/SUMMARY.json`).
   - [int] Their "missing source" was (b), and it has since been cured.

---

## 2. Population decomposition

Source: `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`, generation `43290372543-1`: 15,002 orders, 3,788
decided, 1,251 ready.

Gates: `jobs/larrey-triage/output/GATES.jsonl`, using the `undecided_full` route for undecided orders and the
`decided_lifecycle` route for decided ones [obs].

### 2.1 Orders by era

| Era | Undecided | Decided | Decided, ready | Decided, not ready |
|---|---:|---:|---:|---:|
| Modern | 4,215 | 2,725 | 917 | 1,808 |
| 1900-1936 | 6,878 | 1,050 | 334 | 716 |
| Pre-1900 | 104 | 11 | 0 | 11 |
| Unnumbered | 17 | 2 | 0 | 2 |
| **Total** | **11,214** | **3,788** | **1,251** | **2,537** |

### 2.2 Undecided orders: hard-gate profile [obs]

Each order is counted once.

| Era (n) | All gates pass | Soft gates only | Original only | Status basis only | Original and status basis | No held text |
|---|---:|---:|---:|---:|---:|---:|
| Modern (4,215) | 2,693 | 943 | 53 | 441 | 79 | 6 |
| 1900-1936 (6,878) | 805 | 918 | 2,084 | 1,393 | 1,640 | 38 |
| Pre-1900 (104) | 10 | 1 | 65 | 5 | 22 | 1 |
| Unnumbered (17) | 0 | 0 | 0 | 0 | 1 | 16 |

Column meanings:
- **Original only:** fails only `original_not_usable`.
- **Status basis only:** fails only `no_status_basis_record`.
- **Original and status basis:** fails both.
- **No held text:** `no_held_text`, with or without `no_status_basis_record`.

### 2.3 Undecided orders: each blocking reason mapped to a category

Counts are orders that have the reason; one order can have several.

| Recorded reason (Larrey) | Modern | 1900-1936 | Pre-1900 | Category [int] | Why |
|---|---:|---:|---:|---|---|
| `original_not_usable:machine_read_government_printed_copy` | 63 | 1,724 | 46 | **(f)**, partly (e) | An OCR of a government printing is held (Hathi GPO, Mabillon, Tischendorf). The codebook does not credit it without a check. |
| `original_not_usable:mirror_transcription` | 68 | 1,210 | 36 | **(b)** | An APP or Wikisource text is held. For modern orders the FR printing is at govinfo. For pre-1937 orders the official printing is in known series (ProQuest CIS, CSR, departmental registers). None is a ProQuest-held order [obs]. |
| `original_not_usable:compiled_transcription_lead` | 0 | 561 | 0 | (b) or (a) | A compilation lead only. **[unres]** which are located. |
| `original_not_usable:government_printed_copy` / `official_printing` / `archival_replica_*` | 1 | 229 | 2 | **(f)/(c)** | An official image is held; 137 of these are ProQuest PDFs [obs]. A page or codebook check is owed. |
| `no_held_text` | 6 | 38 | 1 | (a) or (b) | Includes 16 unnumbered orders. |
| `no_status_basis_record` | 525 | 3,063 | 27 | mostly **(b)** before 1937; mixed for modern; **(e)** for at least 44 modern | See §3. 1,217 of the 3,063 (1900-1936) have a usable ProQuest original: only the ending is lacking [obs]. |
| `soft:no_later_order_text_held` | 1,368 | 4,840 | 47 | **(f)** | Many orders were never acted on by a later instrument. Requiring one is a gate, not a lack of evidence. It is the sole reason for 1,592 orders (`REASONS.json`). |
| `soft:page_check_owed` | 251 | 2,599 | 85 | **(f)** (or (c)) | The page image is normally held; the check is our requirement. |

### 2.4 Decided, not-ready orders: tracker blockers grouped [obs]

| Era (n) | Claim-writing or claim-check blockers present | Only claim-writing blockers | Located but not acquired or not checked | OFR catalog search incomplete | No official source located, or only a compiled transcription |
|---|---:|---:|---:|---:|---:|
| Modern (1,808) | 1,778 | **961** | 432 | 0 | 18 |
| 1900-1936 (716) | 716 | 6 | 105 | 708 | 207 |
| Pre-1900 (11) | 11 | 0 | 5 | 11 | 8 |

Blocker codes in each group:
- **Claim-writing or claim-check:** `NO_CLAUSE_INVENTORY`, `FIRST_END_UNPROVED`, `SAVINGS_RESIDUALS_NOT_CLOSED`,
  `CLAIM_INCOMPLETE:*`, `CLAIM_CHECK_FAILED:*`, `FIRST_END_UNRESOLVED`, `CURRENT_BASIS_UNPROVED`.
- **Located but not acquired or not checked:** `OPUS_MEDIA_REFETCH_NEEDED` (414 modern), `ORIGINAL_FOUND_NEEDS_PAGE_CHECK`,
  `SHARED_SOURCE_NOT_RETRIEVED`.
- **No official source located, or only a compiled transcription:** `NO_OFFICIAL_SOURCE_LOCATED`,
  `ONLY_COMPILED_TRANSCRIPTION_FOUND`.

Larrey also keeps out 97 modern decided orders on `soft:nea_continuation_notice_not_held`. That is (b): the notices are
FR documents.

[int] For decided orders, the lifecycle sheet is the work: 98.8% (2,507 of 2,537) carry a claim-writing blocker. For
pre-1937 decided orders, our OFR-catalog search requirement (f) sits on 708 of 716.

### 2.5 Other sources of blocking reasons

| Source [obs] | What it records | Category [int] |
|---|---|---|
| `jobs/claim-kit/output/MISSING_SOURCES.jsonl` (10,258 rows) | 9,231 "target provision not located"; 681 "cited by number, no change provision located"; 342 name-match leads; 4 "acting text absent" | Almost all are **(e)**: the actor text is held, and the kit could not locate the provision. At least one is a parse artifact (EO 110 ← "Executive Order 110.30", §4). |
| `research/excavator/claude-respondendi-2026-11-10/DIAGNOSIS.csv` (111 rows) | route or tool defect 46; missing later event 35; rule too strict 18; producer error 11 | (d)/(e) 46; (f) 18; the 35 "missing" split into fact dates 12, current-status source 9, statutes 7, PLOs 3, others 4, which are mostly (b) |
| `research/readiness/FETCH_QUEUE.jsonl` (1,342 rows) | Acquisition requests, mainly `original_text` (lewis-originals 266) and `ending_or_current_basis` | (b) by construction: each row names a located citation |
| `jobs/cotton-capture-custody/output/FAILURES.jsonl` | 1 row (EO 7208: no fixed capture reproduces the live APP bytes) | (c) |
| `jobs/astra-source-retention/REQUESTS.json` | govinfo FR PDF URLs with expected hashes | (c)/(b): located, retention owed |
| Lind `FAILURES.md`, 22 ME orders | Reclassified in §4 | (b) about 12; (f) about 5; (e) 2; (a) about 3 |

---

## 3. How common is (d), held but not routed, at collection scale?

**Method [obs].**
1. I scanned every held text in `jobs/fr-originals/data/full_run/texts` (6,652 files) and
   `jobs/wikisource-texts/output/texts`. The pattern caught citations by number, including OCR-split words and lists
   ("Executive O rder Nos. 11835, …, 12340"). It skipped heading lines and Wikisource navigation lines.
2. A citation was flagged as acting when one of these words appeared within about 250 characters: revoke, supersede,
   amend, rescind, terminate, modify, abolish, vacate, restore, repeal, cancel, extend.
3. A naming text counted as *routed* when its order appeared among the target's `known_actor_ids`
   (`OVERLAY_INPUTS*.jsonl`), `ACTING_PROVISIONS*` actors, later-events `EDGES.csv` actors, or `MISSING_SOURCES`
   actors.

Check: the scan finds EO 12473 naming EO 12340 with an acting word, and finds no link for it, as the coordinator
verified.

**Counts.** The denominator is undecided orders that fail `no_status_basis_record` or `soft:no_later_order_text_held`.

| Era | Denominator | Held namer not routed (any) | Same, with acting words: **(d) candidates** | Held current-law mention | No held trace in this scan, in the kit indexes, or in current law |
|---|---:|---:|---:|---:|---:|
| Modern | 1,368 | 38 | **7** | 349 | 930 |
| 1900-1936 | 4,840 | 261 | **179** | 54 | 4,513 |
| Pre-1900 | 47 | 13 | **6** | 2 | 33 |

### Caveats [int]

- **Upper bound for these corpora.** An FR text file holds neighbouring documents, so the "namer" is the file the text
  sits in. Example: EO 11156 is revoked by EO 11427, which is held inside `EO_11426.txt` and also routed. Acting words
  near a citation do not prove the text acts on the order.
- **Lower bound for the repository as a whole.** The scan omits `app-executive-orders`, `source-ladder`, `selden-*`,
  ProQuest OCR and eCFR texts.
- **Held current-law mentions that are not framed:**
  - 64 modern orders fail `no_status_basis_record` yet have current-law mentions.
  - For 44 of them, `STATUS_LEADS` carries `current_law_leads`, but every lead lacks text and character offsets, so
    the kit cannot frame it as a CURRENT record [obs]. That is (e), with the evidence held.
  - The roles include 4 `ending_order_in_status_line` and 2 `amending_order_in_ended_status_line` [obs].
- **Tooling gap [obs].** For EO:12340, `cruden.py number` returned 4 hits and none was EO 12473. Cruden does not match
  list-form or OCR-split citations. Number search therefore cannot be relied on to find category (d).

---

## 4. Stratified sample (18 orders, inspected directly)

**How it was drawn.** Random draw, seed 20261113, from strata of not-ready orders in `orders.csv`. Pool sizes are
shown with each group.

**What was checked for each order:**
- the overlay `selected` original;
- `known_actor_ids`, `STATUS_LEADS`, `ACTING_PROVISIONS`, `OWN_TERMS` and `MISSING_SOURCES`;
- later-events `EDGES.csv`;
- current-law `MENTIONS.csv`;
- ProQuest `ORDERS.csv`;
- a `cruden.py number` lookup (every order except the unnumbered one).

### Modern, undecided, soft gates only (two pools: 100 with an unrouted namer, 785 without)

| Order | Recorded block | What the evidence shows | Category |
|---|---|---|---|
| EO 11156 (1964) | `soft:page_check_owed` | Revoker EO 11427 is held (`jobs/fr-originals/output/texts/EO_11427.recheck.txt`) and routed as an ACT, terminate, whole. Nothing is missing. | **(f)** |
| EO 10024 (1948) | `soft:no_later_order_text_held` | Land restoration to mining entry; own-terms `until_event` is held. Cruden finds 0 other texts. A later act is probably not expected. | **(f)** |
| EO 12632 (1988) | `soft:page_check_owed` | 13 amending ACTs held; the 5 U.S.C. 7103 note prints the text and its status line. | **(f)** |

### Modern, undecided, hard gate failed (pool 454 with no namer; pool 64 with a current-law mention)

| Order | Recorded block | What the evidence shows | Category |
|---|---|---|---|
| EO 7899 (1938) | machine-read original; no status basis | Appointment of a named person (Miss Amy G. Maher, Social Security Board) without regard to civil service. Only a Mabillon deposit-copy OCR is held. The FR 1938 printing is located but not in fr-originals. The end is her separation: no fact date held. The 2 cruden hits are PLO 7899, a false match. | (b) for the original; **(a)** for the end, or (f) under PD-CS-ONE-PERSON |
| EO 8568 (1940) | no status basis | FR original held; the order provides for administering an Act. Cruden: 0. The statute's later status is not held, though it is findable in U.S. Code notes and the Statutes at Large. | **(b)** |
| EO 10086 (1949) | no status basis | Designates the South Pacific Commission. **Current eCFR 8 CFR 316.20 lists "South Pacific Commission (E.O. 10086, Nov. 25, 1949)"**, held at `jobs/source-ladder/output/texts/queue_EO_11866_8_CFR_316.20_…`; the 22 U.S.C. 288 note is held too. The status lead exists without text or offsets, so it is not a basis. | **(e)/(d)** |

### Modern, decided, not ready (pool 1,808)

| Order | Recorded block | What the evidence shows | Category |
|---|---|---|---|
| EO 12581 (1987) | clause inventory, first end, savings | ACT held: revoked whole through its parent by EO 12610, and amended by EO 12584. `MISSING_SOURCES` also lists EO 12610 as "target provision not located". | workflow + (e) |
| EO 10294 (1951) | clause inventory, first end, savings, Opus refetch | Later-events edge: "nullified by Public Law 84-870 (70 Stat. 786)". **The statute is held** (`jobs/selden-statutes/output/texts/STATUTE-70-Pg786.txt`) but is not linked to EO 10294 in Selden `BASIS.jsonl`. | workflow + **(d)** |

### 1900-1936, undecided (pools: 1,382 with an unrouted namer; 1,990 with no namer)

| Order | Recorded block | What the evidence shows | Category |
|---|---|---|---|
| EO 5275 (1930) | machine-read original; no later order text | Utah withdrawal for classification, in force "until revoked". Hathi GPO and Mabillon copies held. Wikisource notes on EO 4181 and EO 5037 list it beside "Public Law 351, 46 Stat. 582". That statute is held but linked only to EO 5037. **[unres]** whether it acts on EO 5275. | (f) for the original; possible (d) |
| EO 1494 (1912) | no status basis | ProQuest held and usable; compensation for members of a commission. The only "namer" is Wikisource navigation, a false match. The end is the commission's completion. | **(b)** (congressional documents) or (f) |
| EO 136 (1901) | machine-read original; page check; no status basis | Tischendorf OCR held. The Wikisource note on EO 128 says "Amended by Executive Order 136", so 136 is the actor, not the target. No source for its own end. | (f) for the original; **(a)** for the end |
| EO 1940 (1914) | no status basis | ProQuest held. Temporary withdrawal in aid of legislation to enlarge Pike National Forest. Cruden: 0. The end would be an Act or a revocation in a known series. | **(b)** |
| EO 3817 (1923) | no status basis | ProQuest held. One-time authority for the Alien Property Custodian to sell stock. Cruden: 0. Ended on performance; the sale is recorded in the APC reports, a known series. | **(b)** or (f) |
| EO 1954 (1914) | original page check; no status basis | ProQuest and the Monthly Register printing both held. A withdrawal for a military road. Cruden: 0. The end is in land-status records. | **(b)** |

### 1900-1936, decided (pool 716)

| Order | Recorded block | What the evidence shows | Category |
|---|---|---|---|
| EO 6694 (1934) | claim blockers; OFR search incomplete | EO 8135, 8136 and 9142 are held and name it. 8136 and 9142 are routed as transfer ACTs; **8135 is not**. EO 9095 is listed as "target provision not located". | workflow + **(d)** + (f) |

### Pre-1900 (pool 104) and unnumbered (pool 19)

| Order | Recorded block | What the evidence shows | Category |
|---|---|---|---|
| EO 110 (1899) | mirror original; page check | Only the Wikisource text is held. Its `MISSING_SOURCES` actor, EO 11030, is an OCR parse of "Executive Order 110.30", a false lead. | (b)/(a) **[unres]** |
| EO 74 (1890s) | machine-read original; no status basis | All 18 cruden hits are false: War Food Order No. 74, "74 FR", PLO 74. The status lead points to FR 2010-11639, which is "74 FR" again. | (f) for the original; **(a)** for the end |
| EO:UN:executive-orders-01:row:61 (1912) | no held text | California withdrawal of 13 December 1912. No text of the order is held. Four later acts that name it by date are held (EO 3862, 4225, 6444, 10755), all "target provision not located". | (a)/(b) for the original; **(e)** for its history |

### Sample tally [obs, n = 18; overlaps allowed]

| Category | Count | Orders |
|---|---:|---|
| (a) | 3 to 4 | 7899 end, 136 end, 74 end, 110? |
| (b) | 7 | 8568, 1494, 1940, 3817, 1954, the 7899 FR printing, UN-61 original |
| (d), held text naming by number but absent from the dossier | 3 confirmed | 10086, 10294, 6694; 5275 possible. **Rate 17% (3/18), 22% with 5275.** |
| (e) | 3 | 10086, 12581, UN-61 |
| (f) | 7 | 11156, 10024, 12632, plus original grade on 7899, 5275, 136, 74 |
| Workflow, where the order needs only to be worked | 3 | 12581, 10294, 6694 |

The sample is too small for population rates. It suggests that "no held trace" orders (4,513 in 1900-1936) are
mostly (b), not (a).

### Lind's 22 ME orders reclassified [int]

From `research/excavator/claude-lind-2026-11-12/FAILURES.md`, plus the current ProQuest holdings.

| Category | Orders |
|---|---|
| (b) | 12280 (FR PDF retention); 4658, 4475, 4621, 4788, 4861, 4968 (now ProQuest held); 1957 (EO 2048 official text); 1538, 8678 (land records); 7841 (statute and PLO); 8877 (PLO 5001); 2898 (in part) |
| (e) | 14103 (the current-law lead has no hash or slice); 10755 (FR multi-document span) |
| (f) | 4145 (schema v1 needs an exact date); 13650, 14274 (proof of performance demanded beside a held CURRENT record); 9739 (owner ruling on the saved interval); 9159 (decide the parent first) |
| (a) | 4193, 9481, part of 2898 |

---

## 5. Which category dominates which era, and the levers

### Dominant category by era [int]

| Era | Original-text stage | Ending, current or later-act stage | Lifecycle sheet |
|---|---|---|---|
| Modern | (b), minor (132 orders) | (f) soft gates; (e) unframed current-law leads; Lind residue (b) | **Workflow** (961 decided orders need nothing but the sheet) |
| 1900-1936 | **(f)**, 1,724 machine-read; **(b)**, 1,771 mirror or compiled | **(b)**: land status, PLOs, Statutes at Large, agency reports. (a) for personal fact dates. (d) about 4% at most. | (f) OFR-search rule on 708 decided orders |
| Pre-1900 | (f)/(b) | **(a)** | n/a |

### Levers

**At one stage.** The largest lever needs no acquisition.
- Decide a codebook route that credits held **machine-read government printings** after a page check. Larrey keeps out
  1,833 orders on that grade alone (`REASONS.json`).
- Route modern mirrors to their FR printing.
- These unblock the original-text stage only. 1,640 pre-1937 orders would still lack an ending [obs].
- Dropping `soft:no_later_order_text_held` as an exclusion would admit 1,592 orders for which it is the sole reason.
  That is a rule change, untested (Kean `F-20261112-soft-gates-untested`).

**To complete histories.** The largest lever is one acquisition family: pre-1937 **land-withdrawal and reservation
endings**.
- Public Land Orders (FR 1942 onward; `jobs/selden-fr-acting` already holds some) and GLO/BLM land-status records.
- By ProQuest title keywords, about 555 of the 1,222 ProQuest-held orders that lack a status basis are withdrawals or
  reservations [obs, crude keyword count].
- GAP_ROUTES families among the 1,613 such orders it covers [obs]: national_forest 255, land_withdrawal 77,
  military_reservation 47.
- [proj] Each order still needs matching and its own legal reading; the yield is unmeasured.
- The next largest families: individual civil-service orders (401 in GAP_ROUTES), which need personal fact dates and
  are often (a); and wartime orders (186).

**Cheap held-evidence fixes (d)/(e).** Small but nearly free:
- frame held current-law and eCFR leads with text and offsets (44 modern orders, §3);
- link held statutes to the orders that later-events edges already connect (EO 10294);
- parse list-form and OCR-split citations in cruden and the kit (EO 12473 → 8 targets).

---

## 6. What this does not establish [unres]

- Population rates of (a) versus (b) for the 4,513 pre-1937 orders with "no held trace": n = 6 sampled.
- Whether crediting machine-read printings would survive blind review.
- The share of (d) candidates that truly act on the order. Acting words near a citation are only a proxy.
- Which held texts the decided dossiers actually contain. I checked the kit indexes, not each `dossiers/*.json`.
