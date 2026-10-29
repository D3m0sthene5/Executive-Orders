# Producer report: batch b1b (claude, 2026-10-28)

This is producer work only. No independent review, controls or completion have been run, nothing was committed, and the certified count stays 0. Legal cutoff 2026-10-14.

**Result.** 34 orders submitted, 1 blocked (EO 2954), 0 unresolved.

**Times (UTC).** Started 2026-10-28T19:58:10Z. Ended 2026-10-28T20:44Z.

**Final applied directory:** `research/excavator/claude-production-2026-10-28/b1b/packet/supp/applied-v3`. The batch-check output is saved there as `BATCH_CHECK.stdout.json`.

**Batch-check (applied-v3).**
- Strict claim checks: 34 of 34 pass, 0 fail. Assembly errors: none.
- Actual claim-checker: 34 of 34 pass the gate, with 0 mechanical failures.
- Custody: 32 claims carry `source_held:custody_record_only` items, so they are "unverified". These are web captures and the later-order APP texts, whose raw captures are not yet committed. Only EO 254 (ProQuest scan) and EO 5763 (OFR compilation) pass every check.
- Exit code: 1. The command's exit rule (`kit.py`, line 199) fails whenever `claims_all_checks_passed` is less than `claims_checked`, so the custody-unverified claims alone set it to 1. No other failure remains.

**Earlier versions, kept as produced.**
- applied-v1: EO 254 was rejected with `working_text:page_confirmation_required`. I had not set `pages_confirmed` for the ProQuest scan, although I had checked its page image.
- applied-v2: EO 254 was fixed. EO 6088 then failed the checker with `held_but_different_hash`; the tool-defects section explains why.

## Folder layout

Everything about these orders is inside `b1b/packet`:
- the parent packet and `SUPPLEMENT_DECLARATIONS.json`;
- the supplemented packet `packet/supp`, which is the final packet;
- `packet/supp-source-dossiers`, written by the supplement tool.

The supplement adds 11 held APP excerpts of later further-exemption orders as `SUPPLEMENT:<alias>`: EO 6615, 6974, 6998, 7597, 7006, 7050, 7308, 7569, 7445, 7728 and 7666. Each excerpt runs from the "And Whereas" recital through the operative "Now, Therefore" sentence. Each source was registered by the fragment registry as mirror_transcription and passed the APP page check.

## Common basis for the retirement exemptions (31 orders)

Each order exempts a named employee from automatic separation under section 204 of the Legislative Appropriation Act of June 30, 1932 "until" a stated date. I read each order's registered APP text in full. The page check per AGENT_PROTOCOL.md passed for each: the MIRROR_DOCUMENTS row with the same sha256 names the order, its date appears in the held text, and its text_sha256 matches the held file. I checked the number, date, person and end date against the census register and the WPA 1944 list.

The end is the stated date, recorded inclusive, with the exclusive reading stated as the alternative. A later "further exempt" order is recorded as a later event with its own date and mechanism `separate_further_exemption_order_same_employee`; it is never treated as this order's end.

I ran four name and citation searches for each order: register titles, WPA entries, full-name full text, and "Order No. N" citations. Two held exemptions corroborate that section 204 still operated after every end date in the batch: EO 7725 of October 12, 1937 and EO 7842 of March 15, 1938.

## Per order

