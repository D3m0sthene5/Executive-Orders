#!/usr/bin/env python3
"""Regenerate compact receipts from the retained run RESULT.json files."""
import datetime
import json
from pathlib import Path

root = Path(__file__).resolve().parent
names = ['r1-legacy-unprofiled','r1-repaired-cold','r1-repaired-warm',
         't5-repaired-reuse','t6-repaired-reuse','b06-repaired-reuse']
arms = []
for name in names:
    r = json.loads((root/name/'RESULT.json').read_text())
    d = r.get('implementation_details',{})
    corpus = d.get('corpus',{})
    arms.append({'arm':name,'members':r['member_count'], 'wall_seconds':r['cruden']['wall_seconds'],
                 'rchar':r['cruden']['io_delta']['rchar'], 'setup_seconds':r.get('setup_seconds'),
                 'outputs':r['outputs'],'cache_bytes':r.get('cache_bytes'),
                 'source_manifest_sha256':r['text_manifest_sha256'],
                 'reference_equivalence':r.get('reference_equivalence'),
                 'candidate_files':d.get('candidate_files'),'search_seconds':d.get('search_seconds'),
                 'corpus_timings':corpus.get('timings'), 'corpus_snapshot_sha256':corpus.get('snapshot_sha256'),
                 'input_pins':r['inputs']})
summary = {'schema':'cruden-benchmark-summary/v1','arms':arms,
           'matched_comparison':'Only serialized, unprofiled r1 arms establish this measured timing comparison. One trial each.',
           'r1_cold_ratio':arms[0]['wall_seconds']/arms[1]['wall_seconds'],
           'r1_warm_ratio':arms[0]['wall_seconds']/arms[2]['wall_seconds'],
           'corpus':{'texts':33118,'bytes':200530096,'manifest_sha256':arms[0]['source_manifest_sha256']},
           'model':'OpenAI Codex; exact runtime model SKU unavailable in worker context',
           'tokens':None,'cash':None,
           'cost_clock':{'first_explicit_utc':'2026-10-30T00:08:10+00:00',
                         'summary_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                         'initial_setup_before_first_clock':'unmetered',
                         'code_mode_calls_at_least':76,
                         'call_count_method':'manual transcript count through first summary attempt; later calls, nested tool calls and coordination messages not included'},
           'limits':['No legal, readiness, source-grade, or review conclusion.',
                     'Cruden intentionally uses native load_packet(check_sources=False); full gate tested separately and fails.',
                     'No comparison to the attributed prior Opus 113.6-second measurement.',
                     'Diagnostic cProfile t5/t6/b06 runs overlapped and are not matched speed comparisons.']}
prior_path = root/'SUMMARY.json'
if prior_path.exists():
    prior = json.loads(prior_path.read_text())
    if 'packaging' in prior:
        summary['packaging'] = prior['packaging']
    if 'final_completed_utc' in prior.get('cost_clock',{}):
        summary['cost_clock'] = prior['cost_clock']
(root/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
rows = []
for r in arms:
    output = {x['path']:x['bytes'] for x in r['outputs']}
    rows.append(f"| {r['arm']} | {r['members']} | {r['wall_seconds']:.3f} | {r['rchar']:,} | {output['LOOKUPS.json']:,} / {output['LOOKUPS.md']:,} / {output.get('LOOKUPS.details.json',0):,} |")
text = '''# Cruden profile and bounded matched replay

The largest measured cost is repeated regex scanning. On the full t5 corpus, 794,856 `re.Pattern.search` calls took 216.410 of 303.405 profile seconds (71.3%%). Repeated path resolution took 37.418 cumulative seconds; 1,457,150 lowercase calls took 15.479 seconds. The 250-file microprofile and full non-NRA b06 profile independently put regex search first. The full diagnostic t5/t6/b06 profiles overlapped; their wall times are diagnostic only.

## Matched result

Only the r1 rows below are a serialized matched timing comparison: exact original seven-member Opus packet bytes, one fresh process per arm, identical unprofiled flags, no competing corpus benchmark, and the same frozen corpus. Cold repair took %.3f seconds versus %.3f legacy; warm repair took %.3f. This is one trial each, independent of the earlier attributed 113.6-second Opus result. All four repaired packet families produced byte-identical legacy JSON and Markdown. Distinct t5/t6/b06 rows establish cross-packet cache reuse and equivalence; their earlier legacy profiles are not used to calculate speed ratios.

| Arm | Members | Native-call seconds | rchar bytes | JSON / Markdown / new sidecar bytes |
|---|---:|---:|---:|---:|
''' % (arms[1]['wall_seconds'],arms[0]['wall_seconds'],arms[2]['wall_seconds'])
text += '\n'.join(rows)
text += '''

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
'''
(root/'REPORT.md').write_text(text)
print(json.dumps({'arms':[(r['arm'],r['wall_seconds']) for r in arms], 'cold_ratio':summary['r1_cold_ratio'],'warm_ratio':summary['r1_warm_ratio']},indent=2))
