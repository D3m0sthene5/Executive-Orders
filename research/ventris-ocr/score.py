"""Scoring for the Ventris OCR pilot.

Inputs
  READINGS.jsonl         one JSON object per (passage, engine); fields passage_id, engine, output_text, ...
  PASSAGES.csv           id, category (hard|clean), subtype, ...
  OWNER_SET.json         the 15 passages the owner transcribes
  OWNER_REFERENCES.csv   exported by reference_entry.html: columns id, reference
  SPOTCHECK.csv          exported by reference_entry.html (optional): id, ok (yes/no), corrected
Protocol (Kean D-20261106-encyclopedie-ocr-reference)
  * owner passages: reference = what the owner typed.
  * every other passage: reference = the text on which GPO's layer and the REFERENCE ENGINE (default surya) agree
    EXACTLY after whitespace folding. Passages where they disagree are left out (counted, listed).
    By construction GPO and the reference engine score 100% on those passages, so on them the table only measures the
    other readers (Tesseract, PaddleOCR, Claude, and every voting rule that is not just GPO or the reference engine).
  * the adoption test uses ONLY the owner passages for 'halves GPO's exact-match failures' and only the agreed clean
    passages for 'invents nothing'.

Normalisation ('strict'): Unicode NFC, every whitespace run -> one space, strip. Nothing else: a wrong fraction glyph,
quote, dash or prime is an error. 'lenient' additionally folds curly quotes, dash variants, primes and soft hyphens and
removes spaces before ; : , . ) -- it is reported next to strict, never instead of it.

Invention: align reading to reference with a minimum-edit alignment; the reading 'invents' on a passage when the
alignment contains a run of >= INVENT_RUN (6) consecutive inserted characters (text with no counterpart in the
reference: a fabricated word, a duplicated line, a continued sentence). Isolated inserted characters from noise,
and a wrong glyph replaced by a few characters (a quarter-fraction read as "y4": one substitution plus one insertion),
stay below the threshold. 6 is the shortest word-sized run (a 5-letter word and its space).

Voting rules (04-ocr.md: two engines plus GPO voting; disagreements to an image-aware adjudicator):
  gpo-layer, tesseract-psm6, tesseract-psm3, surya, paddleocr, claude    single readers
  majority-exact    text produced identically by >= 3 of {gpo-layer, tesseract-psm6, surya, paddleocr}; else abstain
  medoid            of those four, the reading with the least summed edit distance to the other three
  agree3-else-claude   surya == paddleocr == gpo-layer exactly, else Claude's reading (Claude adjudicates by reading)
  claude-judge      the non-Claude reading nearest (edit distance) to Claude's reading (cannot invent text no engine
                    produced)
  surya+gpo-else-claude  circular on agreed passages (see above); meaningful only on owner passages
Adoption: a rule is adopted only if (a) on owner passages its exact-match failures are <= half of GPO's (and GPO fails
at least 2 there) and (b) on agreed clean passages it invents nothing (0 passages).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import unicodedata
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
INVENT_RUN = 6
VOTERS = ["gpo-layer", "tesseract-psm6", "surya", "paddleocr"]
SINGLE = ["gpo-layer", "tesseract-psm6", "tesseract-psm3", "surya", "paddleocr", "claude"]


# ---------- text handling ----------
def norm(s, mode="strict"):
    s = unicodedata.normalize("NFC", s or "")
    if mode == "lenient":
        s = (s.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
             .replace("′", "'").replace("″", '"').replace("–", "-").replace("—", "-")
             .replace("−", "-").replace("­", ""))
        s = re.sub(r"\s+([;:,.)])", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def edit_ops(a, b):
    """Minimum-edit alignment of a (reference) to b (reading).
    Returns (distance, inserted, deleted, substituted, longest_insert_run)."""
    n, m = len(a), len(b)
    prev = list(range(m + 1))
    back = [[0] * (m + 1) for _ in range(n + 1)]  # 0 diagonal, 1 deletion (ref char missing), 2 insertion
    for j in range(1, m + 1):
        back[0][j] = 2
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        back[i][0] = 1
        ai = a[i - 1]
        for j in range(1, m + 1):
            d = prev[j - 1] + (ai != b[j - 1])
            u = prev[j] + 1
            l = cur[j - 1] + 1
            if d <= u and d <= l:
                cur[j], back[i][j] = d, 0
            elif u <= l:
                cur[j], back[i][j] = u, 1
            else:
                cur[j], back[i][j] = l, 2
        prev = cur
    i, j = n, m
    ins = dele = sub = run = best = 0
    while i > 0 or j > 0:
        op = back[i][j]
        if op == 0:
            if a[i - 1] != b[j - 1]:
                sub += 1
            run = 0
            i, j = i - 1, j - 1
        elif op == 1:
            dele += 1
            run = 0
            i -= 1
        else:
            ins += 1
            run += 1
            best = max(best, run)
            j -= 1
    return prev[m], ins, dele, sub, best


def edit_distance(a, b):
    return edit_ops(a, b)[0]


def cer(ref, hyp):
    return edit_distance(ref, hyp) / max(1, len(ref))


def invents(ref, hyp):
    return edit_ops(ref, hyp)[4] >= INVENT_RUN


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0, c - h), 3), round(min(1, c + h), 3))


# ---------- loading ----------
def load_readings(path):
    by = defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                by[r["passage_id"]][r["engine"]] = r["output_text"]
    return by


def load_passages(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return {r["id"]: r for r in csv.DictReader(fh)}


# ---------- agreed references ----------
def build_agreed(readings, passages, owner_ids, ref_engine="surya", mode="strict"):
    """Return (agreed {id: text}, disagreed [ids]) over the non-owner passages."""
    agreed, dis = {}, []
    for pid in sorted(passages):
        if pid in owner_ids:
            continue
        r = readings.get(pid, {})
        g, e = r.get("gpo-layer"), r.get(ref_engine)
        if g is not None and e is not None and norm(g, mode) == norm(e, mode) and norm(g, mode):
            agreed[pid] = g
        else:
            dis.append(pid)
    return agreed, dis


# ---------- voting rules ----------
def rule_output(rule, r, mode="strict"):
    """r: {engine: text}. Returns the chosen text, or None when the rule abstains."""
    def n(e):
        return norm(r.get(e, ""), mode) if e in r else None

    if rule in SINGLE:
        return r.get(rule)
    voters = [e for e in VOTERS if e in r]
    if rule == "majority-exact":
        counts = defaultdict(list)
        for e in voters:
            counts[n(e)].append(e)
        best = max(counts.items(), key=lambda kv: len(kv[1]), default=None)
        return r[best[1][0]] if best and len(best[1]) >= 3 else None
    if rule == "medoid":
        if not voters:
            return None
        tot = {e: sum(edit_distance(n(e), n(o)) for o in voters if o != e) for e in voters}
        return r[min(voters, key=lambda e: (tot[e], VOTERS.index(e)))]
    if rule == "agree3-else-claude":
        if all(e in r for e in ("surya", "paddleocr", "gpo-layer")) and n("surya") == n("paddleocr") == n("gpo-layer"):
            return r["gpo-layer"]
        return r.get("claude")
    if rule == "surya+gpo-else-claude":
        if "surya" in r and "gpo-layer" in r and n("surya") == n("gpo-layer"):
            return r["gpo-layer"]
        return r.get("claude")
    if rule == "claude-judge":
        if "claude" not in r or not voters:
            return None
        c = n("claude")
        return r[min(voters, key=lambda e: (edit_distance(c, n(e)), VOTERS.index(e)))]
    raise KeyError(rule)


RULES = SINGLE + ["majority-exact", "medoid", "agree3-else-claude", "claude-judge", "surya+gpo-else-claude"]


# ---------- scoring ----------
def score_set(ids, refs, readings, rules, mode="strict"):
    out = {}
    for rule in rules:
        ex = inv = abst = n = 0
        cers = []
        for pid in ids:
            ref = norm(refs[pid], mode)
            txt = rule_output(rule, readings.get(pid, {}), mode)
            n += 1
            if txt is None:
                abst += 1
                cers.append(1.0)
                continue
            hyp = norm(txt, mode)
            ex += hyp == ref
            cers.append(cer(ref, hyp))
            inv += invents(ref, hyp)
        k = n - ex
        out[rule] = {"n": n, "exact": ex, "exact_rate": round(ex / n, 3) if n else None, "failures": k,
                     "failure_rate_ci95": wilson(k, n), "cer_mean": round(sum(cers) / n, 4) if n else None,
                     "invents": inv, "abstained": abst}
    return out


def adoption(owner_scores, clean_scores, rules):
    gpo_fail = owner_scores["gpo-layer"]["failures"]
    res = {}
    for rule in rules:
        if rule == "gpo-layer":
            continue
        o, c = owner_scores[rule], clean_scores.get(rule)
        halves = gpo_fail >= 2 and o["failures"] <= gpo_fail / 2
        none_invented = c is not None and c["n"] > 0 and c["invents"] == 0
        res[rule] = {"owner_failures": o["failures"], "gpo_owner_failures": gpo_fail,
                     "halves_gpo_failures": bool(halves), "testable": gpo_fail >= 2,
                     "clean_n": None if c is None else c["n"],
                     "clean_invented": None if c is None else c["invents"],
                     "invents_nothing_on_clean": bool(none_invented),
                     "adopt": bool(halves and none_invented)}
    return res


def pairwise_cer(readings, passages, engines, mode="strict"):
    """PREVIEW ONLY, no references: mean CER of engine A taking engine B as the reference, per category."""
    out = defaultdict(dict)
    for cat in ("hard", "clean"):
        ids = [p for p in passages if passages[p]["category"] == cat]
        for a in engines:
            for b in engines:
                if a == b:
                    continue
                vals = [cer(norm(readings[p][b], mode), norm(readings[p][a], mode))
                        for p in ids if a in readings.get(p, {}) and b in readings.get(p, {})]
                if vals:
                    out[cat][f"{a} vs {b}"] = round(sum(vals) / len(vals), 4)
    return out


def read_csv_map(path, key="id", val="reference"):
    if not path or not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {r[key]: r[val] for r in csv.DictReader(fh) if r.get(val, "").strip()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--readings", default=os.path.join(HERE, "READINGS.jsonl"))
    ap.add_argument("--passages", default=os.path.join(HERE, "PASSAGES.csv"))
    ap.add_argument("--owner-set", default=os.path.join(HERE, "OWNER_SET.json"))
    ap.add_argument("--owner-refs", default=os.path.join(HERE, "OWNER_REFERENCES.csv"))
    ap.add_argument("--spotcheck", default=os.path.join(HERE, "SPOTCHECK.csv"))
    ap.add_argument("--ref-engine", default="surya")
    ap.add_argument("--out", default=os.path.join(HERE, "SCORES.json"))
    ap.add_argument("--preview-only", action="store_true", help="only the reference-free pairwise preview")
    a = ap.parse_args(argv)
    readings, passages = load_readings(a.readings), load_passages(a.passages)
    engines = sorted({e for r in readings.values() for e in r})
    report = {"engines": engines, "invent_run": INVENT_RUN,
              "PREVIEW_pairwise_cer_NO_REFERENCES": {m: pairwise_cer(readings, passages, engines, m)
                                                    for m in ("strict", "lenient")}}
    with open(a.owner_set, encoding="utf-8") as fh:
        owner_ids = set(json.load(fh)["ids"])
    agreed, dis = build_agreed(readings, passages, owner_ids, a.ref_engine)
    report["agreed"] = {"reference_engine": a.ref_engine, "n_agreed": len(agreed), "n_disagreed_left_out": len(dis),
                        "disagreed_ids": dis}
    # information only: how many non-owner passages would agree if 'exactly' were loosened (NOT used for references)
    sens = {}
    for mode in ("strict", "lenient"):
        cers = [cer(norm(readings[p]["gpo-layer"], mode), norm(readings[p][a.ref_engine], mode))
                for p in sorted(passages) if p not in owner_ids and a.ref_engine in readings.get(p, {})]
        sens[mode] = {str(t): sum(c <= t for c in cers) for t in (0.0, 0.005, 0.01, 0.02, 0.05)}
        sens[mode]["n_non_owner"] = len(cers)
    report["agreement_sensitivity_gpo_vs_ref_engine_INFORMATION_ONLY"] = sens
    if not a.preview_only:
        owner_refs = {k: v for k, v in read_csv_map(a.owner_refs).items() if k in owner_ids}
        spot = read_csv_map(a.spotcheck, val="ok")
        spot_fix = read_csv_map(a.spotcheck, val="corrected")
        refs_agreed = dict(agreed)
        wrong = []
        for pid, ok in spot.items():
            if pid in refs_agreed and ok.strip().lower() in ("no", "n", "false", "0"):
                wrong.append(pid)
                if spot_fix.get(pid):
                    refs_agreed[pid] = spot_fix[pid]
                else:
                    refs_agreed.pop(pid)
        report["spotcheck"] = {"n_checked": sum(1 for p in spot if p in agreed), "agreed_texts_found_wrong": wrong}
        report["owner_refs_present"] = len(owner_refs)
        for mode in ("strict", "lenient"):
            sets = {}
            oi = sorted(owner_refs)
            sets["owner_hard"] = score_set(oi, owner_refs, readings, RULES, mode) if oi else {}
            for cat in ("hard", "clean"):
                ids = [p for p in sorted(refs_agreed) if passages[p]["category"] == cat]
                sets["agreed_" + cat] = score_set(ids, refs_agreed, readings, RULES, mode) if ids else {}
            report[mode] = {"scores": sets}
            if sets["owner_hard"] and sets.get("agreed_clean"):
                report[mode]["adoption"] = adoption(sets["owner_hard"], sets["agreed_clean"], RULES)
        report["note"] = ("On agreed passages gpo-layer and the reference engine score 100% by construction; those rows "
                          "measure only the other readers. Adoption uses owner passages for the halving test and agreed "
                          "clean passages for the invention test.")
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
    print("agreed", len(agreed), "disagreed", len(dis), "->", a.out)
    return report


if __name__ == "__main__":
    main()
