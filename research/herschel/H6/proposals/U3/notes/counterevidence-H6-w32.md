# Counterevidence, H6-w32 (U3), 2026-11-06T00:15:08Z to 00:20:36Z

Searches (cruden, held corpus snapshot 430b6ed9, 33118 files): literals "McClellan National Forest", "Power-Site Reserve No. 174/235", "Lake Fork", "Beaverhead National Forest", "6131-A", "6131A", "Order No. 6131", "819½", "Hammar", Hayes funeral phrases, "Executive Order 130" (truncated, unused); regexes on CCC termination, Act of July 2 1942, yeomen, nickel/Alien Property Custodian. Only the decisions.csv columns search_ids, conflict_resolutions, unresolved_material_gaps, outcome, approved, research_rationale, agent were written; no earlier value changed; clauses.csv untouched.

- EO:4114: done (submit, approved). Only EO 4114 and four EO 4877 copies mention the forest; revocation 1928-05-04 verified. Opened: EO_4877.vlm_chandra.txt, EO_4114.txt.
- EO:5454: done (submit, approved). Only self copies; three performed revocations confirmed. Opened: APP text, hit list.
- EO:5757: blocked, not approved: no contrary source, but the original-text step never ran (LFS pointer; original columns and working_text blank). Opened: OFR and APP texts.
- EO:2858: blocked: sale occurrence unshown; no later source.
- EO:6131A: blocked. New find: EO 6571 (1934-01-23, offsets 704-940) lets Navy officers be relieved of the 6131-A attachment; an amendment-type event, not an end, so the earlier blocked state is correct; the earlier number search missed it (spelling "6131-A"). later_events left unchanged in clauses.csv.
- EO:130: blocked: no use or extinction shown.
- EO:29: blocked: thirty-day clause confirmed; funeral date not held.
- EO:819½: blocked: only navigation links on EO 819/820 Wikisource pages; no text.

Tool defects: cruden number search does not match suffixed forms written "6131-A" (missed EO 6571); literal "Executive Order 130" is flooded by 13xxx matches.
Time: cruden runs (about 1 min each) dominated.
