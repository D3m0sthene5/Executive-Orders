# Producer report: c01 (Papinian production lane, route correction)

Start 2026-11-10T03:26:14Z; end 2026-11-10T03:52:05Z. Final applied directory: `applied-v2` (applied-v1 kept; it rejected EO 8399 for an unresolved dossier conflict and EO 12743 for a working-text check).

## Outcomes

Submitted (7, all `whole_order_status` no; actual claim checker 7 of 7 pass; Geddes 0 defect flags): EO 11262, 11299, 11367, 11409, 11468, 11499, 8399.
Blocked (14): EO 10440, 11849, 11941, 11971, 11973, 11998, 12323, 12439, 12487, 12499, 12502, 12743, 9303, 9591. Dispatch-blocked and left as prepared (assessment rows only): EO 10494, 11293.

Reasoning applied: owner rulings 2026-10-21 strike-and-insert (a replacement or retitling is an amendment and the clause continues amended until its parent ends; only a deletion without replacement removes a placement), 2026-10-28 evidence-not-convenience (a report date or deadline is not an end; a cleanup revocation is not by default a first end), and the transcription ruling (not needed: all submitted sources are Federal Register text layers).

- EO 11262, 11367, 11409, 11468 (items), 11499: first end 1973-03-23, EO 11708 sec. 3 (revokes EO 11248 as amended except eight level V positions that match none of these items). Replaced or retitled items (EO 11262 item 4 by EO 11409; EO 11367 item 5 by EO 11540; EO 11409 item 9 by EO 11468; EO 11468 item 24 by EO 11516) are recorded as later amendments with a reviewer note that the substance changed.
- EO 11299 and EO 11468 level V item (23): deleted outright (no replacement) by EO 11634, 1971-12-06; this is the first end of those clauses. The abolition of the underlying offices (Reorganization Plan No. 2 of 1968; Postal Reorganization Act) is not held and not relied on; disclosed in the clause reasons.
- EO 8399: both permissions end 1968-04-25, EO 11408 sec. 2 (insofar as amending EO No. 9, which sec. 1 revoked). Open point disclosed: Social Security Board abolished by Reorganization Plan No. 2 of 1946 (not held); no held source shows that it ended the permissions. Conflict FULL_AND_PARTIAL_EVIDENCE_CONFLICT resolved from the text of EO 11408.
- Inventory corrections (overrides) for 11262, 11299 (24 rows of neighbouring FR documents reduced to the one clause), 11367, 11409, 11468, 11499, 8399 (lead folded into the permission it carries).

Blocks, with the exact missing source:
- EO 10440: date the Civil Service Commission completed the sec. 2 Schedule A/B reclassification (sec. 1 clauses end 1955-01-23, EO 10577).
- EO 11849: record of the Committee's termination or renewal (FACA two-year limit); bound 1978-12-31.
- EO 11971, 11973, 11998: report submission or transmittal date (and any extension for 11971); bound 1978-12-31.
- EO 12323, 12439, 12502: final report date (own terms end on the earlier of a fixed date and report plus 30 or 60 days).
- EO 12499: registered original (EO_12499.recheck.txt, 3433 characters) lacks sec. 3(a) and sec. 4 (page 10), so the inventory cannot be confirmed; substantively the first end would be 1985-09-30 (sec. 4(b)), with Pub. L. 98-525 sec. 1632 read and no statutory termination found.
- EO 11941, 12487: pay-period start dates for the first pay period beginning on or after 1977-10-01 and 1985-01-01 (and for 11941, the instrument that replaced Schedules 5-7).
- EO 12743: official text of EO 13286 as a packet evidence record (sec. 35 amendment of sec. 1); the checker rejects the APP transcription ("working_text:official_copy_available_recheck_required", seen in applied-v1). All clauses otherwise end 2004-07-30 (EO 13350).
- EO 9303, 9591: the Department of State order or regulation superseding them (EO 9521 conditional revocation) and whether section V-23 was superseded before 1957-03-01.

## What took the time (one line per order)

- 10440: reading the scrambled FR column text to isolate sec. 2 and EO 10577 secs. 301 and 401.
- 11262, 11299, 11367, 11409, 11468, 11499: tracing each item through the EO 11248 amendment chain (title searches over EO 11262 to 11730) and fixing the inventories.
- 8399: EO 11408 reading and the 1946 abolition issue.
- 11849, 11971, 11973, 11998, 12323, 12439, 12502: confirming no held report-date source (cruden search by commission name).
- 12499: found the registered original truncated; read Pub. L. 98-525 sec. 1632 in source-ladder text.
- 11941, 12487, 9303, 9591: reading EO 12010, EO 12496, EO 10697 sec. 7 and EO 9521 for effective-date and conditional-revocation problems.
- 12743: reading EO 13286 sec. 35 and EO 13350; applied-v1 working-text rejection.
- 10494, 11293: assessment rows from the views only.

## Batch-check (applied-v2)

7 claims checked, 7 strict pass, 0 strict fail; actual claim checker 7 of 7 all checks passed (mechanical pass 7, gate pass 7); 14 blocked, 2 unresolved (dispatch-blocked, rows as prepared). Geddes: 0 defect flags, 7 coverage gaps (citing_corpus_incomplete: 912 held texts missing or changed, advisory); GEDDES_RESOLUTIONS.json is empty.

## Full-packet files opened beyond the views

None of PACKET.json or READ.md or LOOKUPS.details.json was read directly. PACKET.json was loaded once by script (jobs/claim-kit/batch.py load_packet, check_sources=False) to dump evidence-record texts to the scratch folder, and again to inspect the EO 8399 conflict. LOOKUPS.md was read. Repository texts read: held Federal Register and APP-mirror order texts for the later instruments cited (EO 10445, 10577, 11248 amenders 11409 to 11708, 11408, 12010, 12110, 12399, 12496, 12534, 13286, 13350, 13740 by search, 12743 and 12499 originals), Pub. L. 98-525 sections 1511 and 1632 from jobs/source-ladder text, and the cruden search output.

## Tool defects and notes

- `ORIGINAL:EO:12499` record (recheck text) ends before sec. 3(a) and sec. 4; the full text exists only in unregistered jobs/fr-originals/output/texts/EO_12499.txt.
- The view lists only 40 citable evidence ids while the source catalogue holds more (for example the EO 11708 ACT ids); I used the catalogue and records.
- A later order held only as an APP transcription fails the working-text check when an official copy exists elsewhere (EO 13286), even though the packet offers no official record.
- Machine inventories for EO 11299 and 11367 swept in neighbouring Federal Register documents; 11299 listed 24 clauses.
- Nothing certifies anything; certified count unchanged at 0.
