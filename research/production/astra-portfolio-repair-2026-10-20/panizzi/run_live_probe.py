"""Reproduce the bounded three-primary-document probe through source-ladder.

Only the supplied URLs are tried, with no retry. The normal job remains
unchanged: these overrides apply only to this explicit diagnostic process.
"""
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OUTPUT_DIR", HERE / "live-probe")).resolve()
CACHE = Path(os.environ.get("JOB_CACHE_DIR", "/tmp/panizzi-primary-cache")).resolve()
os.environ.update({"REPO_ROOT": str(REPO), "OUTPUT_DIR": str(OUT), "JOB_CACHE_DIR": str(CACHE),
                   "JOB_NAME": "source-ladder", "JOB_CARRY_FORWARD": "0", "JOB_READINESS_PLAN": "0",
                   "JOB_LIMIT": "3", "JOB_MAX_REQUESTS": "3", "JOB_MAX_DOWNLOAD_MB": "50", "JOB_WORKERS": "1",
                   "JOB_ONLY": "queue:EO:13792:Astra portfolio DOI,queue:EO:13807:Astra portfolio OMB"})
os.environ.pop("JOB_OFFLINE", None)
sys.path.insert(0, str(REPO / "jobs/source-ladder"))
import fetch_ladder
import job

original_fetcher_init = fetch_ladder.Fetcher.__init__
original_ladder_init = fetch_ladder.Ladder.__init__


def bounded_fetcher(self, *args, **kwargs):
    kwargs.update(max_retries=0, timeout=30)
    original_fetcher_init(self, *args, **kwargs)


def supplied_urls_only(self, *args, **kwargs):
    kwargs["tiers"] = ("given",)
    original_ladder_init(self, *args, **kwargs)


fetch_ladder.Fetcher.__init__ = bounded_fetcher
fetch_ladder.Ladder.__init__ = supplied_urls_only
start = time.time()
job.main()
files = []
for line in (OUT / "SOURCES.jsonl").read_text().splitlines():
    source = json.loads(line)
    path = CACHE / source["cache_path"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != source["sha256"]:
        raise RuntimeError("downloaded source hash does not match its receipt")
    extension = ".pdf" if path.read_bytes()[:5] == b"%PDF-" else ".html"
    rel = "files/" + actual + extension
    (OUT / "files").mkdir(exist_ok=True)
    shutil.copyfile(path, OUT / rel)
    files.append({"wanted_id": source["wanted_id"], "url": source["url"], "sha256": actual,
                  "bytes": path.stat().st_size, "retained_file": rel, "text_path": source["text_path"],
                  "evidence_tier": source["evidence_tier"]})
(OUT / "PRIMARY_FILES.json").write_text(json.dumps(files, indent=2) + "\n")
pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (REPO / "jobs/source-ladder").glob("*.py")}
(OUT / "LOCAL_RUN.json").write_text(json.dumps({
    "kind": "local bounded primary-source probe; not GitHub STATUS.json",
    "base_commit": "91116f879978902343dafa88490b9b19587b10da", "working_source_sha256": pins,
    "supplied_urls_only": True, "max_document_requests": 3, "max_retries": 0,
    "timeout_seconds": 30, "max_download_mb": 50, "carry_forward": False,
    "seconds_including_tests": round(time.time() - start, 3),
    "model_tokens": 0, "model_token_basis": "deterministic job makes no LLM calls; agent build/review cost unavailable",
    "cash_cost": None, "legal_finding": None}, indent=2) + "\n")
