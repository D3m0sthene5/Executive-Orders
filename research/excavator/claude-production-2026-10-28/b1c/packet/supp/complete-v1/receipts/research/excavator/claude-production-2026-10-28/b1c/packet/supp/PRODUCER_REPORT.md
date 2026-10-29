# Producer report, batch b1c (Claude, 2026-10-28)

Start 2026-10-28T19:58:10Z. End 2026-10-28T20:45:33Z (UTC). Wall time about 47 minutes, of which roughly 20 minutes were
tool runtime (supplement preparation, three applies, two batch-checks).

## Result

- 35 members: 31 submitted, 4 blocked.
- Final packet: `research/excavator/claude-production-2026-10-28/b1c/packet/supp` (source supplement of the prepared parent
  `b1c/packet`; the declarations are `b1c/packet/SUPPLEMENT_DECLARATIONS.json`, 15 excerpts from held APP mirror texts of later
  further-exemption orders).
- Final applied directory: `supp/applied-v3`.
- Batch-check of applied-v3: 31 claims checked, 31 strict pass, 0 strict fail, 31 gate pass; actual claim checker 25 all checks
  passed, 6 mechanically unverified for custody only (`custody_record_only`: EO 7094 sources, and the later-event sources of
  EO 7336, 7413, 7444, 7478, 7531), 0 mechanical failures. The command exits 1 because kit.py fails whenever any claim is
  short of all checks passed, which includes custody-only gaps.
- applied-v1 rejected EO 7094 (`working_text:page_confirmation_required`); applied-v2 assembled 32 but the checker failed
  EO 7094 (held_but_different_hash) and EO 7314 (quote_verbatim not_found). Both are handled in v3 as described below. v1 and v2
  are kept unchanged.

## Method shared by the exemption orders

Each order's registered APP mirror text was read in full; the page check (MIRROR_DOCUMENTS.jsonl record with the same sha256:
heading names the order, date agrees with the text's date line, text_sha256 equal) was done by script and every one passed. The
end cites the own-terms lead on the registered text (not the clause-drafts copy). Later orders were found by three searches:
census-register retirement/exemption titles by surname, full-text name search of every held order text, and a citation search for
the order number. Every later order found recites the earlier order as a past grant and grants a new period; none amends it, so each
is a later event (owner ruling 2026-10-21) and the end stays on the order's own date, inclusive, with the exclusive reading stated.

## Per order

