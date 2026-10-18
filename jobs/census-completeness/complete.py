"""Census completeness: how many early executive orders have the project's lists not found?

Exhaustion cannot be proved. What can be measured is how well independent enumerations of the same
population overlap. This job treats every list the project holds that names pre-1900 executive orders
as a "capture" of the population of such orders, matches the mentions across lists conservatively, and
from the overlap estimates how many orders none of the lists has seen:

  Lord 1943 unnumbered list        the census backbone; cites the printed sources below, so it is NOT
                                   independent of them (positive dependence: estimates are lower bounds)
  WPA numbered list (1862-1899)    the numbered series; by design disjoint from Lord
  Richardson vols VI, VII, IX      "Executive Orders" sections split into documents by richardson-volumes
  Indian reservations (GPO 1912)   309 acts split by indian-reservations-1912
  MR_* and GLO_* books             "Executive order dated ..." mentions read from the pages that
                                   early-orders-hunt fetched (War Department reservation books, General
                                   Land Office reports)

Two kinds of match are kept apart: a *citation link* (the earlier job found Lord's page citation for the
document) and a *blind* match (same day-precise date and at least one shared distinctive word; a date
alone never matches). Estimates are reported on both so the reader can see what the links add.

Estimators: Lord's coverage of each other list (with a Wilson interval), the Chapman form of the
Lincoln-Petersen two-list estimate, and Chao1 over all lists from the counts of orders seen once and
twice. Every estimate is population-level and comes with its assumptions stated in the output. Nothing
here admits an order to the census, assigns a date, or changes any count.
"""
from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import json
import math
import os
import pathlib
import re
import time
from datetime import datetime, timezone

