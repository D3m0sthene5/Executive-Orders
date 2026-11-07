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
    if (HERE / "PAUSED").is_file():
        # Encyclopedie (owner, 2026-11-06): the repository is near GitHub's 10 GB cap. Carry the held
        # files forward and fetch nothing until raw bytes are stored outside git. See PAUSED.
        ptolemy.run(HERE, out, cache, prior=prior, archive_limit=0, live_limit=0)
        return
    ptolemy.run(HERE, out, cache, prior=prior)


if __name__ == "__main__":
    main()
