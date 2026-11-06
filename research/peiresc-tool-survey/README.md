# Peiresc: survey of outside tools that could speed up the project (2026-11-06)

The owner asked for a wide search for programs, harnesses and tools to buy or integrate. Gas Town prompted the
request. Eight Sonnet research agents, coordinated by Opus 5.5, each covered one area. `BRIEF.md` is the brief they
shared, and files 01-08 are their notes. The summary for the owner is a Claude doc:
https://claude.ai/artifact/CGZuSyh3enbp2EQkcuD2rf

## Conclusions

No product changes the project fundamentally. Gas Town is a skip: DoltHub's measured trial cost about $100 per
hour and merged a pull request with failing tests.

The repository is the urgent problem. It is at 9.3-9.9 GB against GitHub's 10 GB limit; GitHub's API size went from
9,175,409 KB to 9,717,466 KB during the survey (Kean ask A-20261106-2).

To adopt:
- source bytes in Cloudflare R2, with only a hash manifest in git;
- `claude --bare -p` driver scripts with an API key, an output schema, a budget cap and a cost log;
- the Batch API for reviews;
- work leases in Kean.

To try:
- an OCR pilot;
- a GPT-family reviewer, scored with Inspect AI;
- the Lowande-Poznansky and Thrower revocation data as controls;
- three status sources: LSA, U.S. Code Table IV and CourtListener.

## Workers

All were Agent-tool subagents running Sonnet. The shared web-search budget (200 searches) ran out.

| File | Tokens | Tool calls | Seconds |
|---|---:|---:|---:|
| 01 | 244,719 | 97 | 583 |
| 02 | 127,080 | 57 | 206 |
| 03 | 167,524 | 104 | 765 |
| 04 | 182,148 | 97 | 566 |
| 05 | 147,299 | 83 | 730 |
| 06 | 161,172 | 68 | 507 |
| 07 | 178,214 | 110 | 506 |
| 08 | 138,410 | 66 | 277 |
