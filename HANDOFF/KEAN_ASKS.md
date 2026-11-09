# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261108-lean-main (2026-11-08, claude)

Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?

*Why:* ChatGPT and claude.ai GitHub connectors and cloud clones see main's whole tree; .ignore, the Claude hook and Ariadne do not reach them. Packing or moving changes evidence paths that pins and certificates cite, so it needs the owner's ruling. No action until answered.

Sources: `.ignore`

## A-20261109-claim-checker-cache (2026-11-09, claude (Palsgraf))

May claim-checker's download cache cap rise from 1,024 MB to 2,048 MB (a CACHE_MB file in jobs/claim-checker)?

*Why:* Each run evicts about 487 MB of extracted texts and verified downloads at the 1 GB cap, so about 22 claims are rechecked and their sources re-downloaded every run (most of a selective run's 144-567 s). It uses about 1 GB more of the repository's shared Actions cache, which may evict other jobs' caches sooner.

Sources: `jobs/claim-checker/README.md`
