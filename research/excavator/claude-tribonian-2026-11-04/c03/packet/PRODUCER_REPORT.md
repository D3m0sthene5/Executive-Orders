# Producer report, packet c03 (Tribonian corrections)

Start UTC 2026-11-04T12:05:25Z. End UTC 2026-11-04T16:35:19Z (approximate; includes the stop for the re-prepare).

## Outcome

Re-prepare: the first `kit.py apply` (2026-11-04T12:32Z) refused with "changed prior research"; the coordinator re-prepared the packet at the same path (stale copy kept at packet-stale-v1). I compared all 34 views and the dossier fingerprints: only prior_research_for_order changed (other batches' completions); no dossier fingerprint changed and no row needed revision.

Final applied directory: applied-v2. Counts: 30 assembled proposals, 4 blocked (12961, 7980, 9027, 9271), 34 members. Started 2026-11-04T12:05:25Z; finished after the re-prepare run (see end time below).

Batch-check (applied-v1 and applied-v2 alike): 30 claims checked, strict pass 30, strict fail 0, actual checker 27 all-checks-passed and 3 mechanical-unverified (EO 13018, 13137, 14075: source held as custody record only, so the checker could not re-hash the file; not fixable on the sheet), gate passed 30, no mechanical failures.

Geddes: applied-v1 lint gave 12 flags (13326 and 13328: EO 13381, 13470, 13526 naming EO 12958; 13422: EO 12875, 13083, 13084, 13132, 13175 naming EO 12866; 7845: 3 FR 1075 citation). Fixed in applied-v2 by stating in the rationales why those orders do not affect the claim and by dropping the page reference. applied-v2 lint: 0 flags, 4 coverage gaps (EO 12785 heading OCR; EO 9938 order printed in pieces), recorded in GEDDES_RESOLUTIONS.json as disputed.

Intended sheet outcome: 30 submit, 4 blocked.

## Blocked orders (precise gap)

- EO 12961: no held source dates the submission of the final supplemental report, which fixes the Committee's end under EO 13034 sec. 3(a); the November 1997 Weekly Compilation statement says only that it was delivered.
- EO 7980: EO 8026 (December 23, 1938, further delay to June 30, 1939) and EO 8182 are held only as American Presidency Project text and are not dossier evidence, so they cannot be cited as later events; a source supplement registering them is needed.
- EO 9027: Transportation Act of 1940 sec. 306 (the Board of Investigation and Research ceasing two years after September 18, 1940 unless extended) is held in jobs/source-ladder but is not dossier evidence; an earlier-end candidate cannot be resolved without a supplement and a source on the Board's actual termination or extension.
- EO 9271: no held source gives George T. Summerlin's retirement or death; the November 30, 1947 date is only an upper bound.

## Corrections by order (all 34 were rejected_in_review)

Re-dated or re-mechanized: 12785 (fixed sunset of amended parent, 1992-12-31, with EO 12869 as later event), 13018 and 13137 (fixed sunset 2001-10-03), 8226 (express supersession by EO 8384 sec. 21, effective as of 1940-03-02, signing 1940-03-29 as alternative), 7845 (later events at effective dates 1938-01-01 and 1939-06-30; 8384 "in part" conflict resolved on record; savings sentence no longer asserts a carry-forward; EO 7880 shown to be a false chain lead), 14010 (items (1)-(4) are self-executing revocations). Inventory corrected: 12910 (adds sec. 1), 13184 (two clauses), 9938 (two spans covering the closing words printed on PDF page 3; effective moment is "the signing of this order", date March 22, 1948). Wording or search description fixed: 8106, 8637 (record signing_date 1946-12-11 disagrees with held text, disclosed), 8804, 8805, 8810, 8897 (Miss Augusta F. Johnston, "applicable to her"), 8997 (class order; name search deselected and disclosed), 9118 (further exemption after EO 8698), 9278 (five namier hits described correctly), 13988, 14004, 14021, 14075 (EO 14168 sec. 7(b) concurrent rescission). Conflict resolutions are recorded for 13422, 13988, 14004, 14010, 14021, 14075, 7845 and 8226. The other orders were rechecked and kept with template wording removed. Label quotation marks in clause reasons were removed so only held text sits in quotation marks.

## What took the time

One line per order: reading the held text and prior claim dominated for all; longer for 7845 (inventory of 41 clauses, conflict, EO 7880 duplicate page), 9938 (scrambled FR page, offsets), 14004/14010 (split clauses and concurrent rescissions), 8226 and 9027 (supersession and Act held outside the dossier), 12961, 7980 and 9271 (searching for a dating source that is not held).

## Batch-check counts, Geddes

See Outcome.

## Full-packet files opened beyond the views

None beyond the blank decisions.csv and clauses.csv templates and PACKET.json (dossier conflicts, evidence ids, current-law leads for EO 13422 and EO 7845). LOOKUPS.md and READ.md were not opened. The CORRECTION_BRIEF.json prior claims named by the brief were read as authorized.

## Tool defects

- Geddes lint was killed by out-of-memory twice on the shared machine and succeeded on the third attempt.
- apply refuses with "changed prior research" although I wrote no research outside the packet; probable cause is concurrent producers in sibling batch folders.
- The dossier source record for EO 8969 (the later event for EO 8637) carries signing_date 1946-12-11; the held text and page title say December 11, 1941.
- The dossier for EO 7845 lists EO 7880 as a section 6 amendment because it shares a Federal Register page (3 FR 1075) with EO 7879; the held EO_7880.txt is a duplicate of the EO 7879 page.
- Held Federal Register text for EO 9938 prints the closing words and date line far from the order's first page; the dossier clause spans the entire PDF.
