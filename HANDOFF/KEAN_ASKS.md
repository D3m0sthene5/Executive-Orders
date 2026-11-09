# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261107-mountweazel-plants-leak (2026-11-06, claude-encyclopedie)

Mountweazel's whole-repository check fails because research/excavator/dorotheus-sample-2026-11-06/PLANTS.csv names seeded item MW-C720-01 (red in the Valla pilot check). Allow the check to accept revealed plant keys under research/excavator/*/PLANTS.csv after reveal, or move revealed keys under jobs/mountweazel/fixtures?

*Why:* The check blocks every PR's Valla pilot; the plants are already revealed, so it is a check-policy question, not a live leak.

Sources: `research/encyclopedie-campaign/LOG.md`
