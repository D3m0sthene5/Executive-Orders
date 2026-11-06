"""Niebuhr verify: fetch every page a searcher quoted, keep its hash and text, and test each quote against it.

Input: research/niebuhr/results/*.jsonl (one searcher result per line; see research/niebuhr/BRIEF.md).
Outputs (OUTPUT_DIR):
  VERIFY.csv          one row per (target, source): HTTP status, sha256 and size of the bytes, and whether the quote is on
                      the page (exact after whitespace/case folding, partial with the share of its words found in order, or no)
  pages/<sha256>.txt  the page as text (capped), so a person can read the quote in context
  CORROBORATION.csv   research/niebuhr/corroborate.py: each result against the WPA indexes the project already holds
  SUMMARY.json        counts
A fetched page and a matching quote show that the page says what the searcher reported. They do not authenticate an
order's identity, admit it to the census, or change any count or grade.
"""
import csv
import collections
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import eo_websearch as web  # noqa: E402

MAX_TEXT = 400_000


def fold(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def quote_on_page(quote, text):
    """('exact'|'partial'|'no'|'no_quote', share of quote words found in order)."""
    q, t = fold(quote), fold(text)
    if not q:
        return "no_quote", 0.0
    if q in t:
        return "exact", 1.0
    words = q.split()
    # longest in-order run of the quote's words that appears on the page
    best = 0
    for i in range(len(words)):
        for j in range(len(words), i + best, -1):
            if " ".join(words[i:j]) in t:
                best = max(best, j - i)
                break
    share = best / len(words)
    return ("partial" if share >= 0.5 else "no"), round(share, 2)


def load_results(root):
    out = []
    for path in sorted(glob.glob(os.path.join(root, "research", "niebuhr", "results", "*.jsonl"))):
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            r["_batch"] = os.path.basename(path)
            out.append(r)
    return out


def run(root, out_dir, cache_dir, transport=None, max_requests=1500):
    os.makedirs(os.path.join(out_dir, "pages"), exist_ok=True)
    results = load_results(root)
    searcher = web.Searcher(cache_dir, max_requests=max_requests, transport=transport, engines=[])
    pages = {}
    rows = []
    for r in results:
        for s in r.get("sources") or []:
            url = (s.get("url") or "").strip()
            if not url.startswith(("http://", "https://")):
                continue
            if url not in pages:
                text, _links, rec = searcher.read_page(url)
                pages[url] = (text, rec)
                if text and rec.get("sha256"):
                    p = os.path.join(out_dir, "pages", rec["sha256"] + ".txt")
                    if not os.path.exists(p):
                        with open(p, "w", encoding="utf-8") as fh:
                            fh.write(url + "\n\n" + text[:MAX_TEXT])
            text, rec = pages[url]
            verdict, share = quote_on_page(s.get("quote", ""), text) if text else ("page_not_fetched", 0.0)
            rows.append({"batch": r["_batch"], "target_id": r.get("target_id", ""), "outcome": r.get("outcome", ""),
                         "kind": s.get("kind", ""), "what": (s.get("what") or "")[:120], "url": url,
                         "status": rec.get("status", ""), "error": rec.get("error", ""), "sha256": rec.get("sha256", ""),
                         "bytes": rec.get("bytes", 0), "seen_only_in_snippet": bool(s.get("seen_only_in_snippet")),
                         "quote_check": verdict, "quote_share": share, "quote": (s.get("quote") or "")[:300]})
    fields = ["batch", "target_id", "outcome", "kind", "what", "url", "status", "error", "sha256", "bytes",
              "seen_only_in_snippet", "quote_check", "quote_share", "quote"]
    with open(os.path.join(out_dir, "VERIFY.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    corro = os.path.join(root, "research", "niebuhr", "corroborate.py")
    if os.path.exists(corro):
        subprocess.run([sys.executable, "-I", corro, os.path.join(root, "research", "niebuhr", "results"),
                        os.path.join(out_dir, "CORROBORATION.csv")], check=False)
    by_target = collections.defaultdict(set)
    for row in rows:
        by_target[row["target_id"]].add(row["quote_check"])
    summary = {"results": len(results), "sources_checked": len(rows), "pages_fetched": sum(1 for t, _ in pages.values() if t),
               "pages_failed": sum(1 for t, _ in pages.values() if not t), "requests_used": searcher.requests_used,
               "quote_check": dict(collections.Counter(r["quote_check"] for r in rows)),
               "targets_with_an_exact_quote": sum(1 for v in by_target.values() if "exact" in v),
               "outcomes": dict(collections.Counter(r.get("outcome", "") for r in results)),
               "what_this_is_not": "Discovery checks only: no census, count, grade or identity change."}
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
    return summary
