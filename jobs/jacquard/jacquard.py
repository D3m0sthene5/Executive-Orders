#!/usr/bin/env python3
"""Jacquard: sampled class review with planted errors, for adopting provisional NO statuses.

Named for the loom that applies one punched-card pattern to every thread. Offline, deterministic,
standard library only. Steps (each a CLI subcommand, each reading the files the earlier ones wrote):

  select    lots defined in lots.json -> LOTS.csv, CALIBRATION.csv, SELECT.json
  sample    random sample per lot (or the whole lot when small) -> SAMPLES.json
  packets   blinded review packets with planted controls + answer key (kept outside the packets)
  verify    grade reviewer output against the key -> VERIFICATION.json
  accept    per-lot acceptance with 95% upper bound -> ACCEPTANCE.json, INDIVIDUAL_REVIEW.csv
  propose   PROPOSED_STATUS_ROWS.csv in the register's own header (never edits the register)

Owner ruling 2026-10-31: statuses stay provisional; human-certified count stays 0; adoption is by an
owner-merged pull request. Nothing here writes to the register.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import random
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_REPO = Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
TYPES_REL = "jobs/x1-class-engine/output/TYPES.csv"
REGISTER_REL = "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
MAX_TEXT_CHARS = 12000
MAX_BATCH = 20
FORBIDDEN_WORDS = ("control", "intruder", "swap", "planted")
IDENTITY_VALUES = ("match", "mismatch", "cannot_tell")
ORIGIN_DATE = "2026-10-31"
RULING = "2026-10-31-jacquard-and-working-texts"
TEMPLATE_ROW = {
    "opus_any_effect_status": "not_recorded_in_opus_overlay",
    "opus_source_text_obtained": "not_applicable",
    "opus_footprint_complete_claim": "not_applicable",
    "opus_first_cause_status": "not_applicable",
    "opus_original_images_in_supplied_zip": "not_applicable",
    "stage16_structured_episode_count": "0",
    "stage16_scoped_first_cause_proven_count": "0",
    "stage17_provision_count": "0",
    "stage17_transition_count": "0",
    "stage17_scoped_first_sunset_count": "0",
    "recorded_legal_event_count": "0",
    "stage17_assessment": "none",
    "stage16_v3_assessment": "none",
    "whole_order_first_cessation_verified_by_this_audit": "no",
    "human_certified_by_this_release": "no",
    "audit_next_step": "AI class status hypothesis adopted as provisional by owner PR; whole-lifecycle claim "
                       "and independent human review still required",
}


# ---------------------------------------------------------------- small helpers

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path, rows, cols):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def sha_seed(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_ws(text):
    return re.sub(r"\s+", " ", text).strip()


def load_config(path=None):
    return read_json(path or HERE / "lots.json")


def load_register(repo):
    header, rows = read_csv(Path(repo) / REGISTER_REL)
    return header, {r["instrument_id"]: r for r in rows}


def load_types(repo):
    return read_csv(Path(repo) / TYPES_REL)[1]


def text_exists(repo, rel):
    return bool(rel) and (Path(repo) / rel).is_file()


def read_text(repo, rel):
    with open(Path(repo) / rel, encoding="utf-8", errors="replace", newline="") as fh:
        return fh.read()


def int_year(value):
    try:
        return int(str(value).strip())
    except ValueError:
        return None


# ---------------------------------------------------------------- statistics

def cp_upper(k, n, alpha=0.05):
    """Exact (Clopper-Pearson) one-sided upper confidence bound on an error rate: k failures in n draws.

    Solves P(X <= k | n, p) = alpha for p. With k = 0 this is 1 - alpha**(1/n).
    """
    if n <= 0:
        return None
    if k >= n:
        return 1.0
    if k == 0:
        return 1.0 - alpha ** (1.0 / n)

    def cdf(p):
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))

    lo, hi = k / n, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if cdf(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------- select

def select_lots(repo, cfg, types_rows=None, register=None):
    """Return (members_by_lot, counts_by_lot, calibration_rows)."""
    types_rows = load_types(repo) if types_rows is None else types_rows
    register = load_register(repo)[1] if register is None else register
    members, counts = {}, {}
    for lot in cfg["lots"]:
        name = lot["lot"]
        c = {"type_rows": 0, "rule_mismatch": 0, "confidence_excluded": 0, "year_excluded": 0,
             "already_in_register": 0, "text_missing": 0, "members": 0}
        got = []
        for r in types_rows:
            if r["type"] != lot["type"]:
                continue
            c["type_rows"] += 1
            if lot.get("rule_id") and r["rule_id"] != lot["rule_id"]:
                c["rule_mismatch"] += 1
            elif r["confidence"] not in lot["confidence"]:
                c["confidence_excluded"] += 1
            elif "max_year" in lot and (int_year(r["year"]) is None or int_year(r["year"]) > lot["max_year"]):
                c["year_excluded"] += 1
            elif r["instrument_id"] in register:
                c["already_in_register"] += 1
            elif not text_exists(repo, r["text_path"]):
                c["text_missing"] += 1
            else:
                got.append(r)
        got.sort(key=lambda r: r["instrument_id"])
        c["members"] = len(got)
        members[name], counts[name] = got, c
    calibration = []
    for lot in cfg["lots"]:
        rows = [r for r in types_rows if r["type"] == lot["type"]]
        st = [register[r["instrument_id"]]["provisional_substantive_status"] for r in rows if r["instrument_id"] in register]
        calibration.append({"lot": lot["lot"], "type": lot["type"], "rule_id": lot.get("rule_id", ""),
                            "type_rows": len(rows), "in_register": len(st),
                            "register_yes": st.count("yes"), "register_no": st.count("no"),
                            "register_other": len(st) - st.count("yes") - st.count("no"),
                            "not_in_register": len(rows) - len(st)})
    return members, counts, calibration


LOT_COLS = ["lot", "instrument_id", "number", "year", "confidence", "text_path", "text_grade", "app_title"]
CAL_COLS = ["lot", "type", "rule_id", "type_rows", "in_register", "register_yes", "register_no",
            "register_other", "not_in_register"]


def step_select(repo, out, cfg):
    members, counts, calibration = select_lots(repo, cfg)
    rows = [dict(r, lot=name) for name in members for r in members[name]]
    write_csv(Path(out) / "LOTS.csv", rows, LOT_COLS)
    write_csv(Path(out) / "CALIBRATION.csv", calibration, CAL_COLS)
    write_json(Path(out) / "SELECT.json", {"schema": "eo-jacquard-select/v1", "counts": counts,
               "lots_csv_sha256": hashlib.sha256((Path(out) / "LOTS.csv").read_bytes()).hexdigest()})
    return members, counts, calibration


def read_lots_csv(out):
    by = {}
    for r in read_csv(Path(out) / "LOTS.csv")[1]:
        by.setdefault(r["lot"], []).append(r)
    for rows in by.values():
        rows.sort(key=lambda r: r["instrument_id"])
    return by


# ---------------------------------------------------------------- sample

def sample_lot(cfg, lot, member_ids):
    ids = sorted(member_ids)
    n = len(ids)
    if n <= cfg["full_review_max"]:
        return {"lot": lot, "seed": cfg["seed"], "lot_size": n, "mode": "full", "sample_n": n, "sampled_ids": ids}
    rng = random.Random(sha_seed(cfg["seed"] + ":" + lot))
    picked = sorted(rng.sample(ids, cfg["sample_size"]))
    return {"lot": lot, "seed": cfg["seed"], "lot_size": n, "mode": "sampled", "sample_n": len(picked),
            "sampled_ids": picked}


def step_sample(out, cfg):
    by = read_lots_csv(out)
    lots = {}
    for lot in cfg["lots"]:
        ids = [r["instrument_id"] for r in by.get(lot["lot"], [])]
        s = sample_lot(cfg, lot["lot"], ids)
        s["bound_if_zero_failures"] = cp_upper(0, s["sample_n"]) if s["mode"] == "sampled" else None
        lots[lot["lot"]] = s
    doc = {"schema": "eo-jacquard-samples/v1", "seed": cfg["seed"], "sample_size": cfg["sample_size"],
           "full_review_max": cfg["full_review_max"], "lots": lots,
           "lots_csv_sha256": hashlib.sha256((Path(out) / "LOTS.csv").read_bytes()).hexdigest()}
    write_json(Path(out) / "SAMPLES.json", doc)
    return doc


# ---------------------------------------------------------------- packets

def control_count(sample_n):
    return max(2, round(0.08 * sample_n))


def claimed_title(row, reg=None):
    return (reg or {}).get("title") or row.get("app_title") or row.get("wpa_summary") or ""


def load_domesday(repo):
    """Full dates and titles from the Domesday register, so reviewers can check identity on more than a year."""
    path = Path(repo) / "jobs/domesday-register/output/REGISTER.csv"
    if not path.exists():
        return {}
    return {r["instrument_id"]: {"date": r.get("date", ""), "title": r.get("title", "")} for r in read_csv(path)[1]}


MARKER_RE = re.compile(r"^-{3,}\s*EXACT [A-Z ]+-{3,}\s*$")


def strip_preamble(raw):
    """Drop the provenance preamble some held texts carry ('# order: EO:...' lines, an '----- EXACT ... -----'
    marker). It names the order and its source, so it would unblind the review; the order text follows it."""
    lines = raw.split("\n")
    for i, line in enumerate(lines[:40]):
        if MARKER_RE.match(line.strip()):
            if all(not l.strip() or l.startswith("#") for l in lines[:i]):
                return "\n".join(lines[i + 1:])
            break
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        i += 1
    return "\n".join(lines[i:])


def make_text(repo, rel):
    raw = strip_preamble(read_text(repo, rel))
    if len(raw) > MAX_TEXT_CHARS:
        return raw[:MAX_TEXT_CHARS].rstrip("\n") + f"\n[TRUNCATED: original {len(raw)} characters]\n"
    return raw


def plan_lot(cfg, lot, members, sampled_ids, mode, pool):
    """Return list of item dicts for one lot (genuine + controls), unshuffled.

    members: LOTS rows of the lot; pool: TYPES rows eligible as intruders for this lot.
    """
    by_id = {r["instrument_id"]: r for r in members}
    sampled = sorted(sampled_ids)
    items = [{"kind": "genuine", "claim": by_id[i], "text": by_id[i]} for i in sampled]
    n_ctrl = control_count(len(sampled))
    rng = random.Random(sha_seed(cfg["seed"] + ":controls:" + lot))
    free_pool = sorted(pool, key=lambda r: r["instrument_id"])
    used_a, used_b = set(), set()
    all_ids = sorted(by_id)
    outside = [i for i in all_ids if i not in set(sampled)]
    for i in range(n_ctrl):
        want_intruder = i % 2 == 0
        if not want_intruder:
            a_opts = [x for x in sampled if x not in used_a]
            a = rng.choice(a_opts) if a_opts else None
            b = None
            if a is not None:
                b_opts = [x for x in (outside or all_ids) if x != a and x not in used_b]
                b_opts = b_opts or [x for x in all_ids if x != a and x not in used_b]
                b = rng.choice(b_opts) if b_opts else None
            if a is None or b is None:
                want_intruder = True
            else:
                used_a.add(a)
                used_b.add(b)
                items.append({"kind": "text_swap", "claim": by_id[a], "text": by_id[b], "a": a, "b": b})
        if want_intruder:
            if not free_pool:
                raise RuntimeError(f"no intruder candidates for lot {lot}")
            row = free_pool.pop(rng.randrange(len(free_pool)))
            items.append({"kind": "intruder", "claim": row, "text": row})
    return items


def arrange_batches(cfg, lot, items):
    """Shuffle and split into batches of at most MAX_BATCH; keep each text-swap away from its own twins."""
    rng = random.Random(sha_seed(cfg["seed"] + ":shuffle:" + lot))
    order = list(items)
    rng.shuffle(order)
    n = len(order)
    nb = max(1, math.ceil(n / MAX_BATCH))
    sizes = [n // nb + (1 if i < n % nb else 0) for i in range(nb)]
    batches, k = [], 0
    for s in sizes:
        batches.append(order[k:k + s])
        k += s

    def locate(item):
        for bi, b in enumerate(batches):
            for pi, x in enumerate(b):
                if x is item:
                    return bi, pi
        raise KeyError

    groups = []
    for it in items:
        if it["kind"] == "text_swap":
            twins = [x for x in items if x["kind"] == "genuine" and x["claim"]["instrument_id"] in (it["a"], it["b"])]
            groups.append([it] + twins)
    grouped = {id(x) for g in groups for x in g}
    if nb > 1:
        for g in groups:
            for _ in range(50):
                where = [locate(x)[0] for x in g]
                if len(set(where)) == len(where):
                    break
                dup = next(i for i, w in enumerate(where) if where.count(w) > 1)
                mover = g[dup]
                mb, mp = locate(mover)
                others = {w for i, w in enumerate(where) if i != dup}
                cands = [(bi, pi) for bi, b in enumerate(batches) if bi not in others and bi != mb
                         for pi, x in enumerate(b) if id(x) not in grouped]
                if not cands:
                    break
                bi, pi = rng.choice(cands)
                batches[mb][mp], batches[bi][pi] = batches[bi][pi], batches[mb][mp]
    for g in groups:
        g[0]["separated"] = len({locate(x)[0] for x in g}) == len(g)
    return batches


def intruder_pool(cfg, lot, types_rows, register, repo, exclude_ids):
    types = set(cfg["control_types"].get(lot, []))
    return [r for r in types_rows if r["type"] in types and r["instrument_id"] not in register
            and r["instrument_id"] not in exclude_ids and text_exists(repo, r["text_path"])]


def step_packets(repo, out, cfg, packets_dir, key_file):
    packets_dir, key_file = Path(packets_dir).resolve(), Path(key_file).resolve()
    if packets_dir == key_file.parent or packets_dir in key_file.parents:
        raise SystemExit("the key file must live outside the packets directory")
    samples = read_json(Path(out) / "SAMPLES.json")
    by = read_lots_csv(out)
    types_rows = load_types(repo)
    domesday = load_domesday(repo)
    register = load_register(repo)[1]
    all_members = {r["instrument_id"] for rows in by.values() for r in rows}
    key = {"schema": "eo-jacquard-key/v1", "seed": cfg["seed"], "items": {}, "lots": {}}
    packets_dir.mkdir(parents=True, exist_ok=True)
    for lot in cfg["lots"]:
        name = lot["lot"]
        members = by.get(name, [])
        if not members:
            continue
        s = samples["lots"][name]
        pool = intruder_pool(cfg, name, types_rows, register, repo, all_members)
        items = plan_lot(cfg, name, members, s["sampled_ids"], s["mode"], pool)
        batches = arrange_batches(cfg, name, items)
        lot_dir = packets_dir / name
        if lot_dir.exists():
            shutil.rmtree(lot_dir)
        key["lots"][name] = {"mode": s["mode"], "genuine": len(s["sampled_ids"]), "controls": len(items) - len(s["sampled_ids"]),
                             "items": len(items), "batches": len(batches)}
        for bi, batch in enumerate(batches, 1):
            bdir = lot_dir / f"batch-{bi:02d}"
            (bdir / "texts").mkdir(parents=True)
            lines = []
            for pi, it in enumerate(batch, 1):
                item_id = f"{name}-B{bi:02d}-{pi:02d}"
                claim = it["claim"]
                with open(bdir / "texts" / f"{item_id}.txt", "w", encoding="utf-8", newline="") as fh:
                    fh.write(make_text(repo, it["text"]["text_path"]))
                reg = domesday.get(claim["instrument_id"], {})
                lines.append(json.dumps({"item_id": item_id, "claimed_number": claim["number"],
                                         "claimed_date": reg.get("date") or str(claim["year"]),
                                         "claimed_title": claimed_title(claim, reg),
                                         "text_file": f"texts/{item_id}.txt"}, ensure_ascii=False))
                key["items"][item_id] = {"lot": name, "batch": f"batch-{bi:02d}", "kind": it["kind"],
                                         "instrument_id": claim["instrument_id"],
                                         "text_instrument_id": it["text"]["instrument_id"]}
                if it["kind"] == "text_swap":
                    key["items"][item_id]["twins_in_other_batches"] = bool(it.get("separated"))
            with open(bdir / "items.jsonl", "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(lines) + "\n")
    write_json(key_file, key)
    errors, warnings = scan_packets(packets_dir, key)
    return key, errors, warnings


def scan_packets(packets_dir, key):
    """Blinding check. errors: a forbidden word in a path or in items.jsonl keys/ids, or any answer-key
    instrument_id anywhere. warnings: forbidden words that occur inside claimed titles or held texts as
    ordinary English (these come from the historical documents and cannot be edited)."""
    errors, warnings = [], []
    word_re = re.compile("|".join(FORBIDDEN_WORDS), re.I)
    ids = {v["instrument_id"] for v in key["items"].values()} | {v["text_instrument_id"] for v in key["items"].values()}
    id_re = re.compile("(?:" + "|".join(re.escape(i) for i in sorted(ids)) + r")(?!\d)") if ids else None
    for p in sorted(Path(packets_dir).rglob("*")):
        rel = str(p.relative_to(packets_dir))
        if word_re.search(rel):
            errors.append(f"forbidden word in path {rel}")
        if not p.is_file():
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        if id_re and id_re.search(body):
            errors.append(f"answer-key instrument_id in {rel}")
        if p.name == "items.jsonl":
            for line in body.splitlines():
                obj = json.loads(line)
                structural = {k: v for k, v in obj.items() if k != "claimed_title"}
                if word_re.search(json.dumps(structural)):
                    errors.append(f"forbidden word in {rel}")
                if word_re.search(obj.get("claimed_title", "")):
                    warnings.append(f"{rel}:{obj['item_id']} title contains a listed word as ordinary text")
        elif word_re.search(body):
            warnings.append(f"{rel} contains a listed word as ordinary text")
    return errors, warnings


# ---------------------------------------------------------------- verify

def _type_ok(value, kind):
    if kind == "str":
        return isinstance(value, str)
    if kind == "bool":
        return isinstance(value, bool)
    if kind == "strlist":
        return isinstance(value, list) and all(isinstance(x, str) for x in value)
    return False


REVIEW_SCHEMA = {"item_id": "str", "identity": "str", "identity_evidence": "str", "type_fits": "bool",
                 "outliers_found": "strlist", "status_no_supported": "bool", "basis": "str",
                 "end_or_bound": "str", "operative_quote": "str", "notes": "str"}


def schema_problems(rev):
    probs = [f"missing or wrongly typed field {f}" for f, k in REVIEW_SCHEMA.items()
             if f not in rev or not _type_ok(rev[f], k)]
    if isinstance(rev.get("identity"), str) and rev["identity"] not in IDENTITY_VALUES:
        probs.append("identity not one of match|mismatch|cannot_tell")
    return probs


def quote_in_text(quote, text):
    q = normalize_ws(quote)
    return bool(q) and q in normalize_ws(text)


def genuine_failures(rev, text):
    """Reasons a genuine review is not upheld (empty list = upheld). rev must be schema-valid."""
    why = []
    if rev["identity"] != "match":
        why.append(f"identity_{rev['identity']}")
    if not rev["type_fits"]:
        why.append("type_does_not_fit")
    if not rev["status_no_supported"]:
        why.append("status_no_not_supported")
    if rev["outliers_found"]:
        why.append("outliers_flagged: " + "; ".join(rev["outliers_found"]))
    exempt = (not rev["status_no_supported"]) and rev["identity"] == "mismatch"
    if not exempt and not quote_in_text(rev["operative_quote"], text):
        why.append("operative_quote_empty" if not normalize_ws(rev["operative_quote"]) else "operative_quote_not_in_text")
    return why


def control_caught(kind, rev):
    if rev is None or schema_problems(rev):
        return False
    if kind == "intruder":
        return (not rev["type_fits"]) or (not rev["status_no_supported"])
    if kind == "text_swap":
        return rev["identity"] == "mismatch"
    raise ValueError(kind)


def read_batch_reviews(path):
    """Return (reviews_by_item_id, structural_errors). Duplicates are reported and removed from the map."""
    errs, seen, dup = [], {}, set()
    if not Path(path).is_file():
        return {}, [f"review file missing: {Path(path).name}"]
    for ln, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            errs.append(f"line {ln}: not JSON ({e.msg})")
            continue
        iid = obj.get("item_id") if isinstance(obj, dict) else None
        if not isinstance(iid, str):
            errs.append(f"line {ln}: no item_id")
            continue
        if iid in seen:
            dup.add(iid)
        seen[iid] = obj
    for iid in dup:
        errs.append(f"duplicate reviews for {iid}")
        del seen[iid]
    return seen, errs


def verify_batch(batch_dir, reviews_path, key_items):
    item_ids = [json.loads(l)["item_id"] for l in (Path(batch_dir) / "items.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    reviews, structural = read_batch_reviews(reviews_path)
    for iid in sorted(set(reviews) - set(item_ids)):
        structural.append(f"review for unknown item {iid}")
    for iid in item_ids:
        if iid not in reviews and not any(iid in e for e in structural):
            structural.append(f"no review for {iid}")
    missed, controls, genuine = [], {}, {}
    for iid in item_ids:
        k = key_items[iid]
        rev = reviews.get(iid)
        if k["kind"] == "genuine":
            if rev is None:
                continue
            probs = schema_problems(rev)
            if probs:
                genuine[iid] = {"instrument_id": k["instrument_id"], "reasons": ["schema: " + "; ".join(probs)]}
            else:
                text = (Path(batch_dir) / "texts" / f"{iid}.txt").read_text(encoding="utf-8", errors="replace")
                genuine[iid] = {"instrument_id": k["instrument_id"], "reasons": genuine_failures(rev, text)}
        else:
            caught = control_caught(k["kind"], rev)
            controls[iid] = {"kind": k["kind"], "caught": caught}
            if not caught:
                missed.append(iid)
    status = "incomplete" if structural else ("invalid" if missed else "valid")
    return {"status": status, "items": len(item_ids), "structural_errors": structural, "missed_controls": missed,
            "controls": controls, "genuine": genuine}


def step_verify(reviews_dir, key_file, packets_dir, out):
    key = read_json(key_file)
    result = {"schema": "eo-jacquard-verification/v1", "lots": {}}
    for lot in sorted(key["lots"]):
        keyed = {k: v for k, v in key["items"].items() if v["lot"] == lot}
        batch_names = sorted({v["batch"] for v in keyed.values()})
        batches, failures, upheld, rereview, discarded = {}, [], [], [], []
        for b in batch_names:
            res = verify_batch(Path(packets_dir) / lot / b, Path(reviews_dir) / lot / f"{b}.jsonl", keyed)
            batches[b] = {k: v for k, v in res.items() if k != "genuine"}
            if res["status"] != "valid":
                rereview.append(b)
                discarded += sorted(res["genuine"])
                continue
            for iid, g in sorted(res["genuine"].items()):
                if g["reasons"]:
                    failures.append({"item_id": iid, "instrument_id": g["instrument_id"], "reasons": g["reasons"]})
                else:
                    upheld.append({"item_id": iid, "instrument_id": g["instrument_id"]})
        result["lots"][lot] = {"batches": batches, "rereview_batches": rereview, "discarded_genuine_items": discarded,
                               "failures": failures, "upheld": upheld}
    write_json(Path(out) / "VERIFICATION.json", result)
    return result


# ---------------------------------------------------------------- accept

def accept_lot(lot_name, sample, verification, member_ids):
    """Decide one lot. sample: SAMPLES.json entry; verification: VERIFICATION.json lot entry or None."""
    mode, n = sample["mode"], sample["sample_n"]
    base = {"mode": mode, "lot_size": sample["lot_size"], "sample_n": n, "failures": None, "upper_bound_95": None,
            "adoptable_ids": [], "adoption_route": None, "individual_review_ids": [], "rereview_batches": []}
    if verification is None or verification["rereview_batches"]:
        base["status"] = "pending_rereview"
        base["rereview_batches"] = ["(no reviews)"] if verification is None else verification["rereview_batches"]
        return base
    failed = {f["instrument_id"] for f in verification["failures"]}
    upheld = sorted(u["instrument_id"] for u in verification["upheld"])
    base["failures"] = len(failed)
    base["failure_ids"] = sorted(failed)
    base["individual_review_ids"] = sorted(failed)
    base["upper_bound_95"] = cp_upper(len(failed), n)
    if mode == "sampled":
        if not failed and len(upheld) == n:
            base["status"] = "accepted"
            base["adoption_route"] = "sampled"
            base["adoptable_ids"] = sorted(set(member_ids) - failed)
        else:
            base["status"] = "rejected"
            base["adoption_route"] = "individual"
            base["adoptable_ids"] = upheld
    else:
        base["status"] = "full_review_complete"
        base["adoption_route"] = "full"
        base["adoptable_ids"] = upheld
        base["note"] = "every order was reviewed; the bound is shown for comparison and is not needed for adoption"
    return base


def step_accept(out):
    samples = read_json(Path(out) / "SAMPLES.json")
    ver = read_json(Path(out) / "VERIFICATION.json")
    by = read_lots_csv(out)
    doc = {"schema": "eo-jacquard-acceptance/v1", "seed": samples["seed"], "lots_csv_sha256": samples["lots_csv_sha256"],
           "lots": {}}
    review_rows = []
    for name, s in sorted(samples["lots"].items()):
        if s["lot_size"] == 0:
            continue
        a = accept_lot(name, s, ver["lots"].get(name), [r["instrument_id"] for r in by.get(name, [])])
        doc["lots"][name] = a
        lv = ver["lots"].get(name)
        if lv and not lv["rereview_batches"]:
            for f in lv["failures"]:
                review_rows.append({"lot": name, "instrument_id": f["instrument_id"], "item_id": f["item_id"],
                                    "reasons": " | ".join(f["reasons"]),
                                    "lot_decision": a["status"]})
    write_json(Path(out) / "ACCEPTANCE.json", doc)
    write_csv(Path(out) / "INDIVIDUAL_REVIEW.csv", review_rows, ["lot", "instrument_id", "item_id", "reasons", "lot_decision"])
    return doc


# ---------------------------------------------------------------- propose

def origin_text(lot, route):
    word = {"sampled": "sampled", "full": "full", "individual": "individual"}[route]
    return (f"jacquard-{lot}-{ORIGIN_DATE}:ai_class_status ({word} review "
            f"research/excavator/jacquard-{ORIGIN_DATE}/{lot}; ruling {RULING})")


def build_rows(header, acceptance, register_ids):
    rows, skipped, seen = [], [], set()
    for lot, a in sorted(acceptance["lots"].items()):
        for iid in a["adoptable_ids"]:
            if iid in register_ids or iid in seen:
                skipped.append(iid)
                continue
            seen.add(iid)
            row = {c: "" for c in header}
            row.update(TEMPLATE_ROW)
            row.update({"instrument_id": iid, "provisional_substantive_status": "no",
                        "decision_origin": origin_text(lot, a["adoption_route"])})
            rows.append(row)
    return rows, skipped


def step_propose(repo, out):
    header, register = load_register(repo)
    missing = [c for c in TEMPLATE_ROW if c not in header]
    if missing:
        raise SystemExit(f"register header lacks expected columns: {missing}")
    acc = read_json(Path(out) / "ACCEPTANCE.json")
    rows, skipped = build_rows(header, acc, set(register))
    write_csv(Path(out) / "PROPOSED_STATUS_ROWS.csv", rows, header)
    return rows, skipped


# ---------------------------------------------------------------- needs.txt

def needed_dirs(members):
    """Top-level folders (beyond jobs/ HANDOFF/ .github/) that selected texts live in."""
    tops = set()
    for rows in members.values():
        for r in rows:
            parts = Path(r["text_path"]).parts
            if parts and parts[0] not in ("jobs", "HANDOFF", ".github"):
                tops.add("/".join(parts[:2]) if parts[0] == "research" and len(parts) > 2 else parts[0])
    return sorted(tops)


# ---------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=["select", "sample", "packets", "verify", "accept", "propose"])
    ap.add_argument("--repo", default=str(DEFAULT_REPO))
    ap.add_argument("--out", default=str(HERE / "output"), help="working directory for LOTS.csv, SAMPLES.json, ...")
    ap.add_argument("--config", default=str(HERE / "lots.json"))
    ap.add_argument("--packets-dir", default=None, help="default OUT/packets")
    ap.add_argument("--key-file", default=None, help="default OUT/CONTROL_KEY.json")
    ap.add_argument("--reviews", default=None, help="directory holding <lot>/batch-NN.jsonl; default OUT/reviews")
    a = ap.parse_args(argv)
    cfg, out, repo = load_config(a.config), Path(a.out), Path(a.repo)
    out.mkdir(parents=True, exist_ok=True)
    packets_dir = Path(a.packets_dir) if a.packets_dir else out / "packets"
    key_file = Path(a.key_file) if a.key_file else out / "CONTROL_KEY.json"
    if a.step == "select":
        members, counts, _ = step_select(repo, out, cfg)
        for k, c in counts.items():
            print(k, json.dumps(c))
        print("needed folders beyond jobs/:", needed_dirs(members) or "none")
    elif a.step == "sample":
        for k, s in step_sample(out, cfg)["lots"].items():
            print(k, s["mode"], "lot", s["lot_size"], "sample", s["sample_n"])
    elif a.step == "packets":
        key, errors, warnings = step_packets(repo, out, cfg, packets_dir, key_file)
        for k, v in key["lots"].items():
            print(k, json.dumps(v))
        for e in errors:
            print("ERROR", e)
        print(f"{len(warnings)} ordinary-text warnings")
        return 1 if errors else 0
    elif a.step == "verify":
        res = step_verify(a.reviews or out / "reviews", key_file, packets_dir, out)
        for lot, v in res["lots"].items():
            print(lot, {b: x["status"] for b, x in v["batches"].items()}, "failures", len(v["failures"]), "upheld", len(v["upheld"]))
    elif a.step == "accept":
        for lot, v in step_accept(out)["lots"].items():
            print(lot, v["status"], "failures", v["failures"], "bound", v["upper_bound_95"], "adoptable", len(v["adoptable_ids"]))
    elif a.step == "propose":
        rows, skipped = step_propose(repo, out)
        print(len(rows), "rows written;", len(skipped), "skipped (already in register or duplicate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
