# Producer report, batch n07 (NIRA code-approval orders)

Producer: Claude (Sonnet 5.5), packet `research/excavator/claude-apollo-2026-10-31/n07/packet/supp`.
Start UTC: 2026-10-31T22:13:09Z. End UTC: 2026-10-31T22:27:40Z (the final apply directory is `applied-v1`; apply plus batch-check ran 22:24:54 to about 22:27).

Result: 23 orders; 16 submitted, 7 blocked. Final applied directory: `applied-v1` (no applied-v2 was needed). Certified count: 0; nothing here certifies an order.

## Outcome per order and what took the time

Submitted (all end by the S.J. Res. 113 repeal, June 14, 1935, unless stated):

- EO 6204-A (Rayon Weaving, partial immediate approval): repeal. The reserved power to revise after the July 25, 1933 hearing states no end and no held record shows it exercised. Time: reading the "approved in part" wording and checking for a later full approval (none held).
- EO 6258-B (Rayon and Synthetic Yarn): repeal; the employer-reports condition is treated as a term of the approval (section 3(a) allows report conditions). Time: deciding the condition is not independent.
- EO 6272 (Salt): two clauses, approval and the code-committee condition, both repeal. The committee clause is the judgment call: it is a creation command with no held record of performance, so it is not recorded as exhausted. Time: the committee clause reasoning.
- EO 6329 (Ship Building amendment): one clause; the "one week unless good cause shown" term is a commencement condition, not an end; EO 6216 is held and is the approval being amended. Time: separating the amendment from EO 6216.
- EO 6331-D, 6375, 6382, 6410, 6425, 6506, 6513-G: plain approvals, repeal. Time: only the plain-clause template and checks.
- EO 6557-C (Raw Peanut Milling): inventory corrected from five machine clauses to one (the four numbered paragraphs are findings that command nothing; the closing "Now, Therefore" paragraph is the only command). Time: locating the correct span.
- EO 6641 (Scrap Iron etc.): inventory split into the approval and the Waste Paper Trade Code Authority report direction (60-day report date is a deadline, not an end); both repeal. Time: deciding that a direction to a code-created body is code-dependent.
- EO 6658 (Shoe Rebuilding): split into approval and the stay of Article VI, Section 6(i) "until the Administrator ... shall order otherwise"; both repeal, with the contingent own end stated as not shown by any held record. Time: the contingent stay.
- EO 6694-A (Retail Rubber Tire and Battery): inventory split into five clauses. The pre-effective-date determination authority ends by its own terms on May 14, 1934; the other four (approval, emergency warranty authority, stay pending further orders, 90-day Code Authority recommendations) end by repeal. Longest order to read and split.
- EO 6744-A (Retail Tobacco): machine inventory kept (six clauses, correct). Clauses 1 and 5 end by their own terms on June 25, 1934 (recorded inclusive, exclusive reading June 24 stated in the reason); clauses 2 and 3 (stays until the Administrator's further order or satisfactory arrangements) and 4 (substituted pricing standards) and the lead end by repeal. Time: six separate end analyses.

Blocked (all with the precise gap in `decisions.csv`):

- EO 6216 and EO 6519: the packet's registered text is a live harvest of the APP page (`DOCUMENTS.jsonl`), which fails offline custody under the production route. For 6519 a Common Crawl mirror fragment with the identical text hash exists but the packet does not cite it; for 6216 the only archive capture is Wayback. Both orders are plain approvals that would take the repeal end once a provable text is registered.
- EO 6449, 6467-A, 6927-A: registered text is a Wayback-only APP capture, which fails offline custody. 6927-A is also a mixed order (code authority appointments with a 30-day period from the code's effective date, stay "pending incorporation ... or pending our further order") that would need separate clauses.
- EO 6524: the direction to the Administrator to investigate and advise within ninety days is an independent direction; the 90 days is a report deadline, no held record shows performance, and nothing in the text makes it depend on the code approval, so the repeal is not shown to have extinguished it. The approval clause alone would take the repeal end.
- EO 6543: condition 1 stays a paragraph until 30 days after the code's effective date, which is not held (so the own-terms end cannot be dated); the order also carries an undated direction to call a hearing.

## Batch-check counts

`kit.py apply` (applied-v1): 16 assembled proposals, 7 blocked, 0 rejected. `kit.py batch-check`: 23 packet members, 16 claims checked, strict pass 16, strict fail 0, actionable failures none; actual claim checker 16 of 16 passed (all checks), 0 unverified, 0 failed; 0 independent human certifications. No "changed Valla review context" refusal occurred.

## Tool defects and friction

- `load_packet` takes `Path` objects, not strings (a `str` folder raises `TypeError`); it returns a tuple of the packet and the decoded dossiers, and `PACKET.json` holds lazy `@eo:ref` pointers, so the decoded second value is the one to use. The brief's call signature does not say this.
- `prepare` registered the live harvest as the original for EO 6216 and 6519 even though MIRROR_FRAGMENTS holds a mirror fragment with identical text bytes (Common Crawl for 6519, Wayback for 6216). For 6519 a Common Crawl text would pass custody, so the pick cost one order.
- An inventory correction applies to every row of that order (all rows must carry `inventory_*` columns and new scope ids); this is documented only in the code.
- `end_id` for an own-terms end with a corrected inventory: the machine TERM evidence ids are bound to the old scope ids. For EO 6694-A's pre-effective-date clause I used the order's own original evidence id with the mechanism `own_terms_window_closed`; the checker accepted it, but the mechanism vocabulary is not documented anywhere I was told to read.

## What LOOKUPS.md missed

- It reports exact code-name matches only. EO 6216's text names the Shipbuilding code under a different spelling from EO 6329 ("Ship Building and Ship Repairing"), so the link between 6329 and 6216 was found only by a looser `cruden.py search`.
- The page check line says `record=live_harvest` but not that a mirror fragment with identical text exists, which decided whether a block was necessary.
- It does not flag that the text for EO 6258-B reads "Yam" and for 6467-A "Industiy" and "Norember" (OCR in the APP transcription); I noted the 6258-B point in the scope check.
- It gives no effective date for a code, so conditions running from "the date this code becomes effective" (EO 6543, EO 6927-A) can only be blocked.

## Where the shared analysis did not fit

- Stays and conditions whose own end is a contingent event (EO 6658, 6694-A proviso 3, 6744-A clauses 2 and 3). The analysis decides code approvals; it does not say whether such a stay's first end may be recorded as the repeal when no held record shows the contingent event. I recorded the repeal as the latest supported end with the limitation stated in each clause (the held corpus contains no Administrator orders), and said a held lifting order would become the first end. A reviewer may prefer a block for these; the clauses are separated so that this is easy to change.
- A direction to a government officer inside a code approval (EO 6524) versus a direction to a code-created body (EO 6641, 6694-A proviso 4). The shared analysis lists "directions to agencies" as independent commands; I treated Code Authority directions as code-dependent and the Administrator direction as independent. This is a judgment, stated in each row.
- A condition that creates a committee (EO 6272, EO 6329 Section 8(a)) was treated as a term of the approval; no held record shows any committee formed.

## Method notes

Quotations in `reason` fields were sliced from the held registered text by script, not typed, so capitalisation, OCR spellings and punctuation match. The S.J. Res. 113 section 2 quotation omits the held line breaks only. No dossier evidence id appears in prose. Nothing outside this packet was written; no git command was run. The builder script is in the session scratchpad (`/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad/n07/build_sheets.py`), outside the repository.

Tool-call count: about 38 (the brief expected few; most calls were reading the briefs, the packet and the held source texts once each, plus one build script, one apply-and-check run and two waits).
