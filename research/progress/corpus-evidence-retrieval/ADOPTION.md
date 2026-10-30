# Bounded adoption handoff for Sol's integration session

Leave this PR unmerged. The base is `f9c6d806ad059dcad7875ab3708715f20ea386df`.
`SOURCE_PINS.json` binds the four implementation/test/documentation files.

- `cruden.py`: `376cfb32f05026899abb94aad937fa1dbdb1fe21266bfc52fd404a965508b2be`
- `cruden_cache.py`: `ab8704b1243a1e059a9b973623c1eaa20a92b90cb6d8e979e1bb46e62c444873`

The implementation has no PR104 dependency and changes no claim-kit/Valla,
runner/dependency declaration, checker/tracker or shared download implementation.
The comparison uses main's claim-kit, so PR104's fragment-cache gain is excluded.
Existing frozen research can continue using its exact old script; adopt the new
script and its adjacent helper together for subsequent lookups. No claim-kit
compiler regeneration, source-grade change or scientific approval is supplied.

## Acceptance checks on the exact combined integration tree

1. Verify the four SHA-256 values in `SOURCE_PINS.json`. Preserve all append-only
   Kean findings from the component PRs, then regenerate `HANDOFF/KEAN.md`.
2. Run the 11 focused checks:
   `python3 -I -m unittest discover -s research/excavator/claude-nira-sweep-2026-10-29 -p 'test_cruden*.py' -v`.
3. Run the independent scripts in `challenge/` against the combined Cruden path,
   following `challenge/FINAL_REVIEW.json`. They use temporary corpora and must
   preserve legacy JSON/Markdown/stdout while refusing stale/corrupt inputs.
4. Reproduce the serialized seven-order comparison using
   `profile/profile_cruden.py` and `native/r1-input/PACKET.json`, a fresh external
   `CRUDEN_CACHE_DIR` for cold, and the same cache for warm and distinct packets.
   Require exact legacy JSON and Markdown equality, complete declared inventory,
   and content verification. Include construction, verification, output volume
   and independent harness setup; the published single-trial times are not a
   performance SLA for another machine.
5. Exercise the new literal route and inspect full held text, including contrary
   passages. A bounded example is the EO10673/10772 assignment in `producer/`.
   Preserve its duplicate, OCR, neighboring-text and source-grade cautions.
6. Run `python3 -I jobs/kean/kean.py check --strict`. Sol retains ownership of
   combined PR103/104 runner/declaration and scientific-pipeline acceptance.
   Separate passes here do not establish combined compatibility or production
   readiness. Do not add an unaudited runner certificate based on this work.

A cold cache is disposable. Its location is outside the repository by default;
`CRUDEN_CACHE_DIR` overrides it. Cache integrity covers accidental corruption;
full source bytes are checked twice, with observed mutations causing refusal.
The filesystem is not locked after the final check. Legacy `search REGEX` remains
unchanged and uncached; `number` and `literal` provide the source-bound route.

## Producer usage

```
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups PACKET_DIR
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py literal "Fitness of American Youth" --write /tmp/fitness.json
```

Read `LOOKUPS.md`, then select member records from `LOOKUPS.details.json` and open
`full_text_path`. Use `--write` for general queries so the model receives a compact
result descriptor rather than the full 33,118-source inventory. No match means
no match for the exact query in the declared available snapshot, subject to its
omissions and limits. Source acquisition and scientific adjudication retain their
existing procedures.

`profile/ARCHIVE_MANIFEST.json` and `QUERY_ARCHIVE_MANIFEST.json` bind lossless
archives of bulky raw manifests, details and query results. Extract them in a
scratch directory to inspect original receipt paths; small results and review
reports remain plain text. Canonical source evidence is not copied or changed.
