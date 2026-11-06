# Pothier: family doctrines for the undecided orders with no dated status history (2026-11-05/06)

Named for Robert-Joseph Pothier, who reduced French law to treatises by subject. Branch
`claude/pothier-family-doctrine`. Every result here is a **status lead** proposed for the owner. No status, codebook
entry, census row or count changed. Certified: 0.

## Conclusions

1. **Eleven family doctrines now cover 5,834 of the 5,918 members** (the undecided orders that `jobs/status-history`
   could not date; 84 members have no usable type and no doctrine). Applied by the zero-token job `jobs/pothier`, they
   **decide 2,139 members (36%): 2,088 `no` leads and 51 `yes` leads**, and leave 3,695 `open`, each with the reason
   and the evidence that would decide it.
2. **The decided leads held up under a blind random pilot.** Eleven blind Opus reviewers checked 30 random members of
   each doctrine (330 leads) against the held texts, with 22 falsified leads planted among them. They caught all 22.
   Of the 129 decided leads in the sample, **1 had the wrong status** (EO 4754, a Civil Service Rules amendment that
   also carries a standing classification direction; fixed). That is 0.8%, with a 95% upper bound of 4.2%. Three more
   decided leads had the right status on the wrong reasoning, and one carried a year-only date. Of the 201 `open`
   leads, 10 (5%) could have been decided from held evidence; the doctrines are cautious rather than wrong.
3. **Every doctrine passed two blind reviews with planted errors.** 22 fresh Opus reviewers, each given a copy with a
   wrong statute citation and a wrong date rule planted in it, caught **44 of 44** planted errors. They also found
   real errors (wrong pages, wrong dates, missed held revocations, leaks in text tests); all eleven doctrines were
   revised against both reviews before the pilot.
4. **Three questions decide most of the result, and they are the owner's.**
   - **Orders that only amend another order (601 leads).** Under the owner's strike-and-insert ruling the amended
     text lives on inside the parent order; Pothier treats the amending order itself as spent on issue, its text
     merged into the parent (ruling P2). If the owner prefers that an amending order lives as long as the text it
     inserted, these 601 leads become `open`.
   - **Orders that only revoke, restore or relinquish (566 leads)** are spent on issue as commands (ruling P1).
   - **BLM's official tables of Public Land Orders** are the basis for about 400 `no` leads (mostly land, military
     and forest orders) while the Public Land Order texts themselves are not yet held.
5. **What would decide most of the open members is acquisition, not more agent work**: BLM land-status records (the
   Mineral & Land Records System withdrawal cases), the Federal Register full text 1936-1994 searched for Public Land
   Orders naming an order, the Forest Service chronology of national forest orders, General Land Office plat filing
   dates, and the statutes the doctrines cite but do not hold (349 fetch lines proposed in
   `research/pothier/work/*/FETCH_PROPOSED.jsonl`; `jobs/pothier/fetch.py` fetches them on GitHub Actions).

## Coverage by doctrine

Measured by `python3 -I jobs/pothier/pothier.py apply` (`jobs/pothier/output/COVERAGE.json`). "Flagged" counts leads
on which the engine found a held later-event edge or current-law mention that seems to disagree; every flag on a
decided lead is explained in its doctrine and none changed a lead (most are later amendments of the parent order,
partial revocations, or edges that belong to another order with the same date or number).

| Doctrine | Members | `no` | `yes` | `open` | Flagged (decided) | Pilot: decided wrong / decided sampled | Pilot: open decidable / open sampled |
|---|---:|---:|---:|---:|---:|---:|---:|
| PD-LAND-WITHDRAWAL (land withdrawals, power, water, mineral) | 1,270 | 485 | 4 | 781 | 15 | 0 / 10 | 3 / 20 |
| PD-CS-ONE-PERSON (one-person civil service orders) | 1,015 | 141 | 0 | 874 | 2 | 0 / 2 | 3 / 28 |
| PD-ADMIN (organization, regulations, pay, allotments, territories) | 801 | 205 | 0 | 596 | 12 | 0 / 7 | 2 / 23 |
| PD-NATIONAL-FOREST | 708 | 314 | 0 | 394 | 1 | 0 / 8 | 0 / 22 |
| PD-CS-RULES (Civil Service Rules amendments) | 540 | 396 | 0 | 144 | 34 | 1 / 21 | 0 / 9 |
| PD-MILITARY-RESERVATION | 316 | 164 | 0 | 152 | 4 | 0 / 17 | 0 / 13 |
| PD-WAR-EMERGENCY (WWI, alien property, eight-hour suspensions) | 263 | 35 | 0 | 228 | 0 | 0 / 5 | 0 / 25 |
| PD-CUSTOMS-CONSULAR | 263 | 111 | 32 | 120 | 2 | 0 / 19 | 1 / 11 |
| PD-REFUGE-LIGHTHOUSE | 243 | 73 | 14 | 156 | 3 | 0 / 14 | 1 / 16 |
| PD-INDIAN (reservations, trust-period extensions) | 230 | 92 | 1 | 137 | 4 | 0 / 15 | 0 / 15 |
| PD-CLASS-EVENTS (NRA, Canal Zone, Philippines) | 185 | 72 | 0 | 113 | 0 | 0 / 11 | 0 / 19 |
| **All** | **5,834** | **2,088** | **51** | **3,695** | **77** | **1 / 129** | **10 / 201** |

