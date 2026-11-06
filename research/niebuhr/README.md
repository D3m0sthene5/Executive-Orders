# Niebuhr: finding the executive orders the project cannot yet identify

Named for Barthold Georg Niebuhr, who in 1816 recognised the lost *Institutes* of Gaius, the only classical Roman law
textbook to survive nearly whole, under a later text in a Verona palimpsest. This folder holds a discovery wave, started by
the owner on 2026-11-05, against the unknowns Clark lists (`jobs/clark-discovery/output/`).

Everything here is **discovery**, not identity authentication. A find says where an order is printed and what that
printing shows. No find enters the census, changes a count or grade, or certifies anything until a person reviews it
under the codebook.

## Routes, cheapest first

1. **Already held, never admitted (no agents).** All 22 census gaps in the June 1932 run (EO 5853–5879) are held twice: the
   American Presidency Project text and the official text from the 1974 Office of the Federal Register compilation of Hoover's
   orders (vol. II, HathiTrust 2027/uc1.c025504761), with the PDF page and hash. `ADMISSION_QUEUE_1932.csv` lists them for
   the person who admits census entries. The dates agree for 21. For EO 5877, the official printing says July 5, 1932, and
   the Presidency Project says July 6.
2. **Clark's web stage with the paid Brave engine.** On GitHub's runners every keyless general web engine refuses the
   requests (969 queries deferred on 2026-11-02). Brave is now the one general engine that answers there. It is used only
   when the free engines found nothing, within the caps in `research/readiness/owner_rulings/2026-11-05-brave-paid-search.md`.
3. **Agent searchers** for what neither route reaches: the 1894 run (EO 36–53), the scattered gaps, lettered and
   half-numbered orders the census has by number only, and 226 references to an "Executive order of <date>" that match
   nothing known. Brief: `BRIEF.md`. Raw results: `results/*.jsonl` (one line per target). Every quoted source is then
   fetched by the runner and its bytes held, so a person can check each quote against the page (`VERIFY.md`).
