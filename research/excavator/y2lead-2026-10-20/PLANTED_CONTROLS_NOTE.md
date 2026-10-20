# Planted controls (Y2LEAD, 2026-10-20)

Scratch planter placed one defect per batch in a copy (review_copy); the reviewer saw only the copy. Keys were kept outside the repo. Both defects were caught; the planted lines are NOT filed.

| Batch | Order | Field | Genuine value | Planted value | Caught |
|---|---|---|---|---|---|
| 01 | EO:10104 | research_rationale | Feb. 1, 1950 | Feb. 1, 1951 | yes (rejected, DATE) |
| 02 | EO:11438 | operative_clauses[].current_predicate.legal_basis | EO 12107 (sec. 2-101, effective 1979-01-01) | EO 12107 (sec. 2-101, effective 1981-01-01) | yes (rejected, DATE) |

Notes: the plan called for two plants in a batch with 4 or more claim lines; each batch (6 claim lines) received only one. Both reviewers said that without the planted error the line would have been upheld, but the unplanted versions were never independently reviewed, so EO 10104 and EO 11438 are not counted as upheld and not filed. CLAIMS.proposed.jsonl here is the producer (work) version, unplanted.
