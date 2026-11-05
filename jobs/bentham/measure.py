#!/usr/bin/env python3
"""Bentham measure: yield rates and token costs, derived from committed files only.

What the numbers mean
---------------------
* A yield rate is "claims filed per order attempted" in a production wave. An order is
  "attempted" when a producer agent was given it; it is "filed" when it was attempted and is
  not listed under that batch's ``not_filed`` (blocked, rejected, rejected_mechanical).
  The rate describes that one wave. It does not say the next wave will do as well, and a
  filed claim is not a certified dossier (the certified count stays 0).
* Strata come from the readiness tracker's ``provisional_status`` (yes / no) and the era of the
  order's EO number (>= 7532 is the Federal Register index era "fr", else "prefr"; a lettered
  or fractional suffix such as ``EO:10026A`` counts by its leading number). Orders whose
  tracker status is blank, or that the tracker does not list, count in ``.all`` but in no
  yes/no stratum.
* ``filed_per_attempt.all`` and the stratified rates use production batches only. The
  correction batches (c01-c03) re-attempt orders that earlier batches already failed, so they
  are measured separately as ``filed_per_attempt.correction`` and kept out of the others.
* Costs are API-equivalent dollars computed from recorded token counts and an assumed list
  price table. They are not an invoice, and plan allowances are not published.
  The coordinator figure is a lower bound (its transcript starts after a context compaction).
  Cache writes of both 5-minute and 1-hour kinds are priced at the one cache_write rate.

Run: ``python3 -I jobs/bentham/measure.py [--out PATH]``
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

WAVE = "tribonian-2026-11-04"
WAVE_DIR = "research/excavator/claude-tribonian-2026-11-04"
DISPOSITION = f"{WAVE_DIR}/evidence/DISPOSITION.json"
BATCHES = f"{WAVE_DIR}/tools/batches.json"
USAGE = f"{WAVE_DIR}/telemetry/AGENT_USAGE.csv"
SUMMARY = f"{WAVE_DIR}/telemetry/SUMMARY.json"
READINESS = "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
FR_FIRST = 7532
CORRECTION_BATCHES = ("c01", "c02", "c03")

PRICE_TABLE = {
    "sonnet": {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_write": 3.75},
    "opus": {"input": 5.0, "output": 25.0, "cache_read": 0.50, "cache_write": 6.25},
    "source": "assumption: Anthropic API list prices; plan allowances are not published",
}
PHASE_FAMILY = {"production": "sonnet", "review": "opus", "coordination": "opus",
                "correction": "sonnet", "integration": "sonnet"}
TOKEN_KEYS = ("fresh_input", "cache_read", "cache_write", "output")


class MeasureError(RuntimeError):
    """A required committed file is missing or has a shape this module cannot parse."""


def repo_root() -> Path:
    env = os.environ.get("REPO_ROOT")
    return Path(env) if env else Path(__file__).resolve().parents[2]


def _squash(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _need(repo: Path, rel: str) -> Path:
    p = repo / rel
    if not p.is_file():
        raise MeasureError(f"required file missing: {rel} (looked under {repo}); no numbers invented")
    return p


def _json(repo: Path, rel: str):
    p = _need(repo, rel)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise MeasureError(f"{rel} is not valid JSON: {e}") from e


def _quotes(repo: Path, candidates: list[tuple[str, str]]) -> list[dict]:
    """Keep only quotes that occur verbatim (whitespace ignored) in the cited file."""
    out = []
    for quote, src in candidates:
        p = repo / src
        if p.is_file() and _squash(quote) in _squash(p.read_text(encoding="utf-8")):
            out.append({"quote": quote, "source": src})
    return out


def eo_number(instrument_id: str) -> int | None:
    m = re.match(r"^EO:(\d+)", instrument_id or "")
    return int(m.group(1)) if m else None


def era_of(instrument_id: str) -> str | None:
    n = eo_number(instrument_id)
    if n is None:
        return None
    return "fr" if n >= FR_FIRST else "prefr"


def load_status(repo: Path) -> dict[str, str]:
    with _need(repo, READINESS).open(newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        if not rd.fieldnames or "instrument_id" not in rd.fieldnames or "provisional_status" not in rd.fieldnames:
            raise MeasureError(f"{READINESS} lacks instrument_id/provisional_status columns")
        return {r["instrument_id"]: (r["provisional_status"] or "").strip() for r in rd}


def _is_disposition(doc) -> bool:
    return (isinstance(doc, dict) and isinstance(doc.get("batches"), list)
            and all(isinstance(b, dict) and "batch" in b for b in doc["batches"]))


def wave_orders(repo: Path, doc: dict, batch_lists: dict) -> list[dict]:
    """One row per attempted order: batch, instrument_id, filed (bool), outcome."""
    rows = []
    for b in doc["batches"]:
        att = b.get("attempted")
        if not att:
            continue  # prepared or applied but never tallied: no attempt count exists
        ids = batch_lists.get(b["batch"])
        if not isinstance(ids, list) or len(ids) != att:
            raise MeasureError(f"batch {b['batch']}: batches.json lists "
                               f"{None if ids is None else len(ids)} orders but DISPOSITION says attempted={att}")
        nf = {n["instrument_id"]: n.get("outcome", "not_filed") for n in b.get("not_filed", [])}
        stray = set(nf) - set(ids)
        if stray:
            raise MeasureError(f"batch {b['batch']}: not_filed orders not in attempted list: {sorted(stray)[:3]}")
        filed = len(ids) - len(nf)
        if "claims_filed" in b and filed != b["claims_filed"]:
            raise MeasureError(f"batch {b['batch']}: attempted-minus-not_filed={filed} "
                               f"but claims_filed={b['claims_filed']}")
        for i in ids:
            rows.append({"batch": b["batch"], "id": i, "filed": i not in nf,
                         "outcome": nf.get(i, "filed")})
    return rows


def _rate_row(key, num, den, source, evidence, pool, note):
    return {"key": key, "value": (num / den) if den else None, "num": num, "den": den,
            "unit": "share", "source": source, "evidence": evidence,
            "population": WAVE, "pool": pool, "n_studies": 1, "note": note}


def compute_rates(repo: Path, rows: list[dict], status: dict[str, str]) -> list[dict]:
    prod = [r for r in rows if r["batch"] not in CORRECTION_BATCHES]
    corr = [r for r in rows if r["batch"] in CORRECTION_BATCHES]
    ev = _quotes(repo, [('"schema": "tribonian-disposition/v1"', DISPOSITION),
                        ("instrument_id,provisional_status", READINESS)])

    def count(sel):
        return sum(1 for r in sel if r["filed"]), len(sel)

    out = []
    for st in ("yes", "no"):
        for era in ("fr", "prefr"):
            sel = [r for r in prod if status.get(r["id"]) == st and era_of(r["id"]) == era]
            n, d = count(sel)
            out.append(_rate_row(
                f"filed_per_attempt.{st}.{era}", n, d, DISPOSITION, ev,
                f"orders attempted in non-correction batches of {WAVE} whose readiness-tracker "
                f"provisional_status is '{st}' and whose EO number is {'>= ' if era == 'fr' else '< '}{FR_FIRST} "
                f"({'Federal Register index era' if era == 'fr' else 'pre-index era'})",
                "Share of attempted orders with a claim filed after review and the completion checker. "
                "Status joined from the tracker as it stands now, not as it stood at attempt time."))
    n, d = count(prod)
    unstrat = sum(1 for r in prod if status.get(r["id"]) not in ("yes", "no"))
    out.append(_rate_row("filed_per_attempt.all", n, d, DISPOSITION, ev,
                         f"all orders attempted in non-correction batches of {WAVE}",
                         f"Includes {unstrat} attempted orders whose tracker status is blank or absent, "
                         "which belong to no yes/no stratum. Correction batches excluded."))
    n, d = count(corr)
    out.append(_rate_row("filed_per_attempt.correction", n, d, DISPOSITION, ev,
                         f"orders attempted in correction batches {', '.join(CORRECTION_BATCHES)} of {WAVE}",
                         "Correction batches re-attempt orders that earlier batches blocked or rejected, "
                         "so this rate is conditional on a prior failure and is not comparable to the others."))
    return out


# ---------------------------------------------------------------- costs
def _int(x) -> int:
    try:
        return int(float(x)) if x not in (None, "") else 0
    except ValueError:
        return 0


def load_usage(repo: Path) -> list[dict]:
    with _need(repo, USAGE).open(newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        need = {"phase", "batch", "model", "fresh_input", "cache_read", "output"}
        if not rd.fieldnames or not need <= set(rd.fieldnames):
            raise MeasureError(f"{USAGE} lacks columns {sorted(need - set(rd.fieldnames or []))}")
        rows = []
        for r in rd:
            cw = sum(_int(r.get(k)) for k in ("cache_write_5m", "cache_write_1h", "cache_write_unclassified"))
            fam = None
            m = (r.get("model") or "").lower()
            for f_ in ("opus", "sonnet"):
                if f_ in m:
                    fam = f_
            recorded = fam is not None
            if fam is None:
                fam = PHASE_FAMILY.get(r["phase"])
            if fam is None:
                raise MeasureError(f"agent {r.get('agent_id')}: no model and unknown phase {r['phase']!r}")
            rows.append({"agent": r.get("agent_id"), "phase": r["phase"], "batch": r["batch"] or "",
                         "family": fam, "recorded": recorded,
                         "tokens": {"fresh_input": _int(r["fresh_input"]), "cache_read": _int(r["cache_read"]),
                                    "cache_write": cw, "output": _int(r["output"])}})
        return rows


def usd(family: str, tokens: dict, prices=PRICE_TABLE) -> float:
    p = prices[family]
    return (tokens["fresh_input"] * p["input"] + tokens["output"] * p["output"]
            + tokens["cache_read"] * p["cache_read"] + tokens["cache_write"] * p["cache_write"]) / 1e6


def _group(rows: list[dict]) -> tuple[float, dict, int]:
    tok = {k: 0 for k in TOKEN_KEYS}
    total = 0.0
    inferred = 0
    for r in rows:
        total += usd(r["family"], r["tokens"])
        inferred += 0 if r["recorded"] else 1
        for k in TOKEN_KEYS:
            tok[k] += r["tokens"][k]
    return total, tok, inferred


def _cost(total, tok, denom, per, source, basis, inferred):
    if not denom:
        raise MeasureError(f"cost denominator is zero for: {basis}")
    return {"usd": total / denom, "total_usd": total, "denominator": denom, "tokens": tok, "per": per,
            "source": source,
            "basis": basis + (f" Model family inferred from phase for {inferred} agent(s)."
                              if inferred else " Model family taken from each agent's recorded model.")}


def compute_costs(repo: Path, doc: dict, rows: list[dict], usage: list[dict]) -> dict:
    _need(repo, SUMMARY)  # summary is the cross-check source; fail clearly if absent
    prod_batches = [b for b in doc["batches"] if b.get("attempted") and b["batch"] not in CORRECTION_BATCHES]
    pset = {b["batch"] for b in prod_batches}
    attempts = sum(b["attempted"] for b in prod_batches)
    submitted = sum(sum((b.get("blind_review_verdicts") or {}).values()) for b in prod_batches)
    corr_attempts = sum(b["attempted"] for b in doc["batches"]
                        if b.get("attempted") and b["batch"] in CORRECTION_BATCHES)
    if not attempts or not submitted:
        raise MeasureError("no attempted orders or review verdicts in DISPOSITION; cannot price per unit")

    def batches_of(u):  # review batches can be joined with '+'
        return set(u["batch"].split("+")) if u["batch"] else set()

    prod_u = [u for u in usage if u["phase"] == "production" and u["batch"] in pset]
    rev_u = [u for u in usage if u["phase"] == "review" and batches_of(u) and batches_of(u) <= pset]
    coord_u = [u for u in usage if u["phase"] == "coordination"]
    corr_u = [u for u in usage if u["phase"] == "correction"]
    skipped_prod = sorted(u["batch"] for u in usage if u["phase"] == "production" and u["batch"] not in pset)
    skipped_rev = sorted(u["batch"] for u in usage if u["phase"] == "review" and not (batches_of(u) and batches_of(u) <= pset))

    costs = {}
    t, k, inf = _group(prod_u)
    costs["production.per_attempt"] = _cost(
        t, k, attempts, "attempted_order", USAGE,
        f"Production-phase agents of {len(prod_u)} batches with a tally, divided by {attempts} orders attempted in "
        f"those non-correction batches. Producer batches without a tally ({', '.join(skipped_prod) or 'none'}) are "
        "excluded from numerator and denominator.", inf)
    t, k, inf = _group(rev_u)
    costs["review.per_submitted"] = _cost(
        t, k, submitted, "submitted_claim", USAGE,
        f"Review-phase agents whose batches are all tallied production batches, divided by {submitted} blind-review "
        "verdicts (upheld + rejected, summed from blind_review_verdicts in DISPOSITION); one verdict is one claim "
        "version judged, so re-reviews of revised versions and planted controls count. Excluded review agents "
        f"(paired trial arms, re-review, untallied batches): {', '.join(skipped_rev) or 'none'}.", inf)
    t, k, inf = _group(coord_u)
    costs["coordination.per_attempt"] = _cost(
        t, k, attempts, "attempted_order", USAGE,
        f"Coordinator agent, divided by {attempts} production orders attempted. Lower bound: the coordinator "
        "transcript covers only the period after a context compaction.", inf)
    share = submitted / attempts
    p, r, c = (costs["production.per_attempt"], costs["review.per_submitted"], costs["coordination.per_attempt"])
    wt = {x: p["tokens"][x] + r["tokens"][x] + c["tokens"][x] for x in TOKEN_KEYS}
    wave_total = p["total_usd"] + r["total_usd"] + c["total_usd"]
    costs["wave.per_attempt"] = {
        "usd": p["usd"] + r["usd"] * share + c["usd"], "total_usd": wave_total, "denominator": attempts,
        "tokens": wt, "per": "attempted_order", "source": USAGE,
        "basis": f"production.per_attempt + review.per_submitted x submit share ({submitted}/{attempts} = "
                 f"{share:.4f} verdicts per attempted order) + coordination.per_attempt."}
    filed = sum(1 for x in rows if x["filed"] and x["batch"] not in CORRECTION_BATCHES)
    if filed:
        costs["wave.per_filed_dossier"] = {
            "usd": wave_total / filed, "total_usd": wave_total, "denominator": filed, "tokens": wt,
            "per": "filed_dossier", "source": USAGE,
            "basis": f"Same total as wave.per_attempt divided by {filed} claims filed in production batches. "
                     "A filed claim is not a certified dossier."}
    if corr_u and corr_attempts:
        t, k, inf = _group(corr_u)
        costs["correction.per_attempt"] = _cost(
            t, k, corr_attempts, "attempted_order", USAGE,
            f"Correction-production agents ({len(corr_u)}), divided by {corr_attempts} orders attempted in "
            "c01-c03. Their review is not separated from the review phase above.", inf)
    return costs


# ---------------------------------------------------------------- other waves
def scan_other_waves(repo: Path) -> tuple[list[dict], list[dict]]:
    waves, skipped = [], []
    ex = repo / "research" / "excavator"
    if not ex.is_dir():
        return waves, skipped
    for d in sorted(ex.iterdir()):
        for sub in ("", "evidence"):
            p = d / sub / "DISPOSITION.json" if sub else d / "DISPOSITION.json"
            rel = p.relative_to(repo).as_posix()
            if not p.is_file() or rel == DISPOSITION:
                continue
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                skipped.append({"source": rel, "reason": "not valid JSON"})
                continue
            if not _is_disposition(doc) or not all("attempted" in b or "claims_filed" in b for b in doc["batches"]):
                skipped.append({"source": rel, "reason": "shape differs from tribonian-disposition/v1"})
                continue
            waves.append({"wave": d.name,
                          "attempted": sum(b.get("attempted") or 0 for b in doc["batches"]),
                          "filed": sum(b.get("claims_filed") or 0 for b in doc["batches"]),
                          "source": rel, "pooled_into_rates": False})
    return waves, skipped


def measure(repo: Path | None = None) -> dict:
    repo = Path(repo) if repo else repo_root()
    doc = _json(repo, DISPOSITION)
    if not _is_disposition(doc):
        raise MeasureError(f"{DISPOSITION} does not have the tribonian-disposition/v1 batch list shape")
    batch_lists = _json(repo, BATCHES)
    status = load_status(repo)
    rows = wave_orders(repo, doc, batch_lists)
    usage = load_usage(repo)
    rates = compute_rates(repo, rows, status)
    costs = compute_costs(repo, doc, rows, usage)
    prod = [r for r in rows if r["batch"] not in CORRECTION_BATCHES]
    waves = [{"wave": WAVE, "attempted": len(rows), "filed": sum(r["filed"] for r in rows),
              "production_attempted": len(prod), "production_filed": sum(r["filed"] for r in prod),
              "source": DISPOSITION}]
    more, skipped = scan_other_waves(repo)
    return {"rates": rates, "costs": costs,
            "price_table": PRICE_TABLE, "waves": waves + more, "skipped": skipped}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write JSON here instead of stdout")
    a = ap.parse_args(argv)
    try:
        res = measure(repo_root())
    except MeasureError as e:
        print(f"measure: {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, indent=2, ensure_ascii=False) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
