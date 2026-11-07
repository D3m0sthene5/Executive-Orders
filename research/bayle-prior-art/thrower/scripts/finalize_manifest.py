"""Add the SHA-256 of every result file, and the project inputs' commit, to MANIFEST.json.

usage: py -I finalize_manifest.py THROWER_DIR
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thrower_lib import sha256_file


def main():
    root = sys.argv[1]
    mp = os.path.join(root, "MANIFEST.json")
    man = json.load(open(mp, encoding="utf-8"))
    res = {}
    skip = {"MANIFEST.json", "PROJECT_INPUTS.json", "thrower_orders.csv"}
    for f in sorted(os.listdir(root)):
        p = os.path.join(root, f)
        if os.path.isfile(p) and f not in skip and f.endswith((".csv", ".json")):
            res[f] = {"bytes": os.path.getsize(p), "sha256": sha256_file(p)}
    man["results"] = res
    pi = json.load(open(os.path.join(root, "PROJECT_INPUTS.json"), encoding="utf-8"))
    man["project_inputs"] = {"ref": pi["ref"], "commit": pi["commit"], "manifest": "PROJECT_INPUTS.json",
                             "manifest_sha256": sha256_file(os.path.join(root, "PROJECT_INPUTS.json")), "files": len(pi["files"])}
    man["derived"]["thrower_orders.csv"]["sha256"] = sha256_file(os.path.join(root, "thrower_orders.csv"))
    with open(mp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(len(res), "result files hashed")


main()
