# Cruden held-text retrieval

Run from any directory with Python 3. Cruden derives the repository root from its
script path. No dependencies beyond the standard library are required.

```
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups PACKET_DIR
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py number EO:10673 EO:10772 --write /tmp/number-results.json
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py literal "Fitness of American Youth" --write /tmp/name-results.json
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py table-number EO:9949 --write /tmp/table-leads.json
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py search 'Executive\s+Order.*10673'
```

`lookups` keeps the original `LOOKUPS.json` and `LOOKUPS.md` contract: the same
members, first exact match per other held file, file order, snippets, and 40 number
/ 60 code-name matching-file limits. `LOOKUPS.details.json` adds source hashes,
full held-file paths, exact match spans, exact query expressions, counts before
those limits, truncation, input-resource pins, and a complete coverage manifest.
The code-name snippet retains the old shortened endpoint and lowercase offset;
the companion span correctly maps the complete literal back to source characters,
including Unicode lowercase expansion.

`number` uses the exact existing executive-order citation regex, including its
existing suffix and list limitations. A decimal run alone is only a candidate.
`literal` searches a case-insensitive literal with Python `str.lower()`, without
stemming, semantic expansion or relevance ranking. Both return at most three
matches per query per file, with full match counts and explicit truncation. Use
`--write` to retain full results and print a small path/hash/count summary. Without
`--write`, the complete JSON, including the source inventory, goes to stdout.
`search` is the unchanged uncached regex full scan with its original stdout and
three-match-per-file behavior; it does not produce the new coverage companion.

`table-number` is a separate opt-in lead route. It uses the same held-text
snapshot and decimal postings, then accepts a bare-number cell only under a
`No. Subject` heading preceded by the explicit "following Executive Orders,
and any amendments thereto, are revoked" introduction. The row must start
with the complete queried 3–5 digit number (and exact optional attached or
hyphenated uppercase letter suffix) followed
on that line by an alphabetic subject. It refuses prose mentions, number-only
split columns, embedded/neighboring numbers and parent/suffix collisions. It
returns up to three rows per source with full matching counts, source hash,
exact number, row, subject, heading and revocation-introduction spans. Repeated
headings inherit context until a recognized signature, White House line, filing,
editorial note, billing code or new numbered order/proclamation heading; a later
explicit introduction can start a new table. These are bounded layout heuristics,
not a general table parser: unknown document boundaries, wrapped subjects and
OCR errors still require complete-source inspection. Physical PDF page is returned
only for a valid held page marker, and printed page only for an explicit
`<page> Federal Register` header near that marker. A source without page markers
reports null pages and a table-section ordinal, which is not a physical page.
The complete source must still be checked; a table lead is not an ACT conclusion
or automatic closure. This route does not alter `lookups`, `number`, `literal`,
`search`, or the cached feature format.

The searched universe remains exactly the existing sorted
`jobs/*/output/texts/**/*.txt` discovery, excluding `clause-drafts`. No sources are
downloaded or silently added. The companion lists unreadable files, directory
walk errors, tracked text paths absent from discovery (including sparse checkout
omissions), and clause-drafts exclusions. An unavailable Git inventory is reported.
No match is evidence of corpus-wide absence or legal completeness.

Cruden stores disposable candidate features outside the repository, by default
under `$XDG_CACHE_HOME/cruden` or `~/.cache/cruden`. Set `CRUDEN_CACHE_DIR` to use a
different cache root; each repository path has a separate subdirectory. Only
source paths, byte sizes/hashes, all decimal runs, and a fixed code-prefix flag
are cached. The entire cache envelope has an integrity digest and pins the feature
compiler's source bytes as well as its schema and algorithm. This detects
accidental corruption; it is not protection against a malicious cache writer.

Every invocation reads and hashes every discovered source, reusing extraction
features only when the bytes match. Candidate texts are reread and rehashed for
exact matching. Before publishing, the complete inventory and every source's
bytes are checked again, including previously irrelevant files. Observed edits,
additions, deletions or changing readability cause refusal and a retry message.
These passes observe a mutable filesystem; they do not lock sources after the
last check. Cache errors fall back to rebuilding from the held bytes and are
reported. Cache replacement is atomic and happens only after source verification.

Offsets are zero-based, half-open Unicode character positions after UTF-8
replacement decoding and universal-newline normalization, exactly as in the
legacy `Path.read_text` calls. They are not raw-byte offsets. Each hit binds the
raw held bytes by SHA256 and links the full text; this establishes no original
authentication, source grade, identity, legal effect or status.

The companion reports construction, feature reuse/building, candidate search,
final validation, cache timings, and bytes read in each corpus pass. Its total
ends before output serialization/writes; process wall timing includes output.
The register, WPA, APP records, packet descriptor, and referenced own/page texts
are pinned before use and rechecked before publication. Native packet loading
retains its existing `check_sources=False` behavior; this tool adds no packet
validation or review certification.

Focused synthetic checks:

```
python3 -I research/excavator/claude-nira-sweep-2026-10-29/test_cruden_cache.py
python3 -I research/excavator/claude-nira-sweep-2026-10-29/test_cruden_table.py
```
