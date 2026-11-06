# GPO slip sets / bound numbered executive orders: discovery results

## Conclusions

No digitized, full-view set of bound or slip-copy numbered executive orders covering orders below 5076 was found on any host I could reach. The only digitized GPO-printed numbered volumes I could verify are the FDR-era Commons DjVu files transcribed from HathiTrust (Executive Orders 6690-6935, April-December 1934, and 7262-8027, 1936-1938), which fall inside the range the project already holds (6071-7599 is covered by the project's eight Commons files). Estimated new coverage: 0 of the ~5,003 target orders below 5076 and ~0 of the ~940 in 6071-7599, on current evidence. Three things remain open: (a) the complete Commons file list could not be retrieved (Commons itself returned "url_not_found" to WebFetch for every page, including robots.txt; only the category's counts were obtained: 4 subcategories, 191 files, most of which are probably Title 3 CFR compilations, unverified); (b) no HathiTrust catalog record for a bound "Executive orders" set was located, so no OCLC number could be passed to the Bibliographic API; (c) Google Books and loc.gov could not be queried (googleapis returned a client error; loc.gov search is robots-disallowed). The Internet Archive "Executive Orders (19xx)" items that look relevant are Philippine Governor-General/President orders, not US. The 1944 Lord "Presidential Executive Orders, Numbered 1-8030" is a list, not the texts. Its introduction says the Documentary Catalog has listed GPO slip-form executive orders since 1895, that State Department numbering began in 1907, and that many orders never reached State Department files and were never numbered.

## Table of volumes found

