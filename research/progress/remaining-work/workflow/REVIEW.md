# Apollo workflow tab: integration record

Requested by the owner on 2026-10-30 Eastern: add a spatial map of the existing
named jobs to the existing Apollo dashboard, with namesakes, Wikipedia links,
plain-English explanations, results and iteration history.

Artifact: https://claude.ai/artifact/531KGTebdrgdeUitKhp8du#workflow

Baseline source: `88cef0253ed735b2a6e612770f25f9148641ce93`.
Production readiness generation: `35b9a7585d83529cfe7287fb30094273db8cd449`.
The baseline catalog is `../snapshots/2026-10-30/TOOLS.csv`; current tool totals
overlap and must not be summed. Ready for human review remains distinct from
human certification.

## Independent inventory

Configured gpt-6.1-sol worker performed a bounded read-only inventory; coordinator
retains implementation integration and final review. Exact token/cash usage and
worker-exclusive time were not available. The artifact authoring session uses
the displayed Opus 5.5 High model; no cost-saving claim is made.

- Discovery and identification: Clark, early-order discovery, census candidates
  and completeness. Leads do not automatically admit an identity to the census.
- Sources and custody: Panizzi/source-ladder, Lewis, Pinakes, Federal Register
  acquisition, official-fixity, Cotton, Cassiodorus and source retention.
- Clauses and dossier assembly: clause-drafts, claim-drafts, claim-kit and
  case-bundles. An assembled packet is not an accepted claim.
- Research: later-events/status-history/current-law, X1, family rules, Namier,
  Shepard, Cruden, NORTON and separately labeled historical campaigns.
- Independent review: exact producer and reviewer versions, whole-case review,
  reviewer-quality controls and Valla correction/revalidation context.
- Mechanical verification: claim-checker and readiness-tracker. Human review
  and certification remain a distinct final authority.
- Cross-stage support: Kean, Hamilton, Junto, Llull, Polya, Revere, Capcom and
  the runner. Proposed Watchman/Spare/Quiet must not appear implemented.

Connections checked against job READMEs and claim-kit protocol:

- Valla runs before claim-kit and seals context into packets, READ and view.
  Valla reads canonical claims/reviews, not generated claim-kit output; no cycle.
- Cruden is the producer script at
  `research/excavator/claude-nira-sweep-2026-10-29/cruden.py`, consuming a prepared
  packet and emitting LOOKUPS files. It is not a standalone runner job or an
  independent source verifier.
- NORTON requires reviewed factual answers and separately reviewed clause
  applications. Its FACT evidence cannot supply first ends, originals or savings.
- Namier supplies person-name leads, not proven identities. Shepard supplies
  citation leads, not legal findings. Custody does not change source grades.

Namesakes explicitly confirmed in source: Alexander Cruden (script docstring),
Sir Robert Cotton (custody README), Thomas Kean (Kean README), Cassiodorus,
Sir Lewis Namier and Frank Shepard (respective READMEs). Lamm has no established
namesake in the inspected repository records.

NORTON's naming was recovered separately through Personal Context: the original
project assistant explanation at `2026-10-20T15:02:16Z` names **Margaret Cross
Norton**, emphasizing governmental provenance and departmental/function histories.
The original cited source was the Illinois State Archives biography:
https://www.ilsos.gov/departments/archives/nortonbio.html . The corresponding
Wikipedia page is https://en.wikipedia.org/wiki/Margaret_Cross_Norton . Both were
independently retrieved for this update. A matching Norton legal case is not the
project's namesake. This recovery supersedes the initial repository-only finding
that the name was undocumented.

An independent web retrieval also resolved the nine unique Wikipedia titles
behind eleven nodes that the authoring session could not verify through its
rate-limited API: Domesday Book, Pinakes, Shepard's Citations, Last Spike
(Canadian Pacific Railway), Pullman Strike, Digest (Roman law), Margaret Cross
Norton, Junto (club), and Capsule communicator (Flight controller). These links
were opened successfully; a failed API lookup was not treated as article absence.

## Publication and UI verification

Initial published implementation: `945fa7ec07de23e99b283e8141d9dc23658d8511`.
Fresh independent engineering review held approval for four bounded corrections:
label shared catalog-row statistics at point of display; remove timeless hardcoded
certification zero; correct 15 distinct shorthand source targets; and distinguish
Sinclair's lean review from its cross-family result. The coordinator retrieved the
pinned CROSS_FAMILY_REPORT.md and confirmed 29 upheld, 2 needing research and
0 rejected. The reviewer checked 297 rendered source paths against the Git tree;
6 builder tests and independent offline JSON/CSV reproduction passed.

Live browser tests of the initial publication confirmed the fifth tab, 79 nodes,
NORTON's Wikipedia hover link, Enter to pin full results/history, Cruden search
(1 match), Historical filter (17), and the four original views, including the
Mission rocket and 498 ready / 0 certified. At 390 px there was no horizontal
overflow. Closing a detail left its originating node about 3,949 px above the
viewport; requested return-focus/scroll correction. Temporary viewport override
was reset.

Final source **04ed4cac94b18f41512310959655542e97bf520c** incorporates correction
commit `9fd0079e5b448e426f4abe97d4d85fa1b5a8c29e` and the automated Kean output
commit without discarding either. The independent reviewer approved this exact
head after checking all four corrections and keyboard/connected-node behavior.
All 301 normalized repository paths exist (the author's 302 count retains one
trailing-slash distinction). Independent offline regeneration still reproduces
the JSON and CSV exactly. The author retained 111 passing interaction checks at
1280, 820 and 390 px in `tests/RESULTS.txt`.

Coordinator live readback after republishing confirmed the persistent #workflow
route, shared NEYMAN/NORTON catalog attribution, corrected Sinclair result in the
actual dataset, removal of timeless certification zero, and the unnumbered-order
caption. At 390 px, Close returned the selected Clark box to the viewport with
the hover hidden; subsequent keyboard focus opened a tooltip normally. All four
older views and the Mission rocket still rendered. The Sources panel identifies
the workflow dataset as built from final head 04ed4cac94. Sharing remains private.
Screenshot: `APOLLO_WORKFLOW.jpg`. No browser watcher or production refresh was
scheduled by this integration.

Reviewed SHA-256 values:

- `../dashboard/index.html`: `65b8f82051ef6454b9c35118b0b7504f3a2ece0a625af14390fd8ded96c2c4db`
- `WORKFLOW_NODES.json`: `900e3d7f814463ba203e6ceef6786922b3eacd1bc75c3bf8c86c3ae9502aa773`
- `WORKFLOW_NODES.csv`: `3eb81de672e81682b67bffd5c5008bac3dc478e079a184f9c586bd813424f814`

The review was source/static plus isolated regeneration; the coordinator supplied
live browser verification. It was not an exhaustive historical research audit.
The authoring session displayed Opus 5.5 High and its read-only readers Sonnet 5.5;
the independent engineering reviewer inherited the coordinator's model. Exact
isolated token, cost and labor totals are unavailable. No efficiency claim follows.

No new production jobs, scientific adoption, census admission or certification
are authorized by this UI change. Preserve the seven existing feeds and the other
four dashboard tabs.

Required acceptance checks: route survives reload; stage ordering and return
paths are readable; hover/focus explains a job; click/tap pins details with
history and source links; search and lifecycle filters work; missing namesakes
are not silently invented; existing Steps left, AI effort, Tool map and Mission
views retain their data. The map represents research purpose and information
flow, not an asserted executable dependency graph. Identification must allow
genuinely unnumbered orders. Historical and proposed work must remain visibly
distinct from the latest recorded production evidence.
