# Selden: questions for the coordinator

## Q1. The Herschel "later law" blocker is mostly not a named instrument the project lacks

The census (`research/selden/census.py`) finds that 30 of the 36 Herschel sample orders blocked on later law have
no acting instrument named anywhere in later-events, Shepard or current-law, and none of the 36 is an order whose
named acting instrument is merely unheld. By projection weight, about 44% of the 1,814 need a current-status source
(current CFR or agency program text), 12% the text of the statute the order rests on, 13% an unnamed later
instrument, 8% a fact date, 7% a kit own-terms record, 2% NEA continuation notices and about 1% a named later order.
**Default:** build three jobs that serve both groups: `selden-fr-citers` (FR full text 1994 on, bounded search per
order: finds unnamed later instruments and supplies counterevidence/current-basis searches), `selden-fr-acting`
(1936-1993 FR pages of named PLOs, proclamations and agency documents), `selden-statutes` (Statutes at Large on
govinfo for statutes named or relied on). Draw the 30-order proof at random from an operational census population
(ending step open, own official text held, status or dated history held; 5,662 orders) and report the 21 known
Herschel sole-blocker orders separately.

## Q2. EO acting instruments without an official text

1,386 acting instruments are executive orders the project holds only as a transcription or not at all. That is
the order-originals lane (Mabillon). **Default:** Selden does not fetch them; the ranked table marks them
"supplied by the originals lane".

## Answers
