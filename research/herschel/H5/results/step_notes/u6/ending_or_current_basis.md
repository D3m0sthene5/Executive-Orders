# ending_or_current_basis (H5-w31)
Start 2026-11-06T00:20:21Z; end 2026-11-06T00:22:35Z

EO:2489: done
Time: confirming EO 8376 revokes 2489 by number and that no earlier end exists (cruden number: only 8376 cites it).
EO:4220: blocked:Bureau of Land Management / Federal Register record (Public Land Order, restoration or revocation order, or current land status) for the Oregon Willamette Meridian lands in EO 4220 (T.1-6N R.35-44E; T.6-7S R.23-25E); no held text cites EO 4220 or ends it
Time: cruden number and one regex search, zero hits.

Notes for next worker:
- 2489: clauses.csv row terminated, end_id ACTOR_TEXT:EO:8376 (FR text layer 5 FR 1077, jobs/fr-originals/output/texts/EO_8376.txt), 1940-03-13, express_revocation_by_named_order, later_events []. Quotes in reason come from the FR text layer ("reserving the above-described lands for military purposes, are hereby revoked."); in the FR bytes there are line breaks/soft hyphens (Novem-ber), so I quoted only the hyphen-free span; verify with kit validation (not run). Effective date = signing date: 8376 states none. Savings/outcome untouched.
- 4220: clauses row left blank (state empty); decisions checks filled with the negative search result. Do not treat absence of a citation as an end. Not run: kit.py view/apply.
- 6111 rows untouched.
