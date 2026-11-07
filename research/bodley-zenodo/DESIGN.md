# Bodley: design of the first public data release (Zenodo version 1)

Named for Thomas Bodley, who refounded Oxford's library and arranged that a copy of every registered book reach it.
Status: **design and drafts only.** Nothing is published, no Zenodo account or deposit exists, no record was changed.
Measured at commit `e146fa4b268b5f42c18226969c48329fa1d3d441` of `origin/main` (2026-11-06); every count below is
that commit's and is re-measured by `build_release.py` at the commit that is actually released.

## 1. What version 1 is

A citable, immutable snapshot of the project's data tables, labelled for what they are: **provisional, AI-produced,
uncertified working data.** It is not a survival rate, not a legal finding and not a certified history of any order.

**Certified = 0, and the release says so in five places.** The human-certified whole-lifecycle count is 0 of the census
(README.md of the repository; the readiness tracker does not count certification at all). The release labels this by:
(1) the first paragraph of the Zenodo description and of the release `README.md`; (2) a `human_certified` column set to
`no` on every row of `filed_claims_index.csv` and `provisional_status_ledger.csv`; (3) `human_certified_whole_lifecycle: 0`
in `MANIFEST.json`; (4) a `status_evidence_tier` column (S1 to S5, section 3) on the ledger; (5) the file-level tier label
in `CONTENTS.csv` and the release README. The tracker's `ready_for_human_review` (1,185 of 14,998 at this commit) is
described everywhere as "machine steps finished; a human has not yet reviewed it", never as "verified".

## 2. Contents (33 files; measured 21.8 MiB built, about 26.9 MiB with the three pending items)

Full list with source paths, sizes and reasons: `CONTENTS.csv`. Summary:

| Group | Files | Tier label | Notes |
|---|---|---|---|
| Census | `census_identity_layer.csv` (14,998 rows), admissions, candidates not in census, register summary | bibliographic identities; authentication **unadjudicated** | one row per working identity; the census is a bibliography, not the national universe |
| Order register | `order_register.csv` | what is held, not what is true | number, date, title, president, best document class held (official original 8,945; transcription only 2,906; archival replica scan 2,746; official found, page check pending 285; nothing 90), blockers. Operational columns (next actions, web-lead scores) dropped |
| Provisional statuses | `provisional_status_ledger.csv` (4,298 rows: 3,893 no, 405 yes) | **provisional, AI-reviewed, uncertified** | with `decision_origin` and the derived `status_evidence_tier` |
| Readiness | `readiness_by_order.csv`, summary, status, tracker, contested | machine readiness | `text_evidence_tier` per order (original_supported / transcription_dependent / missing); `generation_id` pins the run |
| Filed claims | `filed_claims.jsonl.gz`, `filed_claims_index.csv`, `claim_source_refs.csv.gz` | **filed claims: AI-produced, gate-checked, not human-certified** | 1,527 orders (latest claim per order; 205 older lines superseded); 20,404 source references; verbatim text replaced by hash and length |
| Hash manifests | `source_manifest.csv.gz` (21,288 sources), `official_fixity.csv`, `pergamon_manifest.csv.gz` (pending) | custody metadata | URL, SHA-256, bytes, retrieval time, route; GPO preservation-record matches |
| Estimate | `sample_estimate/` | **provisional, n=120** | the stratified-sample estimate with interval and nonresponse sensitivity |
| Codebook | `codebook/` | frozen v2.0.0 | the immutable evidence and legal codebook, with its recovery record |
| Methods and code | `methods/methods_documents.zip`, `code/` | methods | claim schema, estimand, readiness procedure, 19 owner rulings, tracker and checker documentation, the producing code, and `build_release.py` |
| Prior art | `prior_art_crosswalk.csv` (pending) | leads | crosswalk to Thrower (doi:10.7910/DVN/LZGQOH) and Lowande-Poznansky (doi:10.7910/DVN/TZ2QKY); produced by the prior-art stream, not on `main` yet |

### Status evidence tiers (derived column on the ledger)

Taken mechanically from `decision_origin`; they describe how the label was produced, never whether it is right.

