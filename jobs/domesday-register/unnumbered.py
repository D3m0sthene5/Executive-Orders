"""Catalogued-unnumbered identities (owner ruling R10): Lord 1943 rows deduplicated against the census-completeness clusters.

The numbered series is censused elsewhere (the 14,972-order census and the readiness tracker). Orders that
carry no number are a second series. This module lists them as identities of class `catalogued_unnumbered`
and measures, by capture-recapture, how many such orders the two available lists miss. Nothing here admits an
order to the census, authenticates an identity, assigns a status or changes any numbered-series count.

Inputs (all committed): data/UNNUMBERED_SEED.csv (one row per Lord 1943 unnumbered entry), and the committed
outputs of jobs/census-completeness (MENTIONS.csv, MATCHES.csv, CLUSTERS.csv), and the census identity layer
(only to look for a firm EO:UN match).

DEDUPLICATION RULE (never on date alone)
  A Lord row and a completeness-cluster mention are ONE identity when
    (a) the Lord row's date is day-precise and the mention's date is day-precise and the two dates are equal, AND
    (b) their subjects share at least MIN_SHARED_TOKENS (= 2) distinctive words. A distinctive word is a word of
        five or more letters that is not on census-completeness's stop list of generic land-order vocabulary;
        the tokens are the ones census-completeness already computed (MENTIONS.csv `tokens`).
  A month- or year-precise Lord date never merges (no exact date to share). A same-date pair with fewer than two
  shared words stays two identities. The completeness job's own rule is looser (one shared word on a day-precise
  date, or two words on year-only Lord dates, or a page citation); this rule keeps only the pairs that also meet
  (a) and (b). Mentions from non-Lord lists keep the completeness job's grouping among themselves. Lord rows
  that reach the same group are joined into one identity (Lord printed the same order in two entries).
  Sensitivity at one and three shared words is written to the summary.

A row in a completeness cluster that is numbered (it contains a WPA numbered-series mention or a link to one) is
left out of the cluster side, as the completeness job leaves it out of its own estimates. A Lord row that sits in
such a cluster keeps its own identity here (it is on Lord's unnumbered list) and is flagged in the summary.

CAPTURE-RECAPTURE
  List 1 = identities with at least one Lord row; list 2 = identities with at least one mention from the other
  project sources (Richardson, GPO 1912, War Department and General Land Office books). Restricted to 1789-1899,
  the years the cluster list covers (it reads no source after 1899), and to identities whose date is day-precise,
  the only identities the rule can match across lists. Chapman: N = (n1+1)(n2+1)/(m+1) - 1; Seber variance
  v = (n1+1)(n2+1)(n1-m)(n2-m) / ((m+1)^2 (m+2)); with S = n1+n2-m observed and f0 = N - S unseen, the 95% interval
  is S + f0/C .. S + f0*C, C = exp(1.96 * sqrt(ln(1 + v/f0^2))) (Chao's log-normal interval).
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone

MIN_SHARED_TOKENS = 2
LAST_COMMON_YEAR = 1899
SUBJECT_CHARS = 300
SEED_FIELDS = ["seed_id", "lord_page", "date", "date_certainty", "subject", "cluster_id"]
OUT_FIELDS = ["unnumbered_id", "lord_seed_ids", "cluster_ids", "lord_page", "date", "date_certainty", "subject",
              "census_id_if_any", "sources"]
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
WPA_UNNUMBERED = "jobs/x1-class-engine/data/WPA_UNNUMBERED_ENTRIES.csv"
COMPLETENESS = "jobs/census-completeness/output"
CENSUS = "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
SEED_REL = "data/UNNUMBERED_SEED.csv"


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


# ----------------------------------------------------------------------------- seed

def iso_date(year, text):
    """Lord's year plus the printed 'Aug 28' / 'Sept. 7' / '' -> (ISO date as precise as printed, certainty)."""
    y = int(year)
    m = re.match(r"^([A-Za-z]{3,9})\.?\s*(\d{1,2})?(?!\d)", (text or "").strip())
    mon = MONTHS.get(m.group(1).lower()[:3]) if m else None
    if not mon:
        return f"{y:04d}", "year"
    if m.group(2) and 1 <= int(m.group(2)) <= 31:
        return f"{y:04d}-{mon:02d}-{int(m.group(2)):02d}", "day"
    return f"{y:04d}-{mon:02d}", "month"


def lord_mention_id(seq):
    return f"LORD:U:{int(seq):04d}"


