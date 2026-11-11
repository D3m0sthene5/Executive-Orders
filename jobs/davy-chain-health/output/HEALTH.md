# Davy: claim-drafts -> claim-kit chain health

**FAIL** as of `7feb04f74c`: claim-drafts -> claim-kit chain: FAIL in population, drafts, dossiers, identity_case, declarations, unit_tests - FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/Executive-Orders/Executive-Orders/research/ulpian/jacquard-l1-correction/CORRECTION.json'

| Check | Result | Detail |
|---|---|---|
| population | FAIL | FileNotFoundError: [Errno 2] No such file or directory: '/home/runner/work/Executive-Orders/Executive-Orders/research/ulpian/jacquard-l1-correction/CORRECTION.json' |
| drafts | FAIL | not run: the population check failed |
| dossiers | FAIL | not run: the population check failed |
| identity_case | FAIL | not run: the population check failed |
| declarations | FAIL | ValueError: claim-drafts read 4 undeclared path(s), e.g. jobs/fr-originals/fr-originals-cache/blobs/4d/4d0656a416bb08d9edfa8b5b4ee94bec7275d3aa242b29b3c7e908b893a19cca.pdf, jobs/fr-originals/fr-originals-cache/blobs/65/65409311cad3e59624ed65a2b4b29f9507167a8ae7607530d170eee5b742902a.pdf, jobs/fr-originals/fr-originals-cache/blobs/86/86fee1e4cc85e2ff5d1c7ca1675b7962d6fc8dec2259315fd766ce42ef48dbc8. |
| unit_tests | FAIL | ValueError: claim-kit tests failed (FAILED (errors=1, skipped=1)) |
