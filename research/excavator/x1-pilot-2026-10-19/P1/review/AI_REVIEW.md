# P1 independent AI review (claude-x1-reviewer-P1)

This is an AI review by an independent agent. It is **not** a human certification and not an `eo-lifecycle-review/v1` record. The certified whole-lifecycle count stays at 0. The machine-readable record is `AI_REVIEW.json`.

**Counts.** 20 members: 3 submitted, all 3 upheld, 0 rejected. 17 blocked, all 17 block_justified, 0 block_not_justified.

## Submitted claims (applied-v3/CLAIMS.proposed.jsonl)

| Order | End (own terms) | Decision | claim sha256 |
|---|---|---|---|
| EO 5881 | 1932-08-01 | uphold | 60c73895…22eb |
| EO 5981 | 1933-05-31 | uphold | 017c1c2a…fd62 |
| EO 5982 | 1933-03-31 | uphold | 312eb117…8302 |

I read each held OFR 1974 text in full. Each order has one operative clause, its end date is its own stated term, and its only savings are accrued service and pay. For EO 5881, the July 10, 1932 date is the term of the earlier EO 5874, which the order recites. I confirmed this in the held text of EO 5874. The producer correctly overrode the machine TERM record, which still carries 1932-07-10. The human reviewer should be told about that record.

I re-ran the pre-1937 search for each name in three sources:
- the WPA 1944 numbered list (whitespace-insensitive);
- all 526 Hoover texts;
- the APP title index.

No later order names any of these persons. EO 6142 (May 1933) shows that a later order could end one of these exemptions early (the Neagle exemption under EO 5872). That makes the search necessary, and the search finds nothing for these orders. EO 6142 and EO 6146 also show section 204 still being administered through May 31, 1933.

Points for a correction version (not grounds to reject):
1. The structured `later_source_search` lists only USC, eCFR and the OFR catalog, which starts in 1937. The decisive WPA/Hoover-text search appears only in prose and should get its own entry.
2. `original_pages_confirmed` is false. Here the PDF is only an LFS pointer, so I could not check the page images.
3. The OCR for EO 5981 also omits the signature line.

What remains open: unnumbered orders, and multi-person orders whose WPA summary leaves out names.

## Blocked rows

All 17 blocks are justified:
- **Originals not acceptable:** EO 5, 2834, 6128, 6694 and 7180.
- **No dated record of the appointment the waiver allowed:** EO 5620, 5893, 6028, 6061, 6063 and 6067.
- **Later extension orders whose texts are not held:** EO 6013 (EO 6615) and EO 6030 (EO 6975).
- **No located ending provision:** EO 283.
- **Missing ACT record and possible earlier replacement:** EO 5704 (EO 7676 / EO 6390 / Canal Zone Code).

EO 5763 and EO 5930 are blocked by a tooling limit, which I checked in `assemble.py` and `batch.py`. The dossiers have no own-terms record, and the batch CSV has no mechanism column. EO 5763 is otherwise close to submittable. EO 5930 should also list EO 5731 (1931, the earlier Paragraph 6) and EO 6352 (1933, which later amended Paragraph 6) as missing items.
