# Pothier: questions for the night-wave coordinator

Session Pothier, branch `claude/pothier-family-doctrine`. Each question states the default I am working on.

## Q1. Lane boundary for sources (Pothier vs Selden)

Doctrines need two kinds of source not yet held: (a) **class-wide law** (statutes, reorganization plans, blanket
orders, current regulations that apply to a whole family, e.g. FLPMA sec. 701/704, the Indian Reorganization Act sec.
2, the Act of March 3, 1927 sec. 4, the joint resolution of March 3, 1921) and agency **class records** (the Forest
Service chronology of national forest proclamations and orders, BLM withdrawal records, the Fish and Wildlife Service
lands report); (b) the **per-order acting instruments** (a Public Land Order naming one order).

*Default:* Pothier fetches (a) through its own bounded step (`jobs/pothier/fetch.py`, GitHub Actions only, at most
120 URLs, custody copies in `jobs/pothier/output/sources/`) and lists (b) for Selden in
`research/pothier/FOR_SELDEN.csv` without fetching it. Before fetching I skip any URL on Ptolemy's list.

## Q2. How a family doctrine is adopted

*Default:* one Kean ask per family: "adopt doctrine PD-X as the claim kit's first-step guidance for its members".
Adoption would let a producer cite the doctrine's mechanism and sources, but each order still needs the claim kit's
own decision and review; a lead never becomes a status by adoption alone. A separate later ask may propose
Jacquard-style sampled adoption of the `no` leads of a family whose pilot shows zero misses.

## Q3. Review gating

*Default:* the two blind Opus reviews per doctrine and the 30-member pilots are tool-building review, not production,
so I record `bentham.py gate` results but do not stop on an economic STOP; a planted-control miss sends the doctrine
back (as briefed).

## Q4. Kean brief size

The Kean brief is capped at 8,192 bytes and main was at 7,912 before this session. The eleven per-family adoption
asks would not fit, so they are one ask, A-20261106-pothier, whose lines are listed in research/pothier/REPORT.md
("Owner decisions asked"). After this branch the brief is at 8,181 bytes: the next session to add an ask will need to
shorten entries or the cap will need raising.

*Default:* leave the one consolidated ask; the per-family asks are recorded and withdrawn as merged.

## Q5. For Gratian: the lead format (information, no decision needed)

`jobs/pothier/output/LEADS.jsonl` (schema `pothier-status-lead/v1`), one line per member and doctrine: `instrument_id`,
`doctrine_id`, `doctrine_sha256`, `branch_id`, `status_lead` (`no`/`yes`/`open`), `lead_kind`, `basis_kind`
(`TERM`/`ACT`/`CURRENT`/`NONE`, matching the claim kit's `TERM:`/`ACT:`/`CURRENT:` evidence prefixes), `basis`,
`date` (rule and value or interval), `sources` (citation, held, path, URL), `gaps`, `contradictions`, `history_basis`
(the 2026-11-05 empty-history ruling), `decides`. A lead is never a status; a consumer should show it to a producer as
a starting point and never write it into a status field.

*Default:* Pothier does not touch claim-kit or the tracker; Gratian decides whether and how to surface leads.

## Answers

(empty)
