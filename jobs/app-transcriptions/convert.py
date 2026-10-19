"""Make the American Presidency Project (APP) records harvested by app-executive-orders readable by the pipeline.

Reads jobs/app-executive-orders/output/ (never writes there) and writes, under OUTPUT_DIR:

* FRAGMENTS.jsonl: the archive-lane records (MIRROR_FRAGMENTS.jsonl) unchanged except that each text_path
  points from this folder to the held APP text. claim-kit discovers only output/FRAGMENTS*.jsonl, so the
  9,000+ archive-lane records were invisible to it under their MIRROR_ name. Live-lane FRAGMENTS.jsonl is
  already discovered and is not repeated here.
* SOURCES.jsonl: one source record per order (live lane first, then the newest capture) for the jobs that
  read other jobs' SOURCES.jsonl texts (later-events scans them for revocation sentences).
* CATEGORIES.csv: APP categories and attributes per page.
* PROBLEMS.csv and SUMMARY.json.

Every record stays what app-executive-orders made it: grade mirror_transcription, representation_type
secondary_compilation_transcription, acceptable_as_original=false. A record that claims otherwise is refused.
This is historical-document discovery, not identity authentication, custody or a legal finding.
"""

import collections
import copy
import csv
import hashlib
import json
import os
import pathlib
import re

JOB = "app-transcriptions"
SOURCE_JOB = "app-executive-orders"
SOURCE_OUT = f"jobs/{SOURCE_JOB}/output"
UNIVERSE = "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
LEAD_GRADE = "mirror_transcription"
LEAD_TYPE = "secondary_compilation_transcription"
SAFE_TEXT = re.compile(r"^texts/[A-Za-z0-9._-]+\.txt$")


def jsonl(path):
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if line.strip():
                yield n, json.loads(line)


def foreign(text_path):
    """APP output-relative text path -> path relative to this job's output folder."""
    return f"../../{SOURCE_JOB}/output/{text_path}"


class Texts:
    """Hash each held APP text once."""

    def __init__(self, base):
        self.base = base
        self.cache = {}

    def check(self, text_path, expected):
        """None when the record's text is present and is the text it names, else a problem code."""
        if not isinstance(text_path, str) or not SAFE_TEXT.match(text_path):
            return "unsafe_or_missing_text_path"
        if text_path not in self.cache:
            p = self.base / text_path
            self.cache[text_path] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        actual = self.cache[text_path]
        if actual is None:
            return "text_file_missing"
        if not expected:
            return "text_sha256_not_recorded"
        if actual != str(expected).lower():
            # live and archive lanes can share a slug; the file holds the other lane's text
            return "text_file_holds_another_capture"
        return None


def lead_only(rec, data=None):
    """True when every grade field says this is a transcription lead, never an original."""
    for node in (rec,) if data is None else (rec, data):
        if node.get("acceptable_as_original") is not False:
            return False
        if node.get("grade") not in (None, LEAD_GRADE):
            return False
        if node.get("representation_type") not in (None, LEAD_TYPE):
            return False
    return True


def census(repo):
    path = repo / UNIVERSE
    if not path.is_file():
        return None
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r.get("id") or r.get("instrument_id") for r in csv.DictReader(fh)
                if r.get("included_in_bibliography", "1") == "1"}


