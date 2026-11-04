# Valla materialization certificate: re-established for the integrated implementation

Run-jobs run 41822603367 on integration head a19982c2 rejected all seven results as stale. The selector
had put Valla on the full-repository compatibility fallback (`"valla": "audited_version_changed"`) because
PR133 changed `jobs/valla/valla.py`, so the certificate in `.github/scripts/materialization_certificates.json`
(07fef593…, which still matches main) no longer covered the implementation. On that fallback Valla's input
capture includes untracked files in the whole working tree. Claim-checker ran first in the same run and wrote
175 `.job-cache/claim-checker/text/*.json` files, which are not in `.gitignore`. They were captured as Valla
inputs and are absent from the branch tree, so the freshness check reported `inputs_changed`.

## Audit of the change the certificate must cover

The certificate scope (`VALLA_CERTIFICATE_ROOTS`: jobs/valla, jobs/_lib, the materializer, freshness and
runner scripts, run-jobs.yml) differs between main 600ae301 and a19982c2 only in:

- `jobs/valla/valla.py`: `confirmed_findings` adds `instrument_id` (read from the record it has already
  opened) to each refused-review entry, and `attach` copies `index['refused_method_reviews']` into the packet
  context. No new file, path field, glob or pointer is read.
- `jobs/valla/test_valla.py` (tests) and `jobs/valla/README.md` (documentation).

The read closure is unchanged, so the audited narrow materialization still covers this implementation. The
certificate is set to `valla_signature('HEAD')` of the integrated tree:
`4fadcea3dd67ec179fe962123836962daa56005e31d7c51b4c4b2f59b44f4766`. Packets and reviews were not re-hashed;
they keep their own freshness checks.

## Left open

The fallback route itself still fails whenever an earlier job in the same run writes `.job-cache/` while Valla
runs uncertified. That is a runner defect (`.job-cache/` is not ignored, while the runner's own tests assume it
is), recorded as a Kean finding rather than changed here.
