"""Namier: find every held order naming the same person, once for all one-person orders.

Zero-token and offline. Reads the project's held order texts (through jobs/_lib/eo_identity),
the X1 type table and the date indexes; writes leads only. See README.md.
"""
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import namier  # noqa: E402


def main():
    out = pathlib.Path(os.environ.get("OUTPUT_DIR", HERE / "output"))
    repo = pathlib.Path(os.environ.get("REPO_ROOT", HERE.parents[1]))
    out.mkdir(parents=True, exist_ok=True)
    print("namier: running offline tests", flush=True)
    test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py"],
                          cwd=str(repo), capture_output=True, text=True)
    (out / "tests.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    print(test.stderr.strip().splitlines()[-1] if test.stderr.strip() else "tests: no output", flush=True)
    if test.returncode != 0:
        print(test.stdout + test.stderr)
        sys.exit("namier: offline tests failed; no output replaced")
    summary = namier.run(str(repo), str(out))
    counts = summary["counts"]
    if counts.get("subjects", 0) == 0:
        sys.exit("namier: no one-person orders found in the type table; refusing to publish an empty search")


if __name__ == "__main__":
    main()
