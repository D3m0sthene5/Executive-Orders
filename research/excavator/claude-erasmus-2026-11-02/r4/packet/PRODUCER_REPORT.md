# Producer report: Erasmus r4 (resubmission)

- Producer: claude (Opus 5.5). Start 2026-11-02T03:51:30Z; end 2026-11-02T04:12:01Z.
- Final applied directory: `applied-v2/`. Submitted: 9. Blocked: 2 (EO 11343, EO 12095).
- `applied-v1/` is superseded. It held 9 assembled claims and 2 rejections. The rejections came from later events whose source was a held board report graded `held_text_lead`, which the claim kit refuses.
- The sheets (`decisions.csv`, `clauses.csv`) were rebuilt from the prior Apollo rows by a script that holds the reviewed prose. Every quotation in the 9 submitted claims was checked by machine against the held bytes of the cited texts, and all of them match.

## Outcome per order

| Order | Outcome | End | Basis |
|---|---|---|---|
| EO 11314 | submit | 1986-02-25 | EO 12553 revokes it by number. The report date is a deadline, and no report of this Board is held. |
| EO 11329 | submit | 1986-02-25 | Same as EO 11314. |
| EO 11343 | blocked | (drafted: EO 12553, 1986-02-25) | The report-deadline ruling requires the report (dated 1967-05-12) and the end of the standstill (1967-06-11) as later events. The only evidence is the NMB PEB-170 report, held as `held_text_lead` text. The kit refuses that grade as a source, and the PDF is not held, so a source supplement cannot be prepared. |
| EO 11355 | submit | 1994-06-03 | EO 12919 §904(a)(6) supersedes or revokes it. The EO 12107 word substitution (effective 1979-01-01) is a later event of clause 1. |
| EO 11431 | submit | 1986-02-25 | Same as EO 11314. |
| EO 11436 | submit | 1986-02-25 | EO 12553 revokes it by number. Two disclosed unnamed candidates: the National Emergencies Act §502(a)(8) excludes §6386(c), and Pub. L. 96-513 §335 repealed §§6372 and 6386, effective 1981-09-15. |
| EO 12095 | blocked | (drafted: EO 12379 §5, 1982-08-17) | The report-deadline ruling requires the report (dated 1979-02-09) as a later event. The source is the same kind as for EO 11343: a `held_text_lead` copy of the NMB PEB-189 report, with the PDF not held. |
| EO 12121 | submit | 1982-08-17 | EO 12379 §20 revokes EO 12083 "as amended". EO 12156 is a later event. The abolitions of the CSA and COWPS are disclosed as earlier candidates. |
| EO 12398 | submit | 1986-02-25 | EO 12553 revokes it by number. EO 12429, EO 12447 and EO 12455 are later events of §4(b), each with before and after text. EO 12534 (1985-09-30) is disclosed. |
| EO 12429 | submit | 1986-02-25 | Same as EO 12398. EO 12447 and EO 12455 are later events. |
| EO 12891 | submit | 1997-09-30 | EO 13062 §3(a), effective under §7. The §4(b) report-relative sunset is disclosed with the EO 12975 interval (a report existed by 1995-10-03). |

## Brief defects, per order

- **EO 11314, 11329, 11431: confirmed and fixed.** The prior claims put paraphrased report dates in quotation marks. The new claims quote only exact substrings ("on or before October 18th, 1966"; "with the provisions of Section 206 of such Act on or before March 8,"; "on or before October 2,") and paraphrase the rest without quotation marks. Further fixes found on recheck:
  - The prior claims said the by-number scan lists EO 12553. It does not: EO 12553 names these orders only in the number column of its table, which the scan's regex misses.
  - The phrase "no held instrument other than EO 12553 names it" was unverified. It now reads "the by-number scan finds no later order citing it".
  - The independent-command check asserted that the Board reported. No report is held, so the claims now say the report is not established.
- **EO 11343: confirmed.** A held report exists (transmittal letter dated May 12, 1967), and the ruling requires it as a later event. I drafted both later events, using the report as the source for the report and the order's own FR standstill sentence as the source for the standstill end, plus a source note "functionally spent on 1967-06-11". apply-v1 rejected the report source (working-text policy). **Could not resolve; blocked** with the remedy named in the row.
- **EO 11355: confirmed and fixed.** The search account now names full reads of EO 12919 and of EO 12107 §§2-101 and 2-404, not EO 12553. Further fixes found on recheck:
  - An unverified sentence saying the catalog lists "exactly those two" was replaced with the verified catalog note "Amended by: EO 12107, December 28, 1978".
  - Clause 3 (the revocation of Part II of EO 10647) now states the alternative reading that it was exhausted on signing. The whole-order end is unaffected.
