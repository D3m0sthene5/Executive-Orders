"""Ptolemy runner entry: tests first, then one bounded share of the custody work. See README.md."""
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ptolemy  # noqa: E402


def main():
    repo = pathlib.Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
    out = pathlib.Path(os.environ.get("OUTPUT_DIR", HERE / "output")).resolve()
    cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR", HERE.parent / "ptolemy-custody-work")).resolve()
    prior = pathlib.Path(os.environ.get("JOB_PRIOR_OUTPUT_DIR") or str(HERE / "output")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py"],
                          cwd=str(repo), capture_output=True, text=True)
    (out / "tests.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    if test.returncode != 0:
        print(test.stdout + test.stderr)
        sys.exit("ptolemy: offline tests failed; no output replaced")
    ptolemy.run(HERE, out, cache, prior=prior)


if __name__ == "__main__":
    main()
