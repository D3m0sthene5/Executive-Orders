# Davy: claim-drafts -> claim-kit chain health

**FAIL** as of `f56b6d0cb8`: claim-drafts -> claim-kit chain: FAIL in declarations - ValueError: claim-drafts/needs.txt declares research/stage19/output, which is not on main; claim-drafts/needs.txt declares research/stage20/output, which is not on main; claim-drafts/needs.txt declares research/stage21/sources_index, which 

| Check | Result | Detail |
|---|---|---|
| population | PASS | census 14998 ids, 4301 decided (contract 4bc1d8765d1f) |
| drafts | PASS | exact coverage and statuses passed |
| dossiers | PASS | summary counts and index membership/statuses match the decided population (fingerprints not re-read) |
| identity_case | PASS | no undeclared letter-case variants across 4301 ids |
| declarations | FAIL | ValueError: claim-drafts/needs.txt declares research/stage19/output, which is not on main; claim-drafts/needs.txt declares research/stage20/output, which is not on main; claim-drafts/needs.txt declares research/stage21/sources_index, which is not on main; claim-drafts/needs.txt declares research/stage21/original_sources, which is not on main; claim-drafts/needs.txt declares research/stage20/source |
| unit_tests | PASS | claim-drafts and claim-kit unit tests pass |
