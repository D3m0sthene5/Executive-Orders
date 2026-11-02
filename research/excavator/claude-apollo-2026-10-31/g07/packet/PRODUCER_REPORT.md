# Producer report, packet g07 (producer: claude)

Start UTC: 2026-10-31T22:14:57Z. End UTC: see last line of this file (written at report time).

Final applied directory: `applied-v2`. `applied-v1` was an exploratory run with two submitted orders (EO 10975, EO 11015) and the rest blocked; it was kept, not overwritten, and is superseded by `applied-v2`.

## Outcomes (21 submitted, 3 blocked; no status changed)

All submitted orders: provisional status no, state terminated on 2026-10-14, original confirmed from the held Federal Register text, inventory confirmed, searches current-law:usc, current-law:ecfr and later-events:ofr_catalog selected after reading their notes (all complete, no coverage warning).

Revoked by EO 12553 (1986-02-25, listed by number and subject, no effective-date wording, read as signing date, publication 1986-03-03 disclosed as the alternative; EO 12553 has no savings clause or exception):
- Emergency board orders, report deadline and standstill treated as spent facts, not ends (owner ruling 2026-10-21): EO 10975, 11006, 11008, 11011, 11015, 11027, 11033, 11042, 11050, 11121, 11127, 11168, 11169. EO 11015, 11127, 11168 and 11169 have no located acting-provision record, so the end cites the complete held EO 12553 text.
- EO 11013 (Taft-Hartley board of inquiry): same end; the own-terms ending "until the Board is terminated by the President" is not evidenced by any held source and is disclosed, not claimed.
- EO 11026 and EO 11029 (amendments of EO 11025): same end. EO 11029 rewrote the first paragraph that EO 11026 had replaced without naming EO 11026; disclosed as an unnamed earlier candidate, not an end (owner rulings 2026-10-21).
- EO 11138 (one-person waiver for Frederick Strauss): same end; exhaustion by use is not evidenced, so no earlier date is claimed (owner ruling 2026-10-28).
- EO 11086 (two clauses): same end; the Attorney General jurisdiction clause has a contingent "pending discharge" ending that is not evidenced and is disclosed.
- EO 11105 (seven clauses): same end. The dossier's ACT-type record points at the page-11 number column, where the held OCR separates numbers from subjects; the row on page 12 is used instead. Parcel-by-parcel transfers under Section 4 are undated and disclosed.

Other ends:
- EO 10989 (three clauses): first end 1964-06-22, express revocation by number in section 502(k) of EO 11157 (29 FR 7973; year in the signature line is garbled in OCR, read from "Filed, June 22,1964"; publication 1964-06-24 disclosed). Savings: artificial-island clauses restated in sections 202(a)(5)-(6) and 203 of EO 11157.
- EO 11036 (two clauses): first end 1980-06-27, section 1-501 of EO 12220 revokes EO 10900 as amended (the parent these amendments belong to), with the delegations re-delegated in sections 1-401 and 1-405. Intervening EO 11252, 11963, 12148 and 12163 are not ends; the held EO 11836 text prints the number 11036 over a different subject and is not an event.

Blocked:
- EO 10976: the order lasts during the emergency declared by Proclamation 2914 unless sooner terminated, so the end of that emergency is an own-terms ending that may precede EO 12553. Public Law 94-412 (cited in the catalog note) is not a held source. Missing: held text of Public Law 94-412 section 101 and its effect on the Proclamation 2914 emergency. EO 12553 is the held fallback end.
- EO 11025: the only held original is marked requires_page_check; official PDF pages are not held and govinfo was refused by the proxy (403). Missing: page images or a hash-matching copy of 27 FR 5467. Otherwise ready (EO 12553 end; EO 11026 and 11029 as later events).
- EO 11141 (status yes): no held, hash-registered text of a current provision supports a current predicate through 2026-10-14; the thirteen leads are snippets, and the Code and eCFR bulk files are not committed. Missing: held text such as 48 CFR 22.901 or the 5 U.S.C. 3301 note. No ending found (zero catalog hits).

## What took the time (one line each)
- Board orders (14): identical text; time went to confirming rows in the EO 12553 table, the four missing acting-provision records, and the 33k-character whole-text end source.
- EO 10976: working out that the own-terms emergency ending needs a statute that is not held.
- EO 11025: the page-check requirement and the failed attempt to fetch the official PDF.
- EO 11026/11029: reading both amendments to see whether one ended the other.
- EO 11138/11086: applying the 2026-10-28 and 2026-10-21 rulings to a one-person waiver and a contingent clause.
- EO 11105: seven clauses with mislabelled sections and an OCR-split table page.
- EO 10989: reading EO 11120 and EO 11157 and the garbled year.
- EO 11036: five intervening orders, the mirror-only located record, and the EO 11836 misprint.
- EO 11141: judging whether any current-law lead is a held legal-text slice.

## Batch-check (applied-v2)
packet members 24; claims checked 21; strict pass 21, fail 0; actual claim-checker all checks passed 21, mechanical pass 21, unverified 0, fail 0, gate passed 21; actionable failures none; outcomes: 21 assembled proposals, 3 blocked; independent human certifications 0.

## Tool defects
- `kit.py apply` and `batch-check` only work from the real packet folder (the Valla context excludes only the packet's own folder), so a trial copy elsewhere is refused with "changed Valla review context"; exploratory runs therefore consume applied-vN names.
- Ending evidence for pairs with no located acting-provision record can only cite the whole held acting text (33k characters for EO 12553), which inflates claims; a source supplement would give a short quote but was not used.
- Under machine load (many concurrent producers) batch-check took several hours of wall time.
End UTC: 2026-11-01T03:29:44Z
