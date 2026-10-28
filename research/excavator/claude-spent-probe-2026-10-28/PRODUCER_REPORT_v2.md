# Producer report v2: 20-order lifecycle probe (claude, 2026-10-28)

Legal cutoff 2026-10-14. The codebook is unchanged. This is producer work only: there is no independent review, no human certification, and the certified count stays 0. Nothing was committed or pushed.

**Result.** 2 orders submitted (EO 1547 and EO 4782), 18 blocked, 0 unresolved.

**Batch-check passes** (exit 0). Both claims pass the strict check, 2 of 2, and the actual claim-checker, 2 of 2 on all checks, with no mechanical failures.

**Final applied directory:** `packet-v3-supp/applied-v1`.

**Claim sha256 values:**
- EO 1547: `270a0e37…d602`
- EO 4782: `f4221198…031e`

**Times (UTC).** Started 2026-10-28 18:13:37. Ended 2026-10-28 18:22:30.

## Why the work is in packet-v3-supp, not packet-v2

- **packet-v2 could not be applied.** The owner ruling `research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md` landed in the checkout at 18:15 UTC, after packet-v2 was prepared at 18:12. That changed the packet's pinned prior-research context, so `load_packet` refuses it with "changed prior research".
- **packet-v3 is a fresh preparation of the same 20 orders.** Its dossiers are byte-identical to packet-v2.
- **packet-v3-supp adds the held extension texts.** It is packet-v3 plus the source supplement declared in `SUPPLEMENT_DECLARATIONS.json`, which covers seven excerpts: EO 6984, 7307, 7475, 7645, 7516, 7545 and 7209.

The ruling's text matches the version I applied in v1. Its rule 5 (do not route method questions to the owner) led me to decide EO 6874 myself; it is set out below.

## The grade fix is incomplete

The coordinator's first fix did not reach the gate. Two defects remain for every order held as an American Presidency Project (APP) transcription:

1. **The grade labels are swapped against the fragment registry.**
   - The dossier's original, the `app-executive-orders` text, is labeled `compiled_transcription_lead`. The only fragment record for that file, in `jobs/app-transcriptions/output/FRAGMENTS.jsonl`, grades it `mirror_transcription`.
   - The `clause-drafts` copy is labeled `mirror_transcription`, but no fragment record registers it.
   - Result: `working_text_fragment_identity_or_grade_mismatch`.
2. **The page check cannot be satisfied.**
   - The registered APP fragment sets `needs_page_check: true`, so the gate requires `pages_confirmed`.
   - The raw web capture is hashed but not committed (`jobs/app-executive-orders/app_mirror.py`). There is no page to inspect, so I left the confirmation false.
   - Result: `working_text:page_confirmation_required`.

A dry assembly against packet-v3-supp reproduced both errors (EO 7255 with its EO 7516 supplement).

What it would take to fix: claim-kit must label the original with the registered grade, and the APP page check must become satisfiable. That needs either a committed capture or a rule that a web transcription has no page to check.

**A third finding, in the supplement route.** Its source records carry no grade. When `sha256` names the held text file, the working-text gate does not classify the excerpt as a transcription at all. I used it only to pin evidence. The gap should be closed before a claim relies on an ungraded excerpt.

## Per order

### Submitted (unchanged analysis from v1)

- **EO 1547** (Taft, 1912-06-19). Waives the 1912 eight-hour act for Isthmian Canal construction contracts. It ends by its own terms on 1915-01-01, inclusive; the exclusive alternative is stated in the claim.
  - The new packet's text file differs from v1 only in a line break before the signature. The clause span and quote were rechecked against the new `TERM` record.
- **EO 4782** (Coolidge, 1927-12-16). Closes the District of Columbia offices on December 24, 1927. It ends by its own terms at the close of 1927-12-24.

### Blocked by the APP grade and page-check defects (14 orders)

The legal analysis for each of these is complete in its row. I confirmed identity and completeness of every held text, including the extension texts.

**Single-grant retirement exemptions.** Each ends by its own terms on its stated date, inclusive, and no later order names the person:

| Order | Ends |
|---|---|
| EO 6107 | 1933-06-30 |
| EO 6146 | 1935-05-31 |
| EO 6825 | 1935-09-01 |
| EO 7247 | 1937-01-01 |
| EO 7310 | 1937-01-01 |
| EO 7394 | 1937-08-01 |
| EO 7401 | 1937-07-01 |
| EO 7438 | 1937-10-01 |

**Retirement exemptions with extensions.** Each extension is now held in the packet as a supplement excerpt and recorded as a later event in `clauses.csv`:

| Order | Extensions | Own-terms end |
|---|---|---|
| EO 6663 | EO 6984, EO 7307 | 1935-04-01 |
| EO 7208 | EO 7475, EO 7645 | 1936-11-01 |
| EO 7255 | EO 7516 | 1937-01-01 |
| EO 7278 | EO 7545 | 1937-02-01 |

**Where I depart from the coordinator's instruction.** The instruction was to set each first end at the last extension's date. I set it at the order's own date instead, because the texts decide it:
- No extension says the earlier order "is amended" or changes its date. Each recites the earlier order as a past grant and makes a new grant under §204 with a new "until" date.
- EO 7645 counts the earlier orders as separate "periods totaling three years and eight months".
- The strike-and-insert ruling does not apply, because nothing is struck or inserted.
- The employee's exempt status continued without a gap under the later orders.

The alternative reading would put the first ends at 1936-11-01 (EO 6663), 1938-01-01 (EO 7208 and EO 7255) and 1938-02-01 (EO 7278). Each row states that alternative.

**EO 6516.** Ends by its own terms at the close of 1933-12-30.

