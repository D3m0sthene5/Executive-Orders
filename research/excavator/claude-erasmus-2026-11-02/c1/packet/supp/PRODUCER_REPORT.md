# Producer report, Erasmus batch c1 (Claude, Sonnet 5.5)

Start 2026-11-02T03:51:29Z; end 2026-11-02T04:01:11Z (the end time is the time of the final lint; this report was written just after).
Final applied directory: `research/excavator/claude-erasmus-2026-11-02/c1/packet/supp/applied-v1` (no second version needed).

## Outcome

All 17 orders submitted, none blocked. batch-check: 17 members, 17 strict pass, 0 fail, actual checker 17/17 gate passed, 0 actionable failures, Geddes 0 flags and 0 coverage gaps. `GEDDES_RESOLUTIONS.json` is written with an empty resolutions list because there was nothing to resolve. Every order keeps the first end at 1935-06-14 by `SUPPLEMENT:SJRES113`, with the Schechter validity note and savings as accrued effects. The prior claims were read from the n03, n08 and n09 Apollo sheets and the prior-claim text in each Geddes view, as drafts only.

## Per order: outcome, brief defects, and what changed

Eleven orders (6293, 6310, 6331E, 6358, 6377, 6386, 6389, 6392, 6401, 6503, 6531) carried the same defect: the independent-command check quoted "Approval recommended: Hugh S. Johnson, Administrator". The held text has the words "Approval recommended:" followed by the name and title on separate lines, so the one-line quote was not verbatim. Confirmed and fixed for all eleven by replacing it with an unquoted description of the signature-block recommendation line.

- EO 6293: also corrected the EO 6529 sentence (dated December 23, 1933, quote now "made a part of said Code", which is verbatim in EO 6529) and added that no source-backed event record exists for it.
- EO 6331E: reworded the EO 6204-B sentence to match its text (approves certain provisions subject to revision after a hearing set for July 25, 1933). Suffix kept.
- EO 6310: kept the note on the transcription "Franklin 1). Roosevelt".
- EO 6503: kept the condition on price-list inspection as code-dependent with no term of its own.
- EO 6487B, 6811, 6945, 6954, 7000 (brief defect: attributed "approval recommended" absent). Confirmed; none of these texts has a recommendation line. The check now says the order ends with the signature and date line. Other template carry-overs found and fixed:
  - "is a approval" corrected to "an approval" in the rationale and clause reason.
  - EO 6945, 6954 and 7000 recited an "application"; these texts recite only the Federal Alcohol Control Administration's submission and the hearing notice. Scope text rewritten, and it now says the single clause spans the whole short order including both recitals.
  - EO 6487B, 6945 and 6954: the claim that every later order "modifies the previous approval to include an approval of the code in its entirety as amended" was false for EO 6685 (it orders the code amended and modifies the December 9, 1933 order accordingly). Each later order is now described by its own operative sentence.
  - EO 6811 and 7000: a name search on "Distilled Spirits" also returns the separate Rectifying code's orders; this is now stated.
  - Quotation punctuation: clause reasons now end the quoted operative sentence with its period inside the quote, as held.
  - EO 6954: the packet carries a lead "PLO:206". It is a BLM index line (February 3, 1944, Florida) listing a revocation of "EO No. 6954". The subject does not match and the date follows the June 14, 1935 repeal, so it cannot be a first end. Recorded in earlier_end_check.
  - The EO 6487B, 6811 and 6539A inventory corrections (spans 1341-1639, 1405-1916, 1402-1676) were re-sliced against the held text and are correct.
- EO 6539A (brief defect: EO 6900 and EO 7020 named as later actors without a later_events entry). Confirmed as the Geddes flag on the clause reason. No source-backed later event for these orders is available in the packet: only NORTON FACT records can be selected, and the dossier holds none. I removed both numbers from the clause reason and, in earlier_end_check, say plainly that they are amendments and later events that are not entered in later_events for lack of a source. Unresolved in the strict sense: the instrument naming remains in the member check, not in the clause reason. Also removed unverifiable items from the old rationale (the Cotton custody claim, EO 7075/7252 padding, "dossier chain has no located change provision" and the Schechter quotation with PDF double spaces). Verified and kept EO 6829 (quote about reserving approval power, plus its second paragraph on orders of general terms), EO 6723 (May 26, 1934 service-trades suspension, which reaches only designated trades) and the "Twine Industry" false hits of a "wine industry" search.

Brief defects disputed: none. Could not resolve beyond the above: the later_events source gap for the amendment orders (6487B, 6539A, 6811, 6945, 6954, 7000, and EO 6529 for 6293).

## What took the time (one line each)

Everything went through a single template check plus a per-order text check. Longer work: 6539A (rebuilding the evidence chain and verifying EO 6829, 6723, 6900, 7020), 6487B/6945/6954 (reading six Rectifying amendment orders and finding the 6685 mismatch and PLO:206 lead), 6811/7000 (reading 6444, 6756-D, 7018 and separating the Rectifying orders). The other eleven needed only the independent-command fix.

## Process notes

- Tool calls: about 45.
- Full-packet files opened beyond the views: none. I did read the prior sheets and claims under claude-apollo-2026-10-31 (n03, n08, n09), which the views point to, plus held order texts in jobs/app-executive-orders and the BLM index line for PLO 206.
- What the view lacked: nothing needed beyond prior claim text and clause spans; the view does not show the clause `reason` field, so I reconstructed sheets from the Apollo sheets.
- Tool defects: none. `geddes.py lint` ran cleanly (rc 0).
- What LOOKUPS.md missed: it cannot distinguish the Rectifying and plain Distilled Spirits codes (name-prefix matches), does not list the EO 6829 delegation or EO 6723 suspension for the wine code, and does not resolve the PLO:206 number lead.
- Where the shared analysis did not fit: it does not say how to record held amendment orders as later events when no FACT source exists; I disclosed them in the member check instead.
- A quote check script (my own, in the scratchpad) confirmed every quoted string in the sheets is found in the own text, a supplement, or a named held text.
