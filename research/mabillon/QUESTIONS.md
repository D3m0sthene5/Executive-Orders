# Mabillon: questions for the coordinator

Each question has a proposed default that Mabillon is already following.

## Q1. Grade of held government printings proved by text

`jobs/mabillon-held-printings` proves 492 frame orders' official printings from passages `hathi-gpo-orders` already
holds (GPO bound volumes, the 1974 GPO Hoover compilation, 1936 Federal Register issues), with 0 of 4,382 planted
negatives accepted. **Default:** write them exactly as Tischendorf writes strong finds (`grade:
machine_read_government_printed_copy`, `acceptable_as_original: false`, `needs_page_check: false` only when strong),
and leave registering the job in `tracker.py` to the owner, since that changes counts. Kean ask filed.

## Q2. Two rules added to Tischendorf's

The held passages are whole pages, so I score only the order's own segment and require a 0.15 margin over every
order numbered within 3 of it (the controls failed without both; reasons in the job README). **Default:** keep the
additions in Mabillon's job only and do not touch `jobs/tischendorf-originals`. Its `fr_by_date` and `ia_fulltext`
routes read whole pages too, so the same neighbour risk may apply there. Should I tell its owner (a note in Kean)?
I will record it as a Kean finding unless told otherwise.

## Q3. NARA route

The National Archives' own bulk export shows the RG 11 series "Executive Orders" (NAID 299999) has 41 item
descriptions, 27 imaged, covering 3 frame orders. The signed originals are not online. **Default:** no Catalog API
key is needed for this conclusion. File a Kean ask for the owner to choose between a fee-based reproduction order for
the orders with no other witness and continuing ProQuest downloads; spend nothing.

## Status (2026-11-06 04:10 UTC)

Q1 to Q3 answered by the coordinator (NIGHT_WAVE Answers, 03:45 and 04:00 UTC). Q3: the owner chose ProQuest and no
paid NARA reproductions (Kean D-20261105-proquest-not-nara); the fee ask was withdrawn before it was pushed. The
tracker registration for Q1 goes in a separate count-changing PR.
