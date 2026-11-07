"""Print the evidence behind chosen MEASURE.csv rows, for a human to read.

Usage:  py -I examples.py <repository path> --rev <commit> EO:7921 EO:12254 ...

For each order it prints the filed claim's whole-order end (mechanism, date, cited source and the words of the
source at the cited span, or the quoted parts), the earlier-end clause found in the held text, and every place in
the held text of the formal revoking instrument where the order's number appears, with context. It reads the
pinned commit only and writes nothing.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure  # noqa: E402
from gitread import Git  # noqa: E402


def context(text, i, j, pad=260):
    return re.sub(r"\s+", " ", text[max(0, i - pad):j + pad])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--rev", default="origin/main")
    ap.add_argument("eo", nargs="+")
    a = ap.parse_args()
    g = Git(a.repo, a.rev)
    m = measure.Measure(g)
    m.load()
    print("commit", g.commit)
    for i in a.eo:
        r = m.row(i)
        print("=" * 100)
        print(i, r["category"], "| F:", r["formal_revocation_instrument"], r["formal_revocation_date"],
              r["formal_revocation_evidence"], "| E:", r["earliest_earlier_end_route"], r["earliest_earlier_end_date"],
              r["earliest_earlier_end_evidence"], r["earliest_earlier_end_basis"], "| gap", r["gap_days"])
        c = m.claims.get(i)
        if c:
            w = c.get("whole_order_end") or {}
            print("claim file:", m.claim_file[i], "| status", c.get("whole_order_status"), "| clauses",
                  len(c.get("operative_clauses") or []))
            print("whole_order_end:", json.dumps({k: w[k] for k in w if k not in ("source",)}, ensure_ascii=False)[:900])
            src = w.get("source") or {}
            print("  source:", {k: src.get(k) for k in ("url", "page_or_item", "text_path", "sha256")})
            if src.get("quoted_parts"):
                print("  quoted_parts:", src["quoted_parts"])
            for cl in (c.get("operative_clauses") or [])[:3]:
                fe = cl.get("first_end") or {}
                print("  clause", cl.get("scope_id"), "| first_end", fe.get("date"), str(fe.get("mechanism"))[:200])
                print("    text:", re.sub(r"\s+", " ", str(cl.get("original_operative_text", "")))[:500])
                for e in cl.get("later_events") or []:
                    print("    later_event:", e.get("actor"), e.get("effective_date"), str(e.get("mechanism"))[:300])
        E = r["_E"]
        if E and E["basis"] != "filed_claim":
            print("E lead:", E.get("route"), E.get("date"), E.get("source"), "|", E.get("quote", "")[:300])
        F = r["_F"]
        if F:
            num = F["instrument"]
            ids = [x for x in (F.get("source"), f"jobs/fr-originals/data/full_run/texts/{num.replace('EO:', 'EO_')}.txt")
                   if x and x.endswith(".txt")]
            target = i.split(":", 1)[1]
            for p in dict.fromkeys(ids):
                t = g.text(p)
                if t is None:
                    continue
                hits = [mm for mm in re.finditer(r"(?<![\d.,])" + re.escape(target) + r"(?![\d])", t)]
                print(f"  formal text {p} (sha256 {g.sha256(p)[:16]}): {len(hits)} mention(s) of {target}")
                for mm in hits[:2]:
                    print("    ..." + context(t, mm.start(), mm.end()) + "...")
    g.close()


if __name__ == "__main__":
    main()
