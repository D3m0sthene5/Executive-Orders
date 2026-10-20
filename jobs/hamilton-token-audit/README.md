# Hamilton: where an agent session's tokens go

Named for the first Treasury Secretary, who audited the young nation's debts before
proposing how to pay them. Hamilton audits agent sessions before anyone builds a
token-saving tool, and re-audits after, so a saving is claimed only when measured.

Offline. Input: transcript pages saved from the claude-code-remote `list_events`
tool (`{"ccr": {"data": [...]}}` per file). Raw transcripts stay out of the repo;
only the derived profiles are committed.

```
python jobs/hamilton-token-audit/profile.py PAGES_DIR --cost-usd N --label NAME --out OUT_DIR
```

Each model call's usage is rebuilt from the transcript. Fresh cost (new input,
cache writes) goes to the step that triggered the call; re-read cost (cache
reads) goes to the agent's fixed setup, measured as its first call's context,
and to every item still in context, in proportion to its estimated size
(characters / 4). The model's own writing counts as context. Output tokens are
recorded only at the start of streaming, so use get_session totals for output.
Relative prices: input 1, cache read 0.1, 5-minute write 1.25, 1-hour write 2, output 5.
Dollar figures scale by the session's own `cost_usd`, which is API list-price
value, not necessarily what the owner was billed.

The loop: audit, propose a tool aimed at the largest measured cause, probe it on
a small run, re-audit, and keep it only if cost per accepted result falls without
quality falling. Report: `research/production/hamilton-2026-10-20/REPORT.md`.
