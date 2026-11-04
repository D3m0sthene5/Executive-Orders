# Retained root setup/integration exceptions

* Initial checkout attempted unavailable objects from a partial-clone seed. Only this new clone was affected. Reapplied a narrow sparse checkout; restored selected exact Git blobs without touching the seed. A missing report_dates.py Git object initially prevented local commit; writing the already exact held bytes into this clone restored the expected object identity. The local lazy remote was then disabled.
* First history-context integration tests missed later-events.py in the sparse fixture; materialized the exact unchanged helper and passed all five tests.
* History v1 was prepared before adapter finalization and correctly became stale. It was retained unchanged; v2 was freshly prepared.
* First strict Kean check rejected the custom ask identifier in notes (only numeric ids match its notes regex). The author withdrew the administrative duplicate with an append-only revision, registered A-20261104-1, and the final strict check has zero errors/warnings. No owner answer was invented.
* PR132 runtime rehearsal produced two CLI conflict blocks. Combined handling retains both option sets and every command; independent exact combined review passed.

Worker findings, source candidate revisions and independent adversarial failures are retained in their respective reports and seals. This file summarizes root exceptions, not a claim to recover missing raw transcripts or to measure their complete cost.
