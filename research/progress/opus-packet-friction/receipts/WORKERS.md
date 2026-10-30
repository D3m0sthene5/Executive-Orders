# Worker ledger (model, tokens, tool uses, wall time) — from harness task notifications
| worker | model | subagent_tokens | tool_uses | wall_s | files |
|---|---|---|---|---|---|
| valla-scope | sonnet (claude-sonnet-5-5 via Agent model=sonnet) | 108668 | 16 | 202 | jobs/valla/{valla.py,test_valla.py,README.md} |
| completion | sonnet | 127611 | 23 | 264 | jobs/claim-kit/{completion.py,test_completion.py,COMPLETION.md} |
| prior-research | sonnet | 107702 | 16 | 359 | jobs/claim-kit/{prior_research.py,test_prior_research.py} |
| index+undecided | sonnet | 185539 | 53 | 941 | jobs/claim-kit/{fragment_cache.py,test_working_text_index.py,source_supplement.py,test_source_supplement.py,status_overlay.py,test_status_overlay.py} (redirected once by coordinator: working_text.py restored) |
| independent-review | opus (fresh context) | 186337 | 33 | 536 | read-only review of 0f98bc73b9 |
