# Discovery / source identity / text completeness trace

**Scope:** bounded code-and-record investigation of discovery, identity binding, and text/inventory completeness on baseline `f9c6d806ad059dcad7875ab3708715f20ea386df`, branch `lifecycle-assurance-2026-10-29`. Only this report, its admission trace, and its reproduction script were added; no code, census, codebook, claims, or production records were changed. Reproduction code is in `repro.py`.

**Worker:** gpt-6-luna (coordinator supplied actual configured model). Token telemetry unavailable. The 37-second marker interval from 2026-10-29 23:59:42 to 2026-10-30 00:00:19 UTC covers only the final reproduction segment; total session labor was not measured. No test suite was run; the deterministic script invokes the actual selector, checker, and preflight functions on minimal fixtures.

## Current governing requirements

- `research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md`: evidence decides; identity/status cannot be supplied by disclosure, and unresolved whether-an-event-occurred remains open.
- `research/readiness/owner_rulings/2026-10-21-transcription-as-text.md` and `jobs/claim-kit/AGENT_PROTOCOL.md` (working-text section): a labeled transcription can be used provisionally; originals remain the goal. Producer must confirm representation identity and completeness after inspection; reviewers must substantiate. The checker still requires custody and exact quotes; replacing a source reopens the claim.
- `jobs/claim-kit/AGENT_PROTOCOL.md` and `jobs/claim-kit/evidence_preflight.py`: source/citation pointers and machine segmentation are leads. Full inventory confirmation and independent source review remain necessary.

## Two strongest residual hypotheses

### 1. A misattributed source can pass the selector, dossier preflight, and checker identity row

**Reproduction through actual code:** `repro.py` supplies a candidate body headed `EXECUTIVE ORDER 8119` while declaring it as EO:8123. `build.identity_conflict('EO:8123', candidate, body)` returns `None`. `evidence_preflight.inspect()` returns no identity task for that body, since its explicit marker check recognizes only `Instrument: EO:<id>`; it is not an `Executive Order <id>` heading check. The checker’s `check_identity()` returns `pass / recorded_for_this_order` when the source registry associates the candidate SHA with EO:8123, before reading source text. Exact rerun stdout is saved in `REPRO_OUTPUT.txt`:

```text
selector_explicit_wrong_order= None
checker_identity_with_misattributed_registry= [('pass', 'recorded_for_this_order')]
preflight_explicit_wrong_order= []
```

**Exact mechanisms:** `jobs/claim-kit/build.py:133-157` defines `identity_conflict`; it rejects empty/placeholder/date-only texts, statute/public-law/Code printings, and unverified FR leads that fail to print/name the target. It does not reject a candidate whose printed EO heading names a different EO when it is marked as an acceptable original. Selection then segments, calls this contradiction-only check, and accepts a no-refusal result at `jobs/claim-kit/build.py:331-365`. `jobs/claim-kit/evidence_preflight.py:94-106` checks only an `Instrument: EO:...` marker and multiple unnumbered headings. `jobs/claim-checker/checker.py:795-808` trusts source-custody association when the hash record names the target; it returns before scanning body text.

**What this proves:** current machine checks do not independently establish that a source-file attribution is correct. If a custody/index record maps the wrong single-order artifact to target X, the declaration can make identity circular: it says target X, which is then accepted as evidence it belongs to X. The fixture assumes that bad mapping; I did not find or establish a current production record with it.

**Scope caution:** do not reject a source merely because it mentions or prints a different EO number somewhere. A multi-order volume, amendment, citation, or page containing adjacent instruments may legitimately include several identities. The reproduction is specifically an order-specific candidate body headed with a different order number despite being declared for EO:8123. Identity needs to be resolved at the cited document/page boundary; no blanket text-number rejection is proposed.

**Historical source:** the historical source-boundary audit report in the baseline Git object (`git show HEAD:research/excavator/source-boundary-audit-2026-10-26/REPORT.md`; not hydrated in the sparse working tree) documents prior real misbindings: EO8123 received EO8119 text, EO8126 EO8124 text, and EO8992 EO8991 text. It records an extent repair and eight additional page-image-confirmed sampled wrong-document inventories. This establishes the failure class historically, not that the current patched selector reproduces those cases. Current `jobs/claim-kit/test_legacy_extent.py` has real-source regression coverage for those four orders when source files are hydrated; its text states completeness remains unverified.

