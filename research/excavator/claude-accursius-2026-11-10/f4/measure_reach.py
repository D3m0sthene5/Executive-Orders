"""Accursius F4: measured reach of routing held acting texts into undecided dossiers.

Run on a read-only checkout of main with every job output (the reference worktree), importing the F4 compiler
code from this branch:

    python -I measure_reach.py --repo C:/Users/danie/eo-wt/accursius --code C:/Users/danie/eo-wt/acc-f4/jobs/claim-kit --out .

Proxy (no corpus rebuild): the branch's inputs.load_corpus on main data gives the acting-text declarations and
pairs; the main compiled kit (jobs/claim-kit/output, generation 2026-11-10T10:36Z) gives each undecided order's
known actors, located ACT records and census actor sources. For each undecided order this counts the ACTOR_TEXT
records the branch's build.package() would add (exact text, a held file hash, a text that prints the order's
number), as the frozen overlay will after a rebuild. Writes REACH.json and REACH_ORDERS.csv. Nothing else.
"""
import argparse
import collections
import csv
import glob
import hashlib
import json
import pickle
from pathlib import Path
import re
import sys
import time

ENDING = re.compile(r"(?i)\b(?:revok\w*|supersed\w*|terminat\w*|rescind\w*|rescission|abolish\w*|repeal\w*|"
                    r"restor\w*|cancel\w*|vacat\w*|no\s+longer\s+(?:be\s+)?in\s+effect|shall\s+cease|expire\w*)\b")
DIAGNOSED = ["EO:2738", "EO:9211", "EO:9372", "EO:13204", "EO:13354", "EO:13024", "EO:8617", "EO:9181", "EO:9231",
             "EO:10350", "EO:14231", "EO:8790", "EO:8649", "EO:2225", "EO:3748", "EO:5495", "EO:8153", "EO:9554",
             "EO:13836", "EO:3761", "EO:7721", "EO:8266", "EO:8511", "EO:9124", "EO:9390", "EO:8627", "EO:5739",
             "EO:7621", "EO:9013", "EO:12072", "EO:12178", "EO:12379", "EO:13552", "EO:8724", "EO:10565"]


def shards(out, stem):
    return sorted(glob.glob(str(out / (stem + ".jsonl")))) + sorted(glob.glob(str(out / (stem + ".part*.jsonl"))))


def rows(out, stem):
    for path in shards(out, stem):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)


def job_of(origins):
    jobs = sorted({o.split("/")[1] for o in origins if o.startswith("jobs/")})
    return "+".join(jobs) or "unknown"


