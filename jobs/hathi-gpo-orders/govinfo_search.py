"""Three narrow searches through GPO's documented public demonstration API."""
import json
import time
import urllib.error
import urllib.request
from harvest import Harvest, OUT, append, sha, fetch_ladder
from commons_scan import extract


def main():
    h = Harvest()
    endpoint = "https://api.govinfo.gov/search?api_key=DEMO_KEY"
    queries = [
        'collection:GOVPUB AND "Herbert Hoover" AND "executive orders"',
        'collection:GOVPUB AND title:("executive orders") AND publishdate:range(1929-01-01,1938-12-31)',
        'collection:GOVPUB AND "executive orders" AND ("6251" OR "7082" OR "6480")',
    ]
    documents = {}
    for n, query in enumerate(queries, 1):
        payload = {"query": query, "pageSize": "100", "offsetMark": "*", "sorts": [{"field": "score", "sortOrder": "DESC"}]}
        try:
            # FetchPool owns robots retrieval/parsing; this documented POST
            # extension stays local because the shared transport is GET-only.
            delay = h.net.pool.allowed(endpoint)
            time.sleep(max(2, delay))
            req = urllib.request.Request(endpoint, data=json.dumps(payload).encode(),
                  headers={"User-Agent": h.net.pool.user_agent, "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read(5_000_001)
                assert len(raw) <= 5_000_000
                if response.headers.get("Retry-After"):
                    raise ValueError("API requested delay; stop exploration")
            path = OUT / "discovery" / f"govinfo_api_search_{n}.json"
            path.write_bytes(raw)
            h.net.note({"route": "govinfo_govpub_api", "url": endpoint, "method": "POST", "query": payload, "result": "fetched", "sha256": sha(raw), "bytes": len(raw)})
            data = json.loads(raw)
            for row in data.get("results", []):
                documents[row.get("packageId", row.get("title"))] = row
            append(OUT / "ROUTE_RESULTS.jsonl", {"route": "govinfo_govpub_api", "query": query, "count": data.get("count"), "returned": len(data.get("results", []))})
        except Exception as exc:
            h.failure("govinfo_govpub_api", str(exc), query=query)
            h.net.note({"route": "govinfo_govpub_api", "url": endpoint, "method": "POST", "query": payload, "result": "failed", "reason": str(exc)})
            print(json.dumps({"route": "govinfo_govpub_api", "failed": str(exc)}), flush=True)
            break  # No retry, key rotation or alternate endpoint on refusal.
    (OUT / "discovery/govinfo_api_candidates.json").write_text(json.dumps(list(documents.values()), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"route": "govinfo_govpub_api", "candidate_metadata_records": len(documents)}), flush=True)


if __name__ == "__main__":
    main()
