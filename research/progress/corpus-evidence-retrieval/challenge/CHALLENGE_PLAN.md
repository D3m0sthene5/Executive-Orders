# Independent engineering challenge plan

Frozen main baseline: f9c6d806ad059dcad7875ab3708715f20ea386df. Frozen Cruden SHA256: 075ab70f7b312a9b87a106f279502dfd695da0dcaddff49f1eae6bbae9170867.

This is separate-context, same OpenAI-family AI engineering review. It establishes neither legal review nor corpus completeness. Only this challenge directory is owned by this worker; all fixture corpus writes use temporary directories outside the repository. No source edits, Git mutations, source acquisition, legal/canonical artifact changes or PR104 cache work.

## Frozen baseline checks

`fixture_challenge.py` imports the actual candidate module, supplies minimal native register/WPA/APP files and packet members, and invokes its native `lookups` function. Baseline run: nine checks passed. The harness compares existing member fields, allows additional metadata, and records exact candidate hash. Deliberately changed matching semantics must be reviewed individually rather than treating an equivalence failure as automatically acceptable.

- Base EO6242 and suffix C/D distinctions, spaces, hyphens and line breaks.
- 3 F.R.1234 near EO6242 must not become EO1234 evidence.
- Identical text at distinct paths retains both representations, without claiming independent evidence.
- Own text is excluded from other-text citations, and clause-drafts remains excluded.
- Neighboring EO9999 text remains available with the source; citation lookup never assigns its revocation to EO6242.
- Unanchored numbers and absent EO7777 remain empty bounded searches.
- Deliberate baseline gaps are visible: plural `Nos.`/list continuation and code-name phrase lacking `the`. These are not silently accepted as corpus-negative conclusions.

## Final candidate challenges

1. Read exact final code and its cache/schema version; rerun native output compatibility and compare hashes before and after review.
2. Add a file, delete a file, and replace a file with different same-length bytes while restoring mtime. Every verification must detect actual corpus change; stale results must never appear verified.
3. Construction-time change: mutate an already-read file and add/delete a path while construction proceeds. A finished index must correspond to an actually revalidated byte snapshot or clearly refuse/retry construction.
4. Inject unreadability deterministically because this container can run as root. Verify both failed paths and error reasons are preserved, coverage is qualified, and an empty result cannot imply whole-corpus absence.
5. Create over 40 number-bearing and over 60 code-bearing files. Check stable legacy limits plus actual totals, truncation disclosures and omitted-result access; metadata must distinguish documents from occurrences.
6. Rehash source bytes independently, reopen full text using the documented decoding/newline rule, and verify every returned start/end identifies its quoted match. Include CRLF and invalid UTF-8 to test normalization qualifications. Every source must retain full-text access and raw-byte hash; context alone is not complete source access.
7. Search compatibility: native regex command retains case-insensitive matching and first-three-per-pattern-per-file behavior, including patterns that cannot use token prefilters.
8. Corrupt/delete the index or mismatch its semantic/schema version. Rebuild/refusal must preserve explicit coverage and source-byte verification. Exercise validly structured payload corruption too: replace a stored text/match and remove a posting while leaving original source bytes and timestamps untouched. Source snapshot keys alone do not establish correctness of cached derived payloads. Minimal accidental-corruption contract verifies a deterministic digest of the entire cached source inventory, algorithm/schema and derived payload on every load, then rebuilds/refuses on mismatch. Checking returned matches alone misses corrupted omissions. A self-contained digest does not claim protection against coordinated malicious rewriting of both cache and digest.
9. Existing member contexts and counts remain exact for fixed input bytes; any improved full-match end offsets are separate additive metadata, not changes to preserved legacy context rendering.

## Limits and costs

Corpus scope is held `jobs/*/output/texts/**/*.txt`, excluding clause-drafts. Sparse checkout reports 810 tracked notes/reports absent; this worker performs no widening and makes no missing-corpus inference. Temp fixtures validate mechanics, not real OCR identity or legal effects. First prospective clock is in CLOCK.json; setup before that clock was not timed. Exact model identifier, tokens, cache tokens, cash and active labor are unavailable. Parent coordinator owns consolidated Kean/handoff/commit recording and any broader live-corpus result.
