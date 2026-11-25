# Official pages for the numbered labels the census still lacks (Petty lane B, 2026-11-24)

Worker: Claude Sonnet subagent, about 243k tokens, 129 tool calls, 35 minutes. The coordinator wrote this report
from the worker's hand-back, because subagents cannot write report files. The coordinator checked the held-text
claims for EO 6585 and 7010F against `jobs/photius-gpo-volumes/output/texts/`.

## Results

| Label | Date | What was found | Confidence |
|---|---|---|---|
| EO 36, 38, 40, 43, 47 | 1894-11-02 | Civil Service Commission, *Eighteenth Annual Report* (fiscal 1901; printed 1902; also a House document in the Serial Set), printed pp. 246-248 | high, except EO 38 medium: the OCR dateline reads "November 1?, 1894" and Richardson reads November 2 |
| EO 51 | 1894-11-17 | Same report, p. 249 | high |
| EO 92 | 1896-11-02 | Same report, pp. 279-280. Richardson IX pp. 712-714 is a compiled copy the project already holds | high |
| EO 130A | no date in the WPA list; 1900-06-22 in Wikisource and Wikipedia only | Only the WPA numbered list, vol. 1 p. 31, which is a finding aid, not a printing. No text found | low |
| EO 2103 | 1914-12-07 | GPO *Monthly Catalog*, December 1914 (No. 240), p. 321, "(No. 2103.)", read on the archive.org scan of that issue. A catalog entry names the order but prints no text | high |
| EO 2687A | 1917-08-21 | *Foreign Relations of the United States* 1917, Supp. 2, vol. II, doc. 68, p. 927, per history.state.gov. A State Department compilation; page not checked on a scan | medium |
| EO 5151A | 1929-07-08 | *Proclamations and Executive Orders: Herbert Hoover* (Office of the Federal Register, 1974), vol. I pp. 372-373, "[No. 5151-A]". The 1929 slip volume skips from 5151 to 5152; held Hoover vol. II Table 2 (p. 1470) lists it | high |
| EO 6585 | 1934-02-06 | GPO bound slip-order volume, HathiTrust hvd.hl2725, PDF pp. 141-142. **Already held** as `jobs/photius-gpo-volumes/output/texts/EO_6585.txt` | high |
| EO 7010F | 1935-04-10 | GPO bound slip-order volume, HathiTrust hvd.hl2726, PDF p. 276. **Already held** as `jobs/photius-gpo-volumes/output/texts/EO_7010F.txt`. The census row EO:7010P is this order under a misread suffix (`../nothing-held-70/REPORT.md`) | high |
| EO 8606A | 1940-12-06 | Only the American Presidency Project. Not in the FR index, the NARA 1940 disposition table, 3 CFR 1938-1943, the held FR issues of Dec. 5, 11 and 12, or the Harvard slips (8603 jumps to 8608) | medium |

## Cautions

- **EO 36 through 53 are clause numbers.** The 1944 WPA list gave a number to each amended civil-service rule in a
  single Cleveland approval; its note says "a single document bears two or more E. O. numbers." No official page
  prints the numbers themselves. EO 36 is Departmental Rule II, 38 Indian Rule IV, 40 Customs Rule I, 43 General
  Rule III, 47 Postal Rule II, and 51 Departmental Rule VII.
- **Admission rule.** Owner decision D-20261112-graunt-apply admits a label once a held official page is checked.
  Only EO 6585 (and EO 7010F, which is a re-key rather than an addition) has its page held today. The others need
  the runner to fetch the pages listed in `FETCH_URLS.txt`.

## Searches that failed or were refused

HathiTrust full-text search, the Google Books API, govinfo PDF files and archives.federalregister.gov were refused,
both from the shell and from the web-fetch tool. WebFetch could not load en.wikisource.org/wiki/Executive_Order_36.
Archive.org searches for the text of EO 130A found nothing relevant.

What does work through WebFetch: archive.org full-text search
(`services/search/beta/page_production/?service_backend=fts&user_query=...`); archive.org djvu text read in
100,000-character chunks with an offset; history.state.gov; mocat.library.unt.edu; presidency.ucsb.edu;
archives.gov; and govinfo.gov/link/fr/VOL/PAGE.

## Next

Fetch the CSC report pages through the runner and settle EO 38's dateline. Try ProQuest and the National Archives
for EO 130A. For EO 2687A, check the September 1917 *Monthly Catalog* and the *Official U.S. Bulletin*. For EO 8606A,
check the Federal Register for December 12-31, 1940 and the *Department of State Bulletin*.
