# m001: first 50 original-page checks

**Result:** 50 distinct current `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` targets reviewed
by two independent blind contexts after planted controls; 34 pass, 16 fail,
0 unsure, 0 invalid records. `jobs/montfaucon-page-check/job.py` produces 34
derived official fragments and zero replica fragments from these records.
`page_check.assemble` accepts all 50 with zero rejections. This is original
source-location credit, not clean OCR, human certification or a claim finding.

| Source family | Checked | Pass | Fail | Scan SHA-256 |
|---|---:|---:|---:|---|
| Federal Register, July 30 and November 13, 1940 | 9 | 0 | 9 | July `8d63d841…`; November `ba20ff24…` |
| GPO Indian Reservations 1912 | 14 | 14 | 0 | `33e2e606…` |
| GPO Panama Canal 1922 | 13 | 12 | 1 | `01bc3ea7…` |
| GPO Trading with the Enemy Act 1920 | 14 | 8 | 6 | `ba9d0fee…` |

All 34 passes were open on the baseline tracker `original_text` step. Nine
have a provisional status but still have independent lifecycle blockers;
25 lack a provisional status. Therefore **no immediate ready-count increase
is asserted**. The tracker must rerun on main after integration to establish
the actual delta. Every source fragment and held text remains unchanged. The
records retain OCR repairs as review observations; they do not silently fix
the machine transcription. In particular, Indian EO:1517 prints **April 13,
1912** in both the GPO book and WPA list, while its held filename/header says
April 18. The source fragment's signing date is month-only.

## Passing orders

- Indian Reservations: EO:324A, 344B, 744, 1000, 1224, 1359, 1379, 1416,
  1426, 1477, 1480, 1496, 1517, 1538. The GPO book prints no EO numbers;
  both readers checked the relevant printed WPA numbered-list row. Twelve
  page images from that list are retained with hashes as a separate identity
  crosswalk. EO:1496's section 33, township 11 south, range 34 east fraction
  was adjudicated from a high-resolution GPO crop as **N½ of SE¼**. No land
  passage was omitted after restoring visible OCR glyphs.
- Panama Canal: EO:1410, 1792, 1810, 1832, 1989, 2019, 2118, 2152, 2451,
  2475, 2907, 3585. EO:2907's cited two leaves include an extra preceding
  leaf; its full target is on PDF 242. EO:2152's source itself has the
  inconsistent second spelling “Beveley's,” which the held OCR preserves.
- Trading with the Enemy Act: EO:2832, 2846, 2847, 2857, 2956, 2958,
  2959, 2968. EO:2857's citation includes an extra neighboring leaf; its
  full target is on PDF 52. The numerical recognitions `(8)` for printed
  `(3)` in EO:2956 and `SO` for printed `30` in EO:2968 are documented OCR
  repairs, not unexamined substantive substitutions.

## Failed held/cited spans

| Order | Actual complete PDF / printed pages | Why the held citation fails |
|---|---|---|
| 8494 | 5–6 / 5 FR 2681–2682 | Held/cited 1–5 stop mid-sentence; page 6 has remainder and closing. |
| 8495, 8496 | 6 / 5 FR 2682 | Held/cited 1–5 omit each entire numbered order. |
| 8586 | 4–5 / 5 FR 4444–4445 | Held/cited 1–2 contain proclamations, no order. |
| 8587 | 5–8 / 5 FR 4445–4448 | Held/cited 1–2 omit the entire civil-service order. |
| 8588 | 8–9 / 5 FR 4448–4449 | Held/cited 1–2 omit the entire transportation order. |
| 8589 | 9 / 5 FR 4449 | Held/cited 1–2 omit the Payette River order. |
| 8590 | 9–10 / 5 FR 4449–4450 | Held/cited 1–2 omit the entire Selective Service order. |
| 8591 | 10 / 5 FR 4450 | Held/cited 1–2 omit the Arkansas land order. |
| 3130 | 254–256 / Panama printed 252–254 | Held/cited 255–256 begin mid-boundary; paragraph 1 and paragraph 2 opening are on 254. |
| 2813 | 42–47 / Trading printed 37–42 | Held/cited 43–44 contain only interior sections, missing opening and closing. |
| 2844 | 50–51 / Trading printed 45–46 | Held/cited 49–50 omit sale terms, reasons and closing on 51. |
| 2916 | 59–64 / Trading printed 54–59 | Held/cited 60–61 begin mid-item 1 and end mid-item 5. |
| 2953 | 66–68 / Trading printed 61–63 | Held/cited 66–67 stop before reasons and closing. |
| 2955 | 70–71 / Trading printed 65–66 | Held/cited 69–70 omit four reasons and closing. |
| 2991 | 73–76 / Trading printed 68–71 | Held/cited 74–75 begin definition 2 and end mid-item 4. |

The 193 Cujas Photius-stale IDs have zero overlap with these 50 records.
The separate ten rank-13 replica outcomes are carried forward in
`REPLICA_CARRY_FORWARD.md`; none passed, and no restricted ProQuest directory
was opened. The full per-order review text, page hashes and source URLs are
in `checks/m001-*.jsonl`.
