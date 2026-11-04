# a03 producer report

Start 2026-11-04T04:48:13Z; end 2026-11-04T05:46Z. Final applied directory: applied-v3.

## Outcomes
Submitted (12): EO 9837, 9932 (revoked by EO 12292 sec. 10, effective 1981-02-15); EO 11999, 12025, 12035, 12069 (parent EO 11861 revoked by EO 12076, 1978-08-18); EO 11885 (deleted by EO 11976 sec. 2, 1977-03-11); EO 11898 (parent revoked 1978-08-18); EO 11927 (two clauses: sec. 2 deleted 1977-03-11, sec. 1 until 1978-08-18); EO 11417 and 11841 (parent EO 10973 revoked by EO 12163, effective 1979-10-01); EO 12246 (revoked by EO 12251, 1980-11-15).
Blocked (21): EO 10242, 10708, 10746, 10799, 11189, 11331, 11345, 11371, 11415, 11532, 11860, 11963, 11983, 12022, 12054, 12061, 12090, 12091, 12093, 12151, 12195. Each block names its gap in decisions.csv: inventory overrides not completed, sources identified but not read or written up (this is a time and effort limit, not missing held evidence, for most), and report-relative sunsets whose report dates are not held (12022, 12054, 12061, 12093, 12195 and their amenders). EO 11983 sec. 2 (one-time revocation of EO 11872) was left blocked as untested.

## Time
Most time went to inventory corrections (9932, 11927), the shared EO 11861 chain, a stale-packet restart, and slow apply/batch-check runs (about 2.5 minutes each, Geddes about 2.5 minutes).

## Batch-check (applied-v3)
12 claims checked, 12 strict pass, 0 fail; actual checker 12 of 12 all checks passed; 21 blocked; no actionable failures. Earlier runs: v1 had a Geddes ValueError (held corpus inventory commit changed during search); v2 rejected EO 11417 with working_text:official_copy_available_recheck_required, fixed in v3 by clearing the mirror working_text since the fr-originals text is held.

## Geddes
0 flags, 10 coverage gaps; GEDDES_RESOLUTIONS.json is empty.

## Full-packet files opened beyond views
LOOKUPS.md (head), decisions.csv, clauses.csv, PACKET.json via load_packet.

## Tool defects
Geddes crashed once on v1 ("held corpus inventory commit changed during search") while other producers ran; reran cleanly.