STRATA = [("1789-1800", 1789, 1800), ("1801-1861", 1801, 1861), ("1862-1899", 1862, 1899)]
YEAR_MAX = 1899
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
MONTH_NO = {m: i for i, m in enumerate(MONTHS, 1)}
MONTH_NO.update({"jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12})
STOP = set("""the of and to in for a an by at on from with under as that this which be is are was were or its their his
her any all such said same other certain described lands land acres acre part parts section sections township range
county counties state states territory united ordered order orders executive president established reserved reservation
reserve military purposes purpose made act approved stat dated date secretary department war navy interior treasury within
near about between according addressed general national cemetery park fort camp station island river creek point bay lake
mountain valley title acquisition jurisdiction following therein thereof hereby whereas direction command proclamation
congress public domain survey surveyor office commissioner indian agency reservations reserves tract tracts quarter
north south east west northeast northwest southeast southwest meridian boundary boundaries line lines beginning thence
containing situated located""".split())
EO_DATED = re.compile(r"(?i)executive\s+order[s]?\s*(?:of\s+the\s+President\s*)?(?:,?\s*dated|\s+of|,)\s*"
                      r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(\d{1,2})\s*,?\s*(1[789]\d\d))")
HEADING = re.compile(r"^[A-Z][A-Z0-9 .,'\-()&]{4,}\.?$")


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tokens(text: str) -> set:
    out = set()
    for w in re.findall(r"[A-Za-z][A-Za-z'\-]{4,}", text or ""):
        lw = w.lower().strip("'-")
        if len(lw) >= 5 and lw not in STOP:
            out.add(lw)
    return out


def iso_from_parts(year, month_text, day_text):
    y = int(year)
    m = MONTH_NO.get((month_text or "").lower().rstrip(".")[:4]) or MONTH_NO.get((month_text or "").lower().rstrip(".")[:3])
    if not m:
        return f"{y:04d}", "year"
    if day_text and str(day_text).isdigit() and 1 <= int(day_text) <= 31:
        return f"{y:04d}-{m:02d}-{int(day_text):02d}", "day"
    return f"{y:04d}-{m:02d}", "month"


def parse_month_day(year, text):
    """'Aug 28' or 'Sept. 7' with a year -> iso date and precision."""
    s = (text or "").strip().replace(".", " ")
    m = re.match(r"^([A-Za-z]{3,9})\s*(\d{1,2})?(?!\d)", s)
    if not m:
        return f"{int(year):04d}", "year"
    return iso_from_parts(year, m.group(1), m.group(2))


def stratum_of(year):
    for name, lo, hi in STRATA:
        if lo <= year <= hi:
            return name
    return None


# ----------------------------------------------------------------------------- mentions

def mention(source, mid, date, precision, label, ref, link_lord=(), link_wpa=(), **extra):
    year = int(date[:4])
    return {"source": source, "mention_id": mid, "date": date, "precision": precision, "year": year, "stratum": stratum_of(year),
            "label": re.sub(r"\s+", " ", label or "").strip()[:200], "tokens": tokens(label), "ref": ref,
            "link_lord": set(int(x) for x in link_lord if str(x).isdigit()), "link_wpa": set(link_wpa), **extra}


def load_lord(repo, job_dir):
    live = repo / "jobs/wpa-lists/output/UNNUMBERED_ENTRIES.csv"
    vendored = repo / "jobs/early-orders-hunt/data/lord_subset/UNNUMBERED_ENTRIES_pre1900.csv"
    path = live if live.is_file() else vendored
    out = []
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if not r["year"].isdigit() or int(r["year"]) > YEAR_MAX:
                continue
            date, prec = parse_month_day(r["year"], r.get("date"))
            out.append(mention("LORD", f"LORD:U:{int(r['seq']):04d}", date, prec, r.get("summary", ""), f"Lord p. {r.get('page', '')}", seq=int(r["seq"])))
    return out, {"path": str(path.relative_to(repo)), "sha256": sha256_file(path), "mentions": len(out),
                 "note": "Lord cites the GLO, MR, Indian-reservation and Richardson volumes as his printed sources; his list is not independent of them."}


def load_wpa(repo, job_dir):
    live = repo / "jobs/wpa-lists/output/NUMBERED_ENTRIES.csv"
    vendored = job_dir / "data/WPA_NUMBERED_pre1900.csv"
    path = live if live.is_file() else vendored
    out = []
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if not r["year"].isdigit() or int(r["year"]) > YEAR_MAX:
                continue
            date, prec = parse_month_day(r["year"], r.get("month_day"))
            out.append(mention("WPA", r["id"], date, prec, r.get("text", ""), f"WPA numbered list p. {r.get('page', '')}"))
    return out, {"path": str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path), "sha256": sha256_file(path), "mentions": len(out),
                 "note": "The numbered series; Lord's list excludes numbered orders by design, so the two are complementary, not two captures of one population."}


def load_richardson(repo):
    out, files = [], []
    for path in sorted((repo / "jobs/richardson-volumes/output").glob("RICH_*_ORDERS.csv")):
        files.append({"path": str(path.relative_to(repo)), "sha256": sha256_file(path)})
        with path.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("is_order") != "yes" or not r["date"][:4].isdigit() or int(r["date"][:4]) > YEAR_MAX:
                    continue
                prec = "day" if len(r["date"]) == 10 else ("month" if len(r["date"]) == 7 else "year")
                lord = re.findall(r"Lord:(\d+)", r.get("lord_entries", ""))
                wpa = re.findall(r"EO:\d+[A-Za-z\-]*", r.get("wpa_ids", ""))
                out.append(mention(r["volume"], r["doc_id"], r["date"], prec, (r.get("title") or "") + " " + (r.get("first_line") or ""),
                                   f"{r['volume']} printed pp. {r.get('printed_pages', '')}", lord, wpa, signer=r.get("signer", ""), form=r.get("form", "")))
    return out, {"files": files, "mentions": len(out), "note": "Documents in the volumes' EXECUTIVE ORDERS sections; includes orders signed by the President, orders issued by his direction, and departmental orders printed there."}


def load_ir1912(repo):
    path = repo / "jobs/indian-reservations-1912/output/IR1912_ACTS.csv"
    out = []
    if not path.is_file():
        return out, {"path": str(path), "present": False}
    with path.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("kind") != "order" or not r["date"][:4].isdigit() or int(r["date"][:4]) > YEAR_MAX:
                continue
            if r.get("order_lead_id") and r["order_lead_id"] != r["lead_id"]:
                continue  # a reprint of an order already counted
            prec = "day" if len(r["date"]) == 10 else ("month" if len(r["date"]) == 7 else "year")
            lord = re.findall(r"\d+", r.get("lord_seqs", ""))
            wpa = [f"EO:{n}" for n in re.findall(r"\d+", r.get("numbered_eo", ""))]
            out.append(mention("IR1912", r["lead_id"], r["date"], prec, (r.get("reservation") or "") + " " + (r.get("state") or ""),
                               f"IR 1912 printed pp. {r.get('act_printed_pages', '')}", lord, wpa, signer=r.get("signer", "")))
    return out, {"path": str(path.relative_to(repo)), "sha256": sha256_file(path), "mentions": len(out),
                 "note": "Orders (not indorsements or proclamations) printed in Executive Orders Relating to Indian Reservations (GPO 1912); reprints folded into one order."}


def book_mentions(key, pages):
    """'Executive order dated June 21, 1838' mentions in a reservation or land-office book, each labelled with
    the nearest heading above it; repeated mentions of one date under one heading are one mention."""
    seen, out = {}, []
    for p in pages:
        lines = p["text"].split("\n")
        heading = ""
        for i, line in enumerate(lines):
            if HEADING.match(line.strip()) and len(line.split()) <= 9:
                heading = line.strip()
            for m in EO_DATED.finditer(line + " " + (lines[i + 1] if i + 1 < len(lines) else "")):
                mon = re.match(r"[A-Za-z]+", m.group(1)).group(0)
                date, prec = iso_from_parts(m.group(3), mon, m.group(2))
                if int(date[:4]) > YEAR_MAX or prec != "day":
                    continue
                # Land-office schedule rows run over several OCR lines; the reservation's name sits above the date.
                context = " ".join(lines[max(0, i - 4):i + 2])
                k = (date, heading)
                if k in seen:
                    continue
                seen[k] = True
                out.append(mention(key, f"{key}:p{p.get('printed') or p['image']}:{len(out) + 1}", date, prec, heading + " " + context,
                                   f"{key} printed p. {p.get('printed')} (image {p['image']})"))
    return out


def load_books(repo, books_dir):
    out, files = [], []
    for path in sorted(pathlib.Path(books_dir).glob("*_pages.jsonl.gz")):
        key = path.name.replace("_pages.jsonl.gz", "")
        if not (key.startswith("MR_") or key.startswith("GLO_")):
            continue
        with gzip.open(path, "rt", encoding="utf-8") as gz:
            pages = [json.loads(l) for l in gz]
        ms = book_mentions(key, pages)
        out.extend(ms)
        files.append({"book": key, "path": str(path), "sha256": sha256_file(path), "pages": len(pages), "mentions": len(ms)})
    return out, {"books": files, "mentions": len(out), "note": "Dated 'Executive order' mentions read from page text fetched by early-orders-hunt; one mention per date and heading."}


# ----------------------------------------------------------------------------- matching

class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def match_mentions(mentions: list) -> tuple:
    """Matches across sources. Blind: same day-precise date and >= 1 shared distinctive token, or (for a
    year-only Lord entry) same year and >= 2 shared tokens. Citation link: the earlier job recorded Lord's
    or the WPA list's page citation for the document. Same-date pairs with no shared token are written out
    as ambiguous and never matched."""
    by_id = {m["mention_id"]: m for m in mentions}
    lord_by_seq = {m["seq"]: m for m in mentions if m["source"] == "LORD"}
    wpa_by_id = {m["mention_id"]: m for m in mentions if m["source"] == "WPA"}
    by_date = collections.defaultdict(list)
    lord_year_only = collections.defaultdict(list)
    for m in mentions:
        if m["precision"] == "day":
            by_date[m["date"]].append(m)
        elif m["source"] == "LORD":
            lord_year_only[m["year"]].append(m)
    matches, ambiguous = [], []
    seen = set()
    for date, group in by_date.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a["source"] == b["source"]:
                    continue
                shared = a["tokens"] & b["tokens"]
                pair = (a["mention_id"], b["mention_id"])
                row = {"a": a["mention_id"], "b": b["mention_id"], "source_a": a["source"], "source_b": b["source"], "date": date,
                       "shared_tokens": "|".join(sorted(shared)), "label_a": a["label"][:120], "label_b": b["label"][:120]}
                if shared:
                    matches.append({**row, "kind": "blind_date_and_token"})
                    seen.add(pair)
                else:
                    ambiguous.append({**row, "why": "same date, no shared distinctive word"})
    for m in mentions:
        if m["source"] == "LORD" or m["precision"] != "day":
            continue
        for lm in lord_year_only.get(m["year"], []):
            shared = m["tokens"] & lm["tokens"]
            if len(shared) >= 2:
                matches.append({"a": lm["mention_id"], "b": m["mention_id"], "source_a": "LORD", "source_b": m["source"], "date": m["date"],
                                "shared_tokens": "|".join(sorted(shared)), "label_a": lm["label"][:120], "label_b": m["label"][:120], "kind": "blind_year_and_two_tokens"})
    for m in mentions:
        for seq in m.get("link_lord", ()):
            lm = lord_by_seq.get(seq)
            if lm:
                matches.append({"a": lm["mention_id"], "b": m["mention_id"], "source_a": "LORD", "source_b": m["source"], "date": m["date"],
                                "shared_tokens": "|".join(sorted(m["tokens"] & lm["tokens"])), "label_a": lm["label"][:120], "label_b": m["label"][:120], "kind": "citation_link"})
        for wid in m.get("link_wpa", ()):
            wm = wpa_by_id.get(wid)
            if wm:
                matches.append({"a": wm["mention_id"], "b": m["mention_id"], "source_a": "WPA", "source_b": m["source"], "date": m["date"],
                                "shared_tokens": "|".join(sorted(m["tokens"] & wm["tokens"])), "label_a": wm["label"][:120], "label_b": m["label"][:120], "kind": "citation_link"})
    return matches, ambiguous


def clusters(mentions, matches, use_kinds) -> list:
    uf = UnionFind()
    for m in mentions:
        uf.find(m["mention_id"])
    for mt in matches:
        if mt["kind"] in use_kinds:
            uf.union(mt["a"], mt["b"])
    groups = collections.defaultdict(list)
    for m in mentions:
        groups[uf.find(m["mention_id"])].append(m)
    out = []
    for root, ms in groups.items():
        sources = sorted(set(m["source"] for m in ms))
        dated = [m for m in ms if m["precision"] == "day"] or ms
        year = min(m["year"] for m in dated)
        numbered = any(m["source"] == "WPA" or m.get("link_wpa") for m in ms)
        out.append({"cluster_id": root, "sources": sources, "n_sources": len(sources), "year": year, "stratum": stratum_of(year), "numbered": numbered,
                    "date": min(m["date"] for m in dated), "label": max(ms, key=lambda m: len(m["label"]))["label"], "members": [m["mention_id"] for m in ms]})
    return out


# ----------------------------------------------------------------------------- estimators

def wilson(k, n, z=1.96):
    if n == 0:
        return None, None, None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return round(p, 4), round(max(0, centre - half), 4), round(min(1, centre + half), 4)


def chapman(n1, n2, m):
    """Chapman's form of the Lincoln-Petersen estimate and a 95% interval; assumes two independent captures
    of a closed population with equal catchability within list."""
    if n1 == 0 or n2 == 0:
        return None
    N = (n1 + 1) * (n2 + 1) / (m + 1) - 1
    var = (n1 + 1) * (n2 + 1) * (n1 - m) * (n2 - m) / ((m + 1) ** 2 * (m + 2))
    se = math.sqrt(max(var, 0))
    return {"N_hat": round(N, 1), "se": round(se, 1), "ci95": [round(max(N - 1.96 * se, max(n1, n2)), 1), round(N + 1.96 * se, 1)],
            "n1": n1, "n2": n2, "m": m}


def chao1(freq: dict, s_obs: int):
    """Chao1 lower-bound estimate from the numbers of orders seen in exactly one (f1) and exactly two (f2)
    lists, with the log-normal 95% interval (Chao 1987)."""
    f1, f2 = freq.get(1, 0), freq.get(2, 0)
    if f2 > 0:
        N = s_obs + f1 * f1 / (2 * f2)
        r = f1 / f2
        var = f2 * (r ** 4 / 4 + r ** 3 + r ** 2 / 2)
    else:
        N = s_obs + f1 * (f1 - 1) / 2
        var = f1 * (f1 - 1) / 2 + f1 * (2 * f1 - 1) ** 2 / 4 - (f1 ** 4) / (4 * N) if N > 0 else 0
    hidden = N - s_obs
    if hidden > 0 and var > 0:
        C = math.exp(1.96 * math.sqrt(math.log(1 + var / hidden ** 2)))
        ci = [round(s_obs + hidden / C, 1), round(s_obs + hidden * C, 1)]
    else:
        ci = [s_obs, round(N, 1)]
    return {"S_obs": s_obs, "f1": f1, "f2": f2, "N_hat": round(N, 1), "undiscovered_hat": round(hidden, 1), "ci95": ci}


def mt_mle(list_sizes: list, s_obs: int):
    """Maximum-likelihood population size under model Mt (lists differ in catchability, every order equally
    catchable within a list, lists independent): N solves prod(1 - n_j/N) = 1 - S/N (Darroch 1958), by bisection."""
    ns = [n for n in list_sizes if n > 0]
    if s_obs == 0 or len(ns) < 2:
        return None
    if all(n == s_obs for n in ns):
        return float(s_obs)
    if s_obs == max(ns):
        return None

    def g(N):
        return math.prod(1 - n / N for n in ns) - (1 - s_obs / N)

    lo, hi = float(s_obs), float(s_obs) * 50 + 100
    if g(lo + 1e-9) * g(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if g(lo + 1e-9) * g(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2, 1)


def mt_ci(N: float, list_sizes: list, s_obs: int):
    """Asymptotic 95% interval for the Mt estimate (Darroch 1958; Seber 1982):
    var(N) = N / (1/prod(q_j) + (k-1) - sum(1/q_j)), q_j = 1 - n_j/N."""
    ns = [n for n in list_sizes if n > 0]
    if N is None or N <= 0:
        return None
    q = [1 - n / N for n in ns]
    if any(x <= 0 for x in q):
        return None
    den = 1 / math.prod(q) + (len(ns) - 1) - sum(1 / x for x in q)
    if den <= 0:
        return None
    se = math.sqrt(N / den)
    return [round(max(s_obs, N - 1.96 * se), 1), round(N + 1.96 * se, 1)]


def estimate(cl: list, sources: list) -> dict:
    """Estimates per era over the clusters that are not numbered orders (the WPA numbered series is a
    different, already-censused population, and Lord's list excludes it by design)."""
    cap_sources = [s for s in sources if s != "WPA"]
    out = {}
    for name, lo, hi in STRATA + [("1789-1899", 1789, 1899)]:
        in_era = [c for c in cl if lo <= c["year"] <= hi]
        cs = [c for c in in_era if not c.get("numbered")]
        freq = collections.Counter(c["n_sources"] for c in cs)
        per_source = {s: sum(1 for c in cs if s in c["sources"]) for s in cap_sources}
        sizes = list(per_source.values())
        mt = mt_mle(sizes, len(cs)) if cs else None
        ci = mt_ci(mt, sizes, len(cs)) if mt is not None else None
        pairs = {}
        for s in cap_sources:
            if s == "LORD" or per_source[s] == 0:
                continue
            m = sum(1 for c in cs if "LORD" in c["sources"] and s in c["sources"])
            cov = wilson(m, per_source[s])
            pairs[s] = {"in_list": per_source[s], "also_in_lord": m, "lord_coverage": cov[0], "coverage_ci95": [cov[1], cov[2]],
                        "chapman_vs_lord": chapman(per_source["LORD"], per_source[s], m)}
        out[name] = {"clusters_observed": len(cs), "numbered_orders_excluded": len(in_era) - len(cs),
                     "by_number_of_lists": dict(sorted(freq.items())), "per_source": per_source,
                     "lord_vs_each_list": pairs,
                     "mt_all_lists": {"N_hat": mt, "undiscovered_hat": round(mt - len(cs), 1) if mt is not None else None, "ci95": ci,
                                      "model": "Mt: lists differ in catchability, orders equally catchable within a list, lists independent (Darroch MLE, asymptotic interval)"} if cs else None,
                     "chao1_all_lists": chao1(freq, len(cs)) if cs else None}
    return out


# ----------------------------------------------------------------------------- run

def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("|".join(str(x) for x in v) if isinstance(v, (list, set, tuple)) else v) for k, v in r.items()})


