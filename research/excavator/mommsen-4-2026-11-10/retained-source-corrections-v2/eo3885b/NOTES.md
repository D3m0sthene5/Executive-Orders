# EO:3885B source correction proposal

The one page ProQuest replica at `ProQuest Pre-1937 Orders/PT1-1923-EO-3885-B.pdf` (SHA-256 `857239fad8e0e2930e0920d239544fb4f3b4fe241d5f86696c89ea0cc2741d7d`) was visually read from an in-memory render. `TRANSCRIPTION.txt` is a separate attributed reading of that page. It is not an alteration of the PDF, its text layer, the Pinakes output, or the frozen fragment. The typed paragraph spans two lines at “De- / partments”; the page has underlining and ink interference there, but the words are readable. `[signed]` is editorial notation for the handwritten Charles E. Hughes signature. The lower-right handwritten order number reads 3885-B.

The printed header is Department of State / Washington / August 4, 1923, followed by ORDER. The sole command closes all Executive Departments on Tuesday August 7, 1923 on and after one o'clock, and on Wednesday, Thursday and Friday August 8, 9 and 10. The last named date is inclusive in the sentence; an August 11 own-term endpoint is a proposed legal inference, not a native or independent conclusion. The page shows no express savings sentence or additional operative command. That observation needs a corrected-text source pin and separate legal review before use.

## Route checked

1. `python.exe -I jobs/kean/kean.py search faithful transcription text correction 3885B` returned no earlier work. `jobs/pinakes-proquest-ingest/README.md` documents automatic PDF text-layer/OCR extraction and committed immutable machine output, not a manual override. Targeted search of `jobs/pinakes-proquest-ingest`, `jobs/claim-kit`, `jobs/lachmann`, and relevant owner rulings found no sanctioned manual text override.
2. `pdftotext -layout` reproduced the corrupt text layer. The existing Pinakes text SHA-256 is `2d34fd440e76840ca2aa9e69aa9c8d3c4b18f38a21d505b07355fe2580772bbd`. The current claim-kit dossier `jobs/claim-kit/output/dossiers/EO_3885B.json` binds both `ORIGINAL:EO:3885B` and `CLAUSES:EO:3885B#whole` to that text. A prior decision's `complete_text_confirmed: true` and `savings.source_id: null` are not adopted here.
3. `jobs/photius-replica-check/output/FRAGMENTS.jsonl` carries a final PASS for these PDF bytes with grade `archival_replica_checked` and `acceptable_as_original: false`. This proposal does not change those fields or claim authenticated original status. No restricted image was written or copied to the research output.

## Remaining gates

- Identify and authorize a native route that adds a new, separately attributed, hash-pinned corrected text representation without overwriting Pinakes text or the existing fragment. Rebuild the claim-kit dossier and verify exact source/text fingerprints before any decision sheet or dispatch check.
- Reconfirm source identity, entire text, page and clause inventory against the held page in a fresh native packet. The present dossier's evidence IDs refer to the old OCR. There is **no separate valid bound savings evidence ID** for the corrected text; the prior null savings pin cannot be filled by inference.
- Independently assess first ending, potential earlier changes, savings and residual consequences, and the dated August 11 hypothesis. Run applicable native review and control gates. No claim, original authentication, whole-case review, human certification, or publication follows from this source-only proposal.

Model: gpt-6.1-sol. Wall time, tokens and cash: unknown from available telemetry.
