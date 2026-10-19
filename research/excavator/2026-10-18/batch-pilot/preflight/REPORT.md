# Frozen fifty-order preflight

Prepared 2026-10-18 for the corpus-excavator coordinator. This is research preparation, with no new legal finding, claim, status, reservation, queue entry or human certification.

The denominator is the **same fifty evaluated orders**: **12 frozen AI acceptances and 38 unable outcomes**. The preliminary CANDIDATES file has 56 entries and is not the denominator. Every blocked case and its final verbatim reasons remain in `ORDERS.json`; no blocked case was removed to improve the sample.

## Pins and reproduction

- Frozen branch: `957c4a40a3967b174b8d0c7a97a920ba9927a176`.
- Actual producer output freeze: `717e0a4bfad161532e54755f9cf2cb97964ac03d`; code input `3ca7abebf15f6c049b21726b2eea0fbe97032cc7`.
- Current checkout at collection: `c9993c7058d6667d3278384f389a5f0a55857ec4`; local origin/main `43f415dd440d4e7236b625b1b6edebbc0916d436`. The coordinator separately checked live main. This agent's initial direct DNS check failed; connector reads and subsequently approved read-only Git object acquisition succeeded.
- Collection: **13:13:39–13:13:46 UTC**. The current claim-kit job reports successful output from `f3ee24abb019743ec7c603a8eeaa1864ca5214a8`; it precedes the coordinator's pending source-boundary/dedup rebuild. All **50 current fingerprints differ** from the frozen producer dossiers. No frozen decision can be silently reused against them.

`PINS.json` identifies 238 input byte hashes and the saved metadata snapshot hash. Copied pilot inputs match their exact frozen Git blobs. The twelve accepted full dossiers are preserved in the pilot; the 38 unable full dossiers were read from **717e**, because Sol branch HEAD contains later generated dossiers. For example, EO10222's frozen fingerprint is `d1446cc...`, while Sol HEAD has `1c169a...`. Substituting branch HEAD would misidentify the producer's evidence.

All twelve accepted manifest fingerprints and 49/50 current producer-sheet fingerprints match the frozen full dossier. The sole sheet exception is EO11860: its unapproved initial unable sheet was deliberately retained; the full recheck/freeze record preserves that history and supplies the final inability reason. This is recorded, not silently rebased.

Run from the repository root:

```powershell
python research/excavator/2026-10-18/batch-pilot/preflight/preflight.py --verify
```

This regenerates the order/task data solely from `INPUT_SNAPSHOT.json`, checks its pin, preserves fifty/12/38, checks dependency references and the two difficult full snapshots, and prohibits navigation search artifacts being classed as original law witnesses. `--collect` performs a new read-only collection and may need exact frozen Git blobs. Keep the present snapshot if comparing this particular run. Collection detects concurrent input changes; none occurred in this snapshot. `VERIFICATION.json` records deterministic regeneration checks.

## What the preflight establishes

| Gate for the same fifty | Orders |
|---|---:|
| AI-accepted replicas whose target original bytes are locally held | 5 |
| AI-accepted replicas requiring target original-byte recovery | 7 |
| Unable: attributed current law is the immediate gate | 6 |
| Unable: complete image/extent and case judgment are the immediate gate | 2 |
| Unable: continuity interpretation control | 1 |
| Unable: fact or chain research before replay | 29 |

These are preparation gates, not predictions of successful adjudication. Gates are exclusive for navigation; the detailed gaps and task dependencies overlap.

Exact target original bytes were located for **23/50**, but target **and family actor** exact originals for only **3/50**: EO13075, EO13080 and EO13168, all still blocked in the EO13225 family. This demonstrates why custody and legal completion need separate fields. Their actual submission/designation facts and independent-command scope remain unestablished. Every inspected cache miss means only absence from the enumerated local paths; indexed remote runner cache custody was not inspected.

**Held, loaded, and unestablished are separate states.** Full recheck dossiers add actor contexts for 23 cases. Of 32 historical context request memberships, 26 are loaded in the actual frozen full dossiers; the remaining six have held local text but no corresponding frozen actor context: EO10647 for EO11355, EO10480/10773 for EO12521 and EO12649, and EO14008 for EO12898. These are four distinct text sources across four cases, so checking/loading held text comes before acquiring it again. Their legal relevance and completeness still require review. They are not six new authorities proven absent.

**Current law:** the frozen summary's 17 `held_current_law_text` labels are mechanical overlapping navigation labels. Eleven cases have identifiable material current-law requests, deduplicating to **106 citation/context tasks**. EO12592 has an additional unspecified USC/eCFR assertion although both inspected dossiers have no current-law leads: preserve it as an explicit reconciliation task, without inventing a citation. The remaining five labels concern historical scope, general search currency or a conditional predicate and do not justify fabricating current-law acquisition targets.

**Fact and interpretation gaps:** 24 cases receive specific submission, receipt, implementation, activation or completion research tasks. These are scoped questions, not proof that the fact is absent from the wider corpus or that a new download will resolve it. Five other cases with the summary's broad actual-event label instead need particular chain, statutory, transfer-schedule or continuity analysis. EO12852's June 29 expiry / June 30 extension boundary is a held-evidence legal interpretation control; a later formal revocation does not settle it mechanically.

