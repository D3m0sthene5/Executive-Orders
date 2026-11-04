# Valla: diagnose stale review reuse before building another dependency layer

The attachment's numbers are correct at main `600ae3018f71025b3e53dc8538b8f92e6e159b76`: **783 observed shared-rationale references, zero accepted examined dependencies, zero valid components**. These figures do not show an absent or broken dependency engine. The committed index explicitly refuses all five old pilot method reviews and quotation attestations because their pinned `jobs/claim-kit/BATCH.md` changed. The five exact canonical claims and source-text dependencies still agree with their historical records. Existing exact-claim source-audit holds remain unresolved.

`DIAGNOSTIC.json` retains the source/code/claim pins and per-case results. Run from the repository root:

```sh
python3 -I research/progress/maitland/valla-audit/replay.py
```

The script reads pinned Git objects, invokes the existing Valla validators in a temporary tree, and writes only these research diagnostics. It does not run `pilot.py`, launch jobs, write claims, renew review records or alter holds. Pinned Git objects must be locally available or retrievable by the repository's existing promisor remote.

| Existing validator exercise | Method reviews accepted | Quotations reusable |
|---|---:|---:|
| Pinned main dependencies | 0/5 | 0/5 |
| Temporary control with exact historical BATCH bytes | 5/5 | 5/5 |

Historical BATCH SHA-256 is `867ba9f849e18b4faf031eca60841ddad5e42c02b0f9279e93d5158a7f73efb1`; current pinned-main SHA-256 is `f1939a0ed0db6a92f4d96e5adc2f5c2d09367bc13700b314a541ffb0da37c363`. The temporary control demonstrates the refusal's cause; it is **not a renewed review**. Neither arm establishes a replacement first-end date or complete lifecycle approval. Timings, tokens and total savings are not measured.

## One exact previously examined premise

The selected canonical EO 13792 claim is line 3 of `research/readiness/claims/claude-lambertini-s02-2026-10-20.jsonl`, canonical hash `06a353a3f28f924ffbac24dbec9f56afd938f5d8de5ad580c5af4498fa859d42`. Its `/research_rationale` characters 548–589 say:

> No clause's first end needs a report date

The exact JSON-string span hash is `60bc4c84754f5ed7212d9e30da93e8d0a099f81d14b5e238936da011078c1ae6`. Old record `VALLA-M-EO_13792` independently examined that assertion as support for `/operative_clauses/12/first_end`, section 2(e)'s final-report command. The old record supports a revalidation request, not a replacement date. Existing Valla closure reaches `/whole_order_end` from that first-end pointer. It does not prove that the whole-order date must change.

`EO_13792_EVIDENCE.json` retains the exact rationale, affected clause, old first-end and whole-order assertions, original extracted text, and old scoped records. The underlying source text has SHA-256 `d7c0075c6aa9502744cad2d247ff2b86a2b1f3b61a16ec0eba80c90943238a68`; the final-report quotation is original UTF-8 characters 5855–6520. The old component approval concerns quotation fidelity only, and is currently refused after BATCH drift.

The bounded five-case trace is:

| Claim | Previously examined first-end pointer | Existing dependent conclusion |
|---|---|---|
| EO 13792 | `/operative_clauses/12/first_end` | `/whole_order_end` |
| EO 13101 | `/operative_clauses/40/first_end` | `/whole_order_end` |
| EO 13148 | `/operative_clauses/28/first_end` | `/whole_order_end` |
| EO 13783 | `/operative_clauses/9/first_end` | `/whole_order_end` |
| EO 13807 | `/operative_clauses/21/first_end` | `/whole_order_end` |

This is an exact review trace, not a corpus-wide dependency finding from 783 references. Shared package references and lexical matches never establish derivation or legal dependence.

## Real next correction work

The existing second EO 13792 hold already points to a more informative source audit: `research/excavator/astra-portfolio-repair-2026-10-20/lambertini-review/EO_13792.audit.v1.json`. It retains a DOI final report and official January 30, 2018 testimony. The earlier audit reports that the memorandum identifies itself as the section 2(e) final report and that the testimony says the Secretary submitted two reports. The earlier audit does not establish exact transmittal dates, required routing or the legal first cessation. This audit has not independently re-examined those primary artifacts.

`REVIEW_INPUTS.json` hands their exact retained raw/text paths and hashes, original text, exact claim and scope questions to a fresh source examiner. A useful new review must determine what those bytes establish, distinguish sections 2(d) and 2(e), and retain uncertainty about exact performance and continuing obligations. Replacing 2021 with a deadline or a testimony date would be unsupported. A report's completion cannot silently extinguish policy, review, consultation or other independent commands. Section 2(d) is a concrete additional candidate, but the existing Valla record does not approve a dependency for it: it requires separate source-based examination.

