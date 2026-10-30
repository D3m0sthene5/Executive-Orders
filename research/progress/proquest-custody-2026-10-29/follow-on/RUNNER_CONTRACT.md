# Bounded ProQuest restoration contract for Sol

This follow-on leaves PR105 independently adoptable. Sol owns `job.py`, runner
checkout, dependency declarations and combined integration; no such file was
edited here. Coordination was posted to PR103, comment 6511840662. The frozen
GitHub implementation commit is supplied in the publication comment, avoiding a
self-referential commit hash in this document.

## Call and inputs

```python
materialize(repo, out_dir, ids=None, *, max_artifacts=8,
            max_total_bytes=24_000_000, resume=None)
```

`ids=None` selects current effective claims. An explicit iterable of instrument
IDs narrows selection; `ids=DEFAULT_IDS` preserves the original three-case
experiment. Selection uses the ordinary checker's source-field vocabulary and
last valid object in filename/physical-line order. It requires an exact cited
SHA-256, an instrument-specific Pinakes original-representation association,
the existing provisional grade and false original flag, an allowed PDF path,
and a regular blob at the pinned `HEAD` tree. Conflicting identities, paths or
hashes are refused. Shared exact PDFs are read once and retain all claim refs.

Inputs that must remain declared/available:

- `research/readiness/claims/*.jsonl`, each bounded at 32 MB and streamed;
- `jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl`;
- `jobs/claim-checker/checker.py` and its existing import dependencies;
- Git tree/object access at the checkout's pinned HEAD, including permission to
  lazily fetch individual retained promisor objects;
- the ordinary checker's existing Pinakes text, source-index and readiness
  inputs. This helper does not restore text or replace those declarations.

Do not add the entire root PDF collection to sparse checkout. No new provider,
website acquisition, LFS download, or release extraction is part of this call.
The two allowed roots remain `ProQuest Pre-1937 Orders/` and
`research/pre-1937-sources/ProQuest Pre-1937 Orders/`.

## Output and explicit resumption

Each invocation writes `out_dir/PROQUEST_MATERIALIZATION.json`, schema
`eo-proquest-materialization/2`. Existing `receipts` and `errors` fields remain;
receipts now include exact effective claim keys, canonical claim hashes and
reference fields. New fields include deduplicated `artifacts`, `input_sha256`,
`selection_sha256`, `bytes_read`, `artifacts_attempted`, `bounds`, and
`next_cursor`. Legal effect remains none.

Defaults are at most eight attempted distinct artifacts, 8,000,000 bytes per
artifact and 24,000,000 bytes read per invocation. Callers may lower the batch
and invocation bounds, never raise them. Metadata has per-file bounds, no
corpus-wide aggregate cutoff. Oversized artifacts are holds, not permission to
increase limits. A partial-clone fetch retrieves a retained Git object, not a
new source; Git transport/pack bytes are not measured by the payload budget.

Pass the exact previous `next_cursor` to another bounded invocation, under the
same HEAD and input fingerprints, to continue. Use a distinct output directory
per batch so prior receipts remain available. The prefix is explicitly
`before_cursor_not_reverified`, never a fresh success. Changed selection or an
invalid cursor fails before any restoration. `next_cursor=null` means selection
was traversed, not that all artifacts succeeded. Inspect refusal states/errors.

For example, the native replay uses `max_artifacts=2` and three invocations with
their returned cursors. It reads 112,209 / 108,738 / 50,995 bytes and completes
five artifacts as 2 / 2 / 1. It preserves three already-held copies and restores
the two additional exact PDFs. Tests also cover byte-budget deferral/resumption,
shared PDFs, stale cursors, wrong hashes, missing blobs and LFS pointers.

**Integration limit:** current `job.py` invokes the helper once without a
cursor. All five demonstrated cases fit that call. A larger future selection
will explicitly defer its tail; repeated default calls alone will not advance
it. Sol must expose or consume the cursor in bounded follow-up invocations and
retain the batch receipts. The job's old three-case docstring also needs its
owner's update. This follow-on does not claim automatic scheduled resumption.

Always run the ordinary checker after restoration. Let the normal tracker use
fresh ordinary checker receipts under its existing gates. Neither restoration
success, selection completion nor a cursor establishes quotation accuracy,
source authenticity, legal applicability, page confirmation, review or readiness.

## Integration acceptance

Expected frozen-input result: EO254/2171/4354 remain ready; EO4782 becomes ready;
EO1547's custody passes but its working-text mismatch remains. All five remain
transcription-dependent, require original replacement and quotation recheck,
and gain no certification. Reproduce native outputs before publishing any global
count. Do not add the isolated one-case gain to the published dashboard total.