**Controls / unresolved:** current `build.py` source-tier/law-printing checks, dossier preflight, claim-checker custody/identity rows, and required independent source examination reduce risk. But the checks are not sufficient if declarations are wrong in a format not parsed by preflight. Strong control is a reviewer’s actual source-page comparison against the target order number/date/title and page boundaries, with any discrepancy treated as a source-mapping correction and re-reviewed. No source-grade or human approval is established here.

### 2. “Complete inventory” gates do not mechanically detect omitted unnumbered clauses

**Reproduction through actual code:** `repro.py` gives `evidence_preflight.inspect()` a body containing a covered numbered Section 1 and a second unnumbered command (“The Secretary shall separately issue instructions.”) whose text is excluded from the clause range. The function returns no tasks:

```text
preflight_omitted_unnumbered_command_tasks= []
```

`jobs/claim-kit/evidence_preflight.py:107-116` checks only numbered section headings within selected-original extent and proposed inventory ranges. Its alternate-text check at `:117-134` detects additional numbered sections in a second transcription of the same source bytes, not missing prose/paragraphs in an unnumbered section. The actual confirmation gate at `jobs/claim-kit/working_text.py:183-195, 235-239` rejects metadata-known incomplete text, verifies exact text bytes/quote spans/full-file span for the original representation, and requires explicit identity/completeness/page confirmations. Those confirmations remain a human/producer attestation; they do not prove completeness by themselves.

**Historical source:** the same baseline `source-boundary-audit-2026-10-26/REPORT.md` documents a prior EO8083 case where an old preamble-skip rule removed the retirement-extension command before a wrapped `(d)` reference. The current parser has an explicit regression in `jobs/claim-kit/test_legacy_extent.py:29-42` preserving that opening entitlement, and a four-order frozen-source regression at `:50-59`. Historical audit also leaves an EO8220 interposed EO8219 footnote and EO8729 contents/publication text across a page break explicitly unresolved; these are source-layout review issues, not proven remaining parser failures.

**What this proves:** passing the machine preflight is only “no known mechanical gap” and can miss an unnumbered command omission. It does not establish an actual current claim omission. A completeness assertion requires a source-page comparison, operative-text inventory, and independent reviewer check; OCR/text hashes alone cannot establish that the extracted text layer contains every printed line.

**Controls / unresolved:** current corrected extent locator, exact-span checks, segmenter warnings, known `complete_text=False` refusal, page-check debt, working-text declaration, dossier preflight and separate independent-review gates. The remaining gap is intrinsic to semantic inventory confirmation: it must be explicit that `preflight` is diagnostic and a clean result is not proof of completeness. `jobs/claim-kit/batch.py:201-209` labels it “no_known_mechanical_gap,” consistent with that limit.

## Stop boundary

These are the two strongest bounded hypotheses. No production claims, identities, source grades, legal conclusions, census, status, codebooks, or readiness totals were changed or inferred. No implementation change is proposed; the findings describe the limits of current machine checks, with page-level source and completeness review remaining under the existing protocol.

Kean keyword searches performed separately for `source identity`, `text completeness`, `discovery admission`, `misbound source`, `omitted clauses`, and `wrong identity`; the register had no earlier direct findings for the last three terms. I did not change the Kean register because the assignment restricted writes to this discovery folder; coordinator may register these findings and add the report pointer.

## Census / admission transition

The separate transition trace is in [`ADMISSION_TRACE.md`](ADMISSION_TRACE.md). In brief: discovery outputs are candidates/leads; the early candidate job sets `census_membership=NOT_ADMITTED`, keeps legal inclusion on `HOLD`, emits `newly_admitted_EOs=0`, and does not write the identity projection. The operational denominator is the 14,972 included rows in `IDENTITY_LAYER_PROJECTION_14972.csv`; claim-kit and related consumers accept only exact IDs present there. A candidate entering that universe therefore requires a separately reviewed, explicit change to the projection. The candidate job documents required review dimensions (physical content, issuer capacity, duplicates, legal inclusion, chronology) and prohibits date-only identity merges; its output is not an admission record.