**EO 6874.** This is a Schedule A amendment, not a closing order. I decided it on its own terms: the clause terminated on **1935-02-01**, read inclusively.
- **Why the sunset is the end.** The rewritten ¶6 excepts positions only "from this date to February 1, 1935". The period defines the exception, so the text itself shows the exception stopped operating on that date. Nothing held extended it: the WPA list shows no amendment of subdivision VII ¶6 between 1934-10-16 and 1935-10-19.
- **Why EO 7209 is not the end.** EO 7209 (1935-10-19) rewrote the paragraph, which had already stopped operating. Its words show it replaced the text, but under the evidence-decides ruling a later rewrite is not a default end, and an earlier own-terms end is evidenced. EO 7209 is recorded as a later event.
- The row also states the exclusive reading of the sunset and the savings position. EO 6874 remains blocked only by the APP defects.

### Blocked: completion date not held (four 1918 eight-hour suspensions, unchanged)

| Order | Project | Completion source needed |
|---|---|---|
| EO 2842 | DC water mains | Report of the Commissioners of the District of Columbia, fiscal 1918 or 1919 |
| EO 2855 | Treasury Vault No. 17 (dated 1918-05-04 by the WPA list) | Treasury or Supervising Architect report, fiscal 1918 or 1919 |
| EO 2947 | Boston Immigrant Station | Supervising Architect or Commissioner General of Immigration report, fiscal 1919 or 1920 |
| EO 2999 | Barge Office, New York | Supervising Architect report, fiscal 1919 |

For EO 2855, EO 2947 and EO 2999 (the March 4, 1917 proviso orders), the text of Pub. Res. 64 of March 3, 1921 is also needed. No held evidence supports an end for any of the four.

## Searches

The searches are those recorded in `PRODUCER_REPORT.md`:
- census titles and type rows;
- the full WPA 1944 numbered list;
- the full text of every held order under `jobs/*/output/texts`;
- citation searches by order number;
- the 2,750 ProQuest scan texts;
- the machine USC and eCFR searches, which found 0 hits.

The extension texts were read in full before they were added to the packet.

## v4: the 18 orders still blocked after v3 (packet-v4 → packet-v4-supp)

**Time (UTC):** 2026-10-28 18:38:02 to 18:44:58.
**Final applied directory:** `packet-v4-supp/applied-v1`.

EO 1547 and EO 4782 are unchanged. Their claims remain in `packet-v3-supp/applied-v1`, where batch-check passed.

### Outcomes

**14 submitted.** Every one passes the Stage 19 gate and the strict claim check (14 of 14), with no mechanical failures.

| Order | First end |
|---|---|
| EO 6107 | 1933-06-30 |
| EO 6146 | 1935-05-31 |
| EO 6825 | 1935-09-01 |
| EO 7247 | 1937-01-01 |
| EO 7310 | 1937-01-01 |
| EO 7394 | 1937-08-01 |
| EO 7401 | 1937-07-01 |
| EO 7438 | 1937-10-01 |
| EO 6663 | 1935-04-01 |
| EO 7208 | 1936-11-01 |
| EO 7255 | 1937-01-01 |
| EO 7278 | 1937-02-01 |
| EO 6516 | 1933-12-30 |
| EO 6874 | 1935-02-01 |

- **Retirement exemptions (the first 12 rows).** Each order ends on its own stated date, inclusive; each claim states the exclusive reading as the alternative.
- **Extensions.** Each extension is recorded as a later event, with its date taken from its registered supplement excerpt:
  - EO 6663: EO 6984 (1935-03-07) and EO 7307 (1936-02-28).
  - EO 7208: EO 7475 (1936-10-19) and EO 7645 (1937-06-24).
  - EO 7255: EO 7516 (1936-12-16).
  - EO 7278: EO 7545 (1937-01-29).
- **EO 6516.** Ends by its own terms at the close of 1933-12-30.
- **EO 6874.** Ends by its own sunset on 1935-02-01. EO 7209 (1935-10-19) is recorded as a later event, not as the end.

**4 blocked, unchanged:** EO 2842, EO 2855, EO 2947 and EO 2999. No completion records and no text of Pub. Res. 64 are held. These were not re-researched.

### Checks performed

- **Page check.** Done per `AGENT_PROTOCOL.md` for all 20 APP texts (the 14 orders and 6 extension texts). In each case the page record with the same sha256 in `(MIRROR_)DOCUMENTS.jsonl` passes all three tests:
  - its heading names the order number;
  - its date and subject agree with the held text;
  - its `text_sha256` equals the held file's hash.

  `pages_confirmed` is true for those sources. It stays false for EO 7209, a government-printed copy whose registry entry requires no page check and whose scan I did not inspect.
- **Source discipline.** Clauses are quoted only from the registered `jobs/app-executive-orders/output/texts` files. No claim source cites a clause-drafts copy.

### Batch-check: fails (exit 1)

The actual claim-checker reports 14 claims checked, 14 passing the gate, 0 mechanical failures and 14 unverified. Every unverified item is `source_held:custody_record_only`. The raw APP web captures, and the scan behind EO 7209, are recorded only by hash and are not committed, and network verification is disabled in this run.

Under the owner's checker policy (`jobs/claim-checker/checker.py`, `SOURCE_STATUS_RESULT`), a custody record alone counts as unverified. The working-text protocol keeps that byte-custody requirement in force.

This cannot be fixed inside the packet, and nothing was weakened to pass. Two fixes are possible:
- commit the raw APP captures and the Wikimedia DjVu for EO 7209;
- or run the checker with download verification, where the captures can be re-fetched.

**Hashes.** CLAIMS.proposed.jsonl sha256: `a20a0c26…25ce`. The per-claim sha256 values are in `applied-v1/AUDIT.json`.
