#!/usr/bin/env python3
"""Davy: a free daily health check of the claim-drafts -> claim-kit chain on main.

Named for Humphry Davy's safety lamp (1815), whose flame changed in firedamp so miners learned of the danger before
it exploded. On 2026-11-07 Haloander lost about 9 hours to three latent breaks that only a paid batch found: an
undeclared owner-rulings input (#219), a draft summary built for an older population, and the EO:7933a/7933A
identity mismatch (#221). Davy runs the same validators claim-kit runs at build time, against what is committed on
main, every day, and says plainly which one fails, before a wave prepares packets from it.

Checks (each PASS or FAIL with the validator's own message; no tokens are spent):
  population      claim-kit population.validate_inputs: census identities, aliases, admissions, frozen ledger
                  bytes and every pinned accepted addition.
  drafts          population.validate_derived(drafts=...): the committed DRAFT_CLAIMS cover exactly the decided
                  population with the same statuses (the stale draft-summary break).
  dossiers        the committed claim-kit INDEX.json and SUMMARY.json cover exactly the decided population with the
                  same statuses and census size. Per-dossier fingerprints are not re-read (9,000 files); claim-kit's
                  own build does that.
  identity_case   no two ids in census, ledger, drafts and dossier index differ only in letter case unless the
                  contract declares the alias (the 7933a/7933A break).
  declarations    every literal path claim-drafts and claim-kit declare (needs, inputs, triggers) exists on main,
                  and the newest Quo Warranto READ_AUDIT.json of each, where present, found no undeclared read.
  unit_tests      claim-drafts' and claim-kit's own unit tests.

Outputs: HEALTH.json, HEALTH.md and VERDICT.json ({"verdict": "pass"|"fail", "summary": ...}); the runner copies
VERDICT into STATUS.json as job_verdict, and Kean's brief prints the summary. The job exits 0 when it could run its
checks, so a failure is published rather than hidden in an attempt folder.
"""
from __future__ import annotations

import collections
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(os.environ.get("REPO_ROOT") or Path(__file__).resolve().parents[2]).resolve()
OUT = Path(os.environ.get("OUTPUT_DIR") or Path(__file__).resolve().parent / "output")
KIT = REPO / "jobs/claim-kit"
DRAFTS = REPO / "jobs/claim-drafts/output"
DOSSIERS = REPO / "jobs/claim-kit/output"
CHAIN = ("claim-drafts", "claim-kit")
TEST_TIMEOUT = 3600


def _lines(path):
    if not path.is_file():
        return []
    return [s for ln in path.read_text(encoding="utf-8").splitlines() if (s := ln.split("#", 1)[0].strip())]


def check_population(P, pop=None):
    return P.validate_inputs(REPO)


def check_drafts(P, pop):
    return P.validate_derived(pop, drafts=DRAFTS)["drafts"]


def check_dossiers(P, pop):
    statuses = pop["statuses"]
    summary = json.loads((DOSSIERS / "SUMMARY.json").read_text(encoding="utf-8"))
    counts = summary["counts"]
    P.require(counts.get("decided_orders") == counts.get("dossiers") == len(statuses),
              "Dossier summary population stale: decided_orders=%s dossiers=%s decided now=%d"
              % (counts.get("decided_orders"), counts.get("dossiers"), len(statuses)))
    P.require(counts.get("universe_orders") == pop["universe"],
              "Dossier census stale: %s vs %d" % (counts.get("universe_orders"), pop["universe"]))
    index = json.loads((DOSSIERS / "INDEX.json").read_text(encoding="utf-8"))
    P.check_membership(index, statuses, "status", "Dossier index")
    return "summary counts and index membership/statuses match the decided population (fingerprints not re-read)"


def check_identity_case(P, pop):
    aliases = pop.get("id_aliases", {})
    sources = {"census+ledger": set(pop["statuses"])}
    with (DRAFTS / "DRAFT_CLAIMS.jsonl").open(encoding="utf-8") as fh:
        sources["drafts"] = {json.loads(ln).get("instrument_id") for ln in fh if ln.strip()}
    sources["dossier index"] = {r.get("instrument_id") for r in json.loads((DOSSIERS / "INDEX.json").read_text(encoding="utf-8"))}
    spell = collections.defaultdict(set)
    for name, ids in sources.items():
        for i in ids:
            if isinstance(i, str):
                spell[i.upper()].add((aliases.get(i, i), name))
    bad = {k: sorted(v) for k, v in spell.items() if len({x for x, _ in v}) > 1}
    P.require(not bad, "ids differing only in letter case, without a declared alias: "
              + "; ".join("%s: %s" % (k, ", ".join("%s in %s" % x for x in v)) for k, v in sorted(bad.items())[:10]))
    return "no undeclared letter-case variants across %d ids" % len(spell)


