# Owner ruling, 2026-11-06: an unchecked official copy does not take away a provisional working text

**Question put to the owner (00:50 ET):** merging Mabillon's #164 registers official printings that still need a page
check. Under the 2026-10-31 ruling, an order with a checked working text (Lachmann) counts its text step as provisional
only when the remaining text blockers are leads (a compiled transcription or an archival replica) or no official source
located. An official find flagged for a page check (`ORIGINAL_FOUND_NEEDS_PAGE_CHECK`) was not on that list, so finding
a probable official copy would have taken the provisional credit away from 17 orders (Gratian's measurement).

**Owner's answer:** "Yes, keep credit": an unchecked official copy is a lead like the others and lets the order keep the
provisional credit.

**What changes:** `jobs/readiness-tracker/tracker.py` adds `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` to
`PROVISIONAL_LEAD_BLOCKERS`. The step is still shown as `provisional`, never as an original; the order keeps its
original-replacement and quotation-recheck obligations; the official copy's page check is still owed and is what turns
the step into an original. Orders with a claim on file are unaffected (the claim's own checks decide). This can only
raise the provisional count; it changes no grade, census entry or certification.
