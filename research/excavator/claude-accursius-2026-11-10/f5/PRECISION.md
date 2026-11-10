# OWN_TEXT classifier precision (blind reads, 2026-11-10)

Reader: Claude Sonnet 5.5, separate context, told only the four classes; the classifier's labels were sealed
(BLIND_KEY_*.json) until each read was written (BLIND_READS_*.csv). Texts are the dossier originals on main.

| Sample | Classifier version | Positives read | Reader agrees (self-executing or amendment-only) | Precision |
|---|---|---:|---:|---|
| 1 (seed `accursius-own-text-audit-2026-11-10`, 40 positives + 10 negatives) | ed50c8f004 | 39 readable | 33 | 85%; the misses were then fixed, so this sample is no longer an unbiased test |
| 2 (seed `accursius-own-text-audit-2-2026-11-10`, 50 positives + 10 negatives, disjoint) | 4901f1dcdb | 50 readable | 42 | **84% (95% CI about 71-93%)** |

Sample 2 misses (reader: continuing): EO 6215 (effect tied to another order's undated effective date), 1973 and 1924
(land opened to entry for a fixed period from a later day; Pothier treats this class as spent with a fixed
preference period), 11713 and 11354 (a further standing rule beside the amendment), 9499 (a standing inspection
rule), 12315 (a transmittal duty and a savings clause), 5680 ("their occupants" status effect).

Use: an OWN_TEXT record is a lead. A producer must confirm that every command is of the stated kind and an
independent reviewer must check it against the held original. Any lot built on OWN_TEXT kinds needs a full audit
of its members until its own error bound is met; 84% lead precision does not license sampled adoption.
