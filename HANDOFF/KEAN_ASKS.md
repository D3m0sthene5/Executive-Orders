# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261108-lean-main (2026-11-08, claude)

Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?

*Why:* ChatGPT and claude.ai GitHub connectors and cloud clones see main's whole tree; .ignore, the Claude hook and Ariadne do not reach them. Packing or moving changes evidence paths that pins and certificates cite, so it needs the owner's ruling. No action until answered.

Sources: `.ignore`

## A-20261110-mommsen1-grant-source (2026-11-10, mommsen-1)

Does the retained OWNER GRANT and OWNER OVERRIDE in the Nov09 21:46 MOMMSEN-I desktop session supply this lane's exact existing grants despite its session/turn cwd being Documents/Codex/2026-11-09/you-are-mommsen-i-change-to rather than the worktree? No widening is requested.

*Why:* The takeover prompt identifies the grant source by first user message and worktree cwd. No matching-cwd Nov09 session or owner-grants.md was found. No merge grant is assumed; PR254/255 stay unmerged and SAVIGNY controls review and merge order.

Sources: `HANDOFF/packets/2026-11-10-mommsen-1-turn1-takeover.md`
