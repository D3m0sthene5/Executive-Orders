# Producer report: 20-order lifecycle probe (claude, 2026-10-28)

Legal cutoff 2026-10-14. The codebook is unchanged. This is producer work only. It contains no independent review and no human certification, the certified count stays at 0, and nothing was committed or pushed.

**Result.** Two orders were submitted (EO 1547 and EO 4782), 18 were blocked and none were left unresolved. The final applied directory is `packet/applied-v2`. Batch-check **fails**, exit code 1. Both claims pass the Stage 19 gate and the strict claim check (2 of 2). Both fail one mechanical check in the actual claim-checker, `date_valid:not_exact_iso_date`, on `signing_date`. The packet's frozen ProQuest source records carry a year only ("1912", "1927"), and the checker requires a full YYYY-MM-DD date. The value comes from `jobs/pinakes-proquest-ingest`, not from my decisions. I cannot fix it inside this packet without editing source provenance. The fix is for the ingest to emit the full date read from the scan, followed by a re-prepared packet. The scans show June 19, 1912 and December 16, 1927. The legal judgments were not weakened to pass the check.

**Times (UTC).** Started 2026-10-28 17:01:46. Ended 2026-10-28 17:55:16.

**Versions.** `applied-v1` was the first apply. `applied-v2` sets `original_pages_confirmed` to true for the six ProQuest orders whose page images I inspected. It made no legal change. Claim sha256 values in v2: EO 1547 `f8fb1556…0218`, EO 4782 `48f71f49…1093`.

**Owner ruling not found.** `research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md` and the decision `D-20261028-evidence-decides` are not in this checkout, either in `jobs/kean/register` or anywhere in the repository. I applied the version stated in the assignment: evidence decides, disclosure never fills a gap, and a later general rule ends a command only when something shows that it extinguished that command.

## Per order

### Submitted

- **EO 1547** (Taft, 1912-06-19). The order waives the 1912 eight-hour act for Isthmian Canal construction contracts "until January first, nineteen hundred and fifteen".
  - First end: its own terms, 1915-01-01, read inclusively. The exclusive reading, which ends the waiver when that day begins, is stated as the alternative.
  - Savings: work done on contracts formed under the waiver is an accrued effect. It does not keep the order operative.
  - Earlier-end candidates considered and not shown to extinguish the waiver: the Panama Canal Act of 1912 (text not held), EO 1885 and EO 1888.
- **EO 4782** (Coolidge, 1927-12-16). The order closes District of Columbia offices and excuses employees on Saturday, December 24, 1927.
  - First end: its own terms, at the close of 1927-12-24.
  - The sentence "not … a precedent" is not an independent command.
  - EO 5008 (1928) is a separate one-day order, not an extension of EO 4782.

### Blocked: transcription grade the tooling cannot carry (12 retirement exemptions, plus EO 6516 and EO 6874)

For every APP-held order, the packet's original is the clause-drafts copy, graded `derivative_lead`. That grade is outside the working-text gate's accepted grades, and no FRAGMENTS record registers that copy. The registered APP copy is listed as `mirror_transcription`, but the packet labels it `compiled_transcription_lead`, so a claim citing it fails the grade match. A dry assembly confirmed both failures.

This is a packet-preparation defect, not a legal gap. The owner's 2026-10-21 transcription ruling admits these texts as working texts. The fix is to re-prepare the packet against the registered APP fragment with a reconciled grade. For every one of these orders I read the text in full and confirmed its identity and completeness. The working-text confirmations are set to true and the page confirmations stay false.

Legal reading for the retirement exemptions: each exempts one named employee under §204 of the Economy Act of 1932 until the stated date, which is recorded as inclusive. Service and pay are accrued effects. Annuity consequences come from statute and do not keep the order operative. I searched the census titles, the TYPES file, the full WPA 1944 numbered list, and the full text of every held order for each surname.