| Order | Outcome | End / reason | What took the time |
|---|---|---|---|
| EO 3108 | blocked | Original is CSC 1919 annual report OCR (compiled_transcription_lead, page check required) and the report PDF is not held; inventory omits the lead permission (chars 15-455); revocation by EO 9830 Part III (eff. 1947-05-01, held FR text) is not attached as evidence. | Reading the CSC text and locating 3108 in the EO 9830 FR revocation list. |
| EO 4354 | submitted | 1925-12-26, one-day closing, own terms. | Rendering and reading the ProQuest page image. |
| EO 5930 | blocked | Paragraph 6 it added (to Feb 1, 1933) was later amended by EO 6352 (1933, "1934" for "1933") and again by EO 7209, 7487, 8007; lapse vs strike-and-insert continuation undecided; final disposition of paragraph 6 not established. | Finding the paragraph 6 amendment chain and EO 5731 precedent. |
| EO 6030 | submitted | 1935-02-28; later event EO 6975. Original is the OFR 1974 Hoover compilation (acceptable as original); PDF is an LFS pointer, so the confirmation rests on the registered compilation text. | Checking the compilation text and its status. |
| EO 6168 | submitted | 1933-12-31. | Routine text and search check. |
| EO 6263 | submitted | 1935-08-31; later event EO 7167 (names "Joseph L. Smith", same post, cites EO 6263). | The citation search found 7167 under a different name form. |
| EO 6302 | submitted | 1935-09-30. | Routine. |
| EO 6610 | submitted | 1934-08-31; later event EO 6825 (spent-probe order). | Routine; supplement excerpt. |
| EO 6687 | submitted | 1935-05-01; later event EO 7030. | Routine; supplement excerpt. |
| EO 6703 | submitted | 1935-06-01. | Routine. |
| EO 6753 | submitted | 1935-02-01; later event EO 6933. The machine lead's 1934-07-28 (age date) was not used. | Choosing the operative lead. |
| EO 6864 | submitted | 1935-11-01. | Routine. |
| EO 6931 | submitted | 1936-01-01. | Routine. |
| EO 6933 | submitted | 1935-08-01; recites EO 6753. | Routine. |
| EO 6975 | submitted | 1936-03-01; recites EO 6030. | Routine. |
| EO 7030 | submitted | 1936-05-01; recites EO 6687. | Routine. |
| EO 7042 | submitted | 1936-06-01. | Routine. |
| EO 7072 | submitted | 1936-07-01; later event EO 7385. | Routine. |
| EO 7094 | submitted | 1936-08-01; later event EO 7395. End cites ORIGINAL (live registration, sha bbfc2267) because the mirror-bound TERM leads failed the checker as a different saved copy; identical text is held from the mirror capture. | Two fixes: page confirmation of the second registration, then the end citation. |
| EO 7155 | blocked | "For such time as may be deemed necessary, not in excess of five years from October 31, 1935": only an outer bound (1940-10-31); no held record of Carr leaving the service. | Deciding bound vs end. |
| EO 7184 | submitted | 1936-10-01. | Routine. |
| EO 7230 | submitted | 1936-12-01 (recital OCR "193G"; operative sentence reads 1936); later event EO 7494. | Choosing the operative lead. |
| EO 7238 | submitted | 1936-12-01; recites EO 6899 ("Thurson" in that order's APP title). | Routine. |
| EO 7286 | submitted | 1937-03-01. | Routine. |
| EO 7314 | blocked | Ends 1937-05-01 on the held text, but the checker verifies quotes against the clause-drafts copy, which lacks the date line, so the original-representation quote fails (213 of 216 words). Not fixable from the decision sheet. | Diagnosing the checker failure. |
| EO 7336 | submitted | 1937-05-01; later event EO 7580 (the dossier's ACT lead labels it "transfer"; not adopted). | Routine; supplement excerpt. |
| EO 7385 | submitted | 1937-07-01; recites EO 7072. | Routine. |
| EO 7413 | submitted | 1937-09-01; later events EO 7635, 7945, 8231. | Reading three later texts. |
| EO 7444 | submitted | 1937-11-01; later event EO 7727. | Routine. |
| EO 7457 | submitted | 1937-10-01. | Routine. |
| EO 7478 | submitted | 1937-12-01; later event EO 7750. | Routine. |
| EO 7494 | submitted | 1937-12-01; recites EO 7230. | Routine. |
| EO 7516 | submitted | 1938-01-01; recites EO 7255 (spent-probe order). | Routine. |
| EO 7519 | submitted | 1938-01-01. | Routine. |
| EO 7531 | submitted | 1938-01-01; later event EO 7777. | Routine. |

## Tool defects hit

1. Claim checker, EO 7314: quotations are verified against the text recorded for the source hash, and the only recorded text it
   finds is the truncated clause-drafts copy (ends at "The White House,"), not the registered APP mirror file. A correct claim fails
   quote_verbatim; the order had to be blocked.
2. Dual registration, EO 7094: the dossier's original and clause cite the live-harvest registration (sha bbfc2267...) while the
   own-terms leads on the same text bind to the mirror registration (sha d294b396...); the working-text gate needed a page
   confirmation on the live entry, and the checker then failed the mirror-bound lead as held_but_different_hash.
3. Dossier EO 3108: the clause inventory omits the lead paragraph, and "target provision not located: EO:9830" although the held
   FR text of EO 9830 lists "No. 3108 of June 30, 1919" in Part III.
4. Machine own-terms leads: EO 6753 offers the age date 1934-07-28 as a stated end; EO 7230 has a lead with no date because of OCR
   "193G"; the ACT lead EO 7336>EO 7580 carries the verb "transfer".
5. `kit.py batch-check` exits 1 whenever any claim is custody-unverified, so its exit code does not separate expected custody gaps
   from real failures. `apply` took 4 to 7 minutes and `view --order` about 3 seconds per order on this packet.
6. The OFR 1974 Hoover compilation PDF in `releases/source_books` is a Git LFS pointer in this checkout, so official compilation
   pages (EO 5930, 6030) cannot be inspected as images.

Nothing about these orders was written outside `research/excavator/claude-production-2026-10-28/b1c/`. Certified count unchanged at 0.

Update 2026-10-28T20:46:28Z to 21:00:33Z: EO 7314 resubmitted unchanged (end 1937-05-01, inclusive) after the checker fix; applied-v4 has 32 submitted and 3 blocked, and batch-check gives 32 strict pass, 0 strict fail, 26 all checks passed, 6 custody-unverified, 0 mechanical failures (exit 1 only from custody gaps).
Custody-unverified in applied-v4: every EO 7094 source (live-harvest registration, sha256 bbfc2267...), and the later-event excerpts EO 7580 (for 7336), EO 7635, 7945 and 8231 (for 7413), EO 7727 (for 7444), EO 7750 (for 7478) and EO 7777 (for 7531).
