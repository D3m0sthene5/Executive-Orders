"""Copy the project files the Thrower comparison reads out of git (no checkout) into a cache folder.

usage: py -I fetch_project_inputs.py WORKTREE REF CACHE_DIR OUT_MANIFEST.json

Every file is read with `git show REF:path`; the manifest records REF's commit, each path, its git blob id,
SHA-256 and size, so the comparison can be rerun on exactly these bytes.
"""
import hashlib, json, os, subprocess, sys

FILES = [
    "jobs/domesday-register/output/REGISTER.csv",
    "jobs/domesday-register/output/CANDIDATES_NOT_IN_REGISTER.csv",
    "jobs/domesday-register/output/STATUS.json",
    "jobs/later-events/output/EDGES.csv",
    "jobs/later-events/output/CATALOG_INDEX.csv",
    "jobs/later-events/output/STATUS.json",
    "jobs/later-events/CATALOG_DATE_CORRECTIONS.csv",
    "jobs/ofr-codification-1989/output/DISPOSITION_1989.csv",
    "jobs/ofr-codification-1989/output/CODIFIED_1989.csv",
    "jobs/ofr-codification-1989/output/STATUS.json",
    "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
    "jobs/readiness-tracker/output/CONTESTED.csv",
    "jobs/readiness-tracker/output/STATUS.json",
    "jobs/status-history/output/STATUS.json",
    "jobs/peano-formulario/output/STATUS.json",
]
# sharded outputs read as whole folders
FOLDERS = ["jobs/status-history/output/events", "jobs/peano-formulario/output/lemmas"]


def git(wt, *a):
    return subprocess.run(["git", "-C", wt, *a], check=True, capture_output=True).stdout


def main():
    wt, ref, cache, out = sys.argv[1:5]
    commit = git(wt, "rev-parse", ref).decode().strip()
    paths = list(FILES)
    for f in FOLDERS:
        for line in git(wt, "ls-tree", "-r", "--name-only", ref, f + "/").decode().splitlines():
            paths.append(line.strip())
    rows = []
    for p in paths:
        data = git(wt, "show", f"{ref}:{p}")
        dest = os.path.join(cache, p)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(data)
        rows.append({"path": p, "git_blob": git(wt, "rev-parse", f"{ref}:{p}").decode().strip(),
                     "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"ref": ref, "commit": commit, "files": rows}, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(commit, len(rows), "files", sum(r["bytes"] for r in rows), "bytes")


main()