| Order | Person | Stated end | Further blocker beyond the grade |
|---|---|---|---|
| EO 6107 | Reuben Perry | 1933-06-30 | none; no later order names him |
| EO 6146 | Walter L. G. Perry | 1935-05-31 | none |
| EO 6825 | C. Frank Wittenauer | 1935-09-01 | none (EO 6610 is the earlier grant it recites) |
| EO 7247 | Nelson H. Darton | 1937-01-01 | none |
| EO 7310 | W. H. Moran | 1937-01-01 | none (EO 6647 is the earlier grant it recites) |
| EO 7394 | Benjamin F. Taylor | 1937-08-01 | none (EO 7093 is the earlier grant it recites) |
| EO 7401 | Henry Blackwood | 1937-07-01 | none |
| EO 7438 | George S. Rice | 1937-10-01 | none |
| EO 6663 | Luther L. Browning | 1935-04-01 | EO 6984 (to 1936-04-01) and EO 7307 (to 1936-11-01) further exempt him; both are held in the repository but neither is in the packet, so they cannot be recorded as later events |
| EO 7208 | George G. Hedgcock | 1936-11-01 | EO 7475 (to 1937-07-01) is held but not in the packet; EO 7645 (to 1938-01-01) is in the packet only as an unlocated actor text |
| EO 7255 | Elton A. Gongwer | 1937-01-01 | EO 7516 (to 1938-01-01) is held but not in the packet |
| EO 7278 | William H. Ramsey | 1937-02-01 | EO 7545 (to 1938-02-01) is in the packet only as an unlocated actor text with derivative grade |

- **EO 6516.** Closing on December 23 and December 30, 1933. It would end by its own terms at the close of 1933-12-30. The grade block is its only block.
- **EO 6874.** This is not a closing order. It amends Schedule A, Subdivision VII, ¶6 of the civil-service rules to except temporary Postal Service holiday workers "from this date to February 1, 1935", so the type label is wrong. Besides the grade block, two problems remain:
  - Under the strike-and-insert ruling, someone must decide whether the first end is the inserted sunset (1935-02-01) or the replacement of the paragraph by EO 7209 (1935-10-19). EO 7209 is held but not in the packet.
  - The earlier versions of ¶6 (EO 5731, EO 5930 and EO 6352) are not in the packet.

### Blocked: completion date not held (four eight-hour orders)

The page images were inspected and the identity, completeness and page confirmations are set to true. Each order ends when its work was completed, or when its authority ended if that came first. Neither date is held.

- **EO 2842** (1918-04-20). DC water mains. The order names no suspension statute. Source needed: the DC Commissioners' report (Water Department) for fiscal 1918 or 1919.
- **EO 2855** (May 1918). Treasury Vault No. 17. The day of the month cannot be read with certainty on the scan (May 1 or May 4). Source needed: the Treasury or Supervising Architect annual report for fiscal 1918 or 1919.
- **EO 2947** (1918-08-27). Boston Immigrant Station buildings. Source needed: the Supervising Architect or Commissioner General of Immigration report for fiscal 1919 or 1920.
- **EO 2999** (1918-11-18). Barge Office contracts in New York, suspended "during the present national emergency". Sources needed: the Supervising Architect report for fiscal 1919, and the text of the joint resolution of March 3, 1921 (Pub. Res. 64, 41 Stat. 1359; lead X1-E1, source_pending).

The 1921 resolution is needed for every March 4, 1917 proviso order (EO 2855, 2947 and 2999). Without it, nothing can show whether the "national emergency" authority ended before the work was completed.

## Counterevidence searched (2026-10-28, held sources only, no network)

- Census titles (`jobs/domesday-register/output/REGISTER.csv`) and type rows (`jobs/x1-class-engine/output/TYPES.csv`), by surname and by project.
- The full WPA 1944 numbered list, whitespace-insensitive.
- The full text of every held order under `jobs/*/output/texts`, by name.
- A citation search for "No. 1547" and "No. 4782". The only hit was Proclamation No. 1547 of 1919, a different instrument.
- All 2,750 ProQuest scan texts, for Canal eight-hour orders in 1912–1916. The only hits were EO 1547, EO 2514 and EO 4459, and none of them affects EO 1547.
- Every register title containing "Compulsory Retirement" dated after each order.
- The machine USC and eCFR searches, which found 0 hits.
- The OFR catalog, which starts in 1937 and was not relied on alone.

## What would change these outcomes

1. Full signing dates in the ProQuest ingest. This would clear the only batch-check failure.
2. Re-preparing the 14 APP-held orders against the registered `mirror_transcription` fragment. Eight retirement exemptions and EO 6516 would then be ready to submit.
3. Adding EO 6984, 7307, 7475, 7516, 7545 and 7645 as evidence, through a source supplement or new packet. Each extension is then recorded as its own later event.
4. Completion records for the four 1918 projects, plus the text of Pub. Res. 64.
5. A decision on EO 6874's first end under the strike-and-insert ruling.