| Tier | Orders | Meaning |
|---|---:|---|
| S1 inherited legacy v2 AI label | 2,515 | Stage 17 inherited label; its `decision_origin` names no review |
| S2 AI label, Opus overlay | 844 | Opus checkpoint 2 (540) and complete-addition (304) decisions |
| S3 AI class status, sampled independent AI review | 888 | Jacquard classes: separate-context Claude reviewers with planted controls, sampled adoption under the 2026-10-31 ruling |
| S4 AI proposal, adopted after independent review | 44 | Sinclair (29, cross-family GPT review) and Bowditch (15, Opus re-review), owner-adopted under the 2026-10-21 ruling |
| S5 AI sample probe | 7 | Dorotheus sample probe |

The 405 "yes" statuses and 3,893 "no" statuses cover 4,298 of 14,998 orders. The other 10,700 have no status. The
researched orders were not drawn at random (S1 is a legacy selection), so the counts are not an estimate of anything;
the only design-based estimate is the n=120 sample, whose own file warns that only 19 of 120 orders responded.

## 3. What it deliberately excludes

- **Licensed text.** No ProQuest scans, OCR or page images (the repository's `ProQuest Pre-1937 Orders/` folder and
  `pinakes-proquest-ingest` texts); nothing from Westlaw, Lexis or HeinOnline (the project never automated those).
- **Bulk source bytes.** No PDF, image, archive, raw page or full-text source (`texts/`, `blobs/`, `raw/`). Sources are
  cited by URL and SHA-256 in the manifests.
- **Verbatim quotations.** In the filed claims every `quote`, `excerpt`, `original_operative_text`, `before_text`,
  `after_text`, `source_context` and `quoted_parts` value is replaced by `<key>_sha256` and `<key>_len`; `char_start`,
  `char_end`, `text_sha256` and the source hash stay. This is the cautious v1 rule: 76.8 MB of the 115.8 MB of raw claim
  lines is quotation text, drawn from sources of every class (official prints, compilations such as APP and Wikisource, ProQuest scans). Version 1.1 could
  restore quotations for sources that are official US Government publications (decision D5) once the byte store exists.
  The authored fields (`research_rationale`, `judgment_reason`, `reason`) remain and may quote a short fragment.
- **Sealed blind-review answer keys** (Stage 12, 13, 15; kept out of the public repository by the releases README).
- **The Stage 12-17 internal release archives** (about 140 MB of chunked archives, including the Stage 17 SQLite). They are
  superseded by the tables above; `research/releases/RELEASES_MANIFEST.json` records their hashes.
- **Anything human-uncertified presented as certified.** There is no column, file or sentence in the release that
  says certified except to say it is 0. The script has no code path that writes `human_certified` other than `no`.
- **Credentials and personal data.** None are read by the build. `CODEBOOK_PROVENANCE.json` contains a historical local
  path of the original Codex session (`/Users/danielkind/...`); the owner may drop that one file (decision D7).

## 4. Versioning plan

Zenodo facts (verified, section 8): each first publication registers a version DOI and a concept DOI; the concept DOI
resolves to the latest version; a new version is a separate record with its own metadata, files and DOI; after
publication files and the DOI cannot be changed except for minor fixes within 30 days (or justified cases), metadata can.

