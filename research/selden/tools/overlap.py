"""Compare every Selden source URL and sha256 with Ptolemy's request list (PR #159) and Pothier's sources (PR #162).

usage: python3 -I research/selden/tools/overlap.py   (after `git fetch origin claude/ptolemy-custody
claude/pothier-family-doctrine`). Writes research/selden/census/OVERLAP.json. Zero tokens.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def show(ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def norm(u):
    return (u or "").split("#", 1)[0].split("?", 1)[0]


def main():
    pt_urls, pt_sha = set(), set()
    for line in show("origin/claude/ptolemy-custody", "jobs/ptolemy-custody/REQUESTS.jsonl").splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        pt_urls.add(norm(d.get("url")))
        if d.get("sha256"):
            pt_sha.add(d["sha256"])
    po_urls = set()
    ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", "origin/claude/pothier-family-doctrine", "--",
                         "jobs/pothier/output", "research/pothier"], cwd=ROOT, capture_output=True, text=True).stdout
    for path in ls.splitlines():
        if path.endswith("SOURCES.jsonl") or path.endswith("FOR_SELDEN.csv"):
            for line in show("origin/claude/pothier-family-doctrine", path).splitlines():
                for tok in line.replace('"', " ").replace(",", " ").split():
                    if tok.startswith("https://"):
                        po_urls.add(norm(tok))
    report = {"ptolemy_requests": len(pt_urls), "pothier_urls": len(po_urls), "jobs": {}}
    for job in ("selden-fr-citers", "selden-fr-acting", "selden-statutes"):
        p = ROOT / "jobs" / job / "output" / "SOURCES.jsonl"
        rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.is_file() else []
        urls = {norm(r.get("issue_url") or r.get("url")) for r in rows}
        shas = {r.get("sha256") for r in rows} | {r.get("issue_sha256") for r in rows if r.get("issue_sha256")}
        report["jobs"][job] = {"sources": len(rows), "url_on_ptolemy_list": sorted(urls & pt_urls)[:50],
                               "sha_on_ptolemy_list": len(shas & pt_sha), "url_in_pothier": sorted(urls & po_urls)[:50]}
    out = ROOT / "research/selden/census/OVERLAP.json"
    out.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