| Host | Id / URL | Title | Number range | Year | Full view? | Format | Size |
|---|---|---|---|---|---|---|---|
| Commons (via mirror) | File:Executive_Orders_6690-6935.djvu (https://download.osmand.net/wiki/File:Executive_Orders_6690-6935.djvu) | Executive Orders issued by the President (GPO) | 6690-6935A | 25 Apr-29 Dec 1934 | Source "Hathi Trust" (no volume id cited); no license tag shown | DjVu, 648 pp | 16.03 MB |
| Commons (via mirror) | File:Executive_Orders_7262-8027.djvu (https://download.osmand.net/wiki/File:Executive_Orders_7262-8027.djvu) | Executive Orders 7262-8027, Supplemental (Office of the Federal Register) | 7262-8027 | 4 Jan 1936-23 Dec 1938 (Wikisource index says 1938) | Source "HathiTrust" (no id) | DjVu, 560 pp | 10.85 MB |
| Commons | File:Executive_Orders_6071-6250.djvu | (named in the project brief) | 6071-6250 | 1933 | unverified (page not retrievable) | DjVu | unverified |
| Commons | six other FDR-era DjVu files | (named by the project, not retrievable) | unverified | unverified | unverified | DjVu | unverified |
| Internet Archive | PresidentialExecutiveOrdersV1 | Presidential executive orders, numbered 1-8030, 1862-1938: Vol. 1, The List (Hist. Records Survey, ed. Lord) | 1-8030 (list only, no texts) | 1944 | Public Domain Mark 1.0 asserted in metadata (unverified as a copyright matter); download available | PDF, 695 page images | 12.99 MB PDF; 966 MB item |
| Internet Archive | cu31924097621753 | Executive orders relating to Indian reservations, 1855-1912 | not numbered series | 1912 | listed | (already used) | not fetched |
| Internet Archive | executiveordersr00unit, executiveordersr00cana | Panama Canal / Isthmian Canal Commission executive orders | not numbered series | 1922, 1911 | listed | (already used for 1922) | not fetched |
| Internet Archive | publicactsnos27800unit | Public acts nos. 2 and 78, 73d Congress, and executive orders dated March 31, 1933 | few FDR orders | 1933 | listed (microform scan) | not fetched | not fetched |
| Internet Archive (NOT US) | ExecutiveOrders1144-1909, ExecutiveOrdersNos1109-1903 (Nos. 1-109), ExecutiveOrdersNos196-1910, 1911ExecutiveOrders, ExecutiveOrdersNos1102-1912, ExecutiveOrdersNos.1111-1913, ExecutiveOrdersNos1133-1914, ExecutiveOrdersNos.1100-1915, ExecutiveOrdersNos.1101-1916, ExecutiveOrderNos171-1922, ExecutiveOrdersNos.199-1919, ExecutiveOrdersNos.165-1920 | "Executive Orders" by year | restart at 1 each year | 1903-1922 | collections "govph, journals", uploader at pcdspo.gov.ph | PDF/DjVu | 13-133 MB |

Basis for the "not US" label: the three items I fetched in full (1909, 1903, 1920, plus 1912's metadata) are in the Internet Archive collection "govph" with a Philippine government uploader, and the numbering restarts each year (e.g., "Nos. 1-109 (1903)"). The text of these items was not opened, so this is inference from metadata (the US numbered series is continuous, 1 through 8030 by 1938).

## 1. Wikimedia Commons

- Category page https://commons.wikimedia.org/wiki/Category:Executive_orders_of_the_United_States: fetched once; it reported "4 subcategories" and "191 files" but listed no names. Retries via the Commons API, `?action=raw`, and a mirror category page all failed. The complete range list is therefore unverified.
- Verified file pages (through the osmand.net Commons mirror): 6690-6935 (upload history: 7 March 2011 by Slaporte, 18 March 2011 by George Orwell III, who "added OCR text layer; inserted place-holders for missing E.O.s 6692, 6786-A & 6810-A") and 7262-8027. Neither names a HathiTrust volume id. The Wikisource index for 7262-8027 (https://kwx.liehendr.com/content/wikisource_en_all_maxi_2022-09/A/Index%3AExecutive_Orders_7262-8027.djvu) says author "Office of the Federal Register", year 1938, progress "To be proofread", no Hathi id.
- A Kiwix copy of the Wikisource FDR page lists orders 6071-7611 only, so Wikisource transcribes only the FDR range.
- Implication: the Commons uploader pulled GPO-bound "Executive Orders" volumes from HathiTrust in 2011, so full-view HathiTrust copies of those FDR volumes exist. Whether similar full-view volumes exist for orders below 5076 is unknown.

## 2. HathiTrust

- WebSearch for site:catalog.hathitrust.org returned no HathiTrust pages. A second search for catalog records also returned none.
- Bibliographic API tested once, with a guessed OCLC (1767153): the API answered (it returned the record for an unrelated serial, "Tax administrators news"), which confirms the endpoint works but not that any executive-orders record exists. A lccn test also returned an empty record. A real OCLC or htid is needed; the Commons Hathi source field is the best lead, and an Orwell III/Slaporte talk page or Wikisource index page may carry the id.
- No volume list, number ranges, or volume ids were obtained.

## 3. Internet Archive

- Advanced search (title "executive orders", texts) returned 264 hits; first 95 read, plus a second date-filtered search (1907-1938) returned 27. No US bound slip set or GPO numbered "Executive orders" volume before 1937 appeared.
- US-relevant items: Lord's List (above); Hoover 1974 GPO volumes (proclamationsexe0001herb; also 4731703.proc.001/.002.umich.edu, Michigan scans of the same Hoover volume); Indian reservations 1912; Panama Canal 1911 and 1922; the "Codes of fair competition" series (1933-35, includes some executive orders; not numbered-EO sets). Lending status: no lending field in the metadata I read; the Lord item has the Public Domain Mark.
- Other Lord-related item: listindexofpresi0000clif (1979 Glazier reprint of the unnumbered series list; borrowable status unverified).

## 4. Google Books

Unverified. googleapis.com returned a client error and google.com/books feeds are robots-disallowed to WebFetch. No ids obtained.

## 5. Library of Congress

Unverified. loc.gov search URLs are robots-disallowed to WebFetch; no WebSearch hit pointed to a digitized slip set.

## 6. State Department slip series

Source: Lord, "Presidential Executive Orders, Numbered 1-8030" introduction, https://archive.org/stream/PresidentialExecutiveOrdersV1/PresidentialExecutiveOrdersV1_djvu.txt (fetched; first 100,000 characters).
- "This numbering was begun by the Department of State in 1907." The "relatively few Orders then on file" were arranged chronologically and numbered, which is retroactive numbering. Later discoveries got "-A" or "-1" style numbers.
- The Documentary Catalog "has listed every Executive Order printed in slip form by the Government Printing Office" since 1895, whether or not numbered.
- 1925-1936: slip copies were available in "a small number of depository libraries."
- "Many Orders did not make their way into the files of the State Department, and so did not receive numbers"; a full file of the numbered series is held in State Department records at the National Archives.
- Corroboration: Wikipedia "Executive order" (https://en.wikipedia.org/wiki/Executive_order) says State instituted numbering in 1907 starting retroactively with EO 1 (20 October 1862); an FDLP presentation (https://fdlp.gov/file-download/download/public/2154) says pre-1907 orders were unnumbered and often unpublished. The American Presidency Project says its executive-order texts are complete only from Hoover on (https://www.presidency.ucsb.edu/documents/presidential-documents-archive-guidebook/executive-orders-beginning-with-jq-adams). Whether all numbered orders were printed as slips: unverified; Lord implies not all were on file.

## 7. Robots and terms

- archive.org/robots.txt (fetched): `User-agent: *` disallows only /control/ and /report/; no crawl-delay; sitemap listed.
- commons.wikimedia.org/robots.txt and upload.wikimedia.org/robots.txt: could not be fetched (url_not_found); unverified. Wikimedia User-Agent policy was not checked.
- Public-domain marking: the two Commons file pages I read show an empty "Permission" field and no license tag in the text returned (a tag may exist in the page template that the fetch summary dropped; unverified). Underlying works are US government publications. The Lord item carries a CC Public Domain Mark in IA metadata. The Philippine items carry no license statement.
- Wikidata licensing page fetched (CC0 for structured data); not relevant to the scans.

## Suggested next steps (not done)

1. Read Commons file pages for the other six FDR ranges for their Hathi ids; then query the Bibliographic API by htid.
2. Check Wikisource Index pages for any pre-1936 ranges.
3. Check the IA full text of the Lord List (not texts) as a cross-check of which orders exist, since it lists all 8030 numbers.
