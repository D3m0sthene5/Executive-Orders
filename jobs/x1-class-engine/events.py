"""Map orders to candidate events using existing retained source representations.

Panizzi and Astra retention are read independently. Phrase screens, raw-custody
facts, and alternative excerpts remain distinct. Mappings fill no claim fields.
"""
import csv, json, re

import taxonomy as tx
import event_sources

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def held_sources(repo):
    """URL -> distinct held-text representations with provenance and validation."""
    return event_sources.read_sources(repo)


def source_state(repo, events):
    return event_sources.evaluate(repo, events, tx.compact)


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
                        "source_records": json.dumps(st, sort_keys=True),
                        "sources_state": "all_held_phrases_found" if all(s["state"] == "held_phrases_found" for s in st)
                        else "source_pending" if any(s["state"] == "source_pending" for s in st) else "held_check_failed",
                        "agent_must_check": "scope of the event; earlier end; savings; the order's own terms"})
    return reg, states, out