def build_seed(wpa_rows, clusters):
    """One seed row per Lord entry. cluster_id is the completeness cluster whose members include the Lord mention
    (pre-1900 entries only; the completeness job reads no later source)."""
    cluster_of = {}
    for c in clusters:
        for member in c["members"].split("|"):
            cluster_of[member] = c["cluster_id"]
    out = []
    for r in wpa_rows:
        seq = int(r["seq"])
        date, certainty = iso_date(r["year"], r["date"])
        out.append({"seed_id": f"CU:{seq}", "lord_page": r["page"], "date": date, "date_certainty": certainty,
                    "subject": re.sub(r"\s+", " ", r["summary"]).strip()[:SUBJECT_CHARS],
                    "cluster_id": cluster_of.get(lord_mention_id(seq), "")})
    return out


# ----------------------------------------------------------------------------- identities

class UnionFind:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def tokens_of(row):
    return set(t for t in (row.get("tokens") or "").split("|") if t)


def numbered_mentions(mentions, clusters):
    """Mention ids in a cluster that holds a numbered-series (WPA) mention or a link to one."""
    cluster_of = {}
    for c in clusters:
        for member in c["members"].split("|"):
            cluster_of[member] = c["cluster_id"]
    bad = {cid for m in mentions for cid in [cluster_of.get(m["mention_id"])]
           if cid and (m["source"] == "WPA" or m.get("link_wpa"))}
    return {mid for mid, cid in cluster_of.items() if cid in bad}, cluster_of


def build_identities(seed, mentions, matches, clusters, census_rows=(), min_shared=MIN_SHARED_TOKENS):
    by_id = {m["mention_id"]: m for m in mentions}
    numbered, cluster_of = numbered_mentions(mentions, clusters)
    cluster_label = {c["cluster_id"]: c["label"] for c in clusters}
    seeds = {s["seed_id"]: s for s in seed}
    uf = UnionFind()
    for sid in seeds:
        uf.find(sid)
    others = [m for m in mentions if m["source"] not in ("LORD", "WPA") and m["mention_id"] not in numbered]
    for m in others:
        uf.find(m["mention_id"])
    other_ids = {m["mention_id"] for m in others}
    merged_pairs = 0
    seen = set()
    for e in matches:
        a, b = e["a"], e["b"]
        if (a, b) in seen:
            continue
        seen.add((a, b))
        if e["source_a"] == "LORD" and e["source_b"] not in ("LORD", "WPA"):
            sid = f"CU:{int(a.split(':')[-1])}"
            s, m = seeds.get(sid), by_id.get(b)
            if not s or m is None or b not in other_ids:
                continue
            la = by_id.get(a)
            # exact day-precise date on both sides, and a substantial subject overlap
            if (s["date_certainty"] == "day" and m["precision"] == "day" and m["date"] == s["date"]
                    and la is not None and len(tokens_of(la) & tokens_of(m)) >= min_shared):
                uf.union(sid, b)
                merged_pairs += 1
        elif e["source_a"] not in ("LORD", "WPA") and e["source_b"] not in ("LORD", "WPA") and a in other_ids and b in other_ids:
            uf.union(a, b)
    groups = collections.defaultdict(lambda: {"seeds": [], "mentions": []})
    for sid in seeds:
        groups[uf.find(sid)]["seeds"].append(sid)
    for m in others:
        groups[uf.find(m["mention_id"])]["mentions"].append(m["mention_id"])

    un_firm = {}
    for r in census_rows:
        mt = re.match(r"^EO:UNN:LORD1944:p(\d+):(\d{4}-\d{2}-\d{2})$", r.get("id", ""))
        if mt:
            un_firm.setdefault((mt.group(1), mt.group(2)), []).append(r["id"])

    rows = []
    for g in groups.values():
        g["seeds"].sort(key=lambda s: int(s.split(":")[1]))
        ss = [seeds[s] for s in g["seeds"]]
        ms = [by_id[x] for x in sorted(g["mentions"])]
        cids = sorted({cluster_of[x["mention_id"]] for x in ms if x["mention_id"] in cluster_of})
        day = [s for s in ss if s["date_certainty"] == "day"]
        if day:
            date, cert = day[0]["date"], "day"
        elif ms and any(m["precision"] == "day" for m in ms):
            first = next(m for m in sorted(ms, key=lambda m: m["mention_id"]) if m["precision"] == "day")
            date, cert = first["date"], "day"
        elif ss:
            best = sorted(ss, key=lambda s: {"month": 0, "year": 1}[s["date_certainty"]])[0]
            date, cert = best["date"], best["date_certainty"]
        else:
            first = sorted(ms, key=lambda m: m["mention_id"])[0]
            date, cert = first["date"], first["precision"]
        if ss:
            subject = ss[0]["subject"]
            uid = f"CUN:L{int(g['seeds'][0].split(':')[1]):04d}"
            page = ss[0]["lord_page"]
        else:
            lab = max((cluster_label.get(cluster_of.get(m["mention_id"]), m["label"]) for m in ms), key=len)
            subject = re.sub(r"\s+", " ", lab).strip()[:SUBJECT_CHARS]
            uid = f"CUN:M:{ms[0]['mention_id']}"
            page = ""
        srcs = (["LORD"] if ss else []) + sorted({m["source"] for m in ms})
        census = ""
        if ss and cert == "day":
            for s in day:
                hit = un_firm.get((s["lord_page"], s["date"]))
                if hit and s["date"] == date:
                    census = "|".join(sorted(hit))
        rows.append({"unnumbered_id": uid, "lord_seed_ids": "|".join(g["seeds"]), "cluster_ids": "|".join(cids),
                     "lord_page": page, "date": date, "date_certainty": cert, "subject": subject,
                     "census_id_if_any": census, "sources": "|".join(srcs)})
    rows.sort(key=lambda r: (r["date"], r["unnumbered_id"]))
    flagged = sorted(s for s in seeds if f"LORD:U:{int(s.split(':')[1]):04d}" in numbered)
    return rows, {"merged_lord_mention_pairs": merged_pairs, "lord_rows_in_numbered_clusters": flagged}


