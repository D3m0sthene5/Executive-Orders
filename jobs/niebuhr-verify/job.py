"""Niebuhr verify runner entry: tests first, then fetch and check every quoted source. See README.md."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import verify  # noqa: E402


def main():
    root = os.path.abspath(os.environ.get("REPO_ROOT") or os.path.join(HERE, "..", ".."))
    out = os.path.abspath(os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output"))
    cache = os.environ.get("JOB_CACHE_DIR") or os.path.join(HERE, "..", "niebuhr-verify-cache")
    os.makedirs(out, exist_ok=True)
    t = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", HERE, "-p", "test_*.py"], capture_output=True, text=True)
    with open(os.path.join(out, "tests.txt"), "w", encoding="utf-8") as fh:
        fh.write(t.stdout + t.stderr)
    if t.returncode:
        sys.exit("niebuhr-verify: offline tests failed; no output replaced")
    print(json.dumps(verify.run(root, out, cache, max_requests=int(os.environ.get("JOB_MAX_REQUESTS", "1500"))), indent=1))


if __name__ == "__main__":
    main()