## Shared work before another production batch

`TASKS.json` contains **184 typed task nodes**, not 184 downloads: 106 attributed legal-text/context tasks; 21 shared original law-witness custody tasks; one authoritative-witness discovery; 24 factual questions; ten image/extent tasks; nine chain/scope tasks; twelve accepted-replay custody prerequisites; and one unspecified-current-law reconciliation. Dependencies and target memberships deduplicate reuse. All remain proposals and were not appended to FETCH_QUEUE.

Recommended sequence:

1. Recover exact cached originals once per witness, starting with the USC all-title archive shared by seven cases and the eCFR titles shared across cases. The required attributed slices and cutoff assessment follow acquisition. The USC release stops October 9, so the October 10–14 currency gap remains explicit.
2. Do not turn eCFR search-result JSON into law evidence. The 41 CFR 102-76.55 pointer requires an authoritative witness discovery task shared by EO13101/13123; two search-receipt sources are retained as navigation only. A second 1 CFR 601.22 pointer already shares the existing title-1 witness dependency.
3. Inspect EO12692's complete official pages once for its six targets, and EO12919's once for five targets. Close source identity/extent concerns before applying any family provision. Additional source/extent checks cover EO11375, 12607, 12668, 12696, 12751, 13075, 13080 and 13168. Download success alone does not remove page-review flags.
4. Reuse held context for EO10647, 10480, 10773 and 14008 before a new request. Preserve the final recheck's already-resolved actor-context history. The older **93 SOURCES_NEEDED records** remain in the input snapshot as history; they do not all remain active acquisition requests.
5. Batch archival discovery for report-based bodies by family/provider, while preserving each commission's own event evidence and trigger. An outer date, report deadline, or 'within 60 days' window never supplies an actual submission/termination day. Do not merge different bodies' factual questions merely because they share a revoker.

The EO13350 pair EO12722/12724 is especially economical once full 31 CFR 576.201 and the Iraq Sanctions note to 50 USC 1701 are held and attributed: both use the same two witnesses and legal-text tasks. This is a promising preparation family, not a predicted two-claim gain. EO13423's five targets also share law-witness work; EO13134 separately needs P.L.106-224 section 306 and transition provisions.

## Matched six-case experiment

The coordinator's proposed six are sensible for a **controlled replay**: EO12720/12813 (actor12869), EO12734/12817 (actor13350), plus difficult controls EO12696 and EO12722. All fifty remain in the production denominator.

The first four are **Sol-owned accepted replicas**, usable only as experiment proposals until ownership is coordinated. Their full evidence texts are held, but their exact target original PDF bytes are absent from the inspected current custody paths. EO13350's actor PDF is held in `research/stage21/original_sources/EO_13350.pdf`; EO12869's actor PDF is indexed without located local exact bytes. They are text-ready replay candidates, not six source-complete new claims.

EO12696 remains a complete-original/inventory control: the selected original stops after section 3(c), and section 4(b) appears only in a differently hashed, page-check-flagged source. EO12722 remains a law/residual control: complete attributed 31 CFR 576.201 and the Iraq Sanctions note are unheld in the frozen evidence map. Both exact **717e** full dossiers are saved under `snapshots/`, with byte and fingerprint pins.

`EVIDENCE_PACKET_MANIFEST.json` lists the exact six evidence-only dossier files for both arms. The coordinator-only `MATCHED_COHORT.json` contains historical outcomes and experiment controls. **Do not supply prior sheets, claims, reviews, this report, ORDERS.json or INPUT_SNAPSHOT.json to a blinded arm.** Both arms must receive the same six full evidence dossiers, source access, legal tasks and inability option; only the packaging/reuse treatment should vary. Count preparation, acquisition, revisions, failed checks and independent review as separate cost components. Preserve every rejection and inability. Six selected replicas do not establish project-wide savings or causal preflight recall.

Additional difficult controls worth retaining outside that matched six are EO12852 (continuity), EO13080 (independent Presidential designation command), EO13328 (report-use and Presidential commands surviving a body's termination), and EO11246 (delayed changes, OMB schedules, contracts and extensive current law).

## Ownership and limits

No matching local claim line was found in the 13 inspected claim files. The local reservation file was absent. Neither observation releases work owned on another branch: FREEZE_MANIFEST binds all twelve Sol acceptances, and the historical producer evaluations own the experiment history. Coordinate with the root before claim replacement, duplicate production or publication. No claim, source, status, census, lock, FETCH_QUEUE or HANDOFF file was edited by this subtask; the proposed handoff text is included separately inside this assigned folder.

This is a retrospective preflight. It does **not** establish how many inability outcomes could have been predicted cheaply before reading sources, whether facts genuinely do not exist elsewhere, or how much agent/legal-review work source loading saves. Surprise conflicts, incomplete originals, scope distinctions and changed search coverage remain possible. The full reasons and unknowns are preserved so these outcomes stay measurable. `TELEMETRY.json` records observed own-rollout counters and their cutoff; billing and complete active labor are unavailable.
