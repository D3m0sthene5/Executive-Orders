"""Bounded Wikisource acquisition using the project's unchanged shared tools.

Explicit invocation only; this is not an automatically scheduled job.py.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time
from urllib.parse import quote, urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "jobs/_lib"))
import fetch_pool
sys.path.insert(0, str(ROOT / "jobs/source-ladder"))
import fetch_ladder


class SiteStopped(RuntimeError):
    pass


class PageFailure(RuntimeError):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
    temp.replace(path)


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()] if path.exists() else []


def append(path, value):
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def page_identity(html):
    h1 = re.search(r"<h1\b[^>]*>(.*?)</h1>", html, re.S | re.I)
    heading = fetch_ladder.html_to_text(h1[1]) if h1 else ""
    match = re.fullmatch(r"Executive Order (\d+(?:-?[A-Z]|-\d+)?)", heading.strip())
    return ("EO:" + re.sub(r"-(?=[A-Z]$)", "", match[1]) if match else None), heading


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--download", action="store_true", help="Required to authorize network acquisition")
    ap.add_argument("--max-new", type=int, default=1639)
    ap.add_argument("--seed-pilot", action="store_true")
    ap.add_argument("--cache-dir", type=Path, required=True)
    args = ap.parse_args()
    if not args.download:
        ap.error("Use --download explicitly; there is no automatic acquisition")
    here = Path(__file__).resolve().parent
    out = here / "output"
    out.mkdir(exist_ok=True)
    for name in ("SOURCES.jsonl", "FRAGMENTS.jsonl", "FAILURES.jsonl", "ATTEMPTS.jsonl"):
        (out / name).touch(exist_ok=True)
    plan = json.loads((here / "data/PLAN.json").read_text(encoding="utf-8"))
    coverage = json.loads((ROOT / "research/pre-1937-sources/COVERAGE.json").read_text())
    assert set(plan) == set(coverage["matched_instrument_ids"]) and len(plan) == 1639
    for rel, expected in coverage["shared_tools"].items():
        if sha((ROOT / rel).read_bytes()) != expected:
            raise ValueError("Shared tool differs from tested version: " + rel)
    sources = {s["instrument_ids"][0]: s for s in lines(out / "SOURCES.jsonl")}
    failures = {s["instrument_id"]: s for s in lines(out / "FAILURES.jsonl")}
    prior = json.loads((out / "STATE.json").read_text()) if (out / "STATE.json").exists() else {}
    if prior.get("site_stopped") or prior.get("first_200_threshold_exceeded"):
        raise SystemExit("Prior stop condition is preserved; do not resume or work around it")
    attempts = lines(out / "ATTEMPTS.jsonl")
    network_orders = sum(a.get("kind") == "order" for a in attempts)
    network_failures = sum(a.get("kind") == "order" and a.get("result") == "failed" for a in attempts)
    stopped = ""

    def save(iid, raw, url, retrieved, reused=False):
        html = raw.decode("utf-8")
        actual, heading = page_identity(html)
        if actual != iid:
            if actual is None and any(x in html.lower() for x in
                    ("<title>just a moment", "cf-chl-", 'id="challenge-form"', "<title>access denied")):
                raise SiteStopped("HTML access challenge; acquisition stopped")
            raise PageFailure("wrong_order_page: expected " + iid + "; heading=" + heading)
        revision = re.search(r'"wgRevisionId"\s*:\s*(\d+)', html)
        if not revision:
            revision = re.search(r"\boldid=(\d+)", html)
        if not revision:
            raise PageFailure("revision_not_found")
        rev = revision[1]
        title = urlsplit(url).path.split("/wiki/", 1)[-1]
        permalink = "https://en.wikisource.org/w/index.php?title=" + quote(title, safe="_") + "&oldid=" + rev
        name = "EO_" + iid[3:]
        original = out / "originals" / (name + ".html")
        original.parent.mkdir(exist_ok=True)
        original.write_bytes(raw)
        text, _ = fetch_ladder.extract_text(original, "text/html", "html")
        if not text or len(text.strip()) <= 100:
            original.unlink()
            raise PageFailure("no_usable_text")
        text_rel = "texts/" + name + ".txt"
        fetch_ladder.write_text_lf(out / text_rel, text)
        source = {"source_id": "wikisource-texts:" + iid + ":" + sha(raw)[:12],
                  "instrument_ids": [iid], "url": url, "requested_url": plan[iid],
                  "revision_id": rev, "revision_url": permalink,
                  "archival_id": "wikisource:en:revision/" + rev,
                  "sha256": sha(raw), "bytes": len(raw), "retrieved_utc": retrieved,
                  "content_type": "text/html", "route": "mirror/wikisource",
                  "page_or_item": heading + "; Wikisource revision " + rev,
                  "cache_path": "originals/" + name + ".html", "text_path": text_rel,
                  "text_sha256": sha((out / text_rel).read_bytes()),
                  "grade": "mirror_transcription", "representation_type": "volunteer_transcription",
                  "acceptable_as_original": False, "reused_pilot": reused,
                  "notes": "Volunteer Wikisource transcription, not an original. Unchanged project text extractor; page headings, licenses and editorial notes may remain. No legal finding."}
        data = {k: source[k] for k in ("source_id", "url", "sha256", "text_path", "text_sha256",
                                       "page_or_item", "archival_id", "revision_id", "revision_url",
                                       "grade", "representation_type", "acceptable_as_original")}
        data.update(needs_page_check=True, location_verified=False, location_confidence="medium")
        fragment = {"kind": "original_representation", "instrument_id": iid,
                    "produced_by": "wikisource-texts", "grade": "mirror_transcription",
                    "representation_type": "volunteer_transcription", "acceptable_as_original": False,
                    "data": data, "sources": [{k: source[k] for k in ("url", "sha256", "page_or_item", "archival_id")}],
                    "confidence_note": "Exact Wikisource page-title ID checked including suffix. Volunteer transcription only; not an authenticated original or legal conclusion."}
        append(out / "SOURCES.jsonl", source)
        append(out / "FRAGMENTS.jsonl", fragment)
        sources[iid] = source

    if args.seed_pilot:
        pilot = ROOT / "research/pre-1937-sources"
        for record in lines(pilot / "SOURCES.jsonl"):
            iid = record["instrument_ids"][0]
            if iid in sources or iid in failures:
                continue
            raw = (pilot / record["cache_path"]).read_bytes()
            assert iid in plan and sha(raw) == record["sha256"]
            save(iid, raw, record["url"], record["retrieved_utc"], reused=True)

    def checkpoint():
        state = {"updated_utc": stamp(), "planned": len(plan), "saved": len(sources),
                 "failed": len(failures), "not_attempted": len(plan) - len(sources) - len(failures),
                 "reused_pilot": sum(s.get("reused_pilot", False) for s in sources.values()),
                 "network_order_attempts": network_orders, "network_order_failures": network_failures,
                 "first_200_threshold_exceeded": network_orders == 200 and network_failures > 40,
                 "site_stopped": bool(stopped), "stop_reason": stopped,
                 "complete": len(sources) + len(failures) == len(plan)}
        write_json(out / "STATE.json", state)
        print(json.dumps(state), flush=True)
        return state

    def guarded_transport(url, headers, timeout):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "en.wikisource.org" or "/api.php" in parsed.path:
            raise SiteStopped("Unexpected host or API route; request refused")
        started = time.monotonic()
        status, hs, response = fetch_pool.http_transport(url, headers, timeout)
        if status in (401, 403, 408, 425, 429) or status >= 500 or hs.get("retry-after"):
            response.close()
            raise SiteStopped("Site blocking/throttling/server response HTTP " + str(status) +
                              ("; Retry-After=" + hs["retry-after"] if hs.get("retry-after") else ""))
        if time.monotonic() - started > 20:
            response.close()
            raise SiteStopped("Site response exceeded 20 seconds; stopped without retry")
        return status, hs, response

    pool = fetch_pool.FetchPool(args.cache_dir, workers=1, per_host=1, min_interval=1,
                               max_bytes=4_000_000, timeout=25, transport=guarded_transport,
                               user_agent="EO-Historical-Research/1.0 (https://github.com/D3m0sthene5/Executive-Orders)")
    checkpoint()
    started_new = 0
    for iid in sorted(plan, key=lambda x: (int(re.search(r"EO:(\d+)", x)[1]), x)):
        if iid in sources or iid in failures:
            continue
        if started_new >= args.max_new:
            break
        entry = {"kind": "order", "instrument_id": iid, "url": plan[iid], "attempted_utc": stamp()}
        started_new += 1
        network_orders += 1
        try:
            result = pool.fetch(plan[iid])
            save(iid, result["body"], result["final_url"], stamp())
            entry["result"] = "saved"
        except Exception as exc:
            reason = str(exc)
            entry.update(result="failed", reason=reason, error_type=type(exc).__name__)
            failures[iid] = entry
            append(out / "FAILURES.jsonl", entry)
            network_failures += 1
            if isinstance(exc, SiteStopped) or isinstance(exc, (TimeoutError, OSError)) and "tim" in reason.lower():
                stopped = reason
        append(out / "ATTEMPTS.jsonl", entry)
        if stopped:
            checkpoint()
            break
        if network_orders == 200:
            state = checkpoint()
            if state["first_200_threshold_exceeded"]:
                break
        elif started_new % 20 == 0:
            checkpoint()
    checkpoint()


if __name__ == "__main__":
    main()
