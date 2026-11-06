# Niebuhr: finding the executive orders the project cannot yet identify

Named for Barthold Georg Niebuhr, who in 1816 recognised the lost *Institutes* of Gaius, the only classical Roman law
textbook to survive nearly whole, under a later text in a Verona palimpsest. This folder holds a discovery wave, started by
the owner on 2026-11-05, against the unknowns Clark lists (`jobs/clark-discovery/output/`).

Everything here is **discovery**, not identity authentication. A find says where an order is printed and what that
printing shows. No find enters the census, changes a count or grade, or certifies anything until a person reviews it
under the codebook.

## Routes, cheapest first

1. **Already held, never admitted (no agents).** 30 orders in the project's own American Presidency Project index, each
   with its text held, have no census row (one more, EO 7933-A, is in the census as `EO:7933a`). They are the 22 census gaps
   in the June 1932 run (EO 5853–5879) and EO 5151-A, 5605-A, 5638-A, 5855-A, 6005-A, 6585, 7010-F and 8606-A. For 26 of
   them the project also holds the official text from the Office of the Federal Register's compilations (for Hoover, the
   1974 volume II, HathiTrust 2027/uc1.c025504761), with the PDF page and hash. `ADMISSION_QUEUE.csv` lists all 30 for the
   person who admits census entries. The two dates agree for every order with both texts except EO 5877, for which the
   official printing says July 5, 1932, and the Presidency Project says July 6.
2. **Joins against indexes the project already holds (no agents).** `WPA_JOIN.json` matches every target to the WPA
   numbered list (1944) and the New Jersey unnumbered list (1943), both held as OCR text in `jobs/x1-class-engine/data/`;
   the WPA numbered list identifies the whole 1894 run (EO 36–53) and EO 92. `APP_UNNUMBERED_JOIN.csv` pairs dated
   references with the Presidency Project's unnumbered orders of the same date (31 of 226 references; a pairing is a
   candidate until a person checks the subject).
3. **Clark's web stage with the paid Brave engine.** On GitHub's runners every keyless general web engine refuses the
   requests (969 queries deferred on 2026-11-02). Brave is now the one general engine that answers there. It is used only
   when the free engines found nothing, within the caps in `research/readiness/owner_rulings/2026-11-05-brave-paid-search.md`.
4. **Agent searchers** for what neither route reaches: the 1894 run (EO 36–53), the scattered gaps, lettered and
   half-numbered orders the census has by number only, and 226 references to an "Executive order of <date>" that match
   nothing known. Brief: `BRIEF.md`. Raw results: `results/*.jsonl` (one line per target). Every quoted source is then
   fetched by the runner and its bytes held, so a person can check each quote against the page (`jobs/niebuhr-verify/output/VERIFY.csv`).
