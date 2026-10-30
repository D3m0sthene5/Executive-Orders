"""Bounded integration evidence through existing native commands; never publish."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.environ["VALIDATION_OUTPUT"]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
records = []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(label, args, *, env=None, allowed=(0,), timeout=480):
    started = time.monotonic()
    with (OUT / (label + ".log")).open("w") as log:
        result = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT,
                                env={**os.environ, **(env or {})}, stdout=log,
                                stderr=subprocess.STDOUT, timeout=timeout)
    record = {"label": label, "command": list(map(str, args)),
              "returncode": result.returncode, "seconds": time.monotonic() - started,
              "log_sha256": sha(OUT / (label + ".log"))}
    records.append(record)
    assert result.returncode in allowed, record
    return record


claims = {str(p.relative_to(ROOT)): sha(p)
          for p in (ROOT / "research/readiness/claims").glob("*.jsonl")}
try:
    packet = "research/excavator/opus-native-rehearsal-2026-10-29/r1/packet/supp"
    manifest = "research/excavator/opus-native-rehearsal-2026-10-29/r1/completion/COMPLETION.json"
    dest = ROOT / "research/integration-native-rehearsal"
    # A frozen historical packet may be stale after integration. Retain the
    # native refusal rather than repinning it or borrowing old reviewer approval.
    view = run("retained-view", ["-I", "jobs/claim-kit/kit.py", "view", packet], allowed=(0, 2))
    complete = run("retained-complete", ["-I", "jobs/claim-kit/kit.py", "complete", manifest,
                                        "--write", dest], allowed=(0, 1, 2))
    for record in (view, complete):
        log = (OUT / (record["label"] + ".log")).read_text()
        assert "Traceback (most recent call last)" not in log, log
        if record["returncode"] == 2:
            assert "claim-kit:" in log, log
            assert any(x in log.lower() for x in ("stale", "changed", "mismatch")), log
            record["outcome"] = "native_frozen_input_refusal_requires_review"
    if complete["returncode"] in (0, 1):
        assert (dest / "TALLY.json").is_file(), "native completion produced no tally"
    if (dest / "TALLY.json").exists():
        tally = json.loads((dest / "TALLY.json").read_text())
        complete["tally"] = tally
        artifact = dest / "CLAIMS.publishable.jsonl"
        complete["publishable_sha256"] = sha(artifact) if artifact.exists() else None
        assert tally["claims_published"] == 0
        # This is a comparison receipt, not an assertion of scientific adoption.
        complete["matches_retained_five"] = (
            len(tally["eligible"]) == 5 and complete["publishable_sha256"] ==
            "9ddb845bd75f877ba86c5742e9e4e799f6af1871d5b76d7c223792419a2fd897")
    cruden = ROOT / "research/progress/corpus-evidence-retrieval"
    source = ROOT / "research/excavator/claude-nira-sweep-2026-10-29/cruden.py"
    for script, label, extra in [("fixture_challenge.py", "fixture", []),
                                  ("fixture_challenge.py", "overflow", ["--overflow-files", "65"]),
                                  ("staleness_challenge.py", "staleness", []),
                                  ("deep_challenge.py", "deep", []),
                                  ("final_contract_challenge.py", "contract", [])]:
        report = OUT / (label + ".json")
        run(label, [cruden / "challenge" / script, source, "--report", report, *extra])
        assert json.loads(report.read_text())["all_checks_pass"]
    profiler = cruden / "profile/profile_cruden.py"
    native_packet = cruden / "native/r1-input"
    cache_env = {"CRUDEN_CACHE_DIR": str(OUT / "cruden-cache")}
    for label, extra in [("legacy", ["--cruden-source", cruden / "challenge/BASELINE_CRUDEN.py"]),
                          ("cold", ["--reference", OUT / "legacy"]),
                          ("warm", ["--reference", OUT / "legacy"])]:
        run("cruden-" + label, [profiler, ROOT, native_packet, OUT / label,
                               "--no-profile", *extra], env=cache_env)
        result = json.loads((OUT / label / "RESULT.json").read_text())
        assert result["cruden"]["completed"], result
        if label != "legacy":
            assert all(result["reference_equivalence"].values()), result
        records[-1]["profile"] = result
finally:
    unchanged = claims == {str(p.relative_to(ROOT)): sha(p)
                          for p in (ROOT / "research/readiness/claims").glob("*.jsonl")}
    (OUT / "RESULT.json").write_text(json.dumps({
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "records": records, "canonical_claims_unchanged": unchanged,
        "scope": "native engineering rehearsal; no publication or scientific approval"}, indent=2) + "\n")
    assert unchanged, "canonical claims changed during read-only rehearsal"
