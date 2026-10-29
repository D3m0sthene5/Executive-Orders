# Lightweight wiring stack — October 29, 2026

Owner request: create implementation PRs in the recommended order, without merging. Base main: 73d99f666573ee10f5b1ff2ada60f7d9331c3952. Each PR targets the immediately preceding branch so its review diff is narrow. No merge or auto-merge is authorized by this work.

1. PR93, Cotton: isolate test fixtures from the runner's inherited prior-output variable; preserve exact-byte runtime behavior; order custody before selected checker runs. Seven focused tests passed with the variable unset and inherited.
2. PR94, ProQuest checker inputs: restore only the three explicitly cited EO254/2171/4354 scan versions from pinned Git blobs, with bounds and no overwrite. Ten tests passed using real temporary Git repositories.
3. PR95, X1: read both existing event-source providers and expose representation provenance/state in review sheets. Eleven tests passed; source/event legal roles and phrase screens stay unchanged.
4. PR96, Lewis: all 265 audited proposals were already queued, so consume existing queue/result state and suppress redundant proposals. Eleven tests passed in the final stack, including repeat refresh and exact record pointers.
5. PR97, land sources: pass rehashed held PLO extracts to native source supplements; separate optional bounded acquisition from preparation. Twelve tests passed; native acquisition was mocked and no live download run was commissioned.
6. PR99, NEYMAN: connect explicit ordinary completion history to the unchanged native importer and diagnostic CLI. Ten tests passed against the exact native importer; CLI delegation tested with a spy.

Final focused validation: 61 distinct tests, 68 passing executions including Cotton's second environment run. Exact test files, outcomes and code hashes are recorded in FINAL_LOCAL_VALIDATION.json. These are component/contract tests, not a complete live-corpus acceptance run. See the six numbered notes for implementation scope and reproduction commands. Their initial test counts are historical; this final pass includes one additional Lewis regression. Each PR also receives the repository's existing checks; final CI state must be read from GitHub rather than inferred from these local tests.

The final PR99 QA commit includes the Lewis physical-JSONL-line/CSV-record pointer correction and a byte-stable land fixture for Windows, alongside the NEYMAN work. It records Kean finding F-20261029-93 and refreshes the shared brief. Previous Astra notes are preserved as their exact original Git blob in HANDOFF/astra-history-through-20261029.md, still inside Kean's searchable HANDOFF scope.

No claims, provisional statuses, census admissions, source grades, human certifications or canonical readiness counts were edited. No campaign-level hours/tokens savings are asserted. Real source availability, remaining page review and substantive research still govern completion. The standing legal cutoff is unchanged.

The operational sequence is custody/materialization, refreshed event/queue inputs, bounded land-source handoff, ordinary independent research/review/completion, then optional diagnostic import. Discovery and consumption remain separate where a direct dependency would create a cycle.
