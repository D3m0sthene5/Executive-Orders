"""Cassiodorus runner entry: keep the bytes of APP pages that claims cite. See README.md."""
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cassiodorus  # noqa: E402


def main():
    repo = pathlib.Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
    out = pathlib.Path(os.environ.get("OUTPUT_DIR", HERE / "output")).resolve()
    cache = pathlib.Path(os.environ.get("JOB_CACHE_DIR", out / "cache")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    # Carry every page kept by the previous generation forward; its bytes are rehashed before reuse.
    prior = os.environ.get("JOB_PRIOR_OUTPUT_DIR") or str(HERE / "output")
    prior_raw = pathlib.Path(prior) / "raw"
    if prior_raw.is_dir() and prior_raw.resolve() != (out / "raw").resolve():
        (out / "raw").mkdir(exist_ok=True)
        for p in prior_raw.glob("*.html"):
            if cassiodorus.sha256(p.read_bytes()) == p.stem:
                shutil.copyfile(p, out / "raw" / p.name)
    prior_sources = pathlib.Path(prior) / "SOURCES.jsonl"
    if prior_sources.is_file() and prior_sources.resolve() != (out / "SOURCES.jsonl").resolve():
        shutil.copyfile(prior_sources, out / "SOURCES.jsonl")
    test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_*.py"],
                          cwd=str(repo), capture_output=True, text=True)
    (out / "tests.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    if test.returncode != 0:
        print(test.stdout + test.stderr)
        sys.exit("cassiodorus: offline tests failed; no output replaced")
    cassiodorus.run(repo, HERE, out, cache)


if __name__ == "__main__":
    main()
