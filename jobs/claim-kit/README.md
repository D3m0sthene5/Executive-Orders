# Claim kit

A deterministic offline job reads the census, held texts declared by source jobs,
known event pairs, current-law leads and claim drafts once across the whole project.
It emits exact-slice evidence, compact dossiers, blank decision sheets and ranked
families. Nothing chooses or changes legal status. Start with [AGENT_PROTOCOL.md](AGENT_PROTOCOL.md).

Early Federal Register texts with a bare heading and closing `[No. NNNN]` use
the existing `clause-drafts` locator before claim-kit segmentation, own-term and
change-mention extraction. Exact raw-text offsets are retained. These are still
unverified inventories: page furniture, OCR errors and clause boundaries require
source review. Locator cautions appear in the dossier's missing-items list.
The shared locator is pinned in compiler fingerprints and the parser cache key;
recompile outputs after changing either parser.

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

Acting texts of instruments outside the census (public land orders, statutes, agency
Federal Register documents) are declared in SOURCES.jsonl with `role: acting_instrument_text`
and `instrument_ids: [acting instrument, target orders...]`. That binds the text to the
instrument (`PLO:`, `STAT:`, `PL:`, `FRDOC:` ...); it is never an order's own text. Only a
later-event fragment makes a pair. The text enters that target's dossier as `ACTOR_TEXT:`
when a lexical check finds the target's number (`prints_number_lexical: true`); otherwise
the dossier says the number was not found and points at the held text, which may cite the
order by date or in garbled OCR. No `ACT:` record is made for them. Such a record is a NO
basis only when `basis_eligible` (an official printing, the govinfo FR issue scan or
Statutes at Large granule or an official FR page, in which the number was found); a
federalregister.gov rendering stays a lead. An actor text over 50,000 bytes is cited by
exact windows, `ACTOR_TEXT:<actor>@<char_start>`, around located provisions first and then
printed mentions, at most 20,000 bytes per actor. Census actor texts are citable as before.

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
