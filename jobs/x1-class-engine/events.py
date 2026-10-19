"""X1 step 3: map orders to candidate mass-ending events (data/EVENTS.json).

An event's source counts as held only when the source-ladder job has a record
for its URL (jobs/source-ladder/output/SOURCES.jsonl) and every verification
phrase is found in that record's extracted text. Until then every mapping says
source_pending. A mapping is always a candidate: it fills no claim field.
"""
import csv, json, re

import taxonomy as tx

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def held_sources(repo):
    """{url: (sha256, text)} from the source-ladder output."""
    out = {}
    p = repo / "jobs/source-ladder/output/SOURCES.jsonl"
    if not p.exists():
        return out
    for line in open(p):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        for u in {r.get("url"), r.get("requested_url")} - {None}:
            text = ""
            if r.get("text_path"):
                tp = repo / "jobs/source-ladder/output" / r["text_path"]
                if tp.exists():
                    text = tp.read_text(encoding="utf-8", errors="replace")
            out[u] = (r.get("sha256", ""), text)
    return out


def source_state(repo, events):
    held = held_sources(repo)
    states = {}
    for e in events:
        rows = []
        for s in e["sources"]:
            h = held.get(s["url"])
            if not h:
                rows.append({"citation": s["citation"], "url": s["url"], "state": "source_pending", "sha256": ""})
                continue
            sha, text = h
            flat = tx.compact(text)
            missing = [p for p in s["verify_phrases"] if tx.compact(p) not in flat]
            rows.append({"citation": s["citation"], "url": s["url"], "sha256": sha,
                         "state": "held_phrases_found" if not missing else "held_phrases_missing",
                         "phrases_missing": missing})
        states[e["event_id"]] = rows
    return states


def order_date(wpa_row, year):
    """ISO date (or year) from the WPA list's 'Mon D' column."""
    if wpa_row and wpa_row.get("month_day") and wpa_row.get("year", "").isdigit():
        m = re.match(r"([A-Za-z]{3})\w*\.?\s+(\d{1,2})", wpa_row["month_day"])
        if m and m.group(1).lower() in MONTHS:
            return f"{wpa_row['year']}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    return str(year) if year else ""


def in_window(date, lo, hi):
    if not date:
        return False
    if len(date) == 4:
        return lo[:4] <= date <= hi[:4]
    return lo <= date <= hi


def map_events(repo, job, types, wpa):
    reg = json.load(open(job / "data/EVENTS.json"))
    states = source_state(repo, reg["events"])
    out = []
    for iid, r in types.items():
        w = (wpa.get(iid) or [None])[0]
        date = order_date(w, r["year"])
        hay = tx.compact(r["wpa_summary"] + " " + r["app_title"])
        for e in reg["events"]:
            m = e["map"]
            if not in_window(date, m["date_from"], m["date_to"]):
                continue
            basis = ""
            if r["type"] in m.get("types", []):
                basis = "type:" + r["type"]
            elif r["class"] in m.get("classes", []):
                basis = "class:" + r["class"]
            elif m.get("keyword_types_any_land") and r["class"] == "land":
                kw = [k for k in m.get("keywords", []) if k in hay]
                if kw:
                    basis = "keyword:" + kw[0]
            if not basis:
                continue
            st = states[e["event_id"]]
            out.append({"instrument_id": iid, "event_id": e["event_id"], "role": e["role"], "order_date": date,
                        "basis": basis, "type": r["type"], "type_confidence": r["confidence"],
                        "event_candidate_date": e["candidate_date"],
                        "sources_state": "all_held_phrases_found" if all(s["state"] == "held_phrases_found" for s in st)
                        else "source_pending" if any(s["state"] == "source_pending" for s in st) else "held_check_failed",
                        "agent_must_check": "scope of the event; earlier end; savings; the order's own terms"})
    return reg, states, out
