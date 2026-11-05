# Shared sources ranked 1-6 by Bentham (2026-11-05)

Six legal sources, each cited by several orders' claims, keep those orders blocked with
`SHARED_SOURCE_NOT_RETRIEVED`. A Sonnet worker traced each one; the coordinator wrote this report from its hand-back.
Five validated source requests are in `FETCH_REQUESTS.jsonl` (`request_contract.py validate`: valid, no errors).

## Why fetch requests alone do not clear these

The tracker counts a shared source as retrieved only when `jobs/source-ladder/output/SOURCES.jsonl` holds a row with a
SHA-256 whose `wanted_id` equals the Stage 20 authority string exactly (for example `EO::4314`). Requests placed in
`research/readiness/FETCH_QUEUE.jsonl` receive ids such as `queue:EO:5065:EO 4314`, which never match. None of the six has
been attempted by the ladder; its last committed run (2026-10-24) covered 182 of 1,818 items. The Stage 20 items need
their own route: `cached_urls` hints in `research/stage14/QUEUES/INDEXED_CACHED_EO_SOURCE_HINTS.csv` for the three
1934-1935 orders, and a small ladder override for EO 4314 and 26 CFR 458.324. That route is untested.

## By source

| Source | Orders | Finding | Witness |
|---|---:|---|---|
| EO 4314 (Panama Canal navigation rules, 1925) | 10 | No online copy of the 1925 order. | Best witness: Library of Congress scan of 35 CFR Part 4 printing the rules with "E.O. 4314" source notes (official CFR codification, derivative; edition year inferred as about 1938). |
| EO 6868 | 6 | Already held in the GPO volume for orders 6690-6935 (DjVu image 449; `jobs/hathi-gpo-orders`, Commons file). | Machine-read government-printed copy; APP mirror also held. |
| EO 6910 | 3 | Already held, images 559-560 of the same volume. EO 6910A and 6910B are different orders. | Machine-read government-printed copy. |
| EO 6964 | 3 | Already held, GPO volume 6936-7081, images 99-100. | Machine-read government-printed copy. |
| 48 U.S.C. 863 | 3 | Already retrieved. A key mismatch, not a fetch problem: Stage 20 spells it with and without a stray closing parenthesis, and the ladder records the clean spelling. Fixed in the tracker on branch `claude/tischendorf-tracker` (commit 371d684); unblocks EO 10035, 10310 and 10599. The held text is the 2024 edition, which shows only the 1970 repeal. | U.S. Code. |
| 26 CFR 458.324 (cited for EO 10801 and 10876) | 2 | The section was issued by T.D. 6133 at 20 FR 3017 (1955), already held. Part 458 is not in the current CFR, and the 1959-1960 CFR volumes were not located, so later amendments are unchecked. | Official Federal Register scan; original-issue witness only. |

## Not fixable by fetching

The 1925 text of EO 4314 and the 1959-1960 text of 26 CFR 458.324 have no located online official copy. EO 6868, 6910
and 6964 are held; registering them as the Stage 20 shared source is bookkeeping, not acquisition.
