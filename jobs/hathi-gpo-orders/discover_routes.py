"""Save bounded route metadata/robots checks, not order recoveries."""
import json
from pathlib import Path
from urllib.parse import urlencode
from routes_net import RouteNetwork, HERE


def main():
    assert (HERE.parents[1] / "research/orders-1929-1936/ROUTES.md").is_file()
    net = RouteNetwork()
    out = HERE / "output/discovery"
    out.mkdir(exist_ok=True)
    requests = [("app_robots", "https://www.presidency.ucsb.edu/robots.txt"),
                ("govinfo_robots", "https://www.govinfo.gov/robots.txt")]
    queries = {
        "ia_hoover": 'title:("Herbert Hoover") AND title:(proclamations)',
        "ia_gpo": 'title:("Executive orders") AND mediatype:texts AND year:[1929 TO 1938]',
        "ia_fdr": 'title:("Public papers and addresses") AND creator:(Roosevelt)',
    }
    for name, query in queries.items():
        params = [("q", query), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "date"), ("rows", "100"), ("output", "json")]
        requests.append((name, "https://archive.org/advancedsearch.php?" + urlencode(params)))
    requests += [("loc_cfr", "https://www.loc.gov/collections/code-of-federal-regulations/?fo=json&dates=1938&c=100"),
                 ("fraser_robots", "https://fraser.stlouisfed.org/robots.txt"),
                 ("archives_robots", "https://www.archives.gov/robots.txt"),
                 ("hoover_robots", "https://hoover.archives.gov/robots.txt"),
                 ("fdr_robots", "https://www.fdrlibrary.org/robots.txt")]
    summary = {}
    for name, url in requests:
        try:
            r = net.fetch(name, url)
            suffix = ".txt" if "robots" in name else ".json"
            (out / (name + suffix)).write_bytes(r["body"])
            try:
                data = json.loads(r["body"])
                summary[name] = {"numFound": data.get("response", {}).get("numFound"),
                                 "docs": data.get("response", {}).get("docs", []),
                                 "results": [{"id": row.get("id"), "title": row.get("title"), "date": row.get("date")} for row in data.get("results", [])]}
            except ValueError:
                summary[name] = r["body"].decode("utf-8", "replace")[:10000]
        except Exception as exc:
            summary[name] = {"error": str(exc)}
        print(name, json.dumps(summary[name], ensure_ascii=False)[:14000], flush=True)
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
