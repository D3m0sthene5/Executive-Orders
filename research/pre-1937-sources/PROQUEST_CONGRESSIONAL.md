# ProQuest Congressional: pre-1937 executive orders (surveyed 2026-10-19)

Access: the owner's NYU subscription, signed in through OpenAthens. NYU's old EZproxy links are retired.
Nothing was harvested. Only one record (EO 2000) was opened as a sample.

## What the collection holds

Content type Presidential Materials, years 1789-1936: **53,671 records**, all filed under
"Executive Orders and Presidential Proclamations". The facets overlap, so they do not add up:

| Facet | Records |
|---|---:|
| Numbered Executive Orders | 9,503 |
| Unnumbered Executive Orders, Directives, and Proclamations | 20,028 |
| Presidential Pardons | 18,547 |
| Numbered Presidential Proclamations | 2,844 |
| Military orders and pardons | 2,716 |
| Presidential Signing Statements | 33 |
| Signed by the President / Not signed | 44,592 / 9,079 |

The newest hit is dated 1936-12-31 (EO 7531), so the date limit holds. The 9,503 numbered records
exceed the roughly 7,531 numbers issued by then. Lettered orders and extra records per order (some titles
end "[related correspondence]") are likely reasons; this has not been checked.

## What one record contains (EO 7531)

Accession no. `1936-EO-7531`; title; date; signed / not signed; item no. ("Executive Order No. 7531");
length in pages; administration; source "Numbered Executive Orders, 1862-Present"; descriptors; personal
names; a PDF labelled "Replica of Original - Complete". Permalinks take the form
`congressional.proquest.com/congressional/docview/t67.d72.<year>-eo-<number>`.

## Sample PDF (EO 2000, 1914-07-28, 2 pp., 241 KB)

A clear scan of the printed order, "Executive Order Amending the Civil Service Rules", with "2000"
handwritten at the top right, which suggests a filed archival copy (the RG 11 numbered series). The PDF
lives at `/app-s3/jlh-content/PT1-<year>-EO-<number>/PT1-<year>-EO-<number>.pdf`. A phrase search
`"Executive Order No. 2000"` finds the record. Search by Number has no EO field, and the guessed
permalink `t67.d72.1914-eo-2000` opened an empty page.

Custody grade: not decided. If recorded, keep `acceptable_as_original=false` until a person compares the
pages. A scan of the archival copy might qualify for a scan grade rather than `mirror_transcription`; the
codebook decides that, not this note.

## Export

The results list offers only Print and Email. The selected-items export was not reached because the tab
froze on a browser dialog. I found no CSV or RIS export of results.

## Where the 3,593 missing orders can come from

`jobs/app-executive-orders/data/PRIORITY.txt` (sha256 a858a2d7...d79a4) has 3,593 ids with no saved text.

| Public source | Gap orders it can cover |
|---|---:|
| Wikisource (1,639 orders already held) | 0 |
| HathiTrust, Hoover *Proclamations and Executive Orders* vol. I (EO 5076-5549) | 2 |
| HathiTrust, GPO bound Executive Orders volumes (EO 5800-8027) | 28 |
| NARA Catalog, RG 11 (NAID 299999) | unknown; the API needs a key and its terms restrict bulk download |

That leaves **3,563 ids** in `PROQUEST_RESIDUE.txt`: 3,553 below EO 5076 and 10 above EO 7531. For these,
ProQuest is the only full-text source found so far. A request-by-request harvest of about 3,560 PDFs is the
systematic downloading that ProQuest's and NYU's terms prohibit, so it waits for the access request in
`ACCESS_REQUESTS.md`.