def ending_near(text, spans, radius=300):
    return any(ENDING.search(text[max(0, s - radius):e + radius]) for s, e in spans)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--code", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--old-csv", help="the first REACH_ORDERS.csv (commit 04acdce567), for the reviewer's sample")
    ap.add_argument("--cache", help="optional pickle of the corpus subset, outside the repository")
    args = ap.parse_args()
    repo, code, dest = Path(args.repo).resolve(), Path(args.code).resolve(), Path(args.out).resolve()
    sys.path.insert(0, str(code))
    import build as B
    import inputs as I
    t0 = time.time()
    cache = Path(args.cache) if args.cache else None
    if cache and cache.is_file():
        corpus = pickle.loads(cache.read_bytes())
    else:
        full = I.load_corpus(repo)
        corpus = {k: full[k] for k in ("universe", "statuses", "acting_texts", "pairs")}
        if cache:
            cache.write_bytes(pickle.dumps(corpus))
    t_corpus = time.time() - t0
    universe, statuses = corpus["universe"], corpus["statuses"]
    kit = repo / "jobs/claim-kit/output"
    leads = {r["instrument_id"]: r for r in rows(kit, "STATUS_LEADS")}
    undecided = set(leads)
    known, signed = {}, {}
    for r in rows(kit, "OVERLAY_INPUTS"):
        known[r["instrument_id"]] = set(r.get("known_actor_ids") or [])
        signed[r["instrument_id"]] = (r.get("selected") or {}).get("signing_date")
    acts = collections.defaultdict(list)
    for a in rows(kit, "ACTING_PROVISIONS"):
        if a.get("target_id") in undecided:
            acts[a["target_id"]].append(a)

    # ---- non-census acting texts (defects 2 and 3) ------------------------------------------------------
    acting_rows = [r for r in corpus["acting_texts"] if r["instrument_id"] not in universe]
    pairs = {(p["target_id"], p["actor_id"]) for p in corpus["pairs"] if p["target_id"] in universe}
    nc_pairs = {(t, a) for t, a in pairs if a not in universe}
    wanted = {a for _, a in nc_pairs}
    t1 = time.time()
    selected, refused = B.select_acting_texts(repo, acting_rows, wanted)
    t_select = time.time() - t1
    by_order = collections.defaultdict(list)
    pair_stats = collections.Counter()
    for target, actor in sorted(nc_pairs):
        ar = selected.get(actor)
        undec = target in undecided
        if ar is None:
            pair_stats["no_held_text" + ("_undecided" if undec else "")] += 1
            continue
        mentions = B.target_mentions(target, ar["text"], signed.get(target), actor.startswith("FRDOC:"))
        if not mentions:
            pair_stats["held_unnamed" + ("_undecided" if undec else "")] += 1
            continue
        pair_stats["held_named" + ("_undecided" if undec else "")] += 1
        if not undec:
            continue
        evidence, missing = {}, []
        ctx = B._actor_context(target, actor, ar, [], evidence, missing, signed.get(target))
        by_order[target].append({
            "basis_eligible": any(e.get("basis_eligible") for e in evidence.values()),
            "actor_id": actor, "kind": actor.split(":")[0], "job": job_of(ar.get("origins", [])),
            "grade": (ar.get("grade") or "")[:60], "evidence_ids": sorted(evidence),
            "window": "evidence_ids" in ctx, "ending_verb_near_number": ending_near(ar["text"], mentions),
            "text_path": ar["text_path"]})

    # ---- census overflow actors get window ids (defect 1) -----------------------------------------------
    census_sources = {}
    need = set()
    for iid in undecided:
        need |= {a for a in known.get(iid, set()) | {x["actor_id"] for x in acts.get(iid, [])} if a in universe}
    for r in rows(kit, "CLAUSES"):
        if r.get("instrument_id") in need:
            census_sources[r["instrument_id"]] = r["source"]
    texts, sizes = {}, {}
    for actor, src in census_sources.items():
        p = repo / src["text_path"]
        if not p.is_file():
            continue  # not present in this checkout
        if p.stat().st_size > B.ACTOR_TEXT_LIMIT:
            raw = p.read_bytes()
            if hashlib.sha256(raw).hexdigest() == src.get("text_sha256"):
                texts[actor] = raw.decode("utf-8")
    overflow = {}
    for iid in sorted(undecided):
        actors = (known.get(iid, set()) | {x["actor_id"] for x in acts.get(iid, [])}) & set(texts)
        for actor in sorted(actors):
            ar = {"text": texts[actor], "source": census_sources[actor], "text_path": census_sources[actor]["text_path"]}
            evidence, missing = {}, []
            ctx = B._actor_context(iid, actor, ar, acts.get(iid, []), evidence, missing, signed.get(iid))
            named = [e for e in evidence.values() if e.get("prints_number_lexical")]
            mentions = B.target_mentions(iid, ar["text"], signed.get(iid)) or []
            overflow.setdefault(iid, []).append({
                "actor_id": actor, "windows": len(evidence), "windows_naming_target": len(named),
                "evidence_ids": sorted(evidence), "ending_verb_near_number": ending_near(ar["text"], mentions)})

    # ---- SUPPLEMENT eligibility on existing supplement declarations --------------------------------------
    import source_supplement as S
    official = S.official_declarations(repo)
    supp = collections.Counter()
    supp_orders = set()
    for receipt in sorted(glob.glob(str(repo / "research/excavator/*/*/SOURCE_SUPPLEMENT.json")) +
                          glob.glob(str(repo / "research/readiness/*/*/SOURCE_SUPPLEMENT.json"))):
        meta = json.loads(Path(receipt).read_text(encoding="utf-8"))
        supp["receipts"] += 1
        decl = repo / meta["declarations"]["path"]
        try:
            entries = json.loads(decl.read_text(encoding="utf-8"))["sources"]
        except (OSError, ValueError, KeyError):
            supp["declaration_unreadable"] += 1
            continue
        for entry in entries:
            src = entry["source"]
            try:
                text = (repo / src["text_path"]).read_bytes().decode("utf-8")
            except OSError:
                supp["excerpt_text_missing"] += 1
                continue
            supp["entries"] += 1
            for iid in entry["instrument_ids"]:
                if iid not in undecided:
                    continue
                mark = S.basis_mark(repo, src, text, entry["char_start"], entry["char_end"], iid, official)
                supp["undecided_member_excerpts"] += 1
                supp["prints_number_lexical"] += bool(mark["prints_number_lexical"])
                supp["official"] += bool(mark["official_declaration"])
                supp["basis_eligible"] += mark["basis_eligible"]
                if mark["basis_eligible"]:
                    supp_orders.add(iid)

    # ---- totals ----------------------------------------------------------------------------------------
    gain_nc = {iid for iid, recs in by_order.items() if recs}
    gain_ov = {iid for iid, recs in overflow.items() if any(r["windows_naming_target"] for r in recs)}
    by_job = collections.defaultdict(set)
    by_job_end = collections.defaultdict(set)
    by_kind = collections.defaultdict(set)
    for iid, recs in by_order.items():
        for r in recs:
            by_job[r["job"]].add(iid)
            by_kind[r["kind"]].add(iid)
            by_job_end[(r["job"], r["ending_verb_near_number"])].add(iid)
    ending_any = {iid for iid, recs in by_order.items() if any(r["ending_verb_near_number"] for r in recs)}
    eligible_nc = {iid for iid, recs in by_order.items() if any(r["basis_eligible"] for r in recs)}
    eligible_nc_end = {iid for iid in eligible_nc if any(r["basis_eligible"] and r["ending_verb_near_number"] for r in by_order[iid])}
    basis_any = eligible_nc | gain_ov
    lead_only = gain_nc - basis_any
    # The reviewer's false-positive sample: the 130 FRDOC rows (99 orders) below EO 7000 in the first REACH_ORDERS.csv.
    old_low, still = [], []
    if args.old_csv:
        with open(args.old_csv, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                n = r["instrument_id"][3:]
                if r["actor_id"].startswith("FRDOC") and n.isdigit() and int(n) < 7000:
                    old_low.append((r["instrument_id"], r["actor_id"]))
        now = {(iid, r["actor_id"]) for iid, recs in by_order.items() for r in recs}
        still = [pair for pair in old_low if pair in now]
        contexts = []
        for iid, actor in still:
            text = selected[actor]["text"]
            for s0, e0 in (B.target_mentions(iid, text, signed.get(iid), actor.startswith("FRDOC:")) or [])[:2]:
                contexts.append(f"{iid} {actor} | " + text[max(0, s0 - 110):e0 + 70].replace("\n", " "))
        (dest / "LOW_FRDOC_REMAINING.txt").write_text("\n".join(contexts) + "\n", encoding="utf-8")
    ov_end = {iid for iid in gain_ov if any(r["ending_verb_near_number"] and r["windows_naming_target"] for r in overflow[iid])}
    result = {
        "schema": "accursius-f4-reach/v1", "repo_head_note": "reference worktree (origin/main 854514831e with outputs)",
        "proxy": ("branch inputs.load_corpus + build.select_acting_texts/target_mentions/_actor_context on main data; "
                  "known actors and ACT records from the main compiled kit (generation 2026-11-10T10:36Z); "
                  "no corpus rebuild. Version 2 (after the F4 review): pairs only from event fragments, lexical check v2, "
                  "non-census records basis_eligible only as official printings, window bytes capped"),
        "seconds": {"load_corpus": round(t_corpus, 1), "select_acting_texts": round(t_select, 1)},
        "undecided_orders_in_kit": len(undecided),
        "acting_text_declarations_non_census": len(acting_rows),
        "acting_actors_with_text": len({r["instrument_id"] for r in acting_rows}),
        "acting_actors_with_more_than_one_text": sum(1 for _, n in collections.Counter(r["instrument_id"] for r in acting_rows).items() if n > 1),
        "acting_texts_selected_bytes": sum(len(a["text"].encode("utf-8")) for a in selected.values()),
        "acting_texts_refused": refused[:50], "acting_texts_refused_count": len(refused),
        "non_census_pairs": dict(sorted(pair_stats.items())),
        "undecided_gaining_non_census_actor_text": len(gain_nc),
        "of_which_ending_verb_near_number": len(ending_any),
        "by_source_job": {k: len(v) for k, v in sorted(by_job.items())},
        "by_source_job_and_ending_verb": {f"{k[0]}|ending_verb={k[1]}": len(v) for k, v in sorted(by_job_end.items())},
        "by_actor_kind": {k: len(v) for k, v in sorted(by_kind.items())},
        "non_census_records_added": sum(len(r["evidence_ids"]) for recs in by_order.values() for r in recs),
        "census_overflow_actor_texts_in_undecided_dossiers": sum(len(v) for v in overflow.values()),
        "census_overflow_actor_texts_now_with_ids": sum(1 for v in overflow.values() for r in v if r["windows"]),
        "census_overflow_actor_texts_with_window_naming_target": sum(1 for v in overflow.values() for r in v if r["windows_naming_target"]),
        "undecided_gaining_overflow_window_naming_target": len(gain_ov),
        "of_which_ending_verb_near_number_overflow": len(ov_end),
        "undecided_gaining_any_new_actor_text_naming_them": len(gain_nc | gain_ov),
        "undecided_gaining_any_with_ending_verb": len(ending_any | ov_end),
        "undecided_gaining_basis_eligible_non_census_record": len(eligible_nc),
        "of_which_ending_verb_near_number_basis_eligible": len(eligible_nc_end),
        "undecided_gaining_census_overflow_window_naming_them (gate as on main)": len(gain_ov),
        "undecided_gaining_any_citable_basis_record": len(basis_any),
        "undecided_gaining_lead_only_records": len(lead_only),
        "lead_only_by_source_job": {k: len(v & lead_only) for k, v in sorted(by_job.items())},
        "basis_eligible_by_source_job": {k: len({iid for iid, recs in by_order.items() if any(r["job"] == k and r["basis_eligible"] for r in recs)}) for k in sorted(by_job)},
        "reviewer_sample_low_frdoc_rows_before": len(old_low),
        "reviewer_sample_low_frdoc_rows_remaining": len(still),
        "reviewer_sample_low_frdoc_orders_remaining": len({i for i, _ in still}),
        "supplement_existing_declarations": dict(supp), "supplement_basis_eligible_orders": len(supp_orders),
        "diagnosed": {},
        "notice": "Machine reach of citable records only. Whether a record supports a NO is the producers' and reviewers' judgment.",
    }
    for iid in DIAGNOSED:
        result["diagnosed"][iid] = {
            "undecided": iid in undecided,
            "non_census": by_order.get(iid, []),
            "overflow": overflow.get(iid, []),
            "non_census_pairs": sorted(a for t, a in nc_pairs if t == iid),
            "number_not_found_held": sorted(a for t, a in nc_pairs if t == iid and a in selected and not B.target_mentions(iid, selected[a]["text"], signed.get(iid), a.startswith("FRDOC:"))),
            "kit_known_actors": sorted(known.get(iid, set())),
        }
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "REACH.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (dest / "REACH_ORDERS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["instrument_id", "route", "actor_id", "source_job", "evidence_ids", "ending_verb_near_number", "basis_eligible"])
        for iid in sorted(by_order):
            for r in by_order[iid]:
                w.writerow([iid, "non_census_acting_text", r["actor_id"], r["job"], " ".join(r["evidence_ids"]), r["ending_verb_near_number"], r["basis_eligible"]])
        for iid in sorted(gain_ov):
            for r in overflow[iid]:
                if r["windows_naming_target"]:
                    w.writerow([iid, "census_overflow_window", r["actor_id"], "", " ".join(r["evidence_ids"]), r["ending_verb_near_number"], "gate_as_on_main"])
    print(json.dumps({k: v for k, v in result.items() if k != "diagnosed"}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