The legitimate route is already implemented: separately held exact source-backed method review → ordinary `eo-method-dependency-review/v1` record → Valla validator and targeted closure → existing replacement-proposal packet → source-backed correction and independent whole-case review → ordinary completion/owner routing. A new source review can request revalidation while the corrected lifecycle remains blocked. Old approvals must not simply receive current hashes.

## Small operational improvement

`build()` exposed refusal reasons, but `attach()` discarded `refused_method_reviews`. An ordinary correction packet could therefore have no accepted dependencies without explaining that five prior examinations were refused after a rule change. The small repair carries those already computed, request-scoped diagnostics into packet context and adds `instrument_id` to each refusal so ordinary per-order views can display it. Acceptance, closure, holds, approvals and freshness remain controlling. A new regression verifies refusal visibility, zero automatic approval, no invalidated conclusions from stale review, and unchanged context when an unrelated review is added. All 37 Valla tests pass.

No new dependency framework, automatic source-review renewal or weaker rule-pin check is justified by this evidence. Narrower future method pins might reduce harmless protocol churn, but choosing them requires an independently examined method contract, not replacing an old whole-file hash opportunistically. End-to-end token or correction-time saving remains unproved.

## Fresh source examination and existing-route replay

A separate source examiner subsequently read the exact original extracted text, DOI final-report PDF and testimony, visually inspected final-report pages 1 and 3, and wrote **new** scoped method records for sections 2(d) and 2(e). The source examination is `research/progress/maitland/valla-fresh-review/REVIEW.json`, SHA-256 `2d3d41e59d2b371c96200cd2cac047069fb3decbd538861fe54d25b3a4c3e312`; its separate method ledger is `METHOD_REVIEWS.jsonl`, SHA-256 `70aac20cd1db8c6f995a6acfa8a9347994aa58eb979198d00702451c139e22bf`. These are new source-based revalidation requests, not renewed historical records or corrected first-end dates. The reviewer disclosed incidental exposure to unrelated agents' completion summaries after completing the source verdict; the exact disclosure is preserved in the review and replay receipt. Same-family AI source examination is not human certification or different-family review.

```sh
python3 -I research/progress/maitland/valla-audit/fresh_replay.py
```

`fresh_replay.py` verifies those exact hashes and every explicit source/rule dependency, copies them into a disposable tree, and creates temporary queue copies whose `review_ref` pins the separately held ledger. Existing `confirmed_findings()` accepts exactly two new records. Existing `build()` marks exactly `/operative_clauses/11/first_end`, `/operative_clauses/12/first_end` and the derived `/whole_order_end` for revalidation. The older method review remains refused after BATCH drift. Unrelated conclusion pointers receive no automatic invalidation, all frozen sibling claims remain identical, and claims and holds receive no writes.

The replay changes every unique pinned source, rule or examination file and the held method ledger one at a time. Each mutation refuses both new records; restoring original bytes restores the exact index fingerprint. `FRESH_REPLAY.json` retains these probes, exact input pins, refusal reasons, source-review exposure disclosure and unchanged-claim/hold evidence. `FRESH_QUEUE_PROPOSALS.jsonl` holds the research-only queue copies; none are installed in `research/readiness/method_reviews/`.

The source examination supports actual submission of the separately identified reports by January 30, 2018. It does not authenticate the missing raw-original PDF, establish exact receipt/routing or bind the revised final-report PDF to the transmitted version, choose a replacement first end, or establish whole-order cessation.

The first replay recorded an input-availability block: the native EO13792 dossier and claim-kit output summary were absent. After the coordinator materialized the exact existing dossier, INDEX/SUMMARY, source texts and reservation lock, the same replay exercised the existing `correction()` API in its disposable tree and successfully reloaded the resulting native packet. `correction-packet-v1/` retains PACKET, READ, decision/clause sheets and the ordinary preparation receipt. Every decision approval remains false and its outcome unresolved; the packet routes the existing claim as an owner-reviewable replacement proposal and requires independent whole-case review. No complete correction claim or ordinary-completion success is invented.

The selected dossier's canonical fingerprint matches its exact INDEX entry and all referenced source-text hashes were checked. The compiled SUMMARY remains unchanged. Its compiler map differs from current `act_overrides.py`, `excavate.py` and `inputs.py`; `FRESH_REPLAY.json` records each old/current hash. The decided-dossier preparation API accepts and seals the exact selected existing dossier rather than recompiling it. This establishes a bounded research packet under the current API, not freshness of the full production generation or the full repository's prior-research context. Preparing a production packet requires a new version against its actual current inputs; these temporary queue proposals are not installed there.

The native packet refuses a changed original source with `changed held source` and a changed held method ledger with `changed Valla review context; prepare a new version`. Restoring both files permits the original packet to reload unchanged. The source-review output and reservation/claim/hold inputs remain byte-identical in the working repository. The packet is a usable source/revalidation checkpoint with explicit remaining work, not an adopted legal answer.
