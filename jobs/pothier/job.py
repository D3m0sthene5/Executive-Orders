"""GitHub Actions entry point: rebuild the member table, then apply every doctrine (see README.md)."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import members  # noqa: E402
import pothier  # noqa: E402
import fetch  # noqa: E402

out = os.environ.get("OUTPUT_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
fetch.main()
members.main()
pothier.main(["apply", "--members", os.path.join(out, "MEMBERS.jsonl"), "--out", out])
