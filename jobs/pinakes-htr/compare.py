"""Line up Pinakes HTR's readings of each page word by word and mark where they agree.

The readings fail differently: tesseract (`tess300`) and TrOCR (`trocr`) read what the ink shows; the vision-language
model (`vlm`) reads with the sense of the sentence and may supply plausible words where the ink is illegible. The
fullest reading (the VLM's, else TrOCR's) is the backbone; each of its words is aligned (difflib, on lower-cased words
without punctuation) against every other reading and gets a support count. Agreement makes a reading likelier right
but proves nothing: two engines can share a guess, and every text here stays a machine hypothesis.

Writes, per order, texts/EO_<n>.compare.txt: the backbone text with every word no other reading confirms in
double brackets, ⟦like this⟧, so a person checking the page can go straight to them; and COMPARE.csv: per order the
backbone, words, share confirmed by at least one other reading, share confirmed by tesseract (the most literal
reading), words unconfirmed, [illegible] marks, and the pairwise similarity of every two readings; sorted with the
least-confirmed orders first, as a page-check queue. Appends a section to REPORT.md and adds counts to SUMMARY.json.
"""
from __future__ import annotations

import csv
import difflib
import json
import os
import re
import statistics
import sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import htr  # noqa: E402

READINGS = ("vlm", "trocr", "tess300")   # backbone preference order
ILLEGIBLE = "[illegible]"
COMPARE_FIELDS = ["instrument_id", "year", "pages", "backbone", "readings", "words", "confirmed_share", "confirmed_by_tess300_share",
                  "unconfirmed_words", "illegible_marks", "compare_text_path"] + [f"similarity_{a}_{b}" for a, b in combinations(READINGS, 2)]


def norm(token):
    return re.sub(r"[^\w]", "", token.lower())


def tokens(text):
    """Original tokens (whitespace split, line structure kept) and their normalized forms; [illegible] is kept as is."""
    out = []
    text = re.sub(r"\[repeated \d+ times by the model\]", " ", text or "")
    for li, line in enumerate(text.splitlines()):
        for tok in line.replace(ILLEGIBLE, f" {ILLEGIBLE} ").split():
            out.append((li, tok, ILLEGIBLE if tok == ILLEGIBLE else norm(tok)))
    return [t for t in out if t[2]]


def matched(a, b):
    """Indices of a that align with an equal word of b."""
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    hit = set()
    for blk in sm.get_matching_blocks():
        hit.update(range(blk.a, blk.a + blk.size))
    return hit


def similarity(a, b):
    return round(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), 3) if a and b else ""


def compare_order(texts):
    """texts: {reading: text}. Returns (marked text, stats) or (None, None) when fewer than two readings."""
    have = {k: tokens(v) for k, v in texts.items() if v and v.strip()}
    if len(have) < 2:
        return None, None
    backbone = next(k for k in READINGS if k in have)
    base = have[backbone]
    base_norm = [t[2] for t in base]
    support, by_tess = [0] * len(base), set()
    for k, toks in have.items():
        if k == backbone:
            continue
        hit = matched(base_norm, [t[2] for t in toks])
        for i in hit:
            support[i] += 1
        if k == "tess300":
            by_tess = hit
    lines, cur, last = [], [], None
    for i, (li, tok, n) in enumerate(base):
        if last is not None and li != last:
            lines.append(" ".join(cur))
            cur = []
        last = li
        cur.append(tok if (support[i] or n == ILLEGIBLE) else f"⟦{tok}⟧")
    if cur:
        lines.append(" ".join(cur))
    words = [i for i, t in enumerate(base) if t[2] != ILLEGIBLE]
    confirmed = [i for i in words if support[i]]
    stats = {"backbone": backbone, "readings": "+".join(k for k in READINGS if k in have), "words": len(words),
             "confirmed_share": round(len(confirmed) / len(words), 3) if words else 0.0,
             "confirmed_by_tess300_share": round(len([i for i in words if i in by_tess]) / len(words), 3) if words and "tess300" in have and backbone != "tess300" else "",
             "unconfirmed_words": len(words) - len(confirmed), "illegible_marks": sum(t[2] == ILLEGIBLE for t in base)}
    for a, b in combinations(READINGS, 2):
        stats[f"similarity_{a}_{b}"] = similarity([t[2] for t in have.get(a, [])], [t[2] for t in have.get(b, [])])
    return "\n".join(lines), stats


