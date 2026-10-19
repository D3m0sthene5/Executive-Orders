# Public-domain routes for the 3,563 orders ProQuest would otherwise supply (2026-10-19)

Input: `PROQUEST_RESIDUE.txt` (3,563 ids). Subjects and print citations come from the full WPA/Lord numbered
list (`jobs/wpa-lists/output/NUMBERED_ENTRIES.csv` on branch `wpa-lists`, commit 121ca07e). The list
gives a subject hint and the printed sources it knew for each order. Per-order table: `GAP_ROUTES.csv`.
Everything here is a lead. No text was acquired and no order's status changed.

## Result

| Candidate public source | Orders | Basis | Access |
|---|---:|---|---|
| U.S. Civil Service Commission annual reports, 1896-1939 (mostly 1913-1929) | 840 | The WPA list cites report year and page ("1915 CSR 123") | Congressional Serial Set on GovInfo (direct PDFs; the 1915 and 1917 reports seen as Serial Set nos. 7070 and 7415); HathiTrust serial run |
| *Executive Orders Relating to Indian Reservations*, vol. 2, 1912-1922 (GPO 1922) | 46 | Subject and date range only, not text-checked | HathiTrust or HeinOnline; the Internet Archive copy (1975 reprint) is lending-only |
| *Executive Orders Relating to the Panama Canal*, 1904-1921 (Panama Canal Press 1922) | 19 | OCR number hit, or canal subject with a date hit or in range | Free: archive.org `executiveordersr00unit` (Univ. of Florida), djvu text sha256 be996826... |
| Kappler, *Indian Affairs: Laws and Treaties* vol. IV (to Mar. 4, 1927; pub. 1929) | 16 | OCR number hit, or reservation subject with a date hit | Free: archive.org `bwb_S0-DZH-184_4`, djvu text sha256 a45294e7... |
| Richardson, *Messages and Papers* | 7 | WPA cites Richardson | Already partly held by `jobs/richardson-volumes`; see the oddity below |
| **No public compilation found** | **2,635** | WPA lists no printed source for 2,599 of them; 36 have no WPA entry | NARA RG 11 originals (API key needed) or ProQuest |

Ceiling of the public sweep: **about 930 of 3,563 orders (26%)**, most of them through the Civil Service
Commission reports. The rest have no known printing. By WPA subject they are: other 851, national forests 492,
land withdrawals 450, World War I and emergency 288, military reservations 145, individual civil-service
cases 127, customs 114, Indian reservations 44, Canal Zone 30, lighthouses 28, bird refuges 15. Most were
probably never printed, so their texts survive only as the filed originals (NARA RG 11, which ProQuest scanned).

## Caveats

- The WPA citations are the WPA compilers' (1944), read from OCR. A cited report should print the order
  or summarize it; the page still has to be checked.
- Date matches in the two OCR texts are noisy, since several orders share a date. Only matches that fit the
  subject, or that match by number, were kept as candidates. The raw counts (164 Panama, 106 Kappler
  date-or-number hits across all subjects) are not coverage.
- The HathiTrust catalog and full-text search answer automated requests with a Cloudflare challenge. They
  were not bypassed; the volume lookups there need a person in a browser. HathiTrust's Bibliographic API
  (`catalog.hathitrust.org/api/volumes/brief/...`) does answer.
- Oddity: per an earlier repo scan, 8 `PRIORITY.txt` ids appear in `jobs/richardson-volumes` FRAGMENTS but
  are not counted as held by `build_priority.py`. The cause has not been checked; they may not need a new
  source.

## Next steps

1. A bounded `jobs/` job that finds the Civil Service Commission annual reports for 1896-1939 in the GovInfo
   Serial Set, downloads those volumes (public, no login) and extracts the WPA-cited pages for the 840
   orders, as FRAGMENTS with grade conventions like `ofr-compilations`.
2. Extract the Panama 1922 and Kappler IV candidates from the archive.org texts; confirm each by page.
3. Find vol. 2 (1912-1922) of the Indian reservations orders on HathiTrust (owner, in a browser).
4. The remaining ~2,635: NARA API key (draft in `ACCESS_REQUESTS.md`), or ProQuest under NYU's terms.
