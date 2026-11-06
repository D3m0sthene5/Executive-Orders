#!/usr/bin/env python3
"""Find whether the project already holds a source: `python3 -I jobs/pothier/held.py WORDS...`

Searches the citation, URL, notes and page fields of every source registry the project keeps
(source-ladder, astra-source-retention, theophilus-sources, current-law, tischendorf-originals and the
fetch queue) and, with --text, the first 400 characters of each held text file. Prints one line per hit:
registry, citation or URL, the held text path (relative to the repository) and the sha256 of the bytes.
A hit is a pointer to check, not proof that the text contains what a doctrine needs: open the text.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRIES = [
    "jobs/source-ladder/output/SOURCES.jsonl",
    "jobs/astra-source-retention/output/SOURCES.jsonl",
    "jobs/theophilus-sources/output/SOURCES.jsonl",
    "jobs/current-law/output/SOURCES.jsonl",
    "jobs/tischendorf-originals/output/SOURCES.jsonl",
    "research/readiness/FETCH_QUEUE.jsonl",
]


def text_path(reg, r):
    tp = r.get("text_path")
    if not tp:
        return ""
    base = Path(reg).parent
    cand = [REPO / tp, REPO / base / tp]
    for c in cand:
        if c.exists():
            return str(c.relative_to(REPO))
    return tp + " (missing)"


def main(argv):
    with_text = "--text" in argv
    words = [w.lower() for w in argv if w != "--text"]
    if not words:
        print(__doc__)
        return 2
    n = 0
    for reg in REGISTRIES:
        p = REPO / reg
        if not p.exists():
            continue
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            hay = " ".join(str(r.get(k) or "") for k in ("citation", "url", "final_url", "requested_url", "notes",
                                                          "page_or_item", "wanted_id", "note", "urls")).lower()
            tp = text_path(reg, r)
            if with_text and tp and not tp.endswith("(missing)"):
                try:
                    hay += " " + (REPO / tp).read_text(encoding="utf-8", errors="replace")[:400].lower()
                except OSError:
                    pass
            if all(w in hay for w in words):
                n += 1
                print(f"{reg.split('/')[1]}\t{r.get('citation') or r.get('url') or r.get('urls')}\t{tp}\t{r.get('sha256', '')}")
    print(f"# {n} hits", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
