# Producer report: y12 (papinian), 2026-11-10

Start UTC: 2026-11-10T05:24:02Z. End UTC: 2026-11-10T05:55:00Z. Final applied directory: `applied-v1` (one apply, no later version).

## Outcome per order (25 members; 5 submitted, 18 blocked, 2 unresolved)

Submitted (all provisional YES, one clause per section group, operative on 2026-10-14 from the held original plus the three bounded searches):

- EO:10444 (Good Conduct Medal restatement): one clause; later event EO 14085 section 2 (2022-10-03, amendment); U.S. Code note 10 U.S.C. ch. 57 prints it as amended.
- EO:10826 (CSC benefit authority): one clause; later event EO 12107 section 2-101 (effective 1979-01-01, Civil Service Commission to OPM); 5 CFR 351.502 still cites it; authority derivation 5 U.S.C. 3301 held and current.
- EO:11295 (passport rules delegation): inventory corrected by overrides (dossier omitted the recital and section 1); section 1 and section 3 operative, section 2 supersessions terminated 1966-08-05 by performance on issuance; 22 CFR parts 22 and 51 and 22 U.S.C. 211a note cite it; EO 14348 only cites it.
- EO:11698 (Hague Evidence Convention Central Authority): one clause; zero hits in all three searches; no treaty text held (disclosed).
- EO:12638 (Inter-American Letters Rogatory Central Authority): three clauses; zero hits in all three searches; 3 U.S.C. 301 held and current; dossier inventory starts mid-recital (disclosed).

Blocked or unresolved (exact missing source in decisions.csv and ASSESSMENT.jsonl):

- EO:8854: Proclamation 2965 (1952) and PLO 1707 texts not held; held PLO 6458 (1983) limits the remaining withdrawal to 20 years from 1983-09-06 with no held renewal (the held evidence points to lapse unless renewed; operative force unknown, ledger YES not supported).
- EO:11448, EO:12830, EO:11016, EO:12382, EO:12234: Executive Order 13286 amends each, but the packet holds only APP and clause-drafts copies, which the kit rejects (official copy exists in the repository, not registered as packet evidence). EO:12234 also needs a page check and current statute text.
- EO:12228: held text is a bounded fragment (starts mid-section 1-101).
- EO:11155: page check of 29 FR 6909 required and inventory omits sections 3 and 4.
- EO:13863, EO:14024, EO:14032, EO:14065, EO:13094, EO:14144: emergency-dependent; National Emergencies Act continuation notices are not held (a corpus search for the notice titles found none).
- EO:12630, EO:12748, EO:12137, EO:12318: held text not a verified whole order, inventories mis-segmented, later partial revocation or amendments unreconciled.
- EO:11514 and EO:12293 (unresolved): sources held but clause-by-clause reconciliation of the partial revocations (EO 12007; EO 12536) and amendments was not completed in this pass; no missing source.

None of the blocked orders is shown to be out of force except as noted for EO 8854; the ledger is unchanged.

## What took the time (one line each)

EO:8854 PLO 6458 reading; EO:10444 reading EO 14085 and the EO 10445 mislabeled FR items; EO:10826 tracing EO 12107 and 5 U.S.C. 3301; EO:11295 inventory correction and terminated-clause form; EO:11448/12830 discovering the EO 13286 official-copy rejection by test apply; EO:12638 text-boundary check; remaining orders triaged from the views and held-corpus searches.

## Batch-check

25 members; 5 claims checked, 5 strict pass, 5 pass the actual claim checker; outcomes blocked 18, assembled 5, unresolved 2; no actionable failures.

## Geddes

Geddes lint: 0 flags, 7 coverage gaps; no resolutions needed (GEDDES_LINT.json in applied-v1).

## Files opened beyond the views

LOOKUPS.details.json (member lookup structure only); jobs/current-law/output and jobs/later-events/output CSVs (filtered by order via a script); jobs/fr-originals texts for EO 12107, 12312, 14085, 14348; jobs/selden-fr-acting FR_48_40232.txt; jobs/theophilus-sources usc-t3-s301, usc-t5-s3301, usc-t22-s211a; app-executive-orders text for EO 13286; research/readiness/claims/papinian-2026-11-10-y10.jsonl (one claim, read only to learn the claim format).

## Tool defects

The 13286 official-copy rejection cannot be cured inside a packet (the official text is held but not an evidence id). A terminated clause whose end source is an inventory override record has no actor, so the original source id was used as end_id. cruden.py search over the whole corpus exceeds two minutes.
