# Bounded reinstatement lead handoff repair

Base: `600ae3018f71025b3e53dc8538b8f92e6e159b76`. Work occurred only in the
isolated Maitland checkout. No Git/network mutation, job launch, active production
branch change, canonical claim/status write, source-grade change or scientific
approval was performed by this worker. Tokens, cash and full active labor are
unknown; measured command wall times are in `tests.json`.

## Reproduced defect

`before.json` records the actual pre-edit excavator result on five held official-PDF
text layers and their SHA-256 hashes. In EO 14189, claim-kit located only the
EO 13934 amendment. The existing later-events detector already located three
reinstatement candidates (EOs 13933, 13934 and 13978), plus that amendment.

The omissions were demonstrated in code: CHANGE and its verb normalization lacked
reinstatement; agent overrides had no `reinstate` vocabulary; the chain excludes
unclassified `other` records. An additional first-candidate/one-result-per-target
path would have hidden the EO 13934 amendment after merely adding reinstatement.
The chain's `other` refusal remains in place; recognized `reinstate` leads now pass
through it.

## Repair

- `jobs/claim-kit/excavate.py`: plural acting-provision extraction and discovery;
  existing later-events sentence binding for reinstatement, including negation,
  exact suffix identity, partial qualifiers and earlier-revoker citations. Reuses
  `scan_sentence` and `is_partial`; no second reinstatement grammar was created.
  Independent engineering review caught an introduced regression where delegation
  dropped a transfer in a different clause of a mixed sentence. The bounded repair
  preserves the existing transfer extraction only inside a separately joined
  clause that explicitly names this target and contains no other change verb.
  Mixed clauses are scanned separately so the transfer's target also cannot
  inherit the reinstatement. Bounded joins support semicolons and conjunctions
  before an explicit order/functions reference or active transfer predicate;
  a join requires an action before it, preserving coordinated target lists.
  The former singular API remains an explicit first-record compatibility view.
- The compiler already retains exact alternatives in ACTING_REPRESENTATIONS,
  `alternative_provisions` and dossier evidence. The chain now expands those
  alternatives and deduplicates identical actor/source/span/verb/scope records.
  Different source artifacts remain distinct evidence leads. No dossier/schema
  or batch/kit interface was changed by this worker.
- `jobs/claim-kit/act_overrides.py`: adds `reinstate` to the accepted operation
  vocabulary. Every exact-span, source/hash, census, missing-pair, independent
  review, D6 and reviewed-record equality check remains unchanged.
- Reused parser bytes enter the existing persistent-parser cache fingerprint.
  Root integration owns the external parser dependency and compiler-code manifest
  wiring; that wiring must accompany this patch.

`after.json` and `replay.py` retain the exact held-source replay. EO 14189 now
supplies four source-bound operations: EO 13933 reinstatement (whole lead), EO 13934
reinstatement (whole lead), EO 13934 amendment (partial lead), and EO 13978
reinstatement (whole lead). The quoted historical restoration wording is preserved.
The earlier revoker, EO 14029, is a citation rather than a reinstatement target.
All four effective dates remain unasserted (`null`).

The held EO 13933/13934/13978 own-term results are unchanged byte-for-byte as JSON
values. In particular EO 13933's section 5 six-month wording remains a fixed-term
lead, not a newly restarted obligation. A separate dated regression preserves
the original `2020-12-26` computed-end candidate when a 2025 reinstatement is
discovered. This candidate is not an adopted legal cessation date.

## Checks and limits

Retained final focused receipts: 136 tests, 133 successful and 3 disclosed sparse
held-text skips. The suites are 13 reinstatement/transport tests, 19 override tests,
29 excavator tests, 18 build tests, 5 preflight-dependency tests, and 52 existing
later-events tests. Their command
outputs and wall times are in the adjacent logs and `tests.json`. New tests include
an actual ephemeral compiler/dossier replay preserving both operations; no claims
are emitted. Refusal coverage includes negation, construed revival, historical
descriptors, generic unnamed orders, suffix mismatches, earlier-revoker citations,
post-review verb mutation and absent independent review. The added mixed-transfer
regression covers distinct targets, bare/comma conjunctions, reversed clauses,
active and negative transfer, two different operations against the same target,
and coordinated/suffixed target lists, with exact source spans.

An initial attempted full existing later-events suite ran 52 tests and failed 19 setup
operations because its sparse fixture directory was absent (catalog_page.json
and order_text.txt); this is not counted as a passing suite. The other 33 tests
completed without error. After root materialized those unchanged fixtures, the
final retained rerun passes all 52 existing tests.

This is bounded lead transport, not a general parser-completeness claim. Existing
non-reinstatement target binding can still misread historical citations: before
this patch EO 14029 already labeled its EO 14003 historical citation as a
revocation. Plural extraction additionally retains its later actual amendment;
the preexisting false revocation lead is not silently adjudicated here. Multiline
governing lists and all possible compound/active formulations have not received
a corpus-wide recall study. Parent-as-amended reach remains an unconfirmed lead.

Restoration of historical wording does not itself determine operative legal
effect, expiry, exhausted duties, events within the revoked interval, prospective
operation or original authentication. No event here resets a date or duration,
erases a gap, supplies legal review, changes source qualification, or adopts a
status. Source grades, review gates and human certification are unchanged.
