# Producer report, o04 (Tribonian)

Start UTC 2026-11-04T05:12:23Z. End UTC 2026-11-04T06:05Z (includes waiting for long runs and a usage-limit pause).
Final applied directory: applied-v3.

## Outcomes (30 orders: 29 submitted, 1 blocked)

- 26 exemption orders submitted as terminated by their own stated terms (EO 8308, 8309, 8310, 8311, 8312, 8314, 8322, 8326, 8327, 8340, 8345, 8348, 8349, 8350, 8368, 8369, 8374, 8375, 8386, 8391, 8392, 8401, 8408, 8409, 8410, 8412). Each rests on the APP transcription (mirror_transcription, Common Crawl or Wayback capture), with the APP page record checked (heading names the number, date agrees, text hash equal). End date is the stated "ending" day, inclusive, with the exclusive reading disclosed. Later further-exemption orders held as texts are later events, not ends: EO 8312 (8630, 8919), 8322 (8690), 8368 (8710), 8369 (8747, recorded with its OFR "amendment" lead), 8401 (8778).
- 3 revocation orders submitted as terminated on their signing date by performance: EO 8304 (1939-12-19), 8341 (1940-02-08), 8358 (1940-03-02). Held original is the govinfo Federal Register OCR text layer; page image not held, original_pages_confirmed false. Filing and issue dates are disclosed as alternatives. EO 10287 (machine lead for 8304) names a different order (8034) and is rejected in the reasoning.
- EO 8328 blocked: text says "a period not in excess of six months from March 1, 1940" with no end date; the period actually granted is not held (missing: Civil Service Commission or Justice Department record of the period granted).
- No YES orders in the packet.

## What took the time
One line each: all 26 exemption orders were near-identical short texts, handled by a generator with assertions on quotes, dates and page records; 8312/8322/8368/8369/8401 needed later-order reading; 8304/8341/8358 needed Federal Register OCR reading; 8328 needed ceiling-vs-actual analysis. Apply takes 200-410 s and batch-check plus Geddes about 3 minutes each.

## Batch-check (applied-v3)
29 claims checked, 29 strict pass, 0 strict fail, 1 blocked. Actual checker: 29 gate passed, 2 all checks passed, 26 mechanical unverified (custody_record_only; coordinator retains bytes), 1 mechanical fail.
Mechanical fail, EO:8341: order_exists:not_in_universe on the first_end quote. The held OCR text prints the footnote mark inside the order number ("Executive Order No. 83231 of January 22, 1940"), so the checker reads a nonexistent order 83231. The clause cannot be re-spanned without dropping the operative sentence; left as is for the coordinator.

## Geddes
applied-v2 lint: 1 flag (EO:8304, own_order_date_precedes_signing, from my text quoting EO 10287's heading date). Fixed in applied-v3; v3 lint: 0 flags, 0 coverage gaps. Resolution recorded in applied-v3/GEDDES_RESOLUTIONS.json.

## Earlier applied versions
applied-v1: EO 8304 rejected (a source note on a non-working-text source); applied-v2: all assembled, one Geddes flag; applied-v3 final.

## Full-packet files opened beyond the views
PACKET.json (via batch.load_packet, for dossier evidence ids and actor texts), decisions.csv, clauses.csv, RATIONALES.json, LOOKUPS.md. Also read repository sources: held APP texts, FR OCR texts, jobs/later-events FRAGMENTS, jobs/app-executive-orders MIRROR_DOCUMENTS.

## Tool defects
kit.py view and apply need to be run without -I (module import fails under -I). Mid-run checker bug for matched_date was fixed by the coordinator. Held OCR order-number glitch in EO 8341 (above).