def coverage_by_series(job_dir, per_source_all: dict, books_loaded: set) -> list:
    rows = []
    with (job_dir / "data/SOURCE_UNIVERSE.csv").open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            key = r.get("series_key", "")
            n = per_source_all.get(key)
            if key in books_loaded or n is not None:
                r["mentions_read_this_run"] = n if n is not None else 0
            else:
                r["mentions_read_this_run"] = ""
            rows.append(r)
    return rows


def run(repo_root, job_dir, output_dir, books_dir=None) -> dict:
    t0 = time.time()
    repo, job_dir, out = pathlib.Path(repo_root).resolve(), pathlib.Path(job_dir), pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    books_dir = pathlib.Path(books_dir or os.environ.get("COMPLETENESS_BOOKS_DIR") or (repo / "jobs/early-orders-hunt/output/books"))
    lord, lord_src = load_lord(repo, job_dir)
    wpa, wpa_src = load_wpa(repo, job_dir)
    rich, rich_src = load_richardson(repo)
    ir, ir_src = load_ir1912(repo)
    books, books_src = load_books(repo, books_dir) if books_dir.is_dir() else ([], {"books": [], "mentions": 0, "note": f"no books at {books_dir}"})
    mentions = lord + wpa + rich + ir + books
    sources = sorted(set(m["source"] for m in mentions), key=lambda s: (s != "LORD", s))
    counts = collections.Counter(m["source"] for m in mentions)
    print(f"Mentions: {len(mentions)} from {len(sources)} lists ({', '.join(f'{s} {counts[s]}' for s in sources)}).")
    matches, ambiguous = match_mentions(mentions)
    kinds = collections.Counter(m["kind"] for m in matches)
    print(f"Matches: {len(matches)} ({dict(kinds)}); ambiguous same-date pairs: {len(ambiguous)}.")
    all_kinds = set(kinds)
    cl_all = clusters(mentions, matches, all_kinds)
    cl_blind = clusters(mentions, matches, {"blind_date_and_token", "blind_year_and_two_tokens"})
    # Upper bracket on matching: treat every same-date pair as the same order. Unmatched is not missing.
    loose = matches + [{**a, "kind": "same_date_only"} for a in ambiguous]
    cl_loose = clusters(mentions, loose, all_kinds | {"same_date_only"})
    est_all = estimate(cl_all, sources)
    est_blind = estimate(cl_blind, sources)
    est_loose = estimate(cl_loose, sources)

    # Richardson documents by signer: did Lord list them?
    rich_cov = {}
    for m in rich:
        key = (m["source"], m.get("signer", ""))
        d = rich_cov.setdefault(key, {"volume": m["source"], "signer": m.get("signer", ""), "documents": 0, "cited_by_lord": 0, "cited_by_wpa": 0})
        d["documents"] += 1
        d["cited_by_lord"] += bool(m["link_lord"])
        d["cited_by_wpa"] += bool(m["link_wpa"])
    rich_rows = sorted(rich_cov.values(), key=lambda d: (d["volume"], d["signer"]))
    for d in rich_rows:
        cov = wilson(d["cited_by_lord"], d["documents"])
        d["lord_coverage"], d["coverage_ci_low"], d["coverage_ci_high"] = cov

    # ------------------------------------------------------------------ outputs
    write_csv(out / "MENTIONS.csv", [{**m, "tokens": sorted(m["tokens"]), "link_lord": sorted(m["link_lord"]), "link_wpa": sorted(m["link_wpa"])} for m in mentions],
              ["source", "mention_id", "date", "precision", "year", "stratum", "label", "ref", "link_lord", "link_wpa", "signer", "form", "tokens"])
    write_csv(out / "MATCHES.csv", matches, ["kind", "source_a", "a", "source_b", "b", "date", "shared_tokens", "label_a", "label_b"])
    write_csv(out / "AMBIGUOUS_MATCHES.csv", ambiguous, ["source_a", "a", "source_b", "b", "date", "label_a", "label_b", "why"])
    write_csv(out / "CLUSTERS.csv", [{**c, "members": c["members"], "sources": c["sources"]} for c in sorted(cl_all, key=lambda c: (c["date"], c["cluster_id"]))],
              ["cluster_id", "date", "year", "stratum", "n_sources", "sources", "label", "members"])
    matrix = []
    for s1 in sources:
        row = {"list": s1}
        for s2 in sources:
            row[s2] = sum(1 for c in cl_all if s1 in c["sources"] and s2 in c["sources"])
        matrix.append(row)
    write_csv(out / "OVERLAP_MATRIX.csv", matrix, ["list"] + sources)
    write_csv(out / "RICHARDSON_COVERAGE_BY_SIGNER.csv", rich_rows, ["volume", "signer", "documents", "cited_by_lord", "cited_by_wpa", "lord_coverage", "coverage_ci_low", "coverage_ci_high"])
    per_source_all = {s: sum(1 for m in mentions if m["source"] == s) for s in sources}
    cov_rows = coverage_by_series(job_dir, per_source_all, set(b["book"] for b in books_src.get("books", [])))
    write_csv(out / "COVERAGE_BY_SERIES.csv", cov_rows, list(cov_rows[0].keys()) if cov_rows else ["series_key"])

    assumptions = [
        "Closed population: the set of executive orders issued 1789-1899 is fixed; true, but its definition (codebook 2.0.0) decides what counts, and the printed lists apply their own definitions.",
        "Independence: Lincoln-Petersen and Chao1 assume lists catch orders independently. Lord cites the GLO, MR, Indian-reservation and Richardson volumes as his sources, so his list is positively dependent on them. Positive dependence makes these estimators UNDER-estimate the undiscovered remainder: read every N_hat as a lower bound.",
        "Equal catchability: an order printed in a land-office schedule is far easier to catch than an unprinted letter to a Secretary. Orders that reached no printed compilation are nearly invisible to every list here, and no overlap statistic can count them. That remainder is what the archival audit in the source universe map is for.",
        "Which estimator: the Mt maximum-likelihood estimate (Darroch) is the headline, because the lists plainly differ in catchability (Lord catches most, a single land-office report catches a tenth). Chao1 assumes catchability varies across orders, not across lists; when lists differ it over-states the remainder, so it is reported as a check only. Chapman two-list estimates against Lord are given per list.",
        "Matching: a blind match needs the same day-precise date and a shared distinctive word; year-only Lord entries need two shared words. Under-matching inflates N_hat, over-matching deflates it; AMBIGUOUS_MATCHES.csv lists the same-date pairs that were not matched so the reader can judge.",
        "The WPA numbered list and Lord's unnumbered list partition the known orders by design and are not two captures of one population. Clusters that contain a WPA entry or a document the earlier jobs linked to a numbered order are excluded from the estimates (they are numbered orders, already in the census); their count is reported.",
        "Unmatched is not missing: an order the books name that the matcher did not link to Lord may be in Lord under other words or an unpaired date. The 'same-date pairs counted as matches' column is the upper bracket on matching (and the lower bracket on the remainder); the truth lies between it and the strict column, and AMBIGUOUS_MATCHES.csv is the list a reviewer would settle to narrow it.",
    ]
    summary = {
        "leads_only": "Population-level estimates. Nothing here admits an order to the census, assigns a date to one, merges identities or changes any count or status.",
        "run_utc": now_utc(), "seconds": round(time.time() - t0, 1),
        "inputs": {"lord": lord_src, "wpa_numbered": wpa_src, "richardson": rich_src, "indian_reservations_1912": ir_src, "books": books_src},
        "mentions": per_source_all, "matches": dict(kinds), "ambiguous_same_date_pairs": len(ambiguous),
        "estimates_all_matches": est_all, "estimates_blind_matches_only": est_blind, "estimates_same_date_pairs_as_matches": est_loose,
        "richardson_coverage_by_signer": rich_rows, "assumptions": assumptions,
    }
    (out / "ESTIMATES.json").write_text(json.dumps({"estimates_all_matches": est_all, "estimates_blind_matches_only": est_blind,
                                                     "estimates_same_date_pairs_as_matches": est_loose, "assumptions": assumptions}, indent=1), encoding="utf-8")
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "REPORT.md").write_text(report_md(summary, cov_rows), encoding="utf-8")
    return summary


