"""Shared helpers: load passages, append a reading to READINGS.jsonl (never overwrite, never edit GPO text)."""
import csv, hashlib, json, os, sys, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
READINGS = os.path.join(HERE, "READINGS.jsonl")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def passages():
    with open(os.path.join(HERE, "PASSAGES.csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def done_keys():
    out = set()
    if os.path.exists(READINGS):
        for l in open(READINGS, encoding="utf-8"):
            if l.strip():
                r = json.loads(l)
                out.add((r["passage_id"], r["engine"]))
    return out


def append(rec):
    rec["created_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec["output_sha256"] = sha(rec["output_text"])
    with open(READINGS, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def base(p, engine, version, params, prompt=None):
    return {"passage_id": p["id"], "engine": engine, "engine_version": version, "params": params, "prompt": prompt,
            "image_sha256": p["crop_png_sha256"], "crop_box_px": p["crop_box_px"], "source_sha256": p["source_sha256"],
            "pdf_page": int(p["pdf_page"]), "dpi": int(p["dpi"])}