| Order | Outcome | Reason, and what took the time |
|---|---|---|
| EO 254 | submitted | Hanna funeral closing of Ohio offices; ends 1904-02-19 by its own terms. I rendered the ProQuest page and read the order from the image, because the OCR is garbled. The dossier's clause span was OCR noise, so I corrected the inventory to characters 163–565 (scope `EO:254#corrected-1`). |
| EO 2954 | **blocked** | The order voids the 1918 Manila sale of Froehlich & Kuttner and directs the Alien Property Custodian to reject all bids. No held source shows when, or whether, the bids were rejected. Needed: Alien Property Custodian Report (1919), page 540 (WPA "APC 540"), or the Custodian's records. The dossier inventory also wrongly lists reasons (2), (3) and (5) as its clauses. Time went to the type rule and the search for the Custodian's report. |
| EO 5763 | submitted | Closing of District of Columbia offices on December 26, 1931; ends 1931-12-26. The original is the OFR 1974 compilation (acceptable as original). The compilation PDF is only an LFS pointer in this checkout, so the printed pages were not viewed (pages false). Little time. |
| EO 6013 | submitted | Pearson and Nuber; ends 1934-02-28. Later events: EO 6615 and EO 6974 (Nuber). No later held order names Pearson. Time went to correcting the inventory to characters 1003–1632, because the machine span began with the text file's provenance header. |
| EO 6088 | submitted | Bailey; ends 1935-03-31. Later events: EO 6998 and EO 7597. Most time in the batch went here. The dossier's original is the live-harvested APP page. A registered mirror capture with byte-identical text is held, but the checker cannot verify that capture (see tool defects), so the end cites ORIGINAL:EO:6088. The mirror equivalence is disclosed in the rationale. |
| EO 6106 | submitted | Morrison and Roberts; ends 1935-04-30. Later event: EO 7006 (Roberts). The WPA list summarizes EO 7007 (Morrison) as a further exemption, but no text of EO 7007 is held, so it is disclosed in the rationale and not recorded as a later event. |
| EO 6264 | submitted | Metzger; ends 1933-12-31. Routine. |
| EO 6609 | submitted | Bach; ends 1935-02-28. Routine. |
| EO 6615 | submitted | Nuber; ends 1935-02-28. Later event: EO 6974. I skipped the machine own-terms records dated 1933-02-26, which picked up Nuber's birthday as an end date. |
| EO 6688 | submitted | Crone; ends 1934-11-01. Routine. |
| EO 6717 | submitted | Dixon; ends 1935-06-01. Later event: EO 7050. The operative clause reads "Juno 1, 1935", so the end cites the recital's record, which EO 7050 corroborates. |
| EO 6847 | submitted | Summers; ends 1935-10-01. Routine. |
| EO 6893 | submitted | Fenton; ends 1935-11-01. The "Junes P. Fenton" misprint is noted. |
| EO 6914 | submitted | Jeansen; ends 1936-03-31. Later events: EO 7308 and EO 7569. The WPA date (December 14) conflicts with December 6 in the APP text, the register and both recitals; the claim uses December 6. |
| EO 6974 | submitted | Nuber; ends 1936-03-01. No later order found. |
| EO 6998 | submitted | Bailey; ends 1937-04-01. Later event: EO 7597. The WPA date (March 25) conflicts with March 30 in the APP text, the register and the recital in EO 7597; the claim uses March 30. |
| EO 7006 | submitted | Roberts; ends 1937-05-01. No later order found. |
| EO 7050 | submitted | Dixon; ends 1936-06-01. No later order found. |
| EO 7071 | submitted | Hood; ends 1936-07-01. Routine. |
| EO 7122 | submitted | Westcott; ends 1936-01-01. Routine. |
| EO 7166 | submitted | Travis; ends 1936-03-01. Routine. |
| EO 7188 | submitted | O'Reilly; ends 1936-11-01. Later events: EO 7445 and EO 7728. |
| EO 7232 | submitted | Henry; ends 1936-12-01. Routine. |
| EO 7249 | submitted | Half-day closings on December 24 and 31, 1935; ends 1935-12-31. The shift-work paragraph is tied to the same dates. Little time. |
| EO 7273 | submitted | Kumler; ends 1937-02-01. Routine. |
| EO 7300 | submitted | Stuart; ends 1937-03-01. It recites the earlier EO 6932. No later order found. |
| EO 7308 | submitted | Jeansen; ends 1937-04-01. Later event: EO 7569. |
| EO 7317 | submitted | Leffler; ends 1937-05-01. It recites the earlier EO 7008. No later order found. |
| EO 7380 | submitted | Pierro; ends 1937-06-01. Routine. |
| EO 7440 | submitted | Sornborger; ends 1937-10-01. Routine. |
| EO 7445 | submitted | O'Reilly; ends 1937-11-01. Later event: EO 7728. |
| EO 7456 | submitted | Bean; ends 1937-10-01. Routine. |
| EO 7473 | submitted | Planert; ends 1937-11-01. Routine. |
| EO 7492 | submitted | Woods; ends 1937-09-01. Later event: EO 7666. |
| EO 7525 | submitted | Shumate; ends 1938-01-01. Routine. |

No tax-return-inspection order is in this batch.

## Tool defects found

1. **The checker cannot verify a registered mirror capture whose URL also has a live harvest.** For EO 6088, the common-crawl capture (sha256 abbf450a…) is registered in `jobs/app-transcriptions/output/FRAGMENTS.jsonl` and `MIRROR_DOCUMENTS.jsonl`. The checker's custody index (`SOURCES.jsonl`) has no record for that hash, and it resolves the URL to the live bytes (f6ccd51d…). So citing the mirror's own-terms record fails as `held_but_different_hash`, even though the text is byte-identical. The packet also chose the live-harvested file as the dossier's original even though a re-provable mirror capture was held.
2. **The batch-check exit code does not separate custody-unverified claims from real failures.** It exits 1 whenever any claim is not fully passed, so every batch of APP-based claims exits 1 until custody copies are committed. Producers must read the JSON to see the real result.
3. **The dossier's clause inventory is unreliable on OCR texts.** EO 254's machine span is noise. EO 2954's three clauses are reasons, and its operative command is missing. EO 6013's span begins with the text file's provenance header.
4. **The machine own-terms extraction mislabels some dates.** For EO 6615 and EO 6974 it records 1933-02-26 (the employee's 70th birthday) as a stated end or fixed term. For EO 6717 it records no date because of the "Juno" misprint.
5. **The compilation source book is not materialized.** `releases/source_books/OFR_1974_Hoover_...pdf` is a 133-byte pointer, so its page images cannot be checked locally.
6. **Apply and batch-check are slow.** Each takes about 4–5 minutes for 35 orders.

**Update (20:59Z):** once Cotton's custody copies were committed, EO 6088's end was changed to cite the registered mirror capture (`TERM:EO:6088:4be99dca031b2830@6103fadfdda7f197`, sha256 abbf450a…). The rationale was updated to match, and no other row changed. The checker now passes source custody for EO 6088's end (`first_end.source` and `whole_order_end.source`), and the claim has no failures. Its clause quote still cites the live-harvested file, which remains custody-unverified, because an inventory override can only point at the dossier's original.
**New final applied directory:** `applied-v4`. Batch-check gives 34 of 34 strict passes, 0 mechanical failures, 27 claims passing every check and 7 custody-unverified, so the command still exits 1.
