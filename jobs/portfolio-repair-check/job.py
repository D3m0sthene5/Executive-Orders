"""Bounded regression and evidence-to-tracker check for the portfolio repair.

Uses the existing packet loader, source-audit hold loader and actual claim
checker. It publishes observations only, never canonical claims or legal ends.
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
import urllib.parse
import urllib.request

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = "research/excavator/astra-portfolio-repair-2026-10-20"
DISPUTED = ("EO:13792", "EO:13101", "EO:13148", "EO:13783", "EO:13807")
POSITIVE, BLOCKED = "EO:13037", "EO:11513"
CHECKED = (*DISPUTED, POSITIVE)
SUITES = {
    "source-ladder": ["test_request_contract", "test_panizzi2_defects", "test_report_dates",
                      "test_fetch_ladder", "test_panizzi_resolvers"],
    "claim-kit": ["test_lifecycle_obligations", "test_act_overrides", "test_batch", "test_excavate"],
    "hamilton-token-audit": ["test_profile"],
    "mountweazel": ["test_mountweazel"],
    "polya": ["test_polya"],
    "llull": ["test_llull", "test_gates"],
    "junto": ["test_junto"],
    "lambertini": ["test_lambertini", "test_progress"],
    "portfolio-repair-check": ["test_job"],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def offline_guard():
    """Catch accidental Python network access in this process; fixtures use fake transports."""
    attempts = []

    def hook(event, args):
        if event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "socket.gethostbyname"}:
            attempts.append(event)
            raise RuntimeError("network access is disabled in portfolio-repair-check")
    sys.addaudithook(hook)
    return attempts


def load(name, path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_worker(repo, out, job):
    # CLI fixture tests choose their own temporary output. A runner-level
    # OUTPUT_DIR would override that choice in Llull and invalidate the tests.
    os.environ.pop("OUTPUT_DIR", None)
    sys.path.insert(0, str(repo / "jobs" / job))
    attempts = offline_guard()
    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.loadTestsFromNames(SUITES[job]))
    record = {"job": job, "modules": SUITES[job], "tests_run": result.testsRun,
              "failures": len(result.failures), "errors": len(result.errors),
              "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
              "network_attempts_blocked": attempts, "elapsed_seconds": round(time.monotonic() - started, 3),
              "passed": result.wasSuccessful() and not attempts}
    write(out / "tests" / (job + ".json"), record)
    return 0 if record["passed"] else 1


def verification_pairs(checker, claims):
    pairs = set()
    for claim in claims:
        for _, key, value, _ in checker.walk(claim):
            refs = ([value] if key in checker.SOURCE_KEYS and isinstance(value, dict) else
                    value if key in checker.SOURCE_LIST_KEYS and isinstance(value, list) else [])
            for ref in refs:
                if isinstance(ref, dict) and urllib.parse.urlsplit(ref.get("url") or "").hostname == "www.govinfo.gov":
                    pairs.add((ref.get("sha256"), ref.get("url")))
    return pairs


def verify_sources(checker, repo, out, claims, manifest, network):
    """Reuse the existing verifier, once for each frozen source; record swallowed transport errors."""
    sources = manifest["sources"]
    expected = {(r["sha256"], r["url"]) for r in sources}
    if (len(sources) != 10 or len(expected) != 10 or len({r["sha256"] for r in sources}) != 10
            or verification_pairs(checker, claims) != expected
            or any(not checker.S.sha_hex(h) or not u.startswith("https://www.govinfo.gov/") for h, u in expected)):
        raise ValueError("selected claims must match the frozen ten GovInfo SHA256/URL pairs exactly")
    checker._VERIFY.update(left=10 if network else 0, last=0.0)
    cache = out / "checker-cache"
    records = []
    for source in sources:
        digest, url = source["sha256"], source["url"]
        relative = Path("verified") / digest[:2] / (digest + ".bin")
        target, prior = cache / relative, repo / ".job-cache/claim-checker" / relative
        record = {"sha256": digest, "url": url, "download_attempted": False,
                  "bytes_returned_by_read": 0, "reused_cache_bytes": 0, "error": None}
        if not target.exists() and prior.is_file():
            raw = prior.read_bytes()
            if sha(raw) == digest:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                record.update(reused_cache_path=prior.relative_to(repo).as_posix(), reused_cache_bytes=len(raw))
            else:
                record["rejected_prior_cache_sha256"] = sha(raw)
        original_open = urllib.request.urlopen

        @contextlib.contextmanager
        def observed_open(request, *args, **kwargs):
            record["download_attempted"] = True
            try:
                with original_open(request, *args, **kwargs) as response:
                    record.update(http_status=getattr(response, "status", None), final_url=response.geturl())

                    class ObservedResponse:
                        def read(self, limit):
                            try:
                                raw = response.read(min(limit, 5_000_001))
                            except Exception:
                                record["bytes_returned_by_read"] = None
                                raise
                            record.update(bytes_returned_by_read=len(raw), bytes_returned_sha256=sha(raw))
                            if len(raw) > 5_000_000:
                                raise ValueError("cited-source response exceeds the 5,000,000-byte bound")
                            return raw
                    yield ObservedResponse()
            except Exception as exc:
                record["error"] = {"type": type(exc).__name__, "message": str(exc)}
                raise

        started = time.monotonic()
        try:
            urllib.request.urlopen = observed_open
            verified = checker.verify_by_download(url, digest, cache)
        except Exception as exc:
            record["error"] = {"type": type(exc).__name__, "message": str(exc)}
            verified = None
        finally:
            urllib.request.urlopen = original_open
        record.update(verified=verified is True,
                      result="verified" if verified is True else "hash_mismatch" if verified is False else "unavailable",
                      elapsed_seconds=round(time.monotonic() - started, 3),
                      verified_bytes=target.stat().st_size if verified is True else 0,
                      cache_path=target.relative_to(out).as_posix() if verified is True else None)
        records.append(record)
    checker._VERIFY["left"] = 0
    return {"schema": "bounded-existing-source-verification/v1", "network_enabled": network,
            "purpose": "Verify exact sources already cited by six canonical claims; no new research acquisition.",
            "declared_bounds": {"sources": 10, "maximum_initial_url_attempts": 10,
                "timeout_seconds_per_open": 120, "maximum_document_bytes": 5_000_000,
                "response_read_limit_bytes": 5_000_001, "maximum_response_bytes_read": 50_000_010,
                "minimum_attempt_spacing_seconds": 1,
                "retries_per_source": 0, "downloader": "claim-checker.verify_by_download"},
            "source_count": len(records), "verified_count": sum(r["verified"] for r in records),
            "download_attempts": sum(r["download_attempted"] for r in records),
            "cache_reused_count": sum(r["reused_cache_bytes"] > 0 for r in records),
            "cache_reused_bytes": sum(r["reused_cache_bytes"] for r in records),
            "known_bytes_returned_by_read": sum(r["bytes_returned_by_read"] or 0 for r in records),
            "download_byte_coverage_complete": all(r["bytes_returned_by_read"] is not None for r in records),
            "verified_bytes": sum(r["verified_bytes"] for r in records), "sources": records}


def checker_errors(summary, claims):
    errors = []
    current = {r.get("instrument_id"): r for r in claims}
    if len(claims) != len(CHECKED) or set(current) != set(CHECKED):
        errors.append("actual checker must report exactly the six selected claims")
    for key, expected in (("claims_checked", 6), ("claims_parse_errors", 0), ("claims_checker_errors", 0),
                          ("claims_all_checks_passed", 6), ("claims_mechanical_pass", 6), ("claims_gate_passed", 6)):
        if summary.get(key) != expected:
            errors.append(f"actual checker {key}={summary.get(key)!r}; required {expected}")
    for iid in CHECKED:
        row = current.get(iid, {})
        if row.get("mechanical_result") != "pass" or row.get("gate_passed") is not True or row.get("all_checks_passed") is not True:
            errors.append(f"{iid}: checker mechanical={row.get('mechanical_result', 'not_run')}, "
                          f"gate={row.get('gate_passed')!r}, all_checks_passed={row.get('all_checks_passed')!r}")
    return errors


def checker_worker(repo, out):
    checker = load("portfolio_actual_checker", repo / "jobs/claim-checker/checker.py")
    os.environ.update(OUTPUT_DIR=str(out / "checker"), JOB_CACHE_DIR=str(out / "checker-cache"),
                      CLAIM_CHECKER_VERIFY_DOWNLOADS="0", JOB_LIMIT="", CLAIM_CHECKER_CSV_ALL_ROWS="1")
    claims = [json.loads(line) for line in (out / "EFFECTIVE_CLAIMS.jsonl").read_text().splitlines() if line.strip()]
    errors = []
    try:
        verification = verify_sources(checker, repo, out, claims,
            json.loads((HERE / "verification_sources.json").read_bytes()), os.environ.get("GITHUB_ACTIONS") == "true")
        if verification["verified_count"] != 10:
            errors.append("not all ten exact cited GovInfo sources could be byte-verified")
    except Exception as exc:
        verification = {"error": type(exc).__name__ + ": " + str(exc), "verified_count": 0}
        errors.append(verification["error"])
    write(out / "SOURCE_VERIFICATION.json", verification)
    checker._VERIFY["left"] = 0
    attempts = offline_guard()
    summary, checked = {}, []
    try:
        summary = checker.main(["--claims", str(out / "EFFECTIVE_CLAIMS.jsonl")])
        checked = json.loads((out / "checker/PER_CLAIM.json").read_bytes())["claims"]
    except Exception as exc:
        errors.append("checker execution: " + type(exc).__name__ + ": " + str(exc))
    errors += checker_errors(summary, checked)
    if attempts:
        errors.append("actual checker attempted network access after bounded verification")
    current = {r.get("instrument_id"): r for r in checked}
    write(out / "CHECKER_ACCEPTANCE.json", {"passed": not errors, "errors": errors,
        "network_attempts_blocked": attempts, "summary": summary,
        "claims": [{"instrument_id": iid, "observed": iid in current,
                    "mechanical_result": current.get(iid, {}).get("mechanical_result", "not_run"),
                    "gate_passed": current.get(iid, {}).get("gate_passed"),
                    "all_checks_passed": current.get(iid, {}).get("all_checks_passed")} for iid in CHECKED]})
    return 0 if not errors else 1


class Inputs:
    def __init__(self, repo):
        self.repo, self.pins = repo, {}

    def path(self, rel):
        path = (self.repo / rel).resolve()
        if not path.is_relative_to(self.repo):
            raise ValueError("input path outside repository: " + str(rel))
        return path

    def read(self, rel):
        path = self.path(rel)
        raw = path.read_bytes()
        key, value = path.relative_to(self.repo).as_posix(), sha(raw)
        if key in self.pins and self.pins[key] != value:
            raise ValueError("input changed during validation: " + key)
        self.pins[key] = value
        return raw

    def obj(self, rel):
        return json.loads(self.read(rel))

    def verify(self, rel, expected):
        if sha(self.read(rel)) != expected:
            raise ValueError("input hash mismatch: " + str(rel))

    def unchanged(self):
        for rel, value in list(self.pins.items()):
            self.verify(rel, value)


def run_worker(repo, out, flag, job=None):
    label = job or "checker"
    cmd = [sys.executable, "-B", str(HERE / "job.py"), flag]
    if job:
        cmd.append(job)
    log = out / ("tests" if job else "checker") / "{}.log".format(label)
    log.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "REPO_ROOT": str(repo), "OUTPUT_DIR": str(out),
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
           "TMPDIR": str(out / "tmp"), "JOB_CACHE_DIR": str(out / "checker-cache"),
           "CLAIM_CHECKER_VERIFY_DOWNLOADS": "0"}
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(cmd, cwd=repo / "jobs" / job if job else repo,
                                env=env, stdout=stream, stderr=subprocess.STDOUT, check=False)
    print(label + ": " + ("passed" if result.returncode == 0 else "FAILED") + "; " + str(log), flush=True)
    return result.returncode


def integration(repo, out, inputs):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    gate = load("portfolio_claim_gate", repo / "research/stage19/code/claim_gate.py")
    batch = load("portfolio_packet_batch", repo / "jobs/claim-kit/batch.py")
    tracker = load("portfolio_tracker", repo / "jobs/readiness-tracker/tracker.py")
    lambertini = load("portfolio_lambertini", repo / "jobs/lambertini/lambertini.py")
    gate_base = BASE + "/lambertini-gate-v1/"
    inputs.obj(gate_base + "CONTRACT.json")
    observation = inputs.obj(gate_base + "OBSERVATION.json")
    historical_gate = inputs.obj(gate_base + "stopped-continuation/CONTINUATION_GATE.json")
    for evidence in observation["evidence"]:
        inputs.verify(evidence["path"], evidence["sha256"])
    continuation = out / "stopped-continuation"
    with (out / "continuation.log").open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log):
        gate_exit = lambertini.main(["--repo", str(repo), "continue", "--pool", "LAMBS",
            "--n", "1", "--seed", "astra-repair-offline-gate-replay", "--out", str(continuation),
            "--gate-contract", str(inputs.path(gate_base + "CONTRACT.json")),
            "--gate-observation", str(inputs.path(gate_base + "OBSERVATION.json"))])
    gate_receipt = json.loads((continuation / "CONTINUATION_GATE.json").read_bytes())
    require(gate_exit == 5 and gate_receipt == historical_gate
            and gate_receipt.get("status") == "untested" and gate_receipt.get("may_continue") is False
            and not list(continuation.glob("PROBE_BATCH_*.json")),
            "historical incomplete-plant gate did not stop before selecting continuation work")
    packet_path = BASE + "/bounded-preparation/PACKET.json"
    inputs.read(packet_path)
    packet, dossiers = batch.load_packet(inputs.path(packet_path).parent, repo)
    require(set(dossiers) == set((*CHECKED, BLOCKED)), "packet membership differs from the bounded seven-case sample")
    for rel, expected in packet["held_text_file_pins"].items():
        inputs.verify(rel, expected)
    for pin in packet["input_pins"].values():
        inputs.verify(pin["path"], pin["file_sha256"])

    claims, locations = {}, {}
    for path in sorted((repo / "research/readiness/claims").glob("*.jsonl")):
        rel = path.relative_to(repo).as_posix()
        for line_number, line in enumerate(inputs.read(rel).decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            claim = json.loads(line)
            iid = claim["instrument_id"]
            claims[iid] = claim
            locations[iid] = {"path": rel, "line": line_number, "claim_sha256": gate.claim_sha(claim)}
    require(all(iid in claims for iid in CHECKED), "a selected effective canonical claim is missing")
    require(BLOCKED not in claims, "EO:11513 is no longer a no-claim control; update the bounded design explicitly")
    if not all(iid in claims for iid in CHECKED):
        raise ValueError("cannot run the six-claim checker subset: selected canonical claim missing")
    (out / "EFFECTIVE_CLAIMS.jsonl").write_text(
        "".join(json.dumps(claims[iid], sort_keys=True, ensure_ascii=False) + "\n" for iid in CHECKED), encoding="utf-8")

    manifest = inputs.obj(BASE + "/lambertini-review/AUDIT_MANIFEST.v1.json")
    audits = {row["instrument_id"]: row for row in manifest["audits"]}
    require(len(manifest["audits"]) == len(audits) and set(audits) == set(DISPUTED),
            "audit manifest must contain the five distinct disputed claims")
    inputs.read("research/readiness/SOURCE_AUDIT_HOLDS.jsonl")
    hold_problems = []
    holds = tracker.load_source_audit_holds(str(repo), claims, gate, hold_problems)
    # Pin every review used by the existing hold loader, including unrelated active holds.
    for line in inputs.read("research/readiness/SOURCE_AUDIT_HOLDS.jsonl").decode("utf-8").splitlines():
        if line.strip():
            hold = json.loads(line)
            inputs.verify(hold["review_path"], hold["review_sha256"])

    reviews = {}
    for iid in DISPUTED:
        if iid not in audits:
            continue
        entry = audits[iid]
        inputs.verify(entry["audit_path"], entry["audit_sha256"])
        review = inputs.obj(entry["audit_path"])
        reviews[iid] = review
        require(entry["claim_sha256"] == locations[iid]["claim_sha256"] == review.get("claim_sha256"),
                iid + ": review/manifest does not target the exact effective claim")
        require(review.get("instrument_id") == iid, iid + ": review identity mismatch")
        require(entry["target_path"] == locations[iid]["path"] and entry["target_line"] == locations[iid]["line"],
                iid + ": audited canonical claim location changed")
        hold = holds.get(iid)
        require(bool(hold), iid + ": no exact-hash active source-audit hold")
        if hold:
            require(hold["review_path"] == entry["audit_path"] and hold["review_sha256"] == entry["audit_sha256"],
                    iid + ": active hold is not linked to the pinned repair review")
        for source in review.get("additional_primary_sources", {}).values():
            for path_key, hash_key in (("retained_file", "sha256"), ("text_path", "text_sha256")):
                if source.get(path_key):
                    inputs.verify(source[path_key], source[hash_key])

    checker_code = run_worker(repo, out, "--checker")
    require(checker_code == 0, "bounded actual checker did not accept all six claims; inspect CHECKER_ACCEPTANCE.json and checker/checker.log")
    acceptance_path = out / "CHECKER_ACCEPTANCE.json"
    acceptance = json.loads(acceptance_path.read_bytes()) if acceptance_path.exists() else {"passed": False, "errors": ["missing checker acceptance receipt"]}
    require(acceptance.get("passed") is True, "bounded checker acceptance receipt is not passing")
    errors.extend(acceptance.get("errors", []))
    verification_path = out / "SOURCE_VERIFICATION.json"
    verification = json.loads(verification_path.read_bytes()) if verification_path.exists() else None
    checked_path = out / "checker/PER_CLAIM.json"
    checked = json.loads(checked_path.read_bytes()) if checked_path.exists() else {"claims": []}
    current = {row["instrument_id"]: row for row in checked["claims"]}
    require(len(checked["claims"]) == len(CHECKED) and set(current) == set(CHECKED),
            "actual checker did not examine exactly the six selected claims")
    csv_text = inputs.read("jobs/readiness-tracker/output/READINESS_BY_ORDER.csv").decode("utf-8")
    rows = {row["instrument_id"]: row for row in csv.DictReader(csv_text.splitlines())}
    status_path = "jobs/readiness-tracker/output/STATUS.json"
    status = inputs.obj(status_path) if inputs.path(status_path).exists() else None
    if os.environ.get("GITHUB_ACTIONS") == "true":
        require(bool(status) and status.get("result") == "succeeded"
                and status.get("commit_run") == os.environ.get("GITHUB_SHA"),
                "tracker must have succeeded on this exact GitHub execution commit")
    stages = []
    for iid in (*CHECKED, BLOCKED):
        row, claim_check, hold = rows.get(iid), current.get(iid), holds.get(iid)
        require(row is not None, iid + ": missing from the current tracker")
        if iid in CHECKED:
            require(bool(claim_check) and claim_check.get("claim_sha256") == locations[iid]["claim_sha256"],
                    iid + ": bounded checker result has a different claim hash")
        if iid in DISPUTED and row:
            marker = "OPEN_SOURCE_AUDIT:" + locations[iid]["claim_sha256"][:12]
            require(marker in row.get("blockers", "").split("|")
                    and row.get("step_counterevidence") == "open"
                    and row.get("ready_for_human_review") == "no",
                    iid + ": exact active audit hold is not reflected in the integrated tracker")
        d = dossiers.get(iid, {})
        stages.append({"instrument_id": iid,
            "role": "disputed_premise" if iid in DISPUTED else ("positive_control_observed" if iid == POSITIVE else "source_blocked_no_claim_control"),
            "source_and_packet": {"packet": packet_path, "dossier_fingerprint": d.get("fingerprint"),
                "evidence_records": len(d.get("evidence", {})), "missing": d.get("missing", []),
                "preflight": packet.get("preflight", {}).get(iid)},
            "effective_canonical_claim": locations.get(iid),
            "AI_review": ({"path": audits[iid]["audit_path"], "sha256": audits[iid]["audit_sha256"],
                            "status": reviews.get(iid, {}).get("status"),
                            "review_type": reviews.get(iid, {}).get("review_type")} if iid in audits else None),
            "active_source_audit_hold": hold,
            "bounded_actual_checker": claim_check,
            "integrated_tracker": row,
            "human_certification_added": False})
    return {"errors": errors, "packet_fingerprint": packet["fingerprint"], "packet_members": len(dossiers),
            "held_packet_text_files_verified": len(packet["held_text_file_pins"]),
            "actual_checker_claims": len(current), "audit_hold_loader_warnings": hold_problems,
            "bounded_source_verification": verification, "bounded_checker_acceptance": acceptance,
            "tracker_status_observed": status, "tracker_orders_observed": len(rows),
            "tracker_ready_total_observed": sum(r.get("ready_for_human_review") == "yes" for r in rows.values()),
            "continuation_gate_replay": {"exit_code": gate_exit, "receipt": gate_receipt,
                "new_work_selected": False, "prospective_experiment": False,
                "basis": "Replay of a faithfully reconstructed historical contract; no new preregistration claimed."},
            "stages": stages}


def main():
    repo = Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
    out = Path(os.environ["OUTPUT_DIR"]).resolve()
    if out.is_relative_to(repo) and not out.is_relative_to(HERE / "output"):
        raise ValueError("repository output must stay under this job's output directory")
    out.mkdir(parents=True, exist_ok=True)
    (out / "tmp").mkdir(exist_ok=True)
    if sys.argv[1:2] == ["--suite"]:
        return test_worker(repo, out, sys.argv[2])
    if sys.argv[1:] == ["--checker"]:
        return checker_worker(repo, out)
    if sys.argv[1:]:
        raise ValueError("runner entrypoint takes no arguments")
    offline_guard()
    inputs = Inputs(repo)
    for job in (*SUITES, "claim-checker", "readiness-tracker", "portfolio-repair-check"):
        for path in sorted((repo / "jobs" / job).glob("*.py")):
            inputs.read(path.relative_to(repo))
    for path in sorted((repo / "jobs/junto/finders").glob("*.py")):
        inputs.read(path.relative_to(repo))
    inputs.read("research/stage19/code/claim_gate.py")
    inputs.read("jobs/portfolio-repair-check/verification_sources.json")
    tests = []
    for job in SUITES:
        code = run_worker(repo, out, "--suite", job)
        result_path = out / "tests" / (job + ".json")
        result = json.loads(result_path.read_bytes()) if result_path.exists() else {"job": job, "passed": False}
        result["exit_code"] = code
        tests.append(result)
    result = {"schema": "eo-portfolio-repair-validation/v1",
              "repo_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
              "github_execution_commit": os.environ.get("GITHUB_SHA"), "test_suites": tests,
              "canonical_claims_created": 0, "independently_human_certified_added": 0,
              "new_legal_endings_established": 0, "LLM_calls": 0, "token_savings_measured": False,
              "measurement_limit": "Deterministic validation with at most ten exact cited-source verifications on GitHub; model/token cost coverage is unavailable.",
              "stage_interpretation": "Stages overlap. Mechanical passes do not settle the disputed legal premise; AI source-audit holds remain separate from human certification."}
    try:
        result.update(integration(repo, out, inputs))
        inputs.unchanged()
    except Exception as exc:
        result.setdefault("errors", []).append(type(exc).__name__ + ": " + str(exc))
    result["input_sha256"] = dict(sorted(inputs.pins.items()))
    result["passed"] = not result.get("errors") and all(t["passed"] and t["exit_code"] == 0 for t in tests)
    write(out / "VALIDATION.json", result)
    write(out / "OUTPUT_PINS.json", {p.relative_to(out).as_posix(): sha(p.read_bytes())
          for p in sorted(out.rglob("*")) if p.is_file() and p.name != "OUTPUT_PINS.json" and "tmp" not in p.relative_to(out).parts})
    print(json.dumps({"passed": result["passed"], "test_cases": sum(t.get("tests_run", 0) for t in tests),
                      "errors": result.get("errors", []), "stages_observed": len(result.get("stages", []))}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
