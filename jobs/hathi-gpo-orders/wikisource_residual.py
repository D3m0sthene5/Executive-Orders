"""Check residual exact Wikisource HTML titles, never the API or author indexes."""
import json
import re
from urllib.parse import quote, urlsplit
from harvest import Harvest, OUT, ROOT, module, append, fetch_ladder, sha


def main():
    h = Harvest()
    original = module("unchanged_wikisource_helpers", ROOT / "jobs/wikisource-texts/harvest.py")
    done = {r.get("instrument_id") for r in []}
    attempts = OUT / "WIKISOURCE_RESIDUAL.jsonl"
    if attempts.exists():
        done = {json.loads(s)["instrument_id"] for s in attempts.read_text().splitlines() if s.strip()}
    saved, failed = 0, 0
    for identity in sorted(h.missing - done, key=lambda x: (int(re.match(r"EO:(\d+)", x)[1]), x)):
        number = re.sub(r"(?<=\d)([A-Z])$", r"-\1", identity[3:])
        url = "https://en.wikisource.org/wiki/Executive_Order_" + number
        attempt = {"instrument_id": identity, "url": url}
        try:
            result = h.net.fetch("wikisource_residual", url)
            html = result["body"].decode("utf-8")
            actual, heading = original.page_identity(html)
            if actual != identity:
                raise ValueError("wrong_order_heading: " + heading)
            revision = re.search(r'"wgRevisionId"\s*:\s*(\d+)', html)
            if not revision or revision[1] == "0":
                raise ValueError("no_saved_revision")
            rawpath = OUT / "originals" / ("EO_" + identity[3:] + ".html")
            rawpath.parent.mkdir(exist_ok=True)
            rawpath.write_bytes(result["body"])
            text, info = fetch_ladder.extract_text(rawpath, "text/html", "html")
            rev = revision[1]
            source = {"url": result["final_url"], "sha256": result["sha256"],
                      "revision_id": rev, "revision_url": "https://en.wikisource.org/w/index.php?title=" + quote("Executive_Order_" + number) + "&oldid=" + rev,
                      "archival_id": "wikisource:en:revision/" + rev,
                      "page_or_item": heading + "; Wikisource revision " + rev,
                      "source_artifact": rawpath.relative_to(OUT).as_posix(),
                      "notes": "Volunteer website transcription. Exact title ID and revision checked using unchanged Wikisource helper; generic source-ladder extractor retains page furniture. Not original."}
            if not h.save(identity, text, "wikisource_residual", source, "website_transcription"):
                raise ValueError("no_usable_text")
            saved += 1
            attempt["result"] = "saved"
        except Exception as exc:
            failed += 1
            attempt.update(result="failed", reason=str(exc))
            h.failure("wikisource_residual", str(exc), identity, source_url=url)
        append(attempts, attempt)
        if (saved + failed) % 20 == 0:
            print(json.dumps({"route": "wikisource_residual", "attempted_this_run": saved + failed, "saved": saved, "failed": failed, "remaining": len(h.missing)}), flush=True)
        if attempt["result"] == "failed" and ("Host stopped" in attempt["reason"] or "Host already stopped" in attempt["reason"] or "blocked_by_robots" in attempt["reason"]):
            break
    result = {"route": "wikisource_residual", "saved_this_run": saved, "failed_this_run": failed, "remaining": len(h.missing)}
    append(OUT / "ROUTE_RESULTS.jsonl", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