def report_md(s: dict, cov_rows: list) -> str:
    E = s["estimates_all_matches"]
    B = s["estimates_blind_matches_only"]
    U = s["estimates_same_date_pairs_as_matches"]
    L = ["# How complete is the early executive-order census?", "",
         f"Run {s['run_utc']} ({s['seconds']} s). {sum(s['mentions'].values())} dated mentions from {len(s['mentions'])} lists; "
         f"{sum(s['matches'].values())} cross-list matches ({', '.join(f'{k} {v}' for k, v in s['matches'].items())}); {s['ambiguous_same_date_pairs']} same-date pairs left unmatched.", "",
         s["leads_only"], "", "## The claim this run supports", ""]
    tot = E.get("1789-1899", {})
    mt = tot.get("mt_all_lists") or {}
    ci = mt.get("ci95") or ["?", "?"]
    um = (U.get("1789-1899", {}).get("mt_all_lists") or {})
    L += [f"Under codebook 2.0.0's working definition, across the lists read here (Lord 1943, Richardson VI/VII/IX, the 1912 Indian-reservation compilation and the reservation "
          f"and land-office books fetched so far), **{tot.get('clusters_observed', 0)} distinct unnumbered executive orders dated 1789-1899 were observed** "
          f"({tot.get('numbered_orders_excluded', 0)} further clusters are numbered orders already in the census and are set aside). "
          f"The Mt estimate puts the number these lists have collectively missed, *among orders of the kind these lists catch*, between about **{um.get('undiscovered_hat', '?')}** "
          f"(if every same-date pair is the same order) and **{mt.get('undiscovered_hat', '?')}** (strict matching; 95% interval {ci[0]} to {ci[1]} total). "
          f"Because Lord drew on these same books, both are lower bounds on what the printed record holds. "
          f"Orders that never reached a printed compilation are outside what any overlap can count; see the source universe map for the archival series where they would be.", ""]
    L += ["## Lord's coverage of each other list, by era", "", "| Era | List | In list | Also in Lord | Lord coverage (95% CI) | Chapman N (95% CI) |", "|---|---|---:|---:|---|---|"]
    for era in ("1789-1800", "1801-1861", "1862-1899"):
        e = E.get(era, {})
        for src, p in sorted((e.get("lord_vs_each_list") or {}).items()):
            c = p["chapman_vs_lord"] or {}
            L.append(f"| {era} | {src} | {p['in_list']} | {p['also_in_lord']} | {p['lord_coverage']} ({p['coverage_ci95'][0]}–{p['coverage_ci95'][1]}) | "
                     f"{c.get('N_hat', '-')} ({c.get('ci95', ['-', '-'])[0]}–{c.get('ci95', ['-', '-'])[1]}) |")
    L += ["", "## All lists together, by era (unnumbered orders)", "",
          "| Era | Observed | Numbered set aside | Seen in 1 list | Seen in 2 | Mt total (95% CI) | Mt undiscovered, strict | same-date pairs as matches | blind matches only | Chao1 (check) |",
          "|---|---:|---:|---:|---:|---|---:|---:|---:|---:|"]
    for era in ("1789-1800", "1801-1861", "1862-1899", "1789-1899"):
        e, b, u = E.get(era, {}), B.get(era, {}), U.get(era, {})
        c, m, mb, mu = e.get("chao1_all_lists") or {}, e.get("mt_all_lists") or {}, b.get("mt_all_lists") or {}, u.get("mt_all_lists") or {}
        ci = m.get("ci95") or ["-", "-"]
        L.append(f"| {era} | {e.get('clusters_observed', 0)} | {e.get('numbered_orders_excluded', 0)} | {c.get('f1', '-')} | {c.get('f2', '-')} | {m.get('N_hat', '-')} ({ci[0]}–{ci[1]}) | "
                 f"{m.get('undiscovered_hat', '-')} | {mu.get('undiscovered_hat', '-')} | {mb.get('undiscovered_hat', '-')} | {c.get('undiscovered_hat', '-')} |")
    L += ["", "## Richardson's EXECUTIVE ORDERS sections: what Lord listed, by signer", "",
          "Richardson printed these under the heading *Executive Orders*; whether each meets the codebook is a separate judgment. The gap is largest for the Civil War volume.", "",
          "| Volume | Signer | Documents | Cited by Lord | Cited by WPA | Lord coverage (95% CI) |", "|---|---|---:|---:|---:|---|"]
    for d in s["richardson_coverage_by_signer"]:
        L.append(f"| {d['volume']} | {d['signer']} | {d['documents']} | {d['cited_by_lord']} | {d['cited_by_wpa']} | {d['lord_coverage']} ({d['coverage_ci_low']}–{d['coverage_ci_high']}) |")
    L += ["", "## Assumptions and how they bias the numbers", ""] + [f"- {a}" for a in s["assumptions"]]
    L += ["", "## Source universe: where orders could be, and what has been searched", "",
          "| Series | Era | Repository | Status | Mentions read this run |", "|---|---|---|---|---:|"]
    for r in cov_rows:
        L.append(f"| {r.get('series_key')}: {r.get('series')} | {r.get('era_from')}–{r.get('era_to')} | {r.get('repository')} | {r.get('search_status')} | {r.get('mentions_read_this_run')} |")
    L += ["", "The full map, with access routes and next steps per series, is `COVERAGE_BY_SERIES.csv`. A completeness claim is only as good as the "
          "`not_searched` and `planned` rows in it; the random archival audit described in `README.md` is the step that turns those rows into a measured miss rate.", ""]
    return "\n".join(L)


def print_summary(s: dict):
    E = s["estimates_all_matches"].get("1789-1899", {})
    m = E.get("mt_all_lists") or {}
    print(f"Observed distinct unnumbered orders 1789-1899: {E.get('clusters_observed')}; Mt undiscovered, strict matching (lower bound under dependence): {m.get('undiscovered_hat')} (CI {m.get('ci95')}).")
    for era in ("1789-1800", "1801-1861", "1862-1899"):
        e = s["estimates_all_matches"].get(era, {})
        u = s["estimates_same_date_pairs_as_matches"].get(era, {})
        mm, cc, mu = e.get("mt_all_lists") or {}, e.get("chao1_all_lists") or {}, u.get("mt_all_lists") or {}
        print(f"  {era}: observed {e.get('clusters_observed')} (+{e.get('numbered_orders_excluded')} numbered), per list {e.get('per_source')}, "
              f"Mt undiscovered strict {mm.get('undiscovered_hat')} (CI {mm.get('ci95')}), loose {mu.get('undiscovered_hat')}, Chao1 check {cc.get('undiscovered_hat')}")
    print("Population-level estimates; nothing admitted or changed.")
