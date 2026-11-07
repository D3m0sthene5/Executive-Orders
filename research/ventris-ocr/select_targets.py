"""Choose the source PDFs for the Ventris OCR pilot from files the project already holds metadata for.

Reads (via `git show origin/main:...`) jobs/fr-pages, jobs/fr-originals and jobs/selden-statutes SOURCES.jsonl and the
Serial Set URLs cited in jobs/*/output (git grep). Writes TARGETS.json: one row per PDF to fetch, with the project's
own SHA-256 when it holds one (the downloaded bytes are compared against it in fetch.py).
Run: py -I select_targets.py   (from the worktree)
"""
import json, re, subprocess, sys

REPO = "C:/Users/danie/eo-wt/enc-ocr"


def show(path):
    return subprocess.run(["git", "-C", REPO, "show", "origin/main:" + path], capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def jl(path):
    return [json.loads(l) for l in show(path).splitlines() if l.strip()]


FR_PAGES_ISSUES = ["FR-1949-03-10", "FR-1950-08-19", "FR-1951-04-17", "FR-1953-07-10", "FR-1954-02-10", "FR-1954-03-24",
                   "FR-1955-05-17", "FR-1955-11-10", "FR-1955-11-15", "FR-1956-06-28", "FR-1957-04-17", "FR-1962-06-09",
                   "FR-1963-02-28", "FR-1966-09-23", "FR-1969-03-28", "FR-1969-04-19", "FR-1971-08-10"]
FR_ORIG_ISSUES = ["FR-1938-06-02", "FR-1939-05-25", "FR-1940-03-01", "FR-1940-11-20", "FR-1941-07-02", "FR-1942-01-28",
                  "FR-1942-08-14", "FR-1946-06-25"]
STAT_VOLS = ["STATUTE-12-", "STATUTE-26-", "STATUTE-37-", "STATUTE-46-", "STATUTE-48-", "STATUTE-55-", "STATUTE-60-",
             "STATUTE-64-"]
SERIAL_DOCS = ["SERIALSET-08950_00_00-002-0017-0000", "SERIALSET-09097_00_00-002-0377-0000",
               "SERIALSET-09300_00_00-002-0207-0000", "SERIALSET-07878_00_00-002-0867-0000",
               "SERIALSET-07070_00_00-002-0030-0000"]


def main():
    out = []
    seen = set()
    for r in jl("jobs/fr-pages/output/SOURCES.jsonl"):
        iss = r["issue_url"].split("/")[-1][:-4]
        if iss in FR_PAGES_ISSUES and r["issue_url"] not in seen:
            seen.add(r["issue_url"])
            out.append({"kind": "fr_issue", "key": iss, "url": r["issue_url"], "project_sha256": r["issue_sha256"],
                        "project_source": "jobs/fr-pages/output/SOURCES.jsonl"})
    for r in jl("jobs/fr-originals/output/SOURCES.jsonl"):
        iss = r["url"].split("/")[-1][:-4]
        if iss in FR_ORIG_ISSUES and r["url"] not in seen:
            seen.add(r["url"])
            out.append({"kind": "fr_issue", "key": iss, "url": r["url"], "project_sha256": r["sha256"],
                        "project_source": "jobs/fr-originals/output/SOURCES.jsonl"})
    stat = jl("jobs/selden-statutes/output/SOURCES.jsonl")
    for prefix in STAT_VOLS:
        c = [r for r in stat if r.get("granule", "").startswith(prefix) and r.get("pdf_pages", 0) <= 4]
        c.sort(key=lambda r: r["bytes"])
        if c:
            r = c[len(c) // 2]
            out.append({"kind": "statute", "key": r["granule"], "url": r["link_url"], "project_sha256": r["sha256"],
                        "project_source": "jobs/selden-statutes/output/SOURCES.jsonl"})
    for d in SERIAL_DOCS:
        out.append({"kind": "serial_set", "key": d,
                    "url": f"https://www.govinfo.gov/content/pkg/{d}/pdf/{d}.pdf", "project_sha256": None,
                    "project_source": "page URLs cited in jobs/*/output (git grep SERIALSET)"})
    json.dump(out, open("TARGETS.json", "w"), indent=1)
    print(len(out), "targets")


if __name__ == "__main__":
    main()