def convert(repo, out):
    repo, out = pathlib.Path(repo), pathlib.Path(out)
    base = repo / SOURCE_OUT
    out.mkdir(parents=True, exist_ok=True)
    texts = Texts(base)
    universe = census(repo)
    problems = []
    stats = collections.Counter()

    # 1. archive-lane fragments for claim-kit
    frags, frag_ids = [], set()
    path = base / "MIRROR_FRAGMENTS.jsonl"
    for n, rec in (jsonl(path) if path.is_file() else ()):
        stats["mirror_fragments_read"] += 1
        data = rec.get("data") if isinstance(rec.get("data"), dict) else {}
        iid = rec.get("instrument_id")
        why = None
        if rec.get("kind") != "original_representation" or not isinstance(iid, str):
            why = "not_an_order_text_record"
        elif not lead_only(rec, data):
            why = "record_not_marked_lead_only"
        else:
            why = texts.check(data.get("text_path"), data.get("text_sha256"))
        if why:
            problems.append({"file": "MIRROR_FRAGMENTS.jsonl", "line": n, "instrument_id": iid or "", "problem": why,
                             "text_path": data.get("text_path") or ""})
            stats[f"mirror_fragments_refused:{why}"] += 1
            continue
        new = copy.deepcopy(rec)
        new["data"]["text_path"] = foreign(data["text_path"])
        new["converted_by"] = JOB
        new["converted_from"] = f"{SOURCE_OUT}/MIRROR_FRAGMENTS.jsonl:{n}"
        frags.append(new)
        frag_ids.add(iid)
    stats["fragments_written"] = len(frags)

    # 2. one source record per order for SOURCES.jsonl readers (live lane preferred, then newest capture)
    best = {}
    for name, lane in (("SOURCES.jsonl", 0), ("MIRROR_SOURCES.jsonl", 1)):
        path = base / name
        for n, rec in (jsonl(path) if path.is_file() else ()):
            stats[f"source_records_read:{name}"] += 1
            ids = rec.get("instrument_ids") or []
            why = None
            if len(ids) != 1 or not isinstance(ids[0], str):
                why = "not_exactly_one_order"
            elif not lead_only(rec):
                why = "record_not_marked_lead_only"
            elif not str(rec.get("url") or "").startswith("https://") or not re.fullmatch(r"[0-9a-f]{64}", str(rec.get("sha256") or "")):
                why = "no_https_url_or_page_sha256"
            else:
                why = texts.check(rec.get("text_path"), rec.get("text_sha256"))
            if why:
                problems.append({"file": name, "line": n, "instrument_id": ",".join(map(str, ids)), "problem": why,
                                 "text_path": rec.get("text_path") or ""})
                stats[f"source_records_refused:{why}"] += 1
                continue
            stamp = str(rec.get("captured_utc") or rec.get("retrieved_utc") or "")
            cur = best.get(ids[0])
            if cur is None or lane < cur[0] or (lane == cur[0] and stamp > cur[1]):
                best[ids[0]] = (lane, stamp, name, n, rec)
    sources = []
    for iid in sorted(best):
        _, _, name, n, rec = best[iid]
        new = dict(rec, text_path=foreign(rec["text_path"]), converted_by=JOB,
                   converted_from=f"{SOURCE_OUT}/{name}:{n}")
        sources.append(new)
    stats["source_records_written"] = len(sources)

    # 3. categories and attributes per page
    cats = []
    seen = set()
    for name in ("DOCUMENTS.jsonl", "MIRROR_DOCUMENTS.jsonl"):
        path = base / name
        for n, rec in (jsonl(path) if path.is_file() else ()):
            key = (rec.get("instrument_id"), rec.get("path"))
            if key in seen:
                continue
            seen.add(key)
            cats.append({"instrument_id": rec.get("instrument_id") or "", "app_path": rec.get("path") or "",
                         "app_node": rec.get("app_node") or "", "date": rec.get("date") or "",
                         "president": rec.get("president") or "",
                         "categories": "|".join(rec.get("categories") or []),
                         "attributes": "|".join(rec.get("attributes") or []),
                         "lane": "live" if name == "DOCUMENTS.jsonl" else "archive",
                         "in_census": "" if universe is None else ("yes" if rec.get("instrument_id") in universe else "no")})
    cat_counts = collections.Counter(c for r in cats for c in r["categories"].split("|") if c)
    attr_counts = collections.Counter(a for r in cats for a in r["attributes"].split("|") if a)
    combos = collections.Counter((r["categories"], r["attributes"]) for r in cats)

    def write_jsonl(name, rows):
        with open(out / name, "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    def write_csv(name, rows, fields):
        with open(out / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    write_jsonl("FRAGMENTS.jsonl", frags)
    write_jsonl("SOURCES.jsonl", sources)
    write_csv("CATEGORIES.csv", cats, ["instrument_id", "app_path", "app_node", "date", "president",
                                       "categories", "attributes", "lane", "in_census"])
    write_csv("PROBLEMS.csv", problems, ["file", "line", "instrument_id", "problem", "text_path"])
    src_ids = set(best)
    summary = {
        "job": JOB,
        "reads": SOURCE_OUT,
        "what_this_is": ("A shape converter. APP transcriptions remain grade mirror_transcription, "
                         "acceptable_as_original=false: historical-document discovery, not identity authentication, "
                         "custody or a legal finding. Nothing here changes a census, ledger, codebook or certified count."),
        "counts": dict(sorted(stats.items())),
        "orders_with_archive_fragment": len(frag_ids),
        "orders_with_source_record": len(src_ids),
        "census_available": universe is not None,
        "orders_with_source_record_in_census": None if universe is None else len(src_ids & universe),
        "orders_with_source_record_not_in_census": None if universe is None else sorted(src_ids - universe),
        "problems_by_code": dict(collections.Counter(p["problem"] for p in problems)),
        "categories": dict(cat_counts.most_common()),
        "attributes": dict(attr_counts.most_common()),
        "category_attribute_combinations": [{"categories": c, "attributes": a, "pages": k}
                                            for (c, a), k in combos.most_common()],
        "pages_tabulated": len(cats),
    }
    with open(out / "SUMMARY.json", "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return summary


def main():
    repo = pathlib.Path(os.environ.get("REPO_ROOT", ".")).resolve()
    out = pathlib.Path(os.environ["OUTPUT_DIR"]).resolve()
    s = convert(repo, out)
    print(json.dumps({k: s[k] for k in ("counts", "orders_with_archive_fragment", "orders_with_source_record",
                                        "orders_with_source_record_in_census", "problems_by_code")}, indent=2))


if __name__ == "__main__":
    main()