def on_main(entry):
    """True if the path is tracked at HEAD, checked out or not. Davy runs in a sparse checkout, so a working-tree
    test reported real paths as missing (first Actions run, 2026-11-09)."""
    if (REPO / entry).exists():
        return True
    p = subprocess.run(["git", "-C", str(REPO), "ls-tree", "--name-only", "HEAD", "--", entry.rstrip("/")],
                       capture_output=True, text=True)
    return p.returncode == 0 and bool(p.stdout.strip())


def check_declarations(P, pop):
    problems, audits = [], []
    for job in CHAIN:
        folder = REPO / "jobs" / job
        for f in ("needs.txt", "inputs.txt", "triggers.txt"):
            for entry in _lines(folder / f):
                if not any(c in entry for c in "*?[") and not on_main(entry):
                    problems.append("%s/%s declares %s, which is not on main" % (job, f, entry))
        rep = folder / "output/READ_AUDIT.json"
        if rep.is_file():
            r = json.loads(rep.read_text(encoding="utf-8"))
            audits.append("%s %s" % (job, r.get("verdict")))
            if r.get("verdict") != "covered":
                problems.append("%s read %d undeclared path(s), e.g. %s" % (
                    job, len(r.get("violations", [])), ", ".join(v["path"] for v in r.get("violations", [])[:3])))
    P.require(not problems, "; ".join(problems))
    return "literal declarations exist; read audits: " + (", ".join(audits) or "none published yet")


def check_unit_tests(P, pop):
    failed = []
    for job, args in (("claim-drafts", ["-m", "unittest", "test_drafts"]),
                      ("claim-kit", ["-m", "unittest", "discover", "-s", str(KIT), "-p", "test_*.py"])):
        cwd = REPO / "jobs" / job if job == "claim-drafts" else REPO
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
        env.pop("OUTPUT_DIR", None)
        try:
            p = subprocess.run([sys.executable, "-B", *args], cwd=cwd, env=env, capture_output=True, text=True,
                               timeout=TEST_TIMEOUT)
        except subprocess.TimeoutExpired:
            failed.append("%s tests timed out after %ds" % (job, TEST_TIMEOUT))
            continue
        tail = (p.stderr or p.stdout).strip().splitlines()[-1:] or [""]
        if p.returncode:
            failed.append("%s tests failed (%s)" % (job, tail[0][:200]))
    P.require(not failed, "; ".join(failed))
    return "claim-drafts and claim-kit unit tests pass"


CHECKS = [("population", check_population), ("drafts", check_drafts), ("dossiers", check_dossiers),
          ("identity_case", check_identity_case), ("declarations", check_declarations),
          ("unit_tests", check_unit_tests)]
NEEDS_POPULATION = {"drafts", "dossiers", "identity_case"}


def run(checks=CHECKS):
    sys.path.insert(0, str(KIT))
    import population as P
    results, pop = [], None
    for name, fn in checks:
        t0 = time.monotonic()
        if name in NEEDS_POPULATION and pop is None:
            results.append({"check": name, "result": "FAIL", "detail": "not run: the population check failed",
                            "seconds": 0.0})
            continue
        try:
            value = fn(P, pop)
            if name == "population":
                pop = value
                value = "census %d ids, %d decided (contract %s)" % (value["universe"], value["decided"],
                                                                     value["contract_sha256"][:12])
            results.append({"check": name, "result": "PASS", "detail": str(value)})
        except Exception as e:  # a validator's refusal is the finding; report it verbatim
            results.append({"check": name, "result": "FAIL", "detail": "%s: %s" % (type(e).__name__, str(e)[:600])})
        results[-1]["seconds"] = round(time.monotonic() - t0, 1)
    return results


def write(results):
    failed = [r for r in results if r["result"] == "FAIL"]
    verdict = "fail" if failed else "pass"
    summary = ("claim-drafts -> claim-kit chain: " + ("FAIL in " + ", ".join(r["check"] for r in failed)
               + " - " + failed[0]["detail"][:240] if failed else "all %d checks pass" % len(results)))
    commit = os.environ.get("GITHUB_SHA") or ""
    OUT.mkdir(parents=True, exist_ok=True)
    doc = {"schema": "davy-chain-health/1", "verdict": verdict, "summary": summary, "input_commit": commit,
           "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": results}
    (OUT / "HEALTH.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    (OUT / "VERDICT.json").write_text(json.dumps({"verdict": verdict, "summary": summary}) + "\n", encoding="utf-8")
    md = ["# Davy: claim-drafts -> claim-kit chain health", "", f"**{verdict.upper()}** as of `{commit[:10]}`: {summary}", "",
          "| Check | Result | Detail |", "|---|---|---|"]
    md += ["| %s | %s | %s |" % (r["check"], r["result"], r["detail"].replace("|", "/")[:400]) for r in results]
    (OUT / "HEALTH.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(summary)
    return doc


def main():
    write(run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
