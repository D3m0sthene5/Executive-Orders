# Cruden profile and bounded matched replay

The largest measured cost is repeated regex scanning. On the full t5 corpus, 794,856 `re.Pattern.search` calls took 216.410 of 303.405 profile seconds (71.3%). Repeated path resolution took 37.418 cumulative seconds; 1,457,150 lowercase calls took 15.479 seconds. The 250-file microprofile and full non-NRA b06 profile independently put regex search first. The full diagnostic t5/t6/b06 profiles overlapped; their wall times are diagnostic only.

## Matched result

Only the r1 rows below are a serialized matched timing comparison: exact original seven-member Opus packet bytes, one fresh process per arm, identical unprofiled flags, no competing corpus benchmark, and the same frozen corpus. Cold repair took 11.569 seconds versus 71.010 legacy; warm repair took 5.541. This is one trial each, independent of the earlier attributed 113.6-second Opus result. All four repaired packet families produced byte-identical legacy JSON and Markdown. Distinct t5/t6/b06 rows establish cross-packet cache reuse and equivalence; their earlier legacy profiles are not used to calculate speed ratios.

| Arm | Members | Native-call seconds | rchar bytes | JSON / Markdown / new sidecar bytes |
|---|---:|---:|---:|---:|
| r1-legacy-unprofiled | 7 | 71.010 | 232,327,605 | 11,214 / 6,449 / 0 |
| r1-repaired-cold | 7 | 11.569 | 511,480,650 | 11,214 / 6,449 / 7,547,966 |
| r1-repaired-warm | 7 | 5.541 | 526,929,916 | 11,214 / 6,449 / 7,547,905 |
| t5-repaired-reuse | 24 | 6.538 | 540,228,062 | 51,786 / 33,648 / 7,594,282 |
| t6-repaired-reuse | 24 | 6.544 | 538,267,018 | 46,911 / 28,053 / 7,581,106 |
| b06-repaired-reuse | 2 | 4.933 | 518,182,003 | 6,576 / 5,270 / 7,549,462 |

The corpus is 33,118 sorted retained paths, 200,530,096 raw bytes, manifest SHA256 `7a87fb985fcf53f96a9e7087d56bb15a9c4dc6fae311c9834bd62b1b7f183632`. The persistent feature cache is 15,449,266 bytes. Cold construction took 7.7284 seconds, including 4.6438 feature extraction; final validation took 1.6342 seconds; cache writing took 0.6441 seconds. Every repaired call hashes 200,530,096 corpus bytes before matching and again after matching, plus reads candidate bytes. r1 reads 9,582,220 candidate bytes. Cold r1 searched 506 candidate files in 0.8563 seconds. Actual full-call rchar increases substantially, and each new details sidecar is about 7.5 MB. No I/O saving is claimed. Setup (about two seconds per arm for independent manifest pins) is recorded separately from native-call time.

## Existing facilities and smallest compatible repair

| Existing facility | Why it is not an exact Cruden accelerator |
|---|---|
| `eo_identity.find_mentions` | Different prefixes, list/comma/half-number handling and spaced suffix semantics; misses `Order No. 6254`, which Cruden accepts. |
| `later_events.eo_references` / `current-law/eo_refs.py` | Semantic parsers with different prefix/case/list/range rules; not a safe complete filter for the legacy matcher. |
| `namier.Corpus` | Transient name-token index over fragment-defined saved texts; corpus scope differs, includes full-run sources, and caps each text read at two million characters. |
| checker `HeldIndex` / `working_text.Index` | Source SHA/URL and fragment-declaration/grade indexes, not full-text retrieval. Fragment-index repair PR104 is unrelated and was not changed. |

Use disposable source-bound decimal-run and fixed-code-prefix features to select a safe superset, then apply the exact legacy matcher to original source text. Preserve sorted paths, own-path exclusion, first match per source, snippets, caps, and legacy JSON/Markdown. Rewalk and hash actual sources each call; detect additions, deletions, same-size edits and mid-call changes. Cache only retrieval features, not evidence determinations. The implemented helper follows this narrower route rather than introducing a second full-text database. `PARSER_COMPARISON.json` preserves actual existing-parser differences.

The required Cruden scope is exactly every `jobs/*/output/texts/**/*.txt` except clause-drafts, plus REGISTER.csv, WPA_NUMBERED_ENTRIES.csv, both APP document manifests, own/page-check texts, and the selected native packet loader dependencies. This scope is not all held project evidence; full-run `data/` texts and excluded clause-drafts remain outside it.

## Validity and cost limits

The harness redirects only output: the original native member loader receives the real retained packet; new input diagnostics likewise receive the actual packet path. Cruden itself calls `batch.load_packet(..., check_sources=False)` and checks packet/dossier fingerprints without the full production gate. The ordinary default t5 gate independently failed in 0.0918 seconds on the missing pinned clause-drafts text recorded in `T5_DEFAULT_GATE.json`. No bypass is represented as a valid full packet, and no legal or readiness result is inferred. All replay output stays under this profiling directory.

The initial aborted attempt completed its corpus manifest but had no phase telemetry; its exact gate/Cruden outcome and wall duration are unestablished (`t5-baseline/INTERRUPTED.json`). Initial instruction/code reading preceded the first explicit clock. The observed worker interval begins 00:08:10 UTC; detailed native/setup intervals and model/cost limitations are in `SUMMARY.json`. Exact model SKU, tokens, cache-token splits, cash and exclusive human labor are unavailable. The summary records at least 76 manually counted code-mode calls through final packaging verification; nested tools and coordination messages are excluded. Parent owns Kean/HANDOFF integration because this worker may write only `profile/`.

## Reproduce

Run `python3 -I research/progress/corpus-evidence-retrieval/profile/profile_cruden.py REPO PACKET NEW_OUTPUT --no-profile --cruden-source research/progress/corpus-evidence-retrieval/profile/legacy_cruden.py` for the legacy arm. For repaired arms omit `--cruden-source`, set a fresh `CRUDEN_CACHE_DIR` outside the repository for cold and reuse it for warm/distinct packets, and pass `--reference LEGACY_OUTPUT`. `--limit-texts 250` explicitly recreates the diagnostic microprofile. `probe_default_gate.py REPO PACKET OUTPUT --timeout 30` preserves native-gate refusal or timeout. `summarize.py` regenerates the compact benchmark table and summary. Exact source/helper, packet and metadata pins are in each RESULT; all full source manifests share the hash above. `RAW_ARTIFACTS.tar.xz` preserves all full manifests, pstats, and new details sidecars byte-for-byte; `ARCHIVE_MANIFEST.json` identifies exact archive members and raw hashes/bytes. Canonical manifest references in older START/RESULT receipts now refer to archive member `TEXT_MANIFEST.json`. The b06 producer finished reading its raw sidecar; the verified archive now preserves that sidecar.