def run(root, out_dir):
    targets = {t["instrument_id"]: t for t in htr.load_targets(root)}
    rows = []
    for iid, t in sorted(targets.items()):
        stem = iid.replace(":", "_")
        texts = {}
        for k in READINGS:
            p = os.path.join(out_dir, "texts", f"{stem}.{k}.txt")
            if os.path.exists(p):
                with open(p, encoding="utf-8") as fh:
                    texts[k] = fh.read()
        marked, stats = compare_order(texts)
        if stats is None:
            continue
        path = f"texts/{stem}.compare.txt"
        with open(os.path.join(out_dir, path), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(marked)
        rows.append({"instrument_id": iid, "year": t.get("year", ""), "pages": t.get("pages", ""), "compare_text_path": path, **stats})
    rows.sort(key=lambda r: (r["confirmed_share"], r["instrument_id"]))
    htr.write_csv(os.path.join(out_dir, "COMPARE.csv"), COMPARE_FIELDS, rows)
    return summarize(rows)


def summarize(rows):
    shares = sorted(r["confirmed_share"] for r in rows)
    q = (lambda p: round(shares[min(len(shares) - 1, int(p * len(shares)))], 3)) if shares else (lambda p: None)
    words = sum(r["words"] for r in rows)
    unconf = sum(r["unconfirmed_words"] for r in rows)
    return {"orders_compared": len(rows), "words": words, "unconfirmed_words": unconf,
            "confirmed_share_overall": round(1 - unconf / words, 3) if words else None,
            "confirmed_share_quartiles": [q(0.25), q(0.5), q(0.75)],
            "orders_90pct_confirmed": sum(s >= 0.9 for s in shares), "orders_under_50pct_confirmed": sum(s < 0.5 for s in shares),
            "illegible_marks": sum(r["illegible_marks"] for r in rows),
            "median_similarity": {f"{a}_{b}": (statistics.median(v) if v else None) for a, b in combinations(READINGS, 2)
                                  for v in [[r[f"similarity_{a}_{b}"] for r in rows if r[f"similarity_{a}_{b}"] != ""]]}}


def report_section(s):
    q = s["confirmed_share_quartiles"]
    sim = ", ".join(f"{k.replace('_', ' vs ')} {v}" for k, v in s["median_similarity"].items() if v is not None)
    return "\n".join([
        "## Where the readings agree", "",
        f"{s['orders_compared']} orders have two or more readings. Of {s['words']} words in the backbone reading, "
        f"{s['words'] - s['unconfirmed_words']} ({s['confirmed_share_overall']}) are confirmed by at least one other engine and "
        f"{s['unconfirmed_words']} are not; the VLM marked {s['illegible_marks']} words [illegible]. Share confirmed per order, "
        f"quartiles: {q[0]} / {q[1]} / {q[2]}; {s['orders_90pct_confirmed']} orders are 90% or more confirmed, "
        f"{s['orders_under_50pct_confirmed']} under half. Median word-sequence similarity: {sim}.", "",
        "`texts/EO_<n>.compare.txt` marks every unconfirmed word ⟦like this⟧; `COMPARE.csv` lists the orders "
        "least confirmed first, as the queue for a person's page check. Agreement is not proof: engines can share a guess, "
        "and every reading stays a machine hypothesis.", ""])


def main():
    root = os.environ.get("REPO_ROOT") or os.path.abspath(os.path.join(HERE, "..", ".."))
    out_dir = os.environ.get("OUTPUT_DIR") or os.path.join(HERE, "output")
    s = run(root, out_dir)
    rp = os.path.join(out_dir, "REPORT.md")
    body = open(rp, encoding="utf-8").read() if os.path.exists(rp) else ""
    body = body.split("## Where the readings agree")[0].rstrip() + "\n\n" + report_section(s)
    with open(rp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    sp = os.path.join(out_dir, "SUMMARY.json")
    summary = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    summary["compare"] = s
    with open(sp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps({k: s[k] for k in ("orders_compared", "words", "unconfirmed_words", "confirmed_share_overall")}))


if __name__ == "__main__":
    main()