- **EO 11436: confirmed and fixed.** The template text about 5711(b), 5701 and chapter 545 came from EO 11284 and was removed. The claim now cites only §6386(c), and quotes Pub. L. 96-513 §335 (repealing §§6372 and 6386). Added on recheck: the National Emergencies Act §502(a)(8) exclusion of §6386(c), as a candidate that does not reach the order's authority.
- **EO 12095: confirmed and fixed in the draft.** The draft states that the order has only 1-101 and 1-102 and contains no standstill. Recheck found the held PEB-189 report dated February 9, 1979, which the ruling requires as a later event. That source is not usable in the kit, so the order is **blocked** (see the table).
- **EO 12121: confirmed and fixed.** Two earlier candidates are now disclosed with their held sources pinned in prose (path and sha256):
  - The CSA abolition, from the OFR note in `EO_12344.txt`.
  - The COWPS abolition, from the OFR note in `EO_12154.txt`. That note credits EO 12288, but the held text of EO 12288 does not abolish the Council: it treats the Council as still existing. No held source dates the Council's end, so the claim does not establish that both offices had ceased before 1982-08-17.

  The end stays EO 12379 under the unnamed-instruments ruling. I also corrected the EO 12156 quotation, which had spanned a line break.
- **EO 12398: confirmed and fixed.** EO 12429, EO 12447 and EO 12455 are now `later_events`, with sources from the official FR texts (ACTOR_TEXT), signing dates, and before and after text. The note that EO 12429 drops the FACA lead-in words is included.
- **EO 12429: confirmed and fixed.** EO 12447 and EO 12455 are now `later_events`, with before and after text.
- **EO 12891: all three defects confirmed and fixed.**
  - §4(a) assigns the functions to the Working Group, not to an official.
  - sec2-2 now describes the command to advise on specific experiments, with items (1) and (2).
  - sec2-5 now describes item (5) and the paragraph on the 1944 to May 30, 1974 review period. Items (3) to (5) are labelled as list items. sec2 now says the definition has two categories.

  Further fixes found on recheck:
  - The prior "U.S. Code 0 hits, eCFR 0 hits" was false. The two USC hits are notes under 42 U.S.C. 2210 and 6601, and neither yields a current-law predicate.
  - sec1 now gives the cap of 15 members.
  - The EO 12975 interval disclosure was added.

## What took the time (one line each)

- EO 11314, 11329, 11431: checking exact quote substrings and confirming that no report is held.
- EO 11343: tracing the report source and computing the standstill; then the kit rejected the report as a source.
- EO 11355: verifying the EO 12107 §2-101(b) list and the quotes from EO 12919 §903 and §904.
- EO 11436: the Pub. L. 96-513 §§335 and 701-703 text; found the National Emergencies Act exclusion.
- EO 12095: the report front matter (date); then the same kit refusal as EO 11343.
- EO 12121: the OFR editorial notes for CSA and COWPS against the held text of EO 12288.
- EO 12398, 12429: reading the FR texts of EO 12447, EO 12455 and EO 12534, and building the before and after events.
- EO 12891: rewriting the 18 clause reasons; the current-law hits; finding EO 12975.

## batch-check (applied-v2)

- 9 claims checked; 9 pass strict; 0 strict failures. Gate: 9 of 9 passed.
- Actual checker: 8 pass every check. 1 (EO 12891) is `pass_with_unverified`, because the EO 13062 source is a `custody_record_only` hold: the EO 13062 PDF is not held locally. The prior g10 run had the same hold. I cannot fix this from the packet; it needs custody of the EO 13062 PDF. batch-check exits 1 because of this unverified item only.

## Geddes

- `applied-v2/GEDDES_LINT.json`: 0 defect flags.
- 3 coverage gaps, all on EO 12891: own order body unverified because the heading is unresolved, and literal-name items unresolved. Coverage gaps are not defects. I read the full printed order myself, from the heading through the signature.
- `GEDDES_RESOLUTIONS.json` is empty because there are no flags. Geddes did not crash.

## Full-packet files opened beyond the views

- `PACKET.json` `dossiers[*].machine_searches` (resolved through `shared_objects`), for the coverage notes and hit counts. The view lacks the machine searches.
- `PACKET.json` `sources` and `text_blocks`, and the dossier `evidence` for EO 11343 and EO 12095, to find the evidence ids for the held board reports and the order-text TERM spans. The view lists catalogue ids but not the evidence spans or kinds.
- `PACKET.json` `dossiers[EO:12121|EO:12095|EO:11355].chain`.
- Outside the packet (read only): `jobs/status-history` histories, `jobs/later-events/output/FRAGMENTS.jsonl` (to verify the OFR catalog note wording), and `jobs/current-law/output/MENTIONS.csv` (the EO 12891 hits).

## Tool defects and observations

1. The claim kit refuses a `held_text_lead` source anywhere in a claim, including a later event or source note. The working-text policy's GRADES excludes it. The NMB board reports held by source-ladder therefore cannot be used for the later events that the report-deadline ruling requires. A source supplement needs the PDF on disk, but source-ladder holds only a runner cache path. Suggested remedy: commit custody copies of PEB-170-Report.pdf (sha256 5a7a3638…) and PEB-189-Report.pdf (sha256 060e9e9d…), then supplement.
2. `batch.load_packet` needs `Path` arguments. Strings raise a TypeError.
3. The Cruden by-number regex misses EO 12553's and EO 12107's table-column listings, where the number appears without "Executive Order". Producers must read those tables themselves.
4. The view omits `machine_searches`, which every claim needs.

Nothing was published. No filed claim under `research/readiness/claims/` was edited, and no git state was changed.
