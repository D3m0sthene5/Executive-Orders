# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261108-lean-main (2026-11-08, claude)

Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?

*Why:* ChatGPT and claude.ai GitHub connectors and cloud clones see main's whole tree; .ignore, the Claude hook and Ariadne do not reach them. Packing or moving changes evidence paths that pins and certificates cite, so it needs the owner's ruling. No action until answered.

Sources: `.ignore`

## A-20261110-ulpian-l1r-correction (2026-11-10, Claude)

Extend the Jacquard L1 correction to wave 2? 582 L1R provisional NO statuses (PR 119, same L1 card and its 'at least 14' premise, which you declined in D-20261110-ulpian-no-floor) were adopted; 527 are dated on or after 1904-05-03 and 26 have no exact date, plus 3 undated wave-1 L1 rows (EO 940, 1596, 1604). Recommended: yes, read them by the same blind two-arm method with planted controls (research/ulpian/jacquard-l1-correction), keep those whose own text quotes a sufficient fact and return the rest by a correction PR you merge, in batches of at most 100. Alternatives: ratify the premise for wave 2 only (inconsistent with D-20261110-ulpian-no-floor), or leave them.

*Why:* The 42-row wave-1 reading kept 9 and returned 33 (21% kept). At that rate about 110 of the 527 would stay and about 420 would return to undecided. Cost of the 42: about 196k worker tokens (two arms) plus coordination, so the 556 would cost roughly 2.6M worker tokens. Until read, those statuses rest on a basis you declined.

Sources: `research/ulpian/jacquard-l1-correction/README.md`, `research/excavator/jacquard-2026-10-31-w2/README.md`
