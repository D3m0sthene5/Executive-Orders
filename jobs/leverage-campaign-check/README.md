# Bounded offline campaign verification

One-off validation of the October 22 leverage campaign through the existing job
runner. This is not a research producer or an acquisition job. Run only this job
to avoid the normal consumer closure launching Lewis/Clark acquisition work.

The job copies the materialized repository inputs into a disposable hard-linked
view inside OUTPUT_DIR, removes that view's generated directories before writing,
and executes the actual NORTON, claim-kit, checker, tracker and Polya entry points with downloads
disabled. All canonical repository inputs and outputs remain unchanged. The
claim-kit job performs its exact 3,403-member post-build population audit. The
tracker consumes the checker output from the same isolated execution. Polya then
consumes that exact tracker and regenerated claim-kit generation.

Results include command receipts, failures, source/input commit, measured machine
wall time, complete checker/tracker reports, claim-kit population/index/summary
and the bounded diagnostic dossiers. The other generated dossiers are verified
by the population audit, then discarded to avoid a second corpus-sized archive.
No legal claims, approvals, status adoptions or verified savings are produced.

Run: `Run jobs` workflow, input `leverage-campaign-check`. An output-only result
commit will not trigger any additional consumers. A successful validation is not
a canonical claim-kit publication; after integration explicitly run `claim-kit`
and inspect its own receipt before using newly generated dossiers for production.
