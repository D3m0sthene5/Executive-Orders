# HathiTrust GPO orders: stopped at the anonymous access gate

The requested population is pinned in `data/TARGETS.json`: exactly 1,712
all-no rows from main's gap census, with numeric order prefixes 5076–7531.
`data/VOLUMES.json` lists the ten logical volumes identified in the GPO bound
series and the two-volume Hoover compilation, including all intermediate
6251–6935 and 7082–7261 volumes. These are range candidates, not verified
individual order holdings. The Hoover volumes overlap the 5800–6070 volume;
their internal split was not inspected.

`access_check.py` imports the existing, unchanged
`jobs/early-orders-hunt/hunt.py` and uses its shared `FetchPool` with one
worker, one host permit, a two-second minimum interval, and robots checks.
All its writes stay in this folder. It does not use an authenticated session,
retry a refusal, enumerate page-text endpoints, or use an alternate host.
Run explicitly with `python jobs/hathi-gpo-orders/access_check.py`.
There is deliberately no automatically scheduled `job.py` entry point.

The live run stopped before the first volume download: the existing pool
returned `FetchError: blocked_by_robots_txt` for the normal book viewer. Only
the robots request was sent by the pool. An independent browser inspection
also encountered a “Just a moment...” access challenge; it was closed without
interaction. No authenticated or alternate download route was tried.

The HathiTrust extraction adapter was not built after this stop. The existing
`printed_page_map` and passage-cutting code was inspected, but neither was
run on a volume. No machine-read order text, source receipt, status decision,
or original-candidate representation was created. `FAILURES.jsonl` lists all
1,712 orders as **not attempted because the access gate stopped**, not as OCR
or heading failures. `VOLUME_FAILURES.jsonl` records the single viewer check.

The existing claim-kit loader was checked read-only. With no saved order
texts it recognizes zero representations from this producer; this does not
validate a future OCR adapter. Nothing was written to `jobs/claim-kit/output/`.
The first-two-volumes heading-recovery threshold was not reached.

## What HathiTrust allows

HathiTrust's [anonymous-download guidance](https://hathitrust.atlassian.net/wiki/spaces/GS/pages/2387247137/What+You+Can+Download+from+the+Collection)
allows reading full-view items, whole-book downloads for unrestricted copies,
and one-page-at-a-time downloads for restricted copies such as Google scans.
Whole-book downloads of those Google scans are for logged-in member-library
users. Its [format guidance](https://hathitrust.atlassian.net/wiki/spaces/GS/pages/2387247130/Formats+for+Downloading+Materials)
describes OCR text and per-page text ZIPs, subject to the same restrictions.
The [text-only view for 6480–6689](https://babel.hathitrust.org/cgi/ssd?id=mdp.39015087537877)
is marked “Public Domain, Google-digitized,” says anonymous access is one
page at a time, and displays a warning against saving or redistributing that
text-only file. Public viewing therefore did not establish a permitted
anonymous full-volume OCR download. No page-by-page reconstruction was tried.

This run establishes a robots/access blocker, not that HathiTrust has no OCR,
not that every copy requires login for page viewing, and not an absence finding
for any order. No acquisition should resume by bypassing these restrictions.
