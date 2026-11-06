"""Shared helpers for the Thrower comparison (read-only; standard library + pandas + numpy)."""
import hashlib
import math
import os
import re

import pandas as pd

WINDOW_LAST_YEAR = 2013   # Thrower's observations end in 2013 (revoke_year max 2013; her do-file expands to 2014)
NUM_MIN, NUM_MAX = 7532, 13655


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iid_from_thrower(eonumber):
    """'7677-A' -> 'EO:7677A' (the project's id form)."""
    return "EO:" + str(eonumber).replace("-", "").strip().upper()


def norm_id(x):
    """Upper-case the suffix so 'EO:7933a' (register) matches 'EO:7933A'."""
    if not isinstance(x, str):
        return x
    x = x.strip()
    return x.upper() if x.upper().startswith("EO:") else x


def base_number(iid):
    m = re.match(r"^EO:(\d+)", iid or "")
    return int(m.group(1)) if m else None


def read_thrower(archive):
    d = pd.read_csv(os.path.join(archive, "eo_original_list.csv"), dtype=str)
    d["instrument_id"] = d["eonumber"].map(iid_from_thrower)
    return d


def read_csv(cache, rel, **kw):
    return pd.read_csv(os.path.join(cache, rel), dtype=str, **kw)


def year_of(s):
    if isinstance(s, str) and re.match(r"^\d{4}", s):
        return int(s[:4])
    return None


PARTIAL_MECH = {"revocation", "rescission"}
SUPERSEDE_MECH = {"supersession", "supersession_or_revocation"}
OTHER_END_MECH = {"termination", "abolition", "authority_repeal", "nullification", "expiration",
                  "ceased_to_function", "repeal", "voiding"}


def classify_edge(mechanism, qualifier):
    """Project edge class: full / partial revocation, whole / partial supersession, other end, other."""
    q = (qualifier or "").strip()
    if mechanism in PARTIAL_MECH:
        return "revoke_part" if q else "revoke_full"
    if mechanism in SUPERSEDE_MECH:
        return "supersede_part" if q else "supersede_full"
    if mechanism in OTHER_END_MECH:
        return "other_end"
    return "other"


def load_edges(cache):
    e = read_csv(cache, "jobs/later-events/output/EDGES.csv")
    e["target"] = e["target_id"].map(norm_id)
    e["acting"] = e["acting_id"].map(norm_id)
    e["qualifier"] = e["qualifier"].fillna("")
    e["klass"] = [classify_edge(m, q) for m, q in zip(e["mechanism"], e["qualifier"])]
    e["event_year"] = e["date_candidate"].map(year_of)
    e["source_group"] = e["evidence_type"].map(
        lambda t: "ofr_note" if str(t).startswith("ofr_note") else ("order_text" if str(t).startswith("order_text") else "other"))
    return e


def load_c89(cache):
    d = read_csv(cache, "jobs/ofr-codification-1989/output/DISPOSITION_1989.csv")
    d["target"] = d["census_id"].map(norm_id)
    return d


# ---------- small statistics without scipy ----------

def _gammainc_lower_reg(a, x):
    if x <= 0:
        return 0.0
    if x < a + 1:
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-14:
                break
        return s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b = x + 1 - a
    c = 1e300
    d = 1 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d
        dl = d * c
        h *= dl
        if abs(dl - 1) < 1e-14:
            break
    return 1 - math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def chi2_sf(x, df):
    return max(0.0, 1.0 - _gammainc_lower_reg(df / 2.0, x / 2.0))


def chi2_test(table):
    """Pearson chi-square on a 2-D table of counts. Returns (stat, df, p)."""
    t = pd.DataFrame(table).astype(float)
    t = t.loc[t.sum(axis=1) > 0, t.sum(axis=0) > 0]
    n = t.values.sum()
    if t.shape[0] < 2 or t.shape[1] < 2:
        return (float("nan"), 0, float("nan"))
    exp = t.sum(axis=1).values[:, None] * t.sum(axis=0).values[None, :] / n
    stat = float(((t.values - exp) ** 2 / exp).sum())
    df = (t.shape[0] - 1) * (t.shape[1] - 1)
    return stat, df, chi2_sf(stat, df)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


# ---------- derived project layers (peano lemmas, status-history events) ----------

def load_peano(cache):
    """Instance lemmas of jobs/peano-formulario as a DataFrame (one row per lemma-object)."""
    import glob
    import gzip
    import json
    rows = []
    for f in sorted(glob.glob(os.path.join(cache, "jobs/peano-formulario/output/lemmas/EO_*.jsonl.gz"))):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                st = r["statement"]
                for obj in st.get("objects") or []:
                    rows.append({"lemma_id": r["lemma_id"], "status": r["status"], "relation": st["relation"],
                                 "actor": st["subject"], "target": norm_id(obj), "date": st.get("date"),
                                 "qualifier": st.get("qualifier", ""), "origin_from": r["origin"].get("from"),
                                 "edge_id": r["origin"].get("edge_id")})
    return pd.DataFrame(rows)


def load_sh_events(cache):
    import glob
    import json
    rows = []
    for f in sorted(glob.glob(os.path.join(cache, "jobs/status-history/output/events/*.jsonl"))):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                ie = r.get("input_edge") or {}
                rows.append({"event_id": r["id"], "edge_id": r["id"][3:] if r["id"].startswith("EV:") else r["id"],
                             "actor": r["actor_id"], "target": norm_id(r["target_id"]), "mechanism": r["mechanism"],
                             "qualifier": r.get("qualifier", ""), "date": r.get("candidate_date"),
                             "input_path": ie.get("path"), "verified_raw_span": r.get("verified_raw_span")})
    return pd.DataFrame(rows)
