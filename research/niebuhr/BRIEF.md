# Niebuhr search brief: identify executive orders the project cannot yet find

You are one searcher in a team. The project ("The Afterlife of Executive Orders") keeps a census of 14,972 US presidential
executive orders. Your batch file lists orders or references the project cannot yet identify or find a text for. Your job is
**discovery**: find where each one is printed or recorded, and what it is (date, title or subject, president, text). You do
not decide whether it belongs in the census; a person does that later. Report only what a source shows you.

## The four kinds of target

- `number_gap`: an executive-order number with no census row. `window` gives the dates of the nearest known numbers on both
  sides, so the order was signed between those dates. `citations` are sentences in other orders that name it.
- `cited_lettered`: a lettered number (for example 27-A) named in another order but not in the census.
- `in_census_number_only`: an order the census has, but the project knows only its number (often a "½" or lettered number,
  such as 1182½). Find its date, subject and a text.
- `dated_unnumbered_reference`: a later order says "the Executive order of <date>". No numbered order matches that date.
  Find the order being referred to (usually an unnumbered order: a land withdrawal, reservation, civil-service rule).
  First check whether the date is an OCR error (1818 printed for 1918) or refers to a *numbered* order the project
  already has (then say which number). `quote` shows the sentence.

## Where to look (best first)

1. **The WPA/Historical Records Survey indexes**, which list orders with date and subject:
   - "Presidential Executive Orders, Numbered 1–8030, 1862–1938" (New York City Historical Records Survey, ed. Clifford Lord, 1944), 2 vols.
   - "List and Index of Presidential Executive Orders, Unnumbered Series, 1789–1941" (New Jersey Historical Records Survey, 1943).
   Search HathiTrust full text, for example `https://babel.hathitrust.org/cgi/ls?q1=<words>&anyall1=phrase&lmt=ft`, and page
   views `https://babel.hathitrust.org/cgi/pt?id=<id>&seq=<n>`; also Google Books and archive.org full text.
2. **Official printings**: the Federal Register (1936 on, govinfo.gov), Statutes at Large, the Congressional Serial Set,
   annual reports of the Civil Service Commission or General Land Office, "Executive Orders Relating to Indian Reservations"
   (1912, 1922), "Executive orders and proclamations" compilations, the Official Gazette, Public Land Decisions.
3. **The American Presidency Project** (presidency.ucsb.edu), **Wikisource**, the **NARA catalog** (catalog.archives.gov).
4. Newspapers (Chronicling America at loc.gov), law reviews, agency histories: good for the date and subject; say so.

Use WebSearch and WebFetch. Try several phrasings: "Executive Order No. 1182 1/2", "Executive Order 1182-1/2",
"order of June 23, 1932", the subject words plus the year, the president's name.

## Rules

- **Quote exactly.** `quote` must be text copied from the page you fetched, at most 300 characters, unchanged (OCR errors
  included). Never paraphrase inside `quote`. If you saw the fact only in a search-result snippet and could not open the
  page, put it in `notes` and set `seen_only_in_snippet: true` for that source.
- **No guessing.** A plausible date or subject you did not see in a source is not a finding. `not_found` is a good, useful
  answer when you tried properly; list what you tried.
- Keep the kinds of source apart: `official_printing` (a government publication or facsimile), `index` (Lord/WPA lists,
  catalogs), `secondary` (APP, Wikisource, Wikipedia, books, articles, newspapers).
- Budget: about 8 searches and 10 page fetches per target. Move on when a target is exhausted.
- Do not edit the repository, run git, or touch any file except your output file.

## Output

Write one JSON object per target, one per line, to the output file named in your task (create it and append as you go,
so work survives an interruption):

```json
{"target_id": "EO:1182½", "group": "in_census_number_only",
 "outcome": "identified_with_text | identified_no_text | reference_resolved_to_known_order | citation_only | ocr_error | not_found",
 "date": "1910-04-14", "title_or_subject": "...", "president": "...", "resolved_to": "EO:1234 (only for references that turn out to be a known numbered order)",
 "sources": [{"url": "...", "kind": "official_printing|index|secondary", "what": "e.g. Lord 1944 vol 1 p. 93", "page_or_seq": "...",
              "quote": "exact text", "seen_only_in_snippet": false}],
 "confidence": "high|medium|low", "queries_tried": ["..."], "notes": "..."}
```

Use `""` for unknown fields. When done, reply with a short summary: counts by outcome, the best single find, and any
source that would unlock many targets at once (for example a HathiTrust volume id for the Lord index).
