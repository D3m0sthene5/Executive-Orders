# Claim kit

A deterministic offline job reads the census, held texts declared by source jobs,
known event pairs, current-law leads and claim drafts once across the whole project.
It emits exact-slice evidence, compact dossiers, blank decision sheets and ranked
families. Nothing chooses or changes legal status. Start with [AGENT_PROTOCOL.md](AGENT_PROTOCOL.md).

`python jobs/claim-kit/kit.py build` runs locally. The shared runner invokes
`job.py`, runs the offline tests, then builds under `OUTPUT_DIR`. It runs after
`claim-drafts`; it never invokes or modifies that job. `needs.txt` brings in the
census, provisional statuses, schema and decision sheets. Outputs never trigger
upstream jobs, so this dependency introduces no cycle.

Outputs: `CLAUSES.jsonl` is the preferred attributed representation per order;
`TEXT_CLAUSES.jsonl` preserves segmentation of every discovered held representation.
`OWN_TERMS.jsonl` preserves findings from every representation. `ACTING_PROVISIONS.jsonl`
is the located named provision for each target/actor pair, and `CHAINS.jsonl` puts
those leads in order. Missing pairs remain in `MISSING_SOURCES.jsonl`. `dossiers/`
and `sheets/` cover all decided orders. `STATUS_LEADS.jsonl` covers every undecided
census identity separately, with no status assignment. `FAMILIES.json` ranks shared
actors, parents, fixed-term patterns and source volumes. Same-actor single-clause
CSV tables have blank review fields; every row still requires judgment.

New jobs plug in with `output/FRAGMENTS*.jsonl`, `SOURCES.jsonl`, or attributed text
records declared inside `data/PROVENANCE.json`. A declaration provides instrument_id,
text_path and source citation/hash/page; paths are relative to the declaration's
folder or repository root. Set grade and acceptable_as_original explicitly.
Unattributed book dumps never become order originals. Richardson and editorial
codifications remain derivative leads. Missing local files, unsafe paths and hash
mismatches are reported. No network request or LFS download occurs inside the kit.

Parser cache keys include code, source/text hashes, identity and date metadata.
The bounded runner cache can resume unchanged evidence; it is not a source custody
certificate. Source text hashes and offsets are verified again in assembly.
`METRICS.json` separates runtime/cache hits from deterministic research outputs.
The existing claim-checker still establishes source custody and identity; the kit
pre-gates cannot replace it. The producer must explicitly approve every legal field,
and a separate reviewer must check the sources before any pilot claim is copied.

Run `python -m unittest discover -s jobs/claim-kit -p 'test_*.py'` for synthetic,
fixture round-trip and integration tests. The committed baseline regressions skip
when their authoritative census/status files are absent in a sparse checkout.
