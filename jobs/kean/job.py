#!/usr/bin/env python3
"""Daily Kean run: tests, then the register check, then a fresh copy of the brief in output/.

The committed brief at HANDOFF/KEAN.md is written by agents with `kean.py brief`; this job does not
write outside OUTPUT_DIR. It fails (so STATUS.json shows it) when the register has structural errors.
"""
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kean  # noqa: E402


def main():
    out = os.environ.get("OUTPUT_DIR", os.path.join(HERE, "output"))
    root = os.environ.get("REPO_ROOT", ".")
    os.makedirs(out, exist_ok=True)
    tests = subprocess.run([sys.executable, "-I", os.path.join(HERE, "test_kean.py")], capture_output=True, text=True)
    print(tests.stderr[-2000:])
    if tests.returncode:
        print("Kean tests failed")
        return 1
    repo = kean.Repo(root)
    errors, warnings = kean.check(repo)
    with open(os.path.join(out, "KEAN.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(kean.render_brief(repo))
    summary = {"errors": errors, "warnings": warnings,
               "open_owner_questions": sum(1 for a in kean.current(kean.load(repo, "asks")) if a["status"] == "open"),
               "decisions": len(kean.current(kean.load(repo, "decisions"))),
               "findings": len(kean.current(kean.load(repo, "findings"))),
               "legacy_reports_unsummarized": len(kean.legacy_reports(repo))}
    with open(os.path.join(out, "SUMMARY.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")
    for e in errors:
        print("ERROR " + e)
    for w in warnings:
        print("WARN  " + w)
    print(f"Kean: {len(errors)} errors, {len(warnings)} warnings, {summary['open_owner_questions']} open owner questions")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