# ----------------------------------------------------------------------------- capture-recapture

def chapman(n1, n2, m):
    """Chapman two-list estimate with Seber's variance and a log-normal 95% interval on the unseen count."""
    if n1 == 0 or n2 == 0:
        return None
    N = (n1 + 1) * (n2 + 1) / (m + 1) - 1
    var = (n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m) / ((m + 1) ** 2 * (m + 2))
    seen = n1 + n2 - m
    f0 = max(N - seen, 0.0)
    if f0 > 0 and var > 0:
        c = math.exp(1.96 * math.sqrt(math.log(1 + var / f0 ** 2)))
        lo, hi = seen + f0 / c, seen + f0 * c
    else:
        lo = hi = seen + f0
    return {"n1": n1, "n2": n2, "m": m, "observed_union": seen, "N_hat": round(N, 1), "variance": round(var, 1),
            "ci95": [round(lo, 1), round(hi, 1)], "unseen_hat": round(f0, 1)}


def estimate(rows, last_year=LAST_COMMON_YEAR, exclude_seeds=()):
    """Capture-recapture over day-precise identities dated 1789..last_year. Identities holding a Lord row that sits
    in a numbered cluster are left out of both lists (the completeness job leaves those clusters out too)."""
    skip = set(exclude_seeds)

    def pool(sub):
        day = [r for r in sub if r["date_certainty"] == "day" and int(r["date"][:4]) <= last_year
               and not skip.intersection(r["lord_seed_ids"].split("|"))]
        l1 = [r for r in day if r["lord_seed_ids"]]
        l2 = [r for r in day if r["cluster_ids"]]
        both = [r for r in day if r["lord_seed_ids"] and r["cluster_ids"]]
        return chapman(len(l1), len(l2), len(both))
    out = {"1789-1899": pool(rows)}
    for name, lo, hi in (("1789-1861", 1789, 1861), ("1862-1899", 1862, 1899)):
        out[name] = pool([r for r in rows if lo <= int(r["date"][:4]) <= hi])
    return out


# ----------------------------------------------------------------------------- run

ASSUMPTIONS = [
    {"assumption": "Closed population",
     "may_fail_because": "The target is orders signed 1789-1899 and absent from no printed list; the cluster list is built from "
                         "later printings (1880-1916), so orders revoked or never printed are in neither list; a Lord entry can describe "
                         "a signed order or only a departmental act (Richardson prints both). Direction: unclear; a loose boundary "
                         "inflates the Lord-only count and so the estimate."},
    {"assumption": "Independent lists",
     "may_fail_because": "Lord (1943) cites the General Land Office, War Department, Indian-reservation and Richardson volumes as his sources, "
                         "so an order in those books is more likely in Lord. Positive dependence makes m too large, so N is UNDER-stated: "
                         "the interval is a floor on the true uncertainty, not a ceiling."},
    {"assumption": "Equal catchability within each list",
     "may_fail_because": "Large, well-known orders (big reservations, named parks) are caught by every list; small or unusual ones by none. "
                         "Heterogeneity again under-states N. Day-precise dates are caught more often than year-only ones, so the estimate "
                         "is restricted to day-precise identities and says nothing directly about the rest."},
    {"assumption": "Matches are correct",
     "may_fail_because": "The rule needs an exact day-precise date and two shared distinctive words; OCR errors in dates or subjects make true "
                         "matches fail (m too small, N over-stated); same-day orders about similar places can merge falsely (m too large, N under-stated)."},
]


