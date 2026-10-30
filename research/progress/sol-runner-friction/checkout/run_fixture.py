"""Network-free, isolated checkout/materialization regression fixture."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
import time

ROOT = Path(__file__).resolve().parents[4]


def run(args, cwd, **kwargs):
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    if result.returncode:
        raise RuntimeError(f"{args!r} failed ({result.returncode}): "
                           f"{result.stdout[-2000:].decode(errors='replace')} "
                           f"{result.stderr[-2000:].decode(errors='replace')}")
    return result


def put(root, rel, value):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else value.encode())


def measure(root):
    paths, total = {}, 0
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            rel = path.relative_to(root).as_posix()
            size = path.stat().st_size
            paths[rel] = size
            total += size
    return paths, total


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    temp = Path(tempfile.mkdtemp(prefix="sol-runner-checkout-fixture-"))
    try:
        source = temp / "source"
        source.mkdir()
        sys.dont_write_bytecode = True
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
        shutil.copytree(ROOT / ".github/scripts", source / ".github/scripts", ignore=ignore)
        shutil.copytree(ROOT / "jobs/_lib", source / "jobs/_lib", ignore=ignore)
        (source / ".github/workflows").mkdir(parents=True)
        shutil.copy2(ROOT / ".github/workflows/run-jobs.yml", source / ".github/workflows/run-jobs.yml")
        put(source, "HANDOFF/README.md", "fixture\n")
        put(source, "README.md", "root-file-compatibility\n")
        put(source, "jobs/consumer/job.py", "from pathlib import Path\nimport os,sys\n"
            "Path(os.environ['OUTPUT_DIR'],'new.txt').write_text('failed candidate')\nsys.exit(9)\n")
        put(source, "jobs/consumer/after.txt", "producer\n")
        put(source, "jobs/consumer/needs.txt", "")
        put(source, "jobs/consumer/output/STATUS.json", json.dumps({
            "result": "succeeded", "started_utc": "2026-01-01T00:00:00Z",
            "finished_utc": "2026-01-01T00:00:01Z"}))
        put(source, "jobs/consumer/output/PRIOR.txt", "consumer-prior-success")
        put(source, "jobs/producer/job.py", "print('ok')\n")
        put(source, "jobs/producer/output/STATUS.json", json.dumps({"result": "succeeded"}))
        put(source, "jobs/producer/output/CUSTODY.json", "producer-custody")
        put(source, "jobs/distractor/job.py", "print('unused')\n")
        put(source, "jobs/distractor/output/UNRELATED.bin", b"x" * (2 * 1024 * 1024))
        run(["git", "init", "-q"], source)
        run(["git", "config", "user.name", "Fixture"], source)
        run(["git", "config", "user.email", "fixture@example.invalid"], source)
        run(["git", "add", "."], source)
        run(["git", "commit", "-qm", "fixture baseline"], source)
        # This fixture tests an explicitly audited synthetic consumer version.
        # Production signatures cover only the two real reviewed jobs.
        helper_path = source / ".github/scripts/materialize_job_inputs.py"
        script = ("import sys;sys.path.insert(0,'.github/scripts');"
                  "import materialize_job_inputs as m;print(m.narrow_signature('consumer'))")
        signature = run([sys.executable, "-c", script], source,
                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}).stdout.decode().strip()
        helper_path.write_text(helper_path.read_text().replace(
            "NARROW_SIGNATURES = {", 'NARROW_SIGNATURES = {\n    "consumer": "' + signature + '",'))
        run(["git", "add", ".github/scripts/materialize_job_inputs.py"], source)
        run(["git", "commit", "--amend", "--no-edit", "-q"], source)
        commit = run(["git", "rev-parse", "HEAD"], source).stdout.decode().strip()

        baseline = temp / "baseline"
        run(["git", "clone", "-q", "--local", "--no-checkout", str(source), str(baseline)], temp)
        run(["git", "sparse-checkout", "init", "--cone"], baseline)
        start = time.perf_counter()
        run(["git", "sparse-checkout", "set", ".github", "jobs", "HANDOFF"], baseline)
        run(["git", "checkout", "-f", "--detach", commit], baseline)
        baseline_seconds = time.perf_counter() - start

        after = temp / "after"
        run(["git", "clone", "-q", "--local", "--no-checkout", str(source), str(after)], temp)
        run(["git", "sparse-checkout", "init", "--no-cone"], after)
        workflow = (ROOT / ".github/workflows/run-jobs.yml").read_text(encoding="utf-8")
        sparse_block = workflow.split("sparse-checkout: |", 1)[1].split("\n\n", 1)[0]
        bootstrap = "\n".join(line.strip() for line in sparse_block.splitlines() if line.strip()) + "\n"
        start = time.perf_counter()
        run(["git", "sparse-checkout", "set", "--no-cone", "--stdin"], after, input=bootstrap.encode())
        run(["git", "checkout", "-f", "--detach", commit], after)
        bootstrap_seconds = time.perf_counter() - start
        bootstrap_inventory, bootstrap_bytes = measure(after)

        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "JOBS": "consumer",
               "CHECKOUT_INPUT_RECEIPT": "oversized/runner-freshness/CHECKOUT_INPUTS.json"}
        start = time.perf_counter()
        run([sys.executable, ".github/scripts/materialize_job_inputs.py"], after, env=env)
        materialize_seconds = time.perf_counter() - start
        receipt = json.loads((after / env["CHECKOUT_INPUT_RECEIPT"]).read_text())
        spec = importlib.util.spec_from_file_location("fixture_freshness", after / ".github/scripts/result_freshness.py")
        freshness = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = freshness
        spec.loader.exec_module(freshness)
        sys.path.insert(0, str(after / ".github/scripts"))
        helper_spec = importlib.util.spec_from_file_location("fixture_materializer", after / ".github/scripts/materialize_job_inputs.py")
        helper = importlib.util.module_from_spec(helper_spec)
        sys.modules[helper_spec.name] = helper
        helper_spec.loader.exec_module(helper)
        previous_cwd = Path.cwd()
        os.chdir(after)
        try:
            required, _, _ = helper.input_closure(["consumer"])
        finally:
            os.chdir(previous_cwd)
        if len(required) != receipt["path_count"]:
            raise AssertionError(f"Receipt path count {receipt['path_count']} differs from recomputed closure {len(required)}")
        hashes = {path: {"sha256": digest(baseline / path), "same_after": digest(baseline / path) == digest(after / path)}
                  for path in sorted(required)}
        if not all(row["same_after"] for row in hashes.values()):
            raise AssertionError("Selected closure differs from pinned baseline: " +
                                 ", ".join(path for path, row in hashes.items() if not row["same_after"]))
        baseline_inventory, base_bytes = measure(baseline)
        after_inventory, after_bytes = measure(after)
        receipt_rel = env["CHECKOUT_INPUT_RECEIPT"]
        added_paths = sorted(set(after_inventory) - set(bootstrap_inventory) - {receipt_rel})
        added_bytes = sum(after_inventory[p] for p in added_paths)
        receipt_bytes = after_inventory.get(receipt_rel, 0)

        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "JOBS": "consumer", "GITHUB_RUN_ID": "fixture-run",
               "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": commit, "GITHUB_REF_NAME": "fixture",
               "TRIGGER": "fixture"}
        result = subprocess.run([sys.executable, ".github/scripts/run_jobs.py"], cwd=after, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 1:
            raise AssertionError(f"Expected failed job run to return 1, got {result.returncode}: "
                                 f"{result.stdout[-2000:].decode(errors='replace')}")
        fallback_run = run([sys.executable, ".github/scripts/materialize_job_inputs.py"], after,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "JOBS": "distractor",
                                "CHECKOUT_INPUT_RECEIPT": "oversized/fallback.json"})
        fallback_receipt = json.loads((after / "oversized/fallback.json").read_text())
        fallback_preserved = (after / "jobs/distractor/output/UNRELATED.bin").is_file()
        prior_preserved = (after / "jobs/consumer/output/PRIOR.txt").read_text() == "consumer-prior-success"
        prior_status = json.loads((after / "jobs/consumer/output/STATUS.json").read_text())
        attempt = after / "jobs/_attempts/consumer/fixture-run-1"
        attempt_status = json.loads((attempt / "STATUS.json").read_text())
        if not (prior_preserved and prior_status["result"] == "succeeded"
                and attempt_status["result"] == "failed" and (attempt / "new.txt").is_file()):
            raise AssertionError("Failed generation did not retain attempt and preserve prior output")

        return {
            "schema": 1,
            "fixture_commit": commit,
            "scope": "isolated local clones; actual helper, freshness module and runner; network-free",
            "selected_jobs": ["consumer"],
            "baseline_cone": {"files": len(baseline_inventory), "bytes": base_bytes, "checkout_seconds": baseline_seconds},
            "narrow_checkout": {
                "bootstrap_files": len(bootstrap_inventory),
                "bootstrap_bytes": bootstrap_bytes,
                "bootstrap_seconds": bootstrap_seconds,
                "selected_closure_files": receipt["path_count"],
                "selected_closure_bytes": receipt["materialized_bytes"],
                "selected_closure_sparse_patterns": receipt["sparse_pattern_count"],
                "materialize_seconds": materialize_seconds,
                "additional_selected_files": len(added_paths),
                "additional_selected_bytes": added_bytes,
                "receipt_bytes_not_from_git_checkout": receipt_bytes,
                "pre_run_files_excluding_receipt": len(after_inventory) - int(receipt_rel in after_inventory),
                "pre_run_bytes": after_bytes,
            },
            "required_file_hashes": hashes,
            "unrelated_output_materialized_in_narrow_mode": False,
            "implicit_root_file_preserved": (after / "README.md").read_bytes() == (baseline / "README.md").read_bytes(),
            "compatibility_fallback": {"jobs": fallback_receipt["compatibility_fallback_jobs"],
                                       "historical_dynamic_output_preserved": fallback_preserved,
                                       "accounted_materialized_bytes": fallback_receipt["materialized_bytes"]},
            "failed_generation": {
                "prior_output_preserved": prior_preserved,
                "prior_status_result": prior_status["result"],
                "attempt_status": attempt_status["result"],
                "attempt_candidate_retained": (attempt / "new.txt").is_file(),
            },
            "limits": "Synthetic local bytes/timing test proves materialization and custody mechanics. It does not measure GitHub transfer bytes, cold remote latency, or full-repository savings.",
        }
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    report = main()
    target = ROOT / "research/progress/sol-runner-friction/checkout/fixture-receipt.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in (
        "fixture_commit", "baseline_cone", "narrow_checkout", "unrelated_output_materialized_in_narrow_mode", "compatibility_fallback", "failed_generation", "limits")}, indent=2))
