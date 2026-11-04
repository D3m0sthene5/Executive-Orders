# Producer report, packet c03 (Tribonian corrections)

Start UTC 2026-11-04T12:05:25Z. End UTC 2026-11-04T12:33:00Z (stopped).

## Outcome

`kit.py apply` refused at 2026-11-04T12:32Z with "claim-kit: changed prior research; prepare a new version". Per instructions I stopped. No applied-v1 directory exists, no batch-check and no Geddes lint were run, and no GEDDES_RESOLUTIONS.json was written. I wrote nothing about these orders outside this packet and my scratch directory (/tmp/claude-0/tribonian-work/c03/); the refusal is most likely caused by other producers' files appearing in other batch folders, which I did not touch.

decisions.csv and clauses.csv in this packet are filled (34 orders, 338 clause rows, agent=claude); the pre-fill templates are saved as /tmp/claude-0/tribonian-work/c03/decisions.orig.csv and clauses.orig.csv. Applied counts: 0 submitted through apply. Intended sheet outcome: 30 submit, 4 blocked.

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

Not run (apply refused).

## Full-packet files opened beyond the views

None beyond the blank decisions.csv and clauses.csv templates and PACKET.json (dossier conflicts, evidence ids, current-law leads for EO 13422 and EO 7845). LOOKUPS.md and READ.md were not opened. The CORRECTION_BRIEF.json prior claims named by the brief were read as authorized.

## Tool defects

- apply refuses with "changed prior research" although I wrote no research outside the packet; probable cause is concurrent producers in sibling batch folders.
- The dossier source record for EO 8969 (the later event for EO 8637) carries signing_date 1946-12-11; the held text and page title say December 11, 1941.
- The dossier for EO 7845 lists EO 7880 as a section 6 amendment because it shares a Federal Register page (3 FR 1075) with EO 7879; the held EO_7880.txt is a duplicate of the EO 7879 page.
- Held Federal Register text for EO 9938 prints the closing words and date line far from the order's first page; the dossier clause spans the entire PDF.
