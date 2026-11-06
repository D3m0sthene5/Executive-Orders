"""Build Ptolemy's request list: every cited source whose bytes the project does not hold.

Run by an agent or the owner (it needs no network): python3 -I jobs/ptolemy-custody/build_requests.py
It reads the claim checker's own source index, so "held" means exactly what the checker means: a source is
wanted when no copy of its sha256 has kept bytes. Sources that GPO publishes with the same SHA-256 are left
out, because the checker accepts them without a download. Each wanted source gets one route:

  archive  an American Presidency Project page with a recorded Common Crawl or Wayback capture (re-read
           from the archive, never from the live site, as Cassiodorus does)
  live     a file on a host in LIVE_HOSTS, re-downloaded from its own URL and kept only if it hashes as recorded
  skipped  everything else, with the reason (no live APP requests, search pages, wiki pages that change)

The list is written to REQUESTS.jsonl in this folder so the job's inputs stay fixed while a run is going.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "jobs/claim-checker"))

MAX_FILE_BYTES = 25_000_000
# Hosts whose files are stable enough to re-download and match a recorded hash (mostly PDFs and fixed pages).
LIVE_HOSTS = {
    "www.govinfo.gov", "archive.org", "www.federalregister.gov", "nmb.gov", "uscode.house.gov", "www.fws.gov",
    "www.archives.gov", "history.state.gov", "commons.wikimedia.org", "upload.wikimedia.org",
    "www.trumanlibrary.gov", "www.abmc.gov", "archives.library.cornell.edu", "www.loc.gov", "tile.loc.gov",
    "babel.hathitrust.org", "www.justice.gov", "www.whitehouse.gov", 
}
SKIP_REASONS = {
    "www.presidency.ucsb.edu": "APP page with no archive capture; the project does not request live APP pages",
    "lite.duckduckgo.com": "search results page, not a source",
    "html.duckduckgo.com": "search results page, not a source",
    "en.wikipedia.org": "wiki page; its bytes change with every edit",
    "en.wikisource.org": "wiki page; its bytes change with every edit",
    "www.ecfr.gov": "regenerated daily; recorded bytes cannot recur",
    "www.law.cornell.edu": "regenerated page; recorded bytes cannot recur",
}


def main():
    import checker as C
    S = C.S
    index = S.build_index(REPO, REPO / "jobs/claim-checker", [], exclude_jobs=("claim-checker", HERE.name))
    gpo = C.load_gpo_matched(REPO)
    captures = C.load_archive_captures(REPO)
    rows, skipped = [], collections.Counter()
    for sha, copies in index.by_sha.items():
        if any(c.bytes_kept for c in copies) or sha in gpo:
            continue
        url = next((c.url for c in copies if c.url), "") or ""
        size = max([c.bytes or 0 for c in copies] or [0])
        ids = sorted({i for c in copies for i in (c.instrument_ids or []) if isinstance(i, str)})
        host = urllib.parse.urlparse(url).netloc
        cap = captures.get(sha)
        row = {"sha256": sha, "url": url, "bytes": size, "instrument_ids": ids[:25],
               "recorded_in": sorted({c.origin for c in copies})[:6]}
        if cap and ((cap.get("archive") == "common-crawl" and cap.get("warc_filename")) or
                    (cap.get("archive") == "wayback" and cap.get("wayback_url"))):
            rows.append({**row, "route": "archive", "capture": cap})
        elif host in LIVE_HOSTS and url.startswith("https://") and size <= MAX_FILE_BYTES:
            rows.append({**row, "route": "live"})
        else:
            reason = SKIP_REASONS.get(host) or ("larger than the per-file cap" if size > MAX_FILE_BYTES
                                                else "no URL" if not url else "host not on the live list")
            skipped[reason] += 1
    rows.sort(key=lambda r: (r["route"] != "archive", urllib.parse.urlparse(r["url"]).netloc, r["sha256"]))
    with open(HERE / "REQUESTS.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    routes = collections.Counter(r["route"] for r in rows)
    print(json.dumps({"wanted": len(rows), "routes": routes, "skipped": skipped,
                      "orders_touched": len({i for r in rows for i in r["instrument_ids"]})}, indent=1))


if __name__ == "__main__":
    main()