- **One Zenodo version per stage release.** Version 1 is "Bodley 1.0.0". A later stage release is 1.1.0 (same schema,
  more orders or sources) or 2.0.0 (a table's meaning or columns change). The version string is in `.zenodo.json`,
  `CITATION.cff` and `MANIFEST.json`.
- **Cite the concept DOI** for "the Bodley dataset" in general; the law review cites the **version DOI** of the version it
  used (Zenodo's own guidance is to use the version DOI by default so readers get the exact artifact). Both go in
  the article's data-availability note.
- **Each version is a full rebuild** from one pinned commit (`MANIFEST.json` carries `source_commit` and the tracker's
  `generation_id`); files are re-uploaded, not imported, because derived tables change. Zenodo links versions
  automatically (`isNewVersionOf`), so none is written by hand.
- **Never edit published files.** Treat the 30-day correction window as an emergency exception. The release gate is
  `SHA256SUMS` checked after upload; a correction ships as a new version with a line in `RELEASE_NOTES.md`.
- **Pin every table to one run.** `build_release.py` refuses to build when the census, the register and the tracker
  describe different orders. At this commit that gate fires: the register has 14,972 rows, the census and tracker
  14,998 (27 admitted orders absent, one renamed id, EO:7933a/EO:7933A). The daily register job must run after the
  admissions before release; `--allow-stale-register` exists but its use must be disclosed in `RELEASE_NOTES.md`.

## 5. How a reader re-verifies every span

1. Open `claim_source_refs.csv.gz`; a row gives the order, the claim's fingerprint, the source `url` and `sha256`, the
   `text_sha256` of the extracted text, the span `char_start`/`char_end`, and `quote_sha256`/`quote_len`.
2. Look the source `sha256` up in `source_manifest.csv.gz` (URL, bytes, retrieval time, route) and in
   `pergamon_manifest.csv.gz` (where the project's byte store keeps those bytes). Fetch the bytes from the store, or
   download the `url` and check that the bytes hash to `sha256`. A source whose bytes do not hash to the recorded value
   is a failed re-verification, not a variant.
3. Extract the text the project extracted (code in `code/`); check its SHA-256 equals `text_sha256`.
4. Take the Unicode slice `[char_start:char_end]` of the text; its SHA-256 must equal `quote_sha256` and its length
   `quote_len`.
5. `filed_claims_index.csv` gives the claim fingerprint (the project's own `claim_gate.claim_sha`, computed on the
   unstripped claim); the unstripped line is at `claim_file`:`claim_line` in the GitHub repository at `source_commit`.

Tested here on a sample: for 72 references from `claude-2026-10-28-production-b1a.jsonl`, the text hash matched and the
slice equalled the stored quotation in all 72 (UTF-8 text, Python string indices). Coverage of the manifests, measured
by the build: 1,705 of the 1,732 distinct source hashes cited by filed claims are in `source_manifest.csv.gz`; the 27
missing include 30 references graded `archival_replica_scan_pending_codebook` (ProQuest-derived, custody held outside
this release). These are listed, not hidden: `cited_by_a_filed_claim` marks the covered ones. `text_sha256` values are
hashes of project-extracted text and appear in the claims, not in the source manifest.

The **Pergamon byte store** (built in this campaign) is the intended home for the bytes behind those hashes. Version 1
ships its hash manifest, not its bytes: the store is large, mixes public-domain official sources with mirrors, and
Zenodo allows 100 files per record (bytes would have to be zipped). Whether a public-domain subset gets its own record
is decision D6.

## 6. Publication route (decision D3)

- **A. Manual or API deposit (recommended).** Run `build_release.py --build`, check `SHA256SUMS`, upload the folder to a
  draft, paste or POST `.zenodo.json` (the REST API wraps it as `{"metadata": ...}`), have the owner publish. No code
  runs on a schedule; each version is a deliberate act.
- **B. A small dedicated release repository with the GitHub integration enabled.** Each GitHub release then makes a
  new Zenodo version and the metadata comes from `.zenodo.json` (which wins over `CITATION.cff` if both exist). The
  repository would hold the built folder (about 22 MiB). This automates versions but is easy to trigger by accident.
- **C. Enable the integration on `Executive-Orders` itself (not recommended).** What Zenodo archives is the release's
  source archive of the whole repository (about 9 GB of history and, by default, only pointers for Git LFS objects);
  Zenodo's pages do not say what size the integration accepts, and the archive would mix bulk sources and licensed
  files into a public citable record. It would defeat the exclusions in section 3.

## 7. Open items and limits

- **Pending inputs:** `pergamon_manifest.csv.gz` (this campaign), `prior_art_crosswalk.csv` (enc/prior-art),
  `unnumbered_summary.json` (`jobs/domesday-register/output/UNNUMBERED_SUMMARY.json` is not on `main`). The dry run
  lists them as not yet buildable.
- **Numbers in the drafts** (14,998 identities, 1,527 claims, 4,298 statuses) are from the pinned commit and must be
  refreshed from `MANIFEST.json` at release time.
- **Generated files** (`README.md`, `RELEASE_NOTES.md`, licence texts) are written after the owner decides the licences
  and are not produced by the outline script.
- **Schema validation:** `CITATION.cff` validates with cffconvert 2.0.0 (CFF 1.2.0; it caught a wrong `type` in my first
  draft). Zenodo publishes no `.zenodo.json` schema, so `.zenodo.json` is validated against a local schema written
  from the developer documentation; the real test is a Zenodo sandbox deposit by the owner (decision D8).
- The ledger `title` and `president` fields come from "the best index the project has", some of which are compilations;
  they are facts about public documents, but the owner should confirm that is acceptable (D5).

## 8. Zenodo rules verified for this design (read on 2026-11-06)

| Topic | What the pages say | Page |
|---|---|---|
| New version | A new version is "a completely new record with separate metadata, files and persistent identifier"; "Import files" brings files from the previous version | https://help.zenodo.org/docs/deposit/manage-versions/ , https://help.zenodo.org/docs/deposit/about-records/ |
| Concept DOI | Two DOIs on first publication: one for the version, one for all versions; the concept DOI resolves to the latest version; use the version DOI in citations by default | https://zenodo.org/help/versioning , https://support.zenodo.org/help/en-gb/1-upload-deposit/97-what-is-doi-versioning |
| After publication | Metadata can be edited; "Files and the persistent identifier CANNOT be modified"; minor file corrections within 30 days; later only in justified cases (copyright, personal data) | https://help.zenodo.org/docs/deposit/about-records/ , https://help.zenodo.org/docs/deposit/manage-files/ |
| Limits | Up to 100 files and 50 GB per record; extra 150 GB allowance, up to 200 GB, by "Manage storage"; 20+ files should be zipped | https://help.zenodo.org/docs/deposit/manage-files/ , https://help.zenodo.org/docs/deposit/manage-quota/ |
| GitHub integration | Enable per repository (Profile, GitHub, Sync now, toggle); new releases "will be automatically ingested and archived"; GitHub states a new DOI is issued for each release | https://help.zenodo.org/docs/github/enable-repository/ , https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content |
| Metadata files | Zenodo reads `CITATION.cff` and `.zenodo.json` for GitHub releases; if both exist only `.zenodo.json` is used; CITATION.cff support is a subset (no references, funding or communities); cffconvert is the suggested validator | https://help.zenodo.org/docs/github/describe-software/ , https://help.zenodo.org/docs/github/describe-software/citation-file/ , .../zenodo-json/ |
| `.zenodo.json` fields | creators (name "Family, Given", affiliation, orcid), title, version, access_right, related_identifiers (identifier, relation, resource_type), keywords, license, upload_type, language, grants, communities | https://help.zenodo.org/docs/github/describe-software/zenodo-json/ , https://developers.zenodo.org/ |
| Licences | The licence field is required; default CC-BY-4.0 in the web form (cc-zero is the REST default for datasets); SPDX list searchable; custom licences allowed; vocabulary ids checked: `cc0-1.0`, `cc-by-4.0`, `apache-2.0` | https://help.zenodo.org/docs/deposit/describe-records/licenses/ , https://zenodo.org/api/vocabularies/licenses |
| Access and embargo | Metadata always public; files public or restricted; embargo: restrict files, set "Embargo until" date, files become public at midnight UTC that day; REST `access_right` is open, embargoed, restricted or closed | https://help.zenodo.org/docs/deposit/create-new-upload/ , https://developers.zenodo.org/ |

Not found on the pages read (so not relied on): a maximum embargo length; what exactly the GitHub integration archives
(the release source archive is the common understanding; GitHub documents that its archives carry only LFS pointers by
default: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-git-lfs-objects-in-archives-of-your-repository);
a size limit for the integration; whether a published version can be deleted. The earlier survey note that the concept
DOI was unverified is now settled by the Zenodo versioning page above.

Prior datasets (checked via DataCite and Crossref): Thrower's replication data, v1.1, carries "custom terms specific to
this dataset" on Harvard Dataverse, so it is cited and crosswalked, never redistributed. Lowande's replication data,
v1.0, is CC0 1.0. Articles: Thrower (2017) AJPS 61, doi:10.1111/ajps.12294; Lowande and Poznansky, "Executive action
that lasts", Journal of Public Policy 44(2), 2024, doi:10.1017/S0143814X23000442.
