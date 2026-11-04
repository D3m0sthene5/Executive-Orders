# Reviewed occurrence intervals in ordinary partial research

An answer to “did the event occur?” and an answer to “when did this clause end?” are distinct. The October 28 owner ruling accepts a supported interval for an actual occurrence. Stage 19 still requires an exact date for a legal later event or first ending. This route carries the factual observation through an ordinary research proposal without changing that contract.

**Producer and separate factual reviewer.** Use an existing NORTON question, answer and clause application, with the existing independent review of each record. A v1 candidate still requires an exact event date. For an established occurrence with unknown exact day, use `norton-occurrence-evidence/v2` and `event_date: null`. Keep the same entity, question, event kind, identified primary source, held raw and text hashes, page/item, exact quotation and half-open character offsets. Add:

```json
{
  "occurrence_interval": {
    "occurrence": "established",
    "start": "1999-12-01",
    "end": "1999-12-31",
    "start_basis": {"witness": "occurrence_span", "reason": "The witness expressly dates delivery to December of this year."},
    "end_basis": {"witness": "occurrence_span", "reason": "The same witness explicitly puts completed delivery within December."}
  }
}
```

Both dates are inclusive and ordered within the research question's search interval. The dates of the search window alone do not support this record. Each bound needs its own explanation and either the primary occurrence span or another `{source,text,char_start,char_end}` witness with verified raw and text bytes. The witness who gives a bound need not name the exact day of occurrence. A September deadline and no receipt do not establish submission. Keep “unknown whether” as an unresolved question, not this kind of evidence. The validator checks custody, fields, dates and review bindings; only the source examiner can establish that the quotations actually justify the proposition and the bounds.

The answer includes `interval_evidence_sha256`, an exact map from each v2 evidence ID to its canonical NORTON fingerprint; the reviewed application includes `answer_sha256`, the canonical fingerprint of the unannotated answer. Thus changing the bounds, witnesses or answer requires the affected reviews again. A review of an earlier answer, including a previous methodological review, does not attest this new record.

**Ordinary selection.** A prepared dossier lists v2 IDs separately in `factual_interval_ids`. Its evidence entry has role `reviewed_occurrence_interval`, complete interval, a generated `date_qualification` and `legal_effect: unresolved`. Inspect the witnesses. In the existing decisions CSV, submit the member with `publication_kind=partial_research`; the default (blank) still uses the full assembler. Add a `source_notes` record with the interval's evidence ID, the producer's reason and the exact generated `date_qualification`. State a nonempty unresolved material gap. Leave the covered clause's state, end, effective date, confirmation and current predicate unset; retain its source and give a substantive reason. Separately handle other commands, search, savings and original text as usual. An interval cannot supply a dated legal event, legal basis, savings source, scoped cutoff state or whole-order end. Decided cases only; leave undecided orders in their existing separate status/checkpoint route. This is not a general-purpose path for accepting incomplete or malformed sheets.

Ordinary apply emits the original evidence as a proposal and records the specific unresolved gate errors. Ordinary batch-check still reports the complete-claim gate failure. The partial review/manifest must pin the exact proposal, explicitly select partial research and declare the same nonempty gate errors. Completion checks actual mechanical custody, exact selected version and controls, keeps the original errors, and refuses ready credit. Missing bytes, wrong scope, stale reviews, changed bounds and additional unrelated assembly defects are refused. No interval produces an automatic status, certified lifecycle, or exact cessation.

**As of a date.** `factual_events.observations_at(dossier, on, repo=repo)` revalidates frozen membership, the exact current registry, reviews, clause and witnesses. It answers whether this factual event had occurred by the *end of* a civil day: before the lower bound, not yet; from the lower bound up to but excluding the upper bound, unknown whether yet; on or after the upper bound, already occurred. This is retrospective knowledge of a particular event and says nothing about whether its command remained operative. Use MAITLAND's separately reviewed documentary text and legal effects for those questions.

The executable [engineering replay](../../research/progress/sol-evidence-economy/intervals/native_partial_replay.py) exercises the real prepare/apply/check/complete/checker/tracker route in an isolated synthetic fixture. The [held-source candidate](../../research/progress/sol-evidence-economy/intervals/EO13792_FINAL_REPORT_CANDIDATE.json) shows why the date of a testimony is an upper bound, not the date its author delivered the report.