By the owner's WPA family hints (`COVERAGE.json` `by_wpa_family_hint`): land_withdrawal 350 of 842 decided,
civil_service_individual 112 of 797, national_forest 288 of 654, emergency_war 85 of 513, civil_service_rules 296 of
366, military_reservation 117 of 225, indian_reservation 80 of 201, tariff_customs 103 of 187, other 614 of 1,854.
The WPA hints are broader than the doctrines' text tests, so members cross between them.

## What the decided leads rest on

| Basis | Leads |
|---|---:|
| Amending order merged into its parent on issue (P2, `TERM`) | 601 |
| Revocation, restoration or relinquishment spent on issue (P1, `TERM`) | 566 |
| A later order, Public Land Order or statute that names the member (`ACT`) | 505 |
| An express class instrument whose words reach the member (EO 7076's "all existing Executive Orders ... under Title I", ANCSA sec. 19(a), EO 89 "revokes all others", P3) | 94 |
| The named person's life: a dated fact in the order plus the longest verified human life, 122 years 164 days (`TERM`) | 99 |
| The order's own stated period, date or day (`TERM`) | 118 |
| Trust-period extensions that expired before the Indian Reorganization Act or outside its reach (`TERM`) | 66 |
| Abolition by name of the member's only subject (P7) and delegations of statutory powers that ceased (P8) | 35 |
| A current statute or regulation that names the order or its subject (`yes`, `CURRENT`): 19 CFR 101.3 ports of entry (32), ANILCA sec. 305 and other refuge statutes (14), 43 CFR 2566 and BLM records (4), 40 CFR 49.10198 (1) | 51 |

1,972 decided leads rest on an order text that is a transcription or an archival scan, not an authenticated original,
and 567 cite at least one source not yet held; each lead says so in its gaps.

## The doctrines in one line each

- **Land withdrawals.** A withdrawal lasts until revoked (Pickett Act 1910; FLPMA 1976 sec. 701(c) keeps existing
  withdrawals and sec. 704(a) repeals only the power to make new ones). Ends come from later orders and Public Land
  Orders that name the order; revocations that wait for a resurvey plat stay open.
- **National forests.** Exclusions and revocations are spent on issue; additions, transfers and designations persist
  with the land and need the Forest Service chronology; 111 members are ended by later instruments that name them.
- **One-person civil service orders.** A waiver for one named person is extinguished at the latest by that person's
  death; the doctrine dates that only where the order itself fixes the person's age or presence on a date.
- **Civil Service Rules.** Amendments merge into the rules; EO 89 (1896) and EO 209 (1903) expressly revoked the
  earlier rules and their amendments; later whole-text restatements (EO 7915, 9830, 10577) are not ends (P3).
- **Military reservations.** Philippine reservations ended with independence except bases kept under the 1947 Military
  Bases Agreement and the Port of Manila; Canal Zone orders end no later than the 1977 treaty's end (1999-12-31).
- **Indian orders.** Trust extensions end on their own terms unless the Indian Reorganization Act sec. 2 or a later
  statute continued the period (then open); executive-order reservations need per-reservation evidence (25 U.S.C. 398d).
- **War and emergency.** Delegations of Lever Act, Overman Act and shipping-fund powers ended with those powers; Alien
  Property Custodian sale orders stay open until a sale record is held (one is decided by a held sale).
- **Customs and consular.** 32 ports are in force today because 19 CFR 101.3 cites their orders; abolished ports and
  amended consular regulations are decided.
- **Refuges and lighthouses.** 14 refuges are named in current law (ANILCA, Pub. L. 100-226, 50 CFR 216.85); 35 are
  ended by Public Land Orders.
- **Administrative orders.** Spent and own-terms orders are decided; standing organization, regulation and pay orders
  stay open. Tax-return inspection orders stay open: the owner's unnamed-instruments ruling names the Tax Reform Act of
  1976 as an instrument that does not end an order it does not name.
- **Class events.** NRA Title I orders end by 1936-04-01 under EO 7076 and NIRA sec. 2(c); Canal Zone and Philippine
  orders as above.

## How it was done

- **Members and engine.** `jobs/pothier/members.py` builds one record per member from committed outputs (dates, WPA
  1944 summary, X1 type, held texts, literal text features, named persons, later-event edges from later-events,
  Shepard and Namier with partial acts marked `partial_*`, current-law mentions). `pothier.py` applies each doctrine's
  ordered branches and writes `LEADS.jsonl` and `COVERAGE.json`; 15 tests (`test_pothier.py`). Zero tokens, about 15
  seconds for all doctrines. It runs on GitHub Actions when a doctrine changes.
- **Coordinator rulings P1-P8** (`COORDINATOR_RULINGS.md`) settle the questions every family met (spent orders,
  amending orders, unnamed instruments, named persons, territories, abolition of a subject, ceased delegations and
  periods a statute continued), from the owner's standing decisions.
- **Authors and reviewers.** Eleven Opus doctrine authors (one per family) researched the law with held texts and the
  web; 22 blind Opus reviewers with planted errors; 11 revisions; 11 blind Opus pilot reviewers. Briefs:
  `work/AUTHOR_BRIEF.md`, `work/REVIEWER_BRIEF.md`, `work/REVISION_BRIEF.md`, `work/PILOT_BRIEF.md`. Reviews and keys:
  `review/`; pilot packets, reviews, keys and results: `pilot/`.
- **Cost.** About 15 million subagent tokens as the harness reported them (authors 4.8M, reviews 6.0M, revisions 2.1M
  plus five unreported, pilots 1.9M), about 4 hours of wall time, all Opus (`work/USAGE.csv`). `jobs/bentham/sessions.py`
  could not read the subagent transcripts in this session (none are stored locally), so no API-equivalent dollar
  figure is given. No Bentham action id covers this owner-directed work, so `bentham.py gate` had nothing to gate;
  the coordinator ruled the reviews and pilots tool-building review, where an economic STOP is not binding.

## Limits

- The pilot sample is 30 members per doctrine; the per-doctrine rates rest on small numbers (for example 2 decided
  leads in the one-person sample). The pooled decided error bound (4.2%) is the meaningful figure.
- Text tests read the first 12,000 characters of an order's text; 25 decided leads concern longer texts and carry a
  gap telling the reader to read the whole text (the pilot found EO 5947's second clause past that window).
- Several doctrines decide some members by verified per-member lists rather than general patterns; each list entry
  is anchored to a quoted phrase and fails to `open` if the held text changes.
- `yes` leads depend on current regulations read as of their held editions; four rest on records not yet retained.
- About 40 members are routed to another family's rule but stay `open` until retyped.

## Owner decisions asked (Kean)

Kean ask **A-20261106-pothier** collects these decisions in one ask (the Kean brief has a size limit); please answer
each line separately:

1. **Adopt each family doctrine** as the claim kit's first-step guidance for its members (yes or no per family):
   PD-LAND-WITHDRAWAL, PD-NATIONAL-FOREST, PD-CS-RULES, PD-ADMIN, PD-MILITARY-RESERVATION, PD-CUSTOMS-CONSULAR,
   PD-CS-ONE-PERSON, PD-CLASS-EVENTS, PD-INDIAN, PD-REFUGE-LIGHTHOUSE, PD-WAR-EMERGENCY. Adoption lets a producer
   start from the doctrine's lead, mechanism, sources and gaps; it changes no status, and each order still needs its
   own claim-kit decision and review. A later ask can propose Jacquard-style sampled adoption of a family's `no` leads
   (the owner's 2026-10-31 rule: 59-order sample, zero misses).
2. **Amending orders (601 leads):** spent on issue with their text merged into the parent (ruling P2, as applied), or
   alive as long as the text they inserted (the leads become `open` until each parent is decided)?
3. **BLM's Tables of Public Land Orders (about 400 leads):** may a `no` lead rest on the table row before the Public
   Land Order's own text is acquired (as applied, with the gap disclosed)?
