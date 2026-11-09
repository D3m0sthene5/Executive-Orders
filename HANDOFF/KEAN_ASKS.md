# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261108-lean-main (2026-11-08, claude)

Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?

*Why:* ChatGPT and claude.ai GitHub connectors and cloud clones see main's whole tree; .ignore, the Claude hook and Ariadne do not reach them. Packing or moving changes evidence paths that pins and certificates cite, so it needs the owner's ruling. No action until answered.

Sources: `.ignore`

## A-20261109-skipped-witness (2026-11-09, Claude)

May the skipped-witness switch in jobs/claim-kit/WORKING_TEXT_SWITCHES.json be set to "flag"? Today ("void") a frozen Lachmann confirmation goes stale when any field differs; 126 orders are now blocked only because Lachmann added a skipped witness (mostly a Photius GPO printing) that it never compared. Under "flag" those 126 return to the ready path with a visible recheck flag; every other difference still voids. Recommendation: yes, flag. It re-freezes nothing and does not discharge D-20261108-photius-recheck: the h01 page check stays owed and the flag lists the orders it covers.

*Why:* Evidence-policy change; only the owner may switch it. Measured on all 1,530 claims (F-20261109-gutenberg-skipped-witness).

Sources: `jobs/claim-kit/WORKING_TEXT_SWITCHES.json`
