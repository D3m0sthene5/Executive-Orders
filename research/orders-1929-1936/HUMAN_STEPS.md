# Human actions for the 181 texts still missing

The job has saved 1,531 of 1,712 texts. The remaining list is
[MISSING.csv](../../jobs/hathi-gpo-orders/output/MISSING.csv): five Hoover
orders and 176 FDR orders. Each action below takes less than 30 minutes of
your active work; a library's reply can take longer. Counts are explicitly
qualified: a permission request does not guarantee that a collection has the
requested texts. No messages or requests have been sent for you.

## 1. Ask APP for a permitted export of the remaining orders (5–10 minutes)

Potential unlock: **up to 181**, with actual APP overlap unconfirmed. This is
the broadest short action, not a promise of 181 matches. Its robots rules
exclude this agent, so an authorized export is preferable to automated pages.

1. Open [the American Presidency Project contact form](https://www.presidency.ucsb.edu/contact).
2. Enter your name and email. Paste this request, including the remaining-list
   link below, into Message, then click Send if you want to make the request:

   > I am collecting the full text of executive orders numbered 5076–7531
   > for a public historical research project. We have recovered 1,531 texts
   > and have 181 identities left. Could you provide a permitted export of
   > any full order texts you hold for the attached/listed remaining IDs,
   > including letter suffixes? JSONL with instrument_id (EO:1234A), text,
   > url and page_or_item would be ideal. Please include source citations
   > and permission to retain and publish the attributed website
   > transcriptions, or specify an allowed download route. We will respect
   > your robots exclusions and will not scrape around them.

   Remaining list:
   `https://github.com/D3m0sthene5/Executive-Orders/blob/codex/hathi-gpo-orders-20261018/jobs/hathi-gpo-orders/output/MISSING.csv`
3. If an export is supplied with suitable reuse permission, save it as
   `jobs/hathi-gpo-orders/incoming/app-orders.jsonl`. Keep the reply's
   permission statement with your local files. Create `incoming/manifest.json`
   from `manifest.example.json`: set path to `app-orders.jsonl`, format to
   `orders_jsonl`, source_url to the real supplied source/export URL,
   permission_note to the granted scope, and copy_kind to
   `website_transcription`. Use actual order-page URLs in each row.
4. Run the two import/report commands at the bottom. Exact-ID mismatches and
   still-incomplete bodies are recorded as failures, not promoted to texts.

## 2. Check and transcribe a small batch from scans already held (20–25 minutes)

Potential unlock: **up to 10 per batch**, drawn from 105 remaining identities
with candidate number hits. A hit may only be a citation; it needs visual
confirmation. Ten is a work limit, not a guaranteed recovery count.

1. Open [PAGE_CHECK_QUEUE.csv](../../jobs/hathi-gpo-orders/output/PAGE_CHECK_QUEUE.csv)
   and take the first ten distinct identities. Click each source_url and use
   its candidate_scan_pages. The same scan is already in `output/books/`;
   do not redownload it. These public Commons copies have government-work
   notices. An intact heading/body/ending, including the letter suffix, is
   needed to identify the order. Do not infer identity from a mere reference.
2. Read the scan and copy the corresponding OCR passage from its
   `output/books/<volume>_ocr.jsonl.gz`, correcting unreadable characters
   against the image. Keep the complete order, its explicit number, signature
   and date. Skip anything you cannot confirm; no status decision is needed.
3. Save one JSON object per line in `incoming/checked-orders.jsonl`, with
   instrument_id, text, url (the Commons file page), and page_or_item (volume,
   scanned page range, and “human checked against scan”). Use the canonical
   identity in MISSING.csv, e.g. EO:1234A, without inventing an identity.
4. In `manifest.json` use format `orders_jsonl`, the real source URL,
   permission_note `Human transcription of the public-domain US government
   printed copy on Commons; checked against scanned pages`, and copy_kind
   `human_verified_transcription_of_government_printed_copy`. This remains a
   derivative transcription, not an authenticated original. Run the importer.

## 3. Request cleaner page text for the largest residual volume (5–10 minutes)

Potential overlap: **48 remaining range candidates** in 7262–7531, inside
the 7262–8027 volume; individual inclusion is not yet verified. Downloading
the existing Commons scan again unlocks zero new files. Ask for better OCR
or an independently digitized copy instead.

1. Open [Ask a Librarian, Law Library of Congress](https://ask.loc.gov/law/)
   and its question form, or your own university librarian's request form.
2. Ask for a lawful full-volume OCR/PDF or per-order text dataset for
   *Executive orders 7262–8027* (GPO, 1936–1938). Include
   [the public scan](https://commons.wikimedia.org/wiki/File:Executive_Orders_7262-8027.djvu),
   [the bibliographic copy](https://hdl.handle.net/2027/mdp.39015087537844),
   and MISSING.csv filtered to 7262–7531. Explain that an existing scan's OCR
   failed exact order-number/boundary checks and request reuse permission.
3. Save an authorized reply's PDF, XML, DjVu or page-text file in `incoming/`.
   Use the manifest's real source URL and permission statement, the matching
   format, range_min 7262 and range_max 7531. A UTF-8 plain text file can use
   format `text` with form-feed page breaks. A PDF scan is OCRed locally.
   The importer processes only still-missing target IDs. The same request can
   name other volumes from REMAINING_BY_VOLUME.csv if the librarian offers them.

HathiTrust's member-only or restricted full-volume options are not assumed
available. Use only a download the site offers you with applicable reuse
rights; there is no instruction to reconstruct a restricted book page by page.

## 4. Ask NARA for a narrow permitted export and an API key (10 minutes)

Potential ceiling: **181**, actual digitized/full-text overlap unknown. A key
alone unlocks **zero confirmed texts** until storage permission is clear.

1. Open [NARA's API guidance](https://www.archives.gov/research/catalog/help/api).
   Email the listed `Catalog_API@nara.gov` yourself to request a read-only key
   and ask whether the rule against caching/storing API responses permits
   retention/publication of these government order images/OCR, or whether an
   official limited dataset export should be used instead.
2. Give the 181-ID list, date range 1929–1936, and RG 11 executive-order
   series context. Request only matching item IDs, full order text or images,
   page citations, original-object URLs and applicable reuse terms. No entire
   Catalog download is needed.
3. Keep a key outside the repository. If NARA supplies an authorized dataset,
   save its files under `incoming/` with the manifest. This job supports local
   file import; it does not yet implement authenticated NARA API access.

## 5. Optional GovInfo personal key and catalog assistance (5–10 minutes)

Potential ceiling: **181**, with zero additional holdings confirmed. The
public API demonstration check hit an HTTP 500 while checking its robots
policy; obtaining a key does not establish that this server problem is fixed.

1. Open [the official free API signup](https://www.govinfo.gov/api-signup),
   enter your own details and keep the emailed key private. An existing
   api.data.gov key can also be used under GPO's documentation.
2. Use [GovInfo's API documentation](https://api.govinfo.gov/docs/) only after
   the service is available under its policy, or ask GPO/library staff for
   permitted GOVPUB copies of the remaining GPO bound volumes. The job's
   three narrow demo queries are preserved in govinfo_search.py. A personal
   key must not be used to bypass a current access refusal or rate limit.
3. If a public PDF/OCR is found, save it in `incoming/` with the actual offered
   source URL and permission note. The importer accepts it without accessing
   the robots-excluded GovInfo UI search route.

## Import supplied files

Run from the repository root after filling the real manifest values:

```text
python jobs/hathi-gpo-orders/import_local.py --folder jobs/hathi-gpo-orders/incoming
python jobs/hathi-gpo-orders/finish_report.py
```

Per-order exports need an explicit exact order number in their text and at
least 100 characters of body. Book imports need a readable signed passage
with an exact numbered ending. Unsupported or ambiguous items stay in the
failure log. Keep supplied source files: receipts refer to them. They are
ignored by Git until their publication permission and size are reviewed.
The report command calls claim-kit's loader read-only and never writes its
output folder. None of these actions determines whether an order is in force.
