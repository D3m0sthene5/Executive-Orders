# Held-source handoff boundaries

Two source handoff defects were reproduced and repaired without changing source grades or legal standards.

- `current_evidence.enrich_current` matched SOURCES.jsonl by original URL and hash but ignored the declaration's text_sha256. A changed extract retaining the same quote was silently emitted with newly computed quote metadata. Fallback extracts now honor supplied text pins, expose a precise recovery gap when a pin fails, and emit no citable quote fields. Legacy declarations without a text pin retain existing behavior; this does not authenticate their originals or establish legal currency.
- `source_supplement.registered` selected provisional registrations solely by text path and text hash. A separately registered official representation sharing its extraction with a mirror could therefore be rewritten to that mirror's raw hash, URL and grade. Existing `Index.exact_official` now preserves the explicitly selected independently registered official representation. This uses existing official availability rules and does not create a grade or certify source identity.

Seventeen focused regressions cover matching and stale extract pins, malformed pins, wrong original identities, legacy declarations, independently pinned direct sources, exact original caches, shared official/mirror extracts and existing provisional treatment. They pass. The existing 17-test native supplement suite initially failed on a missing sparse dependency (`jobs/later-events/later_events.py`); after exact dependency recovery, all 17 tests passed in 1.329 seconds. Six regressions added after independent review close unpinned direct-source/item-path and legacy-duplicate bypasses; the latest focused 17-test pass took 0.125 seconds. A subsequent native 17-test supplement pass took 2.273 seconds.

No canonical registrations, source inventory, FETCH_QUEUE, evidence, claims, status or certification changed. The new tests contain synthetic witnesses only. Actual EO13286 witness examination remains with the independent source examiner. The final real retained-input native supplement demonstration is retained in `native-v4/`; earlier versions and failures remain unchanged. No measured model-token saving is claimed.

Run `python3 -m unittest discover -s jobs/claim-kit -p test_readiness_economy_sources.py -v` from repository root. Source/test SHA256 values are in PINS.json. Native preparation recompiles source and dossier fingerprints; existing packets cannot inherit the changed code pins.


## Real retained-input source delivery

`demo_13286.py` ran the ordinary `batch.prepare` -> `source_supplement.prepare` -> `source_supplement.verify` -> `batch.views` -> `dispatch.check` route on the four retained actual dossiers EO12312, EO12830, EO12985 and EO12793. It checked current reservations first, rehashed actual original/extract inputs and wrote only fresh Session A research destinations. No model production, apply, review or completion was launched.

One held EO13286 PDF (162,899 bytes, raw hash `0f74e21c46effda67c9a2824675469df809b09a321495030fa551594859554b5`) and its exact existing extraction (`57b106e01d54e1bcf61065a73a3591003b50eef2d8d0f65b0b54f98ea436e6df`) supplied four distinct target excerpts (§§61, 28, 20 and 31 respectively) and common §§89–93 context. `native-v4/SOURCE_DECLARATIONS.json` is one native-compatible source proposal serving all four orders. All eight delivered references passed actual offline checker custody as `held_bytes_verified`; the exact spans survived ordinary packet load and model-facing member views. Native supplement verification returned four orders and exact lineage/source bytes.

Final dispatch remains `source_blocked`: within the explicitly materialized input closure, each target original is represented by record-only raw custody, even though its extracted text is rehashed. This repair makes the shared acting text available; it does not establish current-law coverage or make any target ready. The EO12312 link proceeds through parent EO11448 and remains expressly unresolved. Original replacement, quotation recheck, earlier ending, scope and surviving-command obligations remain. Fifty-two codec issues preserve missing optional held texts literally, rather than hiding them. Sparse prior-work coverage remains explicit in native receipts.

Exact source, code, dossier and declaration pins, original native diagnostics and final receipt are under `native-v4/`. That final route, including two late-selection guard arms, took 4.6137 seconds with a unique temporary cache. The earlier source-delivery-only v1 route took 3.9286 seconds; those different operations do not establish a speed comparison. Model tokens, cash and active labor are unknown. This is source-delivery evidence, not measured model-token savings.

Reproduce with an unused destination, keeping current main reservations and source dependencies explicitly materialized:

```sh
python3 research/progress/sol-readiness-economy/sources/demo_13286.py --repo . --write research/progress/sol-readiness-economy/sources/native-next
```

Native packets pin source bytes and runtime. If dispatch or another runtime file changes during integration, reprepare the packets; never renew their hashes by hand.


## Independent correction and late source selection

Independent engineering review found that the first current-law repair still let an unpinned direct `source.text_path` or item `text_path` outrun a stale matching manifest pin. The final code binds these resolved same-path pointers (and unpinned legacy duplicates) to supplied matching declaration pins. An independently correct direct source text hash and an exact raw-cache witness remain usable; unrelated paths do not cause blanket holds. The reviewer's initial failure evidence remains in the separate review subtree. This was a corrected implementation defect, not a policy change.

The final native demonstration sends two arms of actual retained source references, wrapped only as expressly labelled ENGINEERING source-selection probes, through `dispatch.check_selected`. They are not assembled claims or legal findings. `A._reference` builds their exact dossier-bound references. The delivered official arm passes for all four orders with one unique raw-custody check. The inherited APP-mirror arm remains blocked for all four, with missing text and unavailable custody consolidated into one source-recovery task. Neither outcome approves legal application or the full dossier. Probe objects and both receipts live inside `native-v4/supplemented/` under neutral `ENGINEERING_*` filenames.

V1 preserves the original source-delivery demonstration against its older exact code. V2 retains a freshness refusal: a diagnostic saved outside the packet with a `SELECTED` filename was discovered as a new prior selection record after the first arm ran. V3 retains another refusal when that discoverable diagnostic reappeared after preparation. The final helper computes both arms before writing, stores diagnostics inside its own packet and avoids selected-version manifest filenames. Existing prior-research and source freshness gates were preserved throughout. Historical artifacts are not silently repinned to final code.
