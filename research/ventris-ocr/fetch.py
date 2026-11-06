"""Download the pilot's source PDFs politely and record URL + SHA-256 (PDFs stay outside git).

For every row of TARGETS.json: check robots.txt, wait PACE seconds between requests to the same host, stream the body to
WORK/pdf/<sha256>.pdf, and append a row to SOURCES_MANIFEST.jsonl. If TARGETS carries the project's own SHA-256 for the
file, `matches_project_sha256` says whether our bytes are identical (a mismatch is a finding, not an error).
Run: py -I fetch.py
"""
import hashlib, json, os, time, urllib.parse, urllib.request, urllib.robotparser
from datetime import datetime, timezone

WORK = "C:/Users/danie/eo-ocr-work"
PACE = 3.0
UA = "EO-Road-System/1.0 (ventris-ocr pilot; contact via github D3m0sthene5/Executive-Orders)"
HERE = os.path.dirname(os.path.abspath(__file__))
_robots = {}
_last = {}


def allowed(url):
    o = urllib.parse.urlsplit(url)
    base = f"{o.scheme}://{o.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        req = urllib.request.Request(base + "/robots.txt", headers={"User-Agent": UA})
        rp.parse(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace").splitlines())
        _robots[base] = rp
    return _robots[base].can_fetch(UA, url)


def fetch(url):
    host = urllib.parse.urlsplit(url).netloc
    wait = _last.get(host, 0) + PACE - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    h = hashlib.sha256()
    tmp = os.path.join(WORK, "pdf", "_partial.tmp")
    n = 0
    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as fh:
        final = resp.geturl()
        while True:
            b = resp.read(1 << 20)
            if not b:
                break
            h.update(b)
            fh.write(b)
            n += len(b)
    _last[host] = time.monotonic()
    return tmp, h.hexdigest(), n, final


def main():
    os.makedirs(os.path.join(WORK, "pdf"), exist_ok=True)
    targets = json.load(open(os.path.join(HERE, "TARGETS.json")))
    mpath = os.path.join(HERE, "SOURCES_MANIFEST.jsonl")
    done = set()
    if os.path.exists(mpath):
        done = {json.loads(l)["url"] for l in open(mpath) if l.strip()}
    for t in targets:
        if t["url"] in done:
            continue
        if not allowed(t["url"]):
            row = {"key": t["key"], "url": t["url"], "error": "blocked_by_robots_txt"}
        else:
            try:
                tmp, sha, n, final = fetch(t["url"])
                dest = os.path.join(WORK, "pdf", sha + ".pdf")
                os.replace(tmp, dest)
                row = {"key": t["key"], "kind": t["kind"], "url": t["url"], "final_url": final, "sha256": sha,
                       "bytes": n, "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "local_path": dest, "project_sha256": t.get("project_sha256"),
                       "matches_project_sha256": (sha == t["project_sha256"]) if t.get("project_sha256") else None,
                       "project_source": t["project_source"]}
            except Exception as e:
                row = {"key": t["key"], "url": t["url"], "error": f"{type(e).__name__}: {e}"[:200]}
        with open(mpath, "a") as fh:
            fh.write(json.dumps(row) + "\n")
        print(row.get("key"), row.get("bytes"), row.get("matches_project_sha256"), row.get("error", ""), flush=True)


if __name__ == "__main__":
    main()
