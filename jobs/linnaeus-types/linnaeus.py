"""Linnaeus: classify the undecided orders that have no ending or current-law lead, and match each type to a bulk
status source.

Named for Carl Linnaeus, whose Systema Naturae (1735) sorted every living thing into a few ranks so that each could
be looked up by its kind. Zero model tokens, offline: every input is a committed job output.

Every output is a lead about an order's TYPE and about which held finding aid already names it. Nothing here is a
finding about an order's status: no status, identity, census, codebook or count changes (human-certified: 0). A
source's silence about an order is never evidence about the order (D-20261028-evidence-decides).

No-lead set (Respondendi's S5 stratum, research/excavator/claude-respondendi-2026-11-10/DESIGNS.json): an order
undecided in the readiness tracker whose claim-kit STATUS_LEADS record has no lead_actor_ids, no own_terms and no
current_law_leads.

Type precedence (the first that gives a known type wins):
  1. X1 TYPES.csv (pre-1937: WPA 1944 summary, APP title, held text), jobs/x1-class-engine
  2. the X1 taxonomy run on the APP title (orders from 1937 on are not in TYPES.csv)
  3. Linnaeus title patterns (appointment waivers, seizures, Hawaii lands ...)
  4. the Pothier doctrine the order belongs to (jobs/pothier)
  5. the order's form (its title amends or revokes another order)
  6. unknown
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))

PATHS = {
    "tracker": "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
    "status_leads": "jobs/claim-kit/output/STATUS_LEADS.jsonl",
    "types": "jobs/x1-class-engine/output/TYPES.csv",
    "pothier": "jobs/pothier/output/LEADS.jsonl",
    "app": "jobs/app-executive-orders/output/INDEX.csv",
    "census": "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
    "m1118": "research/photius/RESIDUAL.csv",
    "shepard": "jobs/shepard-citations/output/EDGES.csv",
    "later": "jobs/later-events/output/EDGES.csv",
    "frciters": "jobs/selden-fr-citers/output/CITATIONS.csv",
    "ofr1989": "jobs/ofr-codification-1989/output/DISPOSITION_1989.csv",
}

FAMILY = {
    "land_withdrawal_general": "LAND_WITHDRAWAL", "power_site_reserve": "LAND_WITHDRAWAL",
    "mineral_withdrawal": "LAND_WITHDRAWAL", "public_water_reserve": "LAND_WITHDRAWAL",
    "stock_driveway": "LAND_WITHDRAWAL",
    "national_forest_boundary": "NATIONAL_FOREST",
    "military_naval_reservation": "MILITARY_RESERVATION",
    "bird_refuge": "REFUGE_LIGHTHOUSE", "lighthouse_reservation": "REFUGE_LIGHTHOUSE",
    "indian_reservation_trust": "INDIAN_LAND",
    "cs_waiver_individual": "CS_ONE_PERSON", "retirement_exemption": "CS_ONE_PERSON",
    "state_office_permission": "CS_ONE_PERSON",
    "cs_rules_amendment": "CS_RULES",
    "personnel_designation": "DESIGNATION", "patent_signing_designation": "DESIGNATION",
    "wwi_emergency": "WAR_EMERGENCY", "alien_property_sale": "WAR_EMERGENCY",
    "defensive_sea_area": "WAR_EMERGENCY", "war_seizure": "WAR_EMERGENCY",
    "organization_agency": "ORGANIZATION",
    "regulations_issuance": "REGULATIONS", "pay_allowances": "REGULATIONS",
    "labor_hours_suspension": "REGULATIONS",
    "tariff_customs": "CUSTOMS_CONSULAR", "consular_foreign_service": "CUSTOMS_CONSULAR",
    "customs_port": "CUSTOMS_CONSULAR",
    "canal_zone": "CANAL_ZONE",
    "territories": "TERRITORIAL", "philippines": "TERRITORIAL",
    "nra_code_approval": "NRA_CODE",
    "fund_allotment": "SPENT_ONE_TIME", "property_transfer": "SPENT_ONE_TIME",
    "tax_return_inspection": "SPENT_ONE_TIME", "closing_mourning": "SPENT_ONE_TIME",
    "own_terms_expiry": "SPENT_ONE_TIME",
    "amending_only": "AMENDING_OR_REVOKING", "revoking_only": "AMENDING_OR_REVOKING",
    "unknown": "UNKNOWN",
}

DOCTRINE_TYPE = {
    "PD-LAND-WITHDRAWAL": "land_withdrawal_general", "PD-NATIONAL-FOREST": "national_forest_boundary",
    "PD-MILITARY-RESERVATION": "military_naval_reservation", "PD-REFUGE-LIGHTHOUSE": "bird_refuge",
    "PD-INDIAN": "indian_reservation_trust", "PD-CS-ONE-PERSON": "cs_waiver_individual",
    "PD-CS-RULES": "cs_rules_amendment", "PD-WAR-EMERGENCY": "wwi_emergency",
    "PD-CUSTOMS-CONSULAR": "tariff_customs", "PD-ADMIN": "organization_agency",
    "PD-CLASS-EVENTS": "regulations_issuance",
}

# Title patterns the X1 taxonomy lacks (APP titles, lower case, the "Executive Order N-" prefix removed).
EXTRA = [
    ("cs_waiver_individual", r"authoriz\w* the (appointment|reinstatement|transfer|employment|retention)|"
                             r"waiv\w* .{0,60}civil service|without regard to the civil service|"
                             r"permit(ting)? the (appointment|reinstatement)"),
    ("retirement_exemption", r"compulsory retirement|exempt\w* .{0,60}retire"),
    ("war_seizure", r"take possession|taking possession|possession and (assume )?control|"
                    r"control (of|over) the (plants?|properties|facilities|transportation systems?)|"
                    r"operat\w* (of )?(the )?(plants?|facilities|mines?) of"),
    ("defensive_sea_area", r"defensive sea area|airspace reservation|maritime control area"),
    ("territories", r"hawaii|puerto rico|virgin islands|guam|samoa|alaska railroad|territory of"),
    ("national_forest_boundary", r"national forest"),
    ("military_naval_reservation", r"military reservation|naval reservation|fort \w+|barracks|arsenal"),
    ("land_withdrawal_general", r"withdraw\w* .{0,40}(public )?lands?|public lands?|restor\w* .{0,40}lands?|"
                                r"reserv\w* .{0,30}lands?|townsite|town-site|lands? in .{0,40} county"),
    ("customs_port", r"customs (port|collection district|field organization)|port of entry"),
    ("closing_mourning", r"excus\w* .{0,40}(employees|duty)|closing of (government|executive) departments|"
                         r"half[- ]?(holiday|staff)|day of mourning"),
    ("organization_agency", r"establish\w* .{0,60}(committee|commission|board|council|office|agency|administration)|"
                            r"transfer\w* .{0,40}functions"),
    ("regulations_issuance", r"regulations|prescrib\w*|rules governing|selective service|manual for courts-martial"),
    ("personnel_designation", r"designat\w*"),
]
EXTRA_C = [(t, re.compile(p)) for t, p in EXTRA]

# The order's own command only changes another order (its form, not its subject).
AMEND_FORM = re.compile(r"^(amend\w*|amendment of|amendments to|modif\w*|further amend\w*|supplement\w*)\b", re.I)
REVOKE_FORM = re.compile(r"^(revo\w*|rescind\w*|partial revocation|revocation of|terminat\w* (of )?executive order)\b",
                         re.I)
ENDING_WORDS = ("revoc", "supersed", "supersess", "replace", "termin", "abol", "resc", "restor", "vacat", "nullif")

ERAS = ["1862-1906", "1907-1936", "1937-1945", "1946-1989", "1990-2026", "undated"]

# The bulk status source matched to each family (research/linnaeus/REPORT.md gives the measured coverage and the
# sample behind each). The second item names the job that reads it.
SOURCES = {
    "CS_ONE_PERSON": ("Official Register of the United States (appointment lists): the fact date of the appointment "
                      "the waiver allowed; left to Ulpian (Track 3)", "ulpian"),
    "LAND_WITHDRAWAL": ("Federal Register 1936-1993 full text searched by order number (PLOs, power-site "
                        "restorations, BLM notices)", "cruden"),
    "NATIONAL_FOREST": ("Forest Service FS-612 chronological record 1891-2012, then the Federal Register number "
                        "search", "evelyn+cruden"),
    "MILITARY_RESERVATION": ("Federal Register 1936-1993 number search (PLOs, War and Navy transfers)", "cruden"),
    "REFUGE_LIGHTHOUSE": ("Federal Register 1936-1993 number search (PLOs, FWS boundary notices); the FWS Annual "
                          "Report of Lands lists units, not orders", "cruden"),
    "INDIAN_LAND": ("Federal Register 1936-1993 number search (Interior restorations, BIA notices)", "cruden"),
    "CS_RULES": ("Federal Register 1936-1993 number search (CSC rules, 5 CFR notices)", "cruden"),
    "WAR_EMERGENCY": ("Federal Register 1936-1993 number search (Office of Alien Property orders); the 1921 joint "
                      "resolution names no order, so it is no end by itself (D-20261021-unnamed-instruments)",
                      "cruden"),
    "ORGANIZATION": ("Federal Register 1936-1993 number search (reorganization plans, later orders)", "cruden"),
    "REGULATIONS": ("Federal Register 1936-1993 number search (later regulations naming the order)", "cruden"),
    "CUSTOMS_CONSULAR": ("Federal Register 1936-1993 number search (Treasury decisions on ports and districts); "
                         "19 CFR 101.3 is already read by current-law", "cruden"),
    "CANAL_ZONE": ("Federal Register 1936-1993 number search (Canal Zone orders and regulations)", "cruden"),
    "TERRITORIAL": ("Federal Register 1936-1993 number search", "cruden"),
    "DESIGNATION": ("Federal Register 1936-1993 number search", "cruden"),
    "SPENT_ONE_TIME": ("the order's own text (spent on issue; Respondendi F5 own-text basis); no external source",
                       "own_text"),
    "AMENDING_OR_REVOKING": ("the order's own text and its parent's status (Pothier P2; Respondendi F5)", "own_text"),
    "NRA_CODE": ("Schechter (1935) and the NIRA's expiry name no order; Federal Register number search for a later "
                 "instrument that does", "cruden"),
    "UNKNOWN": ("type the order first; Federal Register number search meanwhile", "cruden"),
}


def era(year):
    if year is None:
        return "undated"
    if year < 1907:
        return "1862-1906"
    if year < 1937:
        return "1907-1936"
    if year < 1946:
        return "1937-1945"
    if year < 1990:
        return "1946-1989"
    return "1990-2026"


def number(iid):
    m = re.match(r"EO:(\d+)", iid)
    return int(m.group(1)) if m else None


def year_of(*vals):
    for v in vals:
        m = re.search(r"(1[789]\d\d|20\d\d)", v or "")
        if m:
            return int(m.group(1))
    return None


def strip_title(t):
    return re.sub(r"^executive order\s*[\w-]*\s*[—–\-]+\s*", "", (t or "").strip(), flags=re.I)


def read_csv(path):
    if not Path(path).is_file():
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path):
    out = []
    if Path(path).is_file():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    out.append(json.loads(line))
    return out


def load(root):
    r = Path(root)
    und = {x["instrument_id"]: x for x in read_csv(r / PATHS["tracker"]) if x["provisional_status"] == ""}
    sl = {x["instrument_id"]: x for x in read_jsonl(r / PATHS["status_leads"])}
    types = {x["instrument_id"]: x for x in read_csv(r / PATHS["types"])}
    pothier = {x["instrument_id"]: x for x in read_jsonl(r / PATHS["pothier"])}
    app = {}
    for x in read_csv(r / PATHS["app"]):
        if x.get("instrument_id"):
            app.setdefault(x["instrument_id"], x)
    census = {x["id"]: x for x in read_csv(r / PATHS["census"])}
    # The M1118 gap: residual orders whose only route is the LC/NARA film (microfilm_pending). Rows whose ProQuest
    # replica check failed or was not read are another gap and are counted apart.
    m1118 = {x["instrument_id"]: ("film" if "microfilm_pending" in (x.get("waits_on") or "") else "replica")
             for x in read_csv(r / PATHS["m1118"])}
    return und, sl, types, pothier, app, census, m1118


def no_lead(und, sl):
    """Undecided orders whose STATUS_LEADS record has no actor, own-terms or current-law lead."""
    out = []
    for iid in sorted(und):
        x = sl.get(iid)
        if x is None:
            continue
        if not (x.get("lead_actor_ids") or x.get("own_terms") or x.get("current_law_leads")):
            out.append(iid)
    return out


def ending(mech):
    m = (mech or "").lower()
    return any(w in m for w in ENDING_WORDS)


def held_leads(root, ids):
    """(ending, mentions): iid -> sorted labels of held finding-aid rows that name the order WITH an ending word about
    it but that STATUS_LEADS does not carry, and iid -> labels of rows that name it WITHOUT one (amendments, cross
    references, the 1989 table's in-force, merged or excluded rows). Only the first kind makes an order
    'held_ending_lead_unrouted'; the second is recorded so 'unsourced' can be stated exactly (named, but by nothing
    that speaks of an end). A 1989-table row counts as an ending only in its ended_by_1989 group; a Selden FR-citer row
    only when its printed relation is in the ending class."""
    r = Path(root)
    end, men = collections.defaultdict(set), collections.defaultdict(set)
    for key, label in (("shepard", "shepard"), ("later", "later_events")):
        for x in read_csv(r / PATHS[key]):
            t = x.get("target_id")
            if t in ids:
                (end if ending(x.get("mechanism")) else men)[t].add(f"{label}:{x.get('evidence_type')}")
    for x in read_csv(r / PATHS["frciters"]):
        t = x.get("target_id")
        if t in ids:
            ok = x.get("acting_on_target") == "True" and x.get("mechanism_class") == "ending"
            (end if ok else men)[t].add("selden_fr_citers")
    for x in read_csv(r / PATHS["ofr1989"]):
        t = x.get("census_id")
        if t in ids:
            (end if x.get("group") == "ended_by_1989" else men)[t].add(f"ofr_1989_table:{x.get('group')}")
    return ({k: sorted(v) for k, v in end.items()}, {k: sorted(v) for k, v in men.items()})


def classify_one(iid, types, pothier, app, census, taxonomy):
    t = types.get(iid, {})
    title = (app.get(iid) or {}).get("title", "")
    yr = year_of((census.get(iid) or {}).get("date_effective"), (app.get(iid) or {}).get("date"), t.get("year"))
    typ, how = "unknown", ""
    if t.get("type") and t["type"] != "unknown":
        typ, how = t["type"], "x1_types"
    st = strip_title(title)
    if typ == "unknown" and st and taxonomy is not None:
        hits = taxonomy.matches(st, yr)
        if hits:
            typ, how = hits[0][0], "x1_taxonomy_on_app_title"
    if typ == "unknown" and st:
        low = st.lower()
        for tid, rx in EXTRA_C:
            if rx.search(low):
                typ, how = tid, "linnaeus_title_pattern"
                break
    p = pothier.get(iid)
    if typ == "unknown" and p and p.get("doctrine_id") in DOCTRINE_TYPE:
        typ, how = DOCTRINE_TYPE[p["doctrine_id"]], "pothier_doctrine"
    summ = t.get("wpa_summary", "") or ""
    form = ""
    if AMEND_FORM.search(st) or re.match(r"\s*(amend|modif)", summ, re.I):
        form = "amends_other_order"
    elif REVOKE_FORM.search(st) or re.match(r"\s*(revok|rescind)", summ, re.I):
        form = "revokes_other_order"
    if typ == "unknown" and form:
        typ, how = ("amending_only" if form == "amends_other_order" else "revoking_only"), "title_form"
    return {
        "instrument_id": iid, "number": number(iid) or "", "year": yr or "", "era": era(yr),
        "type": typ, "family": FAMILY.get(typ, "UNKNOWN"), "type_source": how,
        "x1_class": t.get("class", ""), "x1_confidence": t.get("confidence", ""), "form": form,
        "pothier_doctrine": (p or {}).get("doctrine_id", ""),
        "pothier_status_lead": (p or {}).get("status_lead", ""),
        "pothier_basis_kind": (p or {}).get("basis_kind", ""),
        "pothier_lead_kind": (p or {}).get("lead_kind", ""),
        "title": title[:200], "wpa_summary": summ[:200],
    }


def stratum(row):
    """'pothier_decided_lead' (a family doctrine proposes a status the claim kit does not read),
    'held_ending_lead_unrouted' (a held finding aid names it with an ending word), else 'unsourced'."""
    if row["pothier_status_lead"] in ("no", "yes"):
        return "pothier_decided_lead"
    if row["held_ending_leads"]:
        return "held_ending_lead_unrouted"
    return "unsourced"


def cruden_targets(rows):
    """Numbered orders for the Federal Register 1936-1993 number search: unsourced no-lead orders except the
    one-person civil-service waivers (Ulpian's track: counted, not searched). Oldest first."""
    out = [r for r in rows if r["family"] != "CS_ONE_PERSON" and r["stratum"] == "unsourced"
           and re.fullmatch(r"EO:\d+[A-Z]?", r["instrument_id"])]
    out.sort(key=lambda r: (int(r["number"] or 0), r["instrument_id"]))
    return out


COLS = ["instrument_id", "number", "year", "era", "type", "family", "type_source", "x1_class", "x1_confidence",
        "form", "pothier_doctrine", "pothier_status_lead", "pothier_basis_kind", "pothier_lead_kind", "m1118_gap",
        "residual_replica_gap", "held_ending_leads", "held_mentions_without_ending", "stratum", "matched_source", "title", "wpa_summary"]


def run(root, out, taxonomy=None):
    und, sl, types, pothier, app, census, m1118 = load(root)
    ids = no_lead(und, sl)
    held, mentions = held_leads(root, set(ids))
    rows = []
    for iid in ids:
        row = classify_one(iid, types, pothier, app, census, taxonomy)
        row["m1118_gap"] = "yes" if m1118.get(iid) == "film" else ""
        row["residual_replica_gap"] = "yes" if m1118.get(iid) == "replica" else ""
        row["held_ending_leads"] = "|".join(held.get(iid, []))
        row["held_mentions_without_ending"] = "|".join(mentions.get(iid, []))
        row["stratum"] = stratum(row)
        row["matched_source"] = SOURCES.get(row["family"], ("", ""))[1]
        rows.append(row)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "NO_LEAD_TYPES.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    targets = cruden_targets(rows)
    with open(out / "CRUDEN_TARGETS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["instrument_id", "family", "era"])
        for r in targets:
            w.writerow([r["instrument_id"], r["family"], r["era"]])
    by = collections.defaultdict(collections.Counter)
    for r in rows:
        c = by[r["family"]]
        c["total"] += 1
        c["era:" + r["era"]] += 1
        c["m1118_gap"] += r["m1118_gap"] == "yes"
        c[r["stratum"]] += 1
        c["form_derivative"] += bool(r["form"])
    fam_order = sorted(by, key=lambda k: (-by[k]["total"], k))
    summary = {
        "schema": "linnaeus-no-lead-types/v1",
        "notice": ("Type leads only. A finding aid's silence about an order is never evidence about it. No status, "
                   "identity, census, codebook or count is changed (human-certified 0)."),
        "inputs": dict(PATHS),
        "undecided": len(und), "no_lead": len(rows),
        "m1118_gap_overlap": sum(r["m1118_gap"] == "yes" for r in rows),
        "residual_replica_gap_overlap": sum(r["residual_replica_gap"] == "yes" for r in rows),
        "unsourced_named_without_ending_word": sum(r["stratum"] == "unsourced" and bool(r["held_mentions_without_ending"])
                                                   for r in rows),
        "strata": dict(sorted(collections.Counter(r["stratum"] for r in rows).items())),
        "cs_one_person_left_to_ulpian": by["CS_ONE_PERSON"]["total"],
        "cruden_targets": len(targets),
        "by_era": {e: sum(r["era"] == e for r in rows) for e in ERAS},
        "type_source": dict(sorted(collections.Counter(r["type_source"] or "none" for r in rows).items())),
        "by_family": {k: dict(sorted(by[k].items())) for k in fam_order},
        "matched_sources": {k: {"source": v[0], "job": v[1]} for k, v in SOURCES.items()},
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    head = ("| Family | Orders | Pothier decided lead | Held ending lead (unrouted) | Unsourced | M1118 gap | "
            + " | ".join(ERAS) + " | Matched bulk source |")
    lines = ["# Linnaeus: undecided orders with no ending or current-law lead, by type", "",
             f"Undecided {len(und)}; no lead {len(rows)}; overlap with the M1118 pre-1937 original-text gap "
             f"{summary['m1118_gap_overlap']}. Generated by jobs/linnaeus-types; type leads only, and a finding aid's "
             "silence is never evidence.", "", head, "|---|" + "---:|" * (5 + len(ERAS)) + "---|"]
    tot = collections.Counter()
    for k in fam_order:
        c = by[k]
        tot.update(c)
        lines.append(f"| {k} | {c['total']} | {c['pothier_decided_lead']} | {c['held_ending_lead_unrouted']} | "
                     f"{c['unsourced']} | {c['m1118_gap']} | " + " | ".join(str(c['era:' + e]) for e in ERAS)
                     + f" | {SOURCES.get(k, ('', ''))[0]} |")
    lines.append(f"| **Total** | {tot['total']} | {tot['pothier_decided_lead']} | {tot['held_ending_lead_unrouted']} | "
                 f"{tot['unsourced']} | {tot['m1118_gap']} | " + " | ".join(str(tot['era:' + e]) for e in ERAS) + " | |")
    (out / "TYPE_TABLE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sys.path.insert(0, str(Path(a.root) / "jobs" / "x1-class-engine"))
    import taxonomy  # noqa: E402  (jobs/x1-class-engine/taxonomy.py, read-only reuse)
    rows, summary = run(a.root, a.out, taxonomy)
    print(json.dumps({k: summary[k] for k in ("undecided", "no_lead", "m1118_gap_overlap", "strata",
                                                "cruden_targets")}))
    return summary


if __name__ == "__main__":
    main()
