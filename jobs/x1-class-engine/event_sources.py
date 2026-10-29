"""Read published event-source providers without conflating representations.

A passing phrase screen establishes a held-text lead only. Raw custody and text
pins remain separate. No source identities, event roles or legal rules change.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_TEXT = 4_000_000
MAX_MANIFEST = 16_000_000
MAX_RAW_REHASH = 100_000_000


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def child(base, rel):
    if not isinstance(rel, str) or not rel or "\\" in rel:
        raise ValueError("missing or invalid relative path")
    p = PurePosixPath(rel)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("unsafe provider path")
    result = base.joinpath(*p.parts)
    result.resolve().relative_to(base.resolve())
    return result


def read_sources(repo, wanted_urls=None):
    repo = Path(repo).resolve()
    held = {}
    for manifest in sorted((repo / "jobs").glob("*/output/SOURCES.jsonl")):
        base = manifest.parent
        provider = base.parent.name
        if manifest.stat().st_size > MAX_MANIFEST:
            raise ValueError("event-source manifest exceeds bound: " + provider)
        with manifest.open("rb") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("event source is not an object")
                urls = {row.get(k) for k in ("url", "requested_url", "final_url") if isinstance(row.get(k), str)}
                if wanted_urls is not None:
                    urls &= set(wanted_urls)
                if not urls:
                    continue
                item = {"provider": provider, "source_record": str(manifest.relative_to(repo)) + ":" + str(number),
                        "record_sha256": hashlib.sha256(line).hexdigest(), "sha256": row.get("sha256", ""),
                        "page_or_item": row.get("page_or_item"), "raw_custody": "not_rehashed_here",
                        "error": "", "_text": ""}
                try:
                    if not isinstance(item["sha256"], str) or not HEX.fullmatch(item["sha256"]):
                        raise ValueError("invalid raw source hash")
                    tp = child(base, row.get("text_path"))
                    if not tp.is_file() or tp.stat().st_size > MAX_TEXT:
                        raise ValueError("text missing or oversized")
                    actual = digest(tp)
                    expected = row.get("text_sha256")
                    if provider == "astra-source-retention" and not expected:
                        raise ValueError("retention text pin missing")
                    if expected and expected != actual:
                        raise ValueError("text hash mismatch")
                    item.update(text_path=str(tp.relative_to(repo)), text_sha256=actual,
                                text_pin="producer_verified" if expected else "computed_legacy_text")
                    item["_text"] = tp.read_text(encoding="utf-8")
                    if row.get("cache_path"):
                        raw = child(base, row["cache_path"])
                        item["raw_path"] = str(raw.relative_to(repo))
                        if raw.is_file() and raw.stat().st_size <= MAX_RAW_REHASH:
                            if digest(raw) != item["sha256"]:
                                raise ValueError("raw hash mismatch")
                            item["raw_custody"] = "bytes_rehashed"
                except (OSError, ValueError) as exc:
                    item["error"] = str(exc)
                    item["_text"] = ""
                for url in sorted(urls):
                    held.setdefault(url, []).append(item.copy())
    return held


def evaluate(repo, events, compact):
    held = read_sources(repo, {s["url"] for e in events for s in e["sources"]})
    states = {}
    for event in events:
        result = []
        for spec in event["sources"]:
            alternatives = []
            for rec in held.get(spec["url"], []):
                missing = [p for p in spec["verify_phrases"] if compact(p) not in compact(rec["_text"])]
                view = {k: v for k, v in rec.items() if k != "_text"}
                view.update(phrases_missing=missing, state="held_invalid" if rec["error"] else
                            "held_phrases_missing" if missing else "held_phrases_found")
                alternatives.append(view)
            versions = {r["sha256"] for r in alternatives if HEX.fullmatch(str(r["sha256"]))}
            selected = next((r for r in alternatives if r["state"] == "held_phrases_found"), None)
            if len(versions) > 1:
                state, selected = "held_conflicting_versions", None
            else:
                state = "held_phrases_found" if selected else alternatives[0]["state"] if alternatives else "source_pending"
            result.append({"citation": spec["citation"], "url": spec["url"], "state": state,
                           "sha256": selected["sha256"] if selected else "",
                           "selected": selected, "representations": alternatives,
                           "phrases_missing": [] if selected else (alternatives[0]["phrases_missing"] if alternatives else spec["verify_phrases"])})
        states[event["event_id"]] = result
    return states
