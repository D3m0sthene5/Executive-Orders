"""Lachmann: collate held working texts against the register and record machine confirmations.

Offline and deterministic. Reads the readiness tracker output, the Domesday register, the Pinakes
ingest tables and every held fragment text; writes CONFIRMATIONS.jsonl, RESIDUAL.csv and SUMMARY.json
to OUTPUT_DIR. See README.md.
"""
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lachmann  # noqa: E402


def main():
    out = pathlib.Path(os.environ.get("OUTPUT_DIR", HERE / "output"))
    repo = pathlib.Path(os.environ.get("REPO_ROOT", HERE.parents[1]))
    out.mkdir(parents=True, exist_ok=True)
    print("lachmann: running offline tests", flush=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py"],
                          cwd=str(repo), capture_output=True, text=True, env=env)
    (out / "tests.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    print(test.stderr.strip().splitlines()[-1] if test.stderr.strip() else "tests: no output", flush=True)
    if test.returncode != 0:
        print(test.stdout + test.stderr)
        sys.exit("lachmann: offline tests failed; no output replaced")
    start = time.time()
    summary = lachmann.run(repo, out)
    print(f"lachmann: {summary['confirmed']} of {summary['in_scope']} in-scope orders confirmed "
          f"in {time.time() - start:.1f}s", flush=True)
    if summary["in_scope"] == 0:
        sys.exit("lachmann: no in-scope orders found; the tracker output may be missing")


if __name__ == "__main__":
    main()
