"""Make hathi_seed/ (MANIFEST.csv, SCAN.json) by running the Hathi part of prewar.py from a machine that
www.hathitrust.org does not challenge (the owner's PC). The GitHub runner is challenged every time and the job does
not answer or evade a challenge, so it carries this seed instead. Usage: py -I seed_hathi.py
Standard library only; same robots.txt and pacing rules as the job (jobs/_lib/fetch_pool.py)."""
import csv
import json
import pathlib
import sys
import tempfile

here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here))
sys.path.insert(0, str(here.parent / "_lib"))
import lsa  # noqa: E402
import prewar  # noqa: E402
from fetch_pool import FetchPool  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    pool = FetchPool(pathlib.Path(tmp), workers=2, per_host=2, user_agent=lsa.UA, min_interval=0.25, max_bytes=60_000_000, timeout=180)
    rows, summ = prewar.build(pool, lsa.UA, skip_hathi=False)
hathi = [r for r in rows if r["source"] == "hathitrust"]
if not summ["hathi"].get("scan"):
    sys.exit("hathifile could not be read from this machine: " + json.dumps(summ["hathi"])[:300])
out = here / "hathi_seed"
out.mkdir(exist_ok=True)
with open(out / "MANIFEST.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=prewar.MANIFEST_COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(hathi)
scan = {"made_utc": lsa.__dict__.get("now") or __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hathifile": summ["hathi"]["scan"], "bib_api": {k: v for k, v in summ["hathi"].get("bib_api", {}).items() if k != "records"}}
(out / "SCAN.json").write_text(json.dumps(scan, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print("rows", len(hathi), json.dumps(scan)[:600])