def load_inputs(root, seed_path=None):
    seed_path = seed_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), SEED_REL)
    seed = read_csv(seed_path)
    cdir = os.path.join(root, COMPLETENESS)
    mentions = read_csv(os.path.join(cdir, "MENTIONS.csv"))
    matches = read_csv(os.path.join(cdir, "MATCHES.csv"))
    clusters = read_csv(os.path.join(cdir, "CLUSTERS.csv"))
    census = read_csv(os.path.join(root, CENSUS)) if os.path.isfile(os.path.join(root, CENSUS)) else []
    return seed, mentions, matches, clusters, census, seed_path, cdir


def run(root, out_dir, seed_path=None):
    seed, mentions, matches, clusters, census, seed_path, cdir = load_inputs(root, seed_path)
    os.makedirs(out_dir, exist_ok=True)
    rows, info = build_identities(seed, mentions, matches, clusters, census)
    write_csv(os.path.join(out_dir, "UNNUMBERED.csv"), rows, OUT_FIELDS)
    est = estimate(rows, exclude_seeds=info["lord_rows_in_numbered_clusters"])
    main = est["1789-1899"]
    sens = {}
    for k in (1, 3):
        r2, _ = build_identities(seed, mentions, matches, clusters, census, min_shared=k)
        sens[f"min_shared_tokens_{k}"] = {"identities": len(r2), "estimate_1789_1899": estimate(r2, exclude_seeds=info["lord_rows_in_numbered_clusters"])["1789-1899"]}
    seed_by = collections.Counter(s["date_certainty"] for s in seed)
    day_pool_obs = main["observed_union"] if main else 0
    outside = len(rows) - day_pool_obs
    lo = round(outside + main["ci95"][0]) if main else None
    hi = round(outside + main["ci95"][1]) if main else None
    both = [r for r in rows if r["lord_seed_ids"] and r["cluster_ids"]]
    lord_clusters = {c["cluster_id"] for c in clusters if "LORD" in c["sources"].split("|")}
    only = [r for r in rows if not r["lord_seed_ids"] and not r["census_id_if_any"]]
    # A cluster the completeness job joined to a Lord row, but whose pair failed the stricter rule, is an
    # unresolved candidate, not a clean non-Lord order: keep it out of the discovery targets.
    residue = [r for r in only if not lord_clusters.intersection(r["cluster_ids"].split("|"))]
    summary = {
        "class": "catalogued_unnumbered",
        "owner_ruling": "R10",
        "leads_only": "Counts of catalogued identities and a population estimate. Nothing here admits an order, authenticates an identity, "
                      "assigns a status, or changes a numbered-series count.",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "unnumbered_series_observed": len(rows),
        "unnumbered_series_observed_note": "Lower-bound census: identities found by Lord 1943 (all years, 1789-1941) or by the completeness "
                                           "cluster list (1789-1899), after deduplication by the rule below.",
        "unnumbered_series_estimate_95": [lo, hi],
        "estimate_sensitivity_note": "The estimate depends strongly on the matching threshold (see capture_recapture.sensitivity_to_matching_threshold); "
                                     "the interval covers sampling error at the chosen threshold only.",
        "unnumbered_series_estimate_95_note": "Chapman interval for the day-precise 1789-1899 pool, plus every other observed identity taken "
                                              "as observed only (month- or year-precise dates, and Lord rows 1900-1941): a floor, since no unseen "
                                              "count is estimated for those.",
        "lord_rows": len(seed),
        "lord_rows_by_date_certainty": dict(seed_by),
        "lord_rows_with_completeness_cluster": sum(1 for s in seed if s["cluster_id"]),
        "identities_with_lord_row": sum(1 for r in rows if r["lord_seed_ids"]),
        "identities_in_both_lord_and_cluster": len(both),
        "identities_from_cluster_lists_only": len(only),
        "non_lord_residue_targets": len(residue),
        "cluster_only_identities_whose_cluster_holds_a_rejected_lord_candidate": len(only) - len(residue),
        "lord_rows_merged_into_other_lord_identity": len(seed) - sum(1 for r in rows if r["lord_seed_ids"]),
        "identities_with_census_id": sum(1 for r in rows if r["census_id_if_any"]),
        "lord_rows_in_numbered_clusters": info["lord_rows_in_numbered_clusters"],
        "dedup_rule": {"exact_day_precise_date": True, "min_shared_distinctive_tokens": MIN_SHARED_TOKENS,
                       "never_on_date_alone": True, "merged_lord_mention_pairs": info["merged_lord_mention_pairs"],
                       "text": "A Lord row and a cluster mention are one identity when both dates are day-precise and equal and the subjects share "
                               "at least two distinctive words (5+ letters, not on census-completeness's stop list). See unnumbered.py."},
        "capture_recapture": {
            "years_covered_by_both_lists": "1789-1899 (the cluster list reads no source after 1899; Lord runs to 1941, so Lord rows 1900-1941 are outside the overlap)",
            "list_1": "identities with at least one Lord 1943 row, day-precise date",
            "list_2": "identities with at least one mention from another project source (Richardson, GPO 1912, MR and GLO books), day-precise date",
            "estimator": "Chapman N=(n1+1)(n2+1)/(m+1)-1; Seber variance (n1+1)(n2+1)(n1-m)(n2-m)/((m+1)^2(m+2)); "
                         "95% interval S+f0/C..S+f0*C, S=n1+n2-m, f0=N-S, C=exp(1.96*sqrt(ln(1+var/f0^2)))",
            "estimate": est,
            "sensitivity_to_matching_threshold": sens,
            "assumptions": ASSUMPTIONS,
            "direction_of_bias": "Dependence between Lord and the printed sources and unequal catchability both under-state the total; "
                                 "OCR failures to match over-state it. Read the interval as a floor on uncertainty.",
        },
        "inputs": {"seed": {"path": "jobs/domesday-register/" + SEED_REL, "sha256": sha256(seed_path)},
                   **{n: {"path": f"{COMPLETENESS}/{n}", "sha256": sha256(os.path.join(cdir, n))}
                      for n in ("MENTIONS.csv", "MATCHES.csv", "CLUSTERS.csv")}},
    }
    with open(os.path.join(out_dir, "UNNUMBERED_SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")
    write_targets(os.path.join(out_dir, "TARGETS_NON_LORD_RESIDUE.txt"), residue)
    return summary


TARGET_HEADER = """# Estimated non-Lord residue of the catalogued_unnumbered series (owner ruling R10).
# Each line is one identity seen only in the project's other lists (Richardson, GPO 1912, MR and GLO books) --
# a completeness-cluster identity with no Lord 1943 row and no EO:UN census id. These are the orders Lord did not
# list, found by other sources; the capture-recapture estimate says more such orders exist unseen.
# Id form: CUN:M:<census-completeness mention id> (see jobs/census-completeness/output/MENTIONS.csv and
# jobs/domesday-register/output/UNNUMBERED.csv for its date, subject and cluster). Identities whose cluster holds a
# Lord row that failed the exact-date-and-two-words rule are left out: they may be Lord's.
# Written by jobs/domesday-register (unnumbered.py) from {n} identities; refresh, do not edit by hand.
# Discovery only: nothing here admits an order or changes a count.
"""


def write_targets(path, residue):
    ids = sorted(r["unnumbered_id"] for r in residue)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(TARGET_HEADER.format(n=len(ids)))
        fh.write("\n".join(ids) + ("\n" if ids else ""))


def rebuild_seed(root):
    """Regenerate data/UNNUMBERED_SEED.csv from Lord's list and the completeness clusters (run by a person, then commit)."""
    wpa = read_csv(os.path.join(root, WPA_UNNUMBERED))
    clusters = read_csv(os.path.join(root, COMPLETENESS, "CLUSTERS.csv"))
    rows = build_seed(wpa, clusters)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), SEED_REL)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_csv(path, rows, SEED_FIELDS)
    return len(rows)


if __name__ == "__main__":
    import sys
    r = os.environ.get("REPO_ROOT") or "."
    if sys.argv[1:] == ["--rebuild-seed"]:
        print(rebuild_seed(r), "seed rows written")
