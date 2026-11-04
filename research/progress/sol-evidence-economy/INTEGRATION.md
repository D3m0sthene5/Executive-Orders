# Landing after the active wave

Leave this work and PR132/133 unmerged during the active run. This branch is a
stack on PR133, not a replacement for either existing draft. It does not include
the PR132 runtime; the retained rehearsal demonstrates the combination.

1. Check actual current main, final production checker changes, and heads of
   PR132/133. Preserve the running wave and all its packets/reviews. Do not use a
   quiet branch or workflow list to infer completion.
2. Combine approved PR132, PR133 and this branch in an isolated checkout after
   the wave. Append-only Kean entries are unioned by id/revision, then regenerate
   the brief; preserve dedicated notes and handoffs. The only workflow change adds the unchanged Stage19 validator to the
   read-only Geddes lint checkout; the production runner workflow is unchanged. Any runner certificate affected by code must be re-established normally.
3. The rehearsal applies [PR132_RUNTIME.patch](integration/PR132_RUNTIME.patch)
   from main600ae301 to PR132 bd066444 onto local candidate94d3f319. Preserve both
   `prepare --history-bundle` and `--research-only`, dispatch-check, all history,
   factual and view handlers. The exact resolution is retained in
   [PR132_CLI_RESOLUTION.patch](integration/PR132_CLI_RESOLUTION.patch). Do not copy
   that old file over a newer implementation. Independent combined pins are in
   [COMBINED_REVIEW.json](engineering-review/COMBINED_REVIEW.json).
4. Rerun the combined claim-kit/Geddes/Norton checks, dispatch refusal checks,
   native partial replay, real bounded history packet and fresh source/fingerprint
   checks against the actual final tree. Recheck platform portability. Prior pins
   describe their exact trees only; changed dependencies require fresh review.
5. Rebuild the relevant production dossiers and prepare **new** packets after
   engineering landing. Use existing readiness/source-supplement/checkpoint tools;
   obtain missing raw bytes through validated acquisition requests before launch.
   Re-run dispatch immediately before assigning a model. Never renew an old
   packet's hashes to make it usable on new code.
6. For EO13792, continue from the retained checkpoint and five exact request
   proposals, preserving existing queue membership. Register acquired exact
   sources, obtain fresh factual answer/application review, and then decide what
   legal-effect/receipt/version questions remain. A new whole-case correction
   needs full review, controls and existing owner acceptance. Historical Valla
   reviews do not cover the new candidate. The proposed legal interval contract
   is a separate scientific decision; it does not gate engineering use of scoped
   observations.

Useful branch commands (ordinary Python, not `python -I`, for sibling imports):

```sh
python3 jobs/claim-kit/kit.py prepare EO:13934 --agent NAME --history-bundle research/progress/maitland/native/BUNDLE.json --write research/production/NEW_PACKET
python3 jobs/claim-kit/kit.py views research/production/NEW_PACKET EO:13934 --slim --write-dir research/production/NEW_VIEWS
python3 jobs/claim-kit/kit.py factual-at research/production/NEW_PACKET --order EO:13934 --on 2017-12-15
python3 jobs/claim-kit/kit.py blind-verify --card EXACT_BLINDED_CARD.json --source-root REPO --allow-source-root REPO/DECLARED_SOURCE_TREE
python3 research/progress/sol-evidence-economy/intervals/native_partial_replay.py
```

After PR132 integration a blocked normal preparation exits nonzero; use its
explicit `--research-only` only to export blocked research, not approve dispatch.
The factual query reports only reviewed interval observations actually present;
an empty list supplies no finding. Run the blind check on the actual blinded
variants with exact card pins, never genuine counterparts or a control key.

Publication maps the local candidate to an identical Git tree through GitHub's
commit API. [LOCAL_CANDIDATE_COMMIT.txt](integration/LOCAL_CANDIDATE_COMMIT.txt)
preserves the original commit object, so its reviewed hash can be reconstructed
with `git hash-object -t commit -w` once the published tree and parent are present.
The remote commit id may differ due to API author/time metadata; exact reviewed
source hashes and tree identity are the acceptance condition, not inferred labels.
