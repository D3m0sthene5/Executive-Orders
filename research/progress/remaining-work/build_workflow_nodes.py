"""Build WORKFLOW_NODES.csv for the dashboard's Workflow tab.

Reads workflow/WORKFLOW_NODES.json (the hand-kept, source-cited node metadata: stage, kind,
namesake, role, inputs, outputs, dated results and history, caveats, sources) and writes
workflow/WORKFLOW_NODES.csv, one row per node, list fields as JSON strings. Catalog stats are
NOT copied here: the page joins each node's `catalog_tool` to the live tools dataset (TOOLS.csv),
so a catalog refresh updates the stats without touching this file.

Checks, and refuses to write on any failure:
  - ids unique; stage, kind and status_class from the allowed sets;
  - every catalog_tool is an exact `tool` value in the newest snapshots/*/TOOLS.csv (or --tools);
  - every id named in feeds exists;
  - namesake_status is documented | recovered | inferred | undocumented | none, and an inferred or
    undocumented namesake is never presented as documented;
  - wikipedia_url, when present, is an en.wikipedia.org/wiki/ address.
With --check-wikipedia it also asks Wikipedia's API that every linked article exists.

Usage: python3 -X utf8 build_workflow_nodes.py [--tools PATH] [--check-wikipedia]
"""
import argparse, csv, json, sys, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC, OUT = HERE / "workflow" / "WORKFLOW_NODES.json", HERE / "workflow" / "WORKFLOW_NODES.csv"
STAGES = {"discover", "identify", "acquire", "draft", "research", "review", "verify", "ready", "support"}
KINDS = {"software", "campaign", "protocol", "gate", "proposal"}
STATUS = {"current", "historical", "proposed"}
NAMESAKE = {"documented", "recovered", "inferred", "undocumented", "none"}
LISTS = ["jobs", "inputs", "outputs", "results", "history", "feeds", "caveats", "sources"]
COLS = ["id", "name", "label", "catalog_tool", "stage", "order", "kind", "status_class", "namesake_status", "namesake_text",
        "namesake_short", "namesake_note", "namesake_evidence", "wikipedia_url", "role", "history_note", "source_pin"]


def newest_tools():
    snaps = sorted((HERE / "snapshots").glob("*/TOOLS.csv"))
    return snaps[-1] if snaps else HERE / "TOOLS.csv"


def check_wikipedia(urls):
    titles = sorted({urllib.parse.unquote(u.split("/wiki/", 1)[1]).replace("_", " ") for u in urls})
    missing = []
    for i in range(0, len(titles), 40):
        q = urllib.parse.urlencode({"action": "query", "titles": "|".join(titles[i:i + 40]), "redirects": 1, "format": "json"})
        req = urllib.request.Request("https://en.wikipedia.org/w/api.php?" + q, headers={"User-Agent": "eo-workflow-check/1.0"})
        pages = json.load(urllib.request.urlopen(req, timeout=30))["query"]["pages"]
        missing += [p["title"] for p in pages.values() if "missing" in p or "invalid" in p]
    return missing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", type=Path, default=None)
    ap.add_argument("--check-wikipedia", action="store_true")
    a = ap.parse_args()
    nodes = json.load(open(SRC, encoding="utf-8"))
    tools_path = a.tools or newest_tools()
    tools = {r["tool"] for r in csv.DictReader(open(tools_path, encoding="utf-8"))}
    ids = [n["id"] for n in nodes]
    errors = []
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids: " + ", ".join(sorted({i for i in ids if ids.count(i) > 1})))
    known = set(ids)
    for n in nodes:
        where = n.get("id", "?")
        for f, allowed in (("stage", STAGES), ("kind", KINDS), ("status_class", STATUS), ("namesake_status", NAMESAKE)):
            if n.get(f) not in allowed:
                errors.append(f"{where}: {f}={n.get(f)!r}")
        if n.get("catalog_tool") and n["catalog_tool"] not in tools:
            errors.append(f"{where}: catalog_tool {n['catalog_tool']!r} is not a TOOLS.csv row")
        for f in n.get("feeds", []):
            if f not in known:
                errors.append(f"{where}: feeds unknown id {f!r}")
        if n.get("namesake_status") in ("undocumented", "none") and n.get("wikipedia_url"):
            errors.append(f"{where}: no documented namesake but a Wikipedia link")
        u = n.get("wikipedia_url", "")
        if u and not u.startswith("https://en.wikipedia.org/wiki/"):
            errors.append(f"{where}: wikipedia_url {u!r}")
        if not n.get("role"):
            errors.append(f"{where}: no role")
    if a.check_wikipedia:
        missing = check_wikipedia([n["wikipedia_url"] for n in nodes if n.get("wikipedia_url")])
        errors += [f"Wikipedia has no article {t!r}" for t in missing]
    if errors:
        sys.exit("refused:\n  " + "\n  ".join(errors))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLS + [c + "_json" for c in LISTS])
        for n in nodes:
            w.writerow([n.get(c, "") for c in COLS] + [json.dumps(n.get(c, []), ensure_ascii=False) for c in LISTS])
    print(json.dumps({"nodes": len(nodes), "tools_checked_against": str(tools_path.relative_to(HERE)),
                      "catalog_rows_mapped": len({n['catalog_tool'] for n in nodes if n.get('catalog_tool')}),
                      "catalog_rows_total": len(tools), "out": str(OUT.relative_to(HERE))}, indent=1))


if __name__ == "__main__":
    main()
