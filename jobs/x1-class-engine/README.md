# X1, the lifecycle class engine (pre-1937 orders)

Zero-token, offline job. Design: `research/plans/EXCAVATOR_SERIES_2026-10-19.md` (X1).
Report and measurements: `research/production/x1-2026-10-19/REPORT.md`.

Every output is a **lead**. No type, rule, event, cluster or sheet fills a judgment
field, decides an order, changes a status, an identity, a count or the codebook,
or touches the human-certified count (0). Agents decide each row.

| Step | Code | Output |
|---|---|---|
| 1. Type classifier | `taxonomy.py`, `classify.py` | `TYPES.csv` (type, class, rule, confidence, evidence per order), `GAP_TYPES.csv` |
| 2. Type rule book | `type_rules_spec.py`, `build_type_rules.py` → `research/readiness/type-rules/` | `TYPE_RULES_CHECK.json` (frozen hash vs independent review, exact quote) |
| 3. Extinction-event register | `data/EVENTS.json`, `events.py` | `EVENT_CANDIDATES.csv`, `EVENT_SOURCES_STATE.json` |
| 4. Look-alike clusterer | `cluster.py` | `CLUSTERS.json`, `CLUSTER_MEMBERS.csv`, `CLONED_CLAUSES.jsonl`, `MODERN_FAMILIES.json` |
| 5. Batch review sheets | `sheets.py` | `sheets/X1-<type>-NNN.csv` (≤50 rows), `BATCHES.json` |

## Types

The classifier reads the WPA 1944 numbered list's summary (`data/`, copied from the
unmerged `wpa-lists` branch, commit `121ca07e`), APP's title, and, only as a
fallback, the first 2,500 characters of a held text (compiled volumes often run
into the next order). Patterns run on compacted text because the WPA OCR joins
and splits words. Classes: **spent** (ends by its own performance or terms),
**land** (reservations and withdrawals), **swept** (candidate for a mass-ending
event), **standing** (known type, order-by-order research), **unknown**.

Confidence: *high* = two sources agree on the type (or a strong type and another
source on the class); *medium* = one strong source, no contradiction; *low* =
generic words only, or a text-only match; *none* = unknown.

## Rules, events, clusters

- Type rules are `eo-type-rule/v1`, in the family-rule vocabulary plus
  `ending_pattern`, `required_evidence` and `outlier_conditions`. Each carries an
  exact operative quote from a held exemplar text with its SHA-256. The job marks a
  rule `reviewed_frozen` only when its file hash equals the hash in
  `research/production/x1-2026-10-19/TYPE_RULES_REVIEW.json`.
- Events cite primary sources (Statutes at Large, U.S. Reports on govinfo) queued
  in `research/readiness/FETCH_QUEUE.jsonl`. A source counts only after the
  source-ladder holds it **and** its verification phrases are in its text. FLPMA
  (1976) is registered as *not an end*: it removed the authority, not existing
  withdrawals.
- Clusters compare each order's own machine clause spans (claim-kit
  `TEXT_CLAUSES`), word 3-gram MinHash on the template words, Jaccard ≥ 0.5, within
  one type, exemplar-centred. A member's clone is kept only when no operative or
  qualifying word (`LEGAL_WORDS`) differs inside a clause, its own segmentation has
  the same clause count, and its own spans re-read from its own file. Otherwise it
  drops out to individual review, with the diff shown.

## Sheets and review

Route per row: `claim_kit_prepare` (provisional status, dossier and text held),
`status_first` (no provisional status: claim-kit `history` / overlay path first),
`text_first`. Review tier is **full** independent AI review. Risk-tiered review
(a 20% audit) exists only behind `X1_RISK_TIERED_REVIEW=1`, default off: **the
owner has not approved it**.

Tests: `python -m unittest discover -s jobs/x1-class-engine -v`.
