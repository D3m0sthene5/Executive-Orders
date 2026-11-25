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

When an order has no acceptable original, the kit chooses its text from the provisional working texts that a
producer registered under the owner's 2026-10-21 transcription ruling. A ProQuest replica that passed the
Photius page check (owner decision D-20261106-photius-p4) is one of these working texts, and it comes first
among them. The kit reads the Pinakes text file named in the Photius fragment
(`jobs/pinakes-proquest-ingest/output/texts/`), hashes it, and uses it only when the hash equals the
fragment's `text_sha256`, the fragment's grade is `archival_replica_checked`, no page check is owed and the
check's final verdict is pass. That text then becomes the order's held text: the kit inventories its
clauses, own terms and change mentions from it, and the dossier and overlay input disclose it with the grade
`archival_replica_checked` and `acceptable_as_original: false`. The source keeps the ProQuest PDF's SHA-256
and URL, so custody is judged on ProQuest's bytes, and the dossier says the bytes remain ProQuest-dependent.
A replica whose check failed or is still pending, or whose text file no longer matches the recorded hash,
earns no credit and does not displace another text. A page-checked R37 official printing of the same order
still ranks above the replica. For an order with no checked replica, an official printing keeps its earlier
rank, and lifecycle claims on an official printing are still refused by `assemble.py`; wiring R37 into the
kit is a separate change.

A federalregister.gov full-text capture of a later Federal Register document (selden-fr-citers grade
`fr_document_full_text`, held as `ACTOR_TEXT:FRDOC:<number>`) may be cited as the source of a clause's later
event, such as a National Emergencies Act continuation notice (owner decision D-20261125-fr-capture-later-events).
`working_text.py` accepts it only at `operative_clauses[i].later_events[j].source`, only under its own FRDOC
identity, only when its URL is that document's federalregister.gov full text, the cited `<volume> FR <page>` and
FR Doc number agree with the capture's printed header, and the held bytes hash to both pins. `assemble.py` then
writes the claim's `fr_fulltext_captures` disclosure (grade `fr_fulltext_capture`), which the checker requires
exactly. The same capture as an order's original, an end, a current basis or a note is refused as before.

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

## Held sources and the pre-screen at prepare (Naude, Gilbreth)

`prepare` writes `HELD_SOURCES.json`: for each member, every `jobs/*/output/SOURCES.jsonl` row whose
`instrument_ids`, `requested_for_instrument_ids` or `mentioned_instrument_ids` name it and whose bytes and text the
dossier does not already cite, with the actual checker's offline custody status. A row that only declares the
order's own text (a mirror, say) is left to the original and working-text routes. States: `supplement_ready`
(bytes held on this machine, text hash matches, spans by the ACTOR_TEXT rule: the whole text up to 50,000 bytes,
else windows around lexical mentions of the number), `held_needs_span` (a large held text that never prints the
number; someone must declare the span), `bytes_not_held` (held text but no held bytes: acquire, never cite),
`held_bytes_not_on_this_machine`, `held_locator_incomplete`, `text_unavailable`, and
`census_actor_text_without_evidence` (a paired census actor whose large text the compiler could not window).
The `supplement_ready` spans are written as a `source_supplement` declaration, `HELD_SUPPLEMENT.json`.
`kit.py prepare ... --held-supplement` seals it into a new packet `<write>-held`, which is the one to dispatch; its
`SUPPLEMENT:` excerpts are unreviewed held text and need a `basis_eligible` mark to be a NO basis, exactly as
for any supplement. Nothing here decides relevance or a status.

`DISPATCH_CHECK.json` carries an advisory `prescreen` per member and a packet summary (`flagged_ids`). Rule
`gilbreth_r3r`, correction route only (an owner-reviewable replacement of a filed claim): the member needs an
actual-event fact and no event source (a TERM:/FACT: record other than the order's own page or a Presidency
Project mirror) has held bytes. Gilbreth measured 66 of 79 correction-route blocks predicted and 0 of 9
submissions flagged; on the YES route the rule flagged two claims later upheld, so it is not applied there. The
pre-screen never blocks: `ok` and `dispatchable_ids` are unchanged. A coordinator may hold a flagged order for
acquisition.

`kit.py prepare` exits 0 when every member is dispatchable, 1 when it wrote the packet but some member is
source-blocked (read `dispatch_check`), and 2 when it refused or failed.
