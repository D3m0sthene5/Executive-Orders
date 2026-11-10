"""Ulpian: the outer bound for one-person executive orders (zero tokens, standard library only).

Named for Ulpian's life-expectancy table (Digest 35.2.68), the Roman jurist's rule for valuing a legacy that ran for
a person's life: a lifetime is a bounded interval, and the law may say how far it can run.

A one-person order (a civil-service waiver, a reinstatement, transfer or retention authority, a retirement
exemption) permits or confers one thing for one named natural person. It cannot operate after that person dies. The
death is not recorded, so its latest possible date is used: if the order's text shows the person alive on date X
(or at least A years old on the order date D, so born no later than D - A years), the person died no later than
that date plus 44,724 days, the longest verified human life (Jeanne Calment, 1875-02-21 to 1997-08-04, 122 years 164
days). The order then ended within the interval (D, bound], with use of the permission unknown.

Version 2 (after the hostile review in research/ulpian/REVIEW.md): there is no flat working-age floor. Tier 1 is an
order bounded on a fact quoted from its own text (Pothier PD-CS-ONE-PERSON's branches B10-B13, each re-run through
every gate here). Tier 2 lists, for each remaining one-person order, its required age r: the smallest whole-year age
on the order date that puts the bound before the cutoff. A tier-2 order stays open until a reading quotes a fact in
the order that excludes an age below r; this tool does not make that reading.

    python -I jobs/ulpian-outer-bound/ulpian.py measure [--out research/ulpian]   # class, tiers, counts; writes files
    python -I jobs/ulpian-outer-bound/ulpian.py rule-sha                           # hash an approval must cite
    python -I jobs/ulpian-outer-bound/ulpian.py tag [--write]                      # refuses without the owner decision
    python -I jobs/ulpian-outer-bound/ulpian.py bound 1915-04-13 14                # one bound, for checking by hand

`measure` decides nothing: it writes CLASS.csv (one row per candidate with its gate, tier, bound and required age)
and MEASURE.json (counts; pinned inputs). `tag` would write research/ulpian/TAGS.jsonl, the tier-1 orders as
proposals for the Respondendi lot `ulpian-life-bound`; it refuses unless a committed Kean decision and a committed
owner-ruling file both cite `ulpian-rule-sha256:<sha256 of RULE.md>`. Neither command changes a status, a claim, the
codebook or a count.
"""
import argparse
import ast
import csv
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
RULE = "jobs/ulpian-outer-bound/RULE.md"
DECISIONS = "jobs/kean/register/decisions.jsonl"
RULINGS = "research/readiness/owner_rulings/"
APPROVE = "ulpian-rule-sha256:"

POTHIER_MEMBERS = "jobs/pothier/output/MEMBERS.jsonl"
POTHIER_LEADS = "jobs/pothier/output/LEADS.jsonl"
POTHIER_DOCTRINE = "research/pothier/doctrines/PD-CS-ONE-PERSON.md"    # Appendix A: per-member born-by dates
NAMIER_LINKS = "jobs/namier/output/NAME_LINKS.jsonl"
LEDGER = "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
JACQUARD_ROWS = "research/excavator/jacquard-2026-10-31/PROPOSED_STATUS_ROWS.csv"
READINGS = "research/ulpian/READINGS.csv"    # Ulpian's own read facts, each anchored by its exact quote

CUTOFF = dt.date(2026, 10, 14)
LIFE_DAYS = 44724                          # Jeanne Calment, 1875-02-21 to 1997-08-04 (122 years 164 days)

# Pothier PD-CS-ONE-PERSON branches. Tier 1: bounded on a quoted fact, with the minimum age the branch's fact fixes
# (None: the per-member born-by date of Appendix A). B09 (retirement lists) and B12b (Commission narratives, no
# command held) are not one-person orders with a held command, so they are kept out here.
LIFE_BRANCHES = {"B10": 64, "B11": None, "B12": 0, "B13": None}
RESIDUE_BRANCH = "B99"
EXCLUDED_BRANCHES = {
    "B09": "several named persons (a retirement list)",
    "B12b": "held text is the Commission's account, not the order's command",
    "B20": "held text is not the member's own order or lacks its command",
    "B21": "not a one-person order (other family)",
    "B22": "class order, general authority or rule instrument",
    "B04": "pre-1903 special rule",
    "B25": "retirement class order",
    "B27": "list of several specified persons",
    "B26": "possible minor (messenger, boy, girl, apprentice)",
    "B23": "designation of an officer to an office",
    "B24": "land-patent signer designation (an office function)",
}

# Text screens. Each is a reason to keep the order out; a false hit only narrows the class. Patterns read the whole
# held text, case-insensitive, whitespace collapsed. AGE_SCREENS apply only where no quoted fact carries the bound.
SCREENS = [
    ("text_not_located", r"\btext not located\b|\bno text\b|\bpage does not exist\b"),
    ("several_persons",
     r"\brespectively\b|\b(?:they|them)\b|\bthe following[- ]named\b|\bpersons\b"
     r"|\b(?:mr|mrs|miss|dr)\b\.?\s+[a-z][\w.' -]{1,40}?\s+and\s+(?:mr|mrs|miss|dr)\b"),
    ("rule_or_order_amended",
     r"\b(?:is|are) (?:hereby )?(?:amended|revoked|rescinded|superseded|modified)\b|\bamended to read\b"
     r"|\bschedule [ab]\b|\brule [ivxl]+\b|\bsection \d+ of (?:the )?(?:civil[- ]service )?rule"),
    ("ratifies_or_confirms", r"\b(?:is|are) (?:hereby )?(?:[\w ,]{0,60})?(?:confirmed|approved|ratified)\b"),
    ("second_clause", r"\b(?:and|but) (?:will|shall) be (?:suspended|reduced|demoted|transferred|detailed|assigned)\b"
                      r"|\bsuspended for\b|\bsuspension\b"),
    ("conditional", r"\bsubject to\b|\bwhen a vacancy\b|\bprovided(?:,)? (?:that|further)\b|\bupon condition\b"
                    r"|\bon condition\b|\bprobation"),
    ("outside_civil_service_rules", r"\blabor regulations\b"),
    ("general_or_continuing",
     r"\bhereafter\b|\bany person\b|\ball persons\b|\bsuch persons\b|\bin like circumstances\b"
     r"|\bany employee\b|\buntil otherwise ordered\b|\bsimilar cases\b|\blike cases\b|\bother cases\b"),
    ("position_not_person",
     r"\bvacancy\b|\bmay be filled\b|\bpositions? (?:of|as) [^.]{0,80}? (?:is|are) (?:hereby )?(?:placed|excepted|classified)"),
    ("property_money_or_estate",
     r"\bestate\b|\bheirs?\b|\bposthumous|\bpension(?:er)? (?:to|for|of \$)|\bannuity\b|\bbounty\b|\breimburse"
     r"|\blands?\b|\bacres?\b|\bconvey|\blease\b|\bbe paid\b|\bpayment of\b|\bback pay\b|\bwith pay\b"),
    ("office_designation",
     r"\bdesignated?\b|\bto act as\b|\bperform the duties\b|\bacting (?:secretary|director|commissioner|chief)"),
]
AGE_SCREENS = [
    ("age_mentioned", r"\bage[sd]?\b|\byears? old\b|\bminor\b|\bbirth"),
    ("possible_minor", r"\bmes ?sen ?ger|\bboy\b|\bgirl\b|\bapprentice|\bpage\b|\bstudent|\bjuvenile|\bschool\b"),
]
SCREENS = [(n, re.compile(p, re.I)) for n, p in SCREENS]
AGE_SCREENS = [(n, re.compile(p, re.I)) for n, p in AGE_SCREENS]
RETIREMENT_FACT = re.compile(r"compulsory retirement|automatic separation|retirement age|retirement for age", re.I)


class Refused(Exception):
    pass


# ------------------------------------------------------------------------------------------------- arithmetic

def minus_years(day, years):
    """Latest birth date for a person at least `years` whole years old on `day` (Feb 29 goes to Feb 28)."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:
        return day.replace(year=day.year - years, day=28)


def death_bound(born_by):
    """Latest possible death of a person born no later than born_by: the longest verified life, in days."""
    return born_by + dt.timedelta(days=LIFE_DAYS)


def bound(order_date, a_min):
    """Latest possible death of a person at least a_min whole years old on order_date."""
    return death_bound(minus_years(order_date, a_min))


def date_threshold(a_min):
    """Orders dated strictly before this date have a bound before the cutoff at this a_min."""
    day = dt.date(1860, 1, 1)
    lo, hi = 0, (CUTOFF - day).days
    while lo < hi:                       # first order date whose bound is on or after the cutoff
        mid = (lo + hi) // 2
        if bound(day + dt.timedelta(days=mid), a_min) < CUTOFF:
            lo = mid + 1
        else:
            hi = mid
    return day + dt.timedelta(days=lo)


def required_age(order_date):
    """Smallest whole-year age on order_date at which the person's latest possible death falls before the cutoff."""
    age = 0
    while bound(order_date, age) >= CUTOFF:
        age += 1
    return age


def parse_day(value):
    if not value or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)):
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


# ------------------------------------------------------------------------------------------------- inputs

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def pin(rel):
    data = (REPO / rel).read_bytes().replace(b"\r\n", b"\n")
    return {"path": rel, "sha256": sha_bytes(data)}


def read_jsonl(rel):
    with open(REPO / rel, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def ledger():
    with open(REPO / LEDGER, encoding="utf-8", newline="") as fh:
        return {r["instrument_id"]: r["provisional_substantive_status"] for r in csv.DictReader(fh)}


def read_text(rel):
    path = REPO / rel if rel else None
    if not path or not path.is_file():
        return ""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8", errors="replace")).strip()


def as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.startswith("["):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return []
    return []


def appendix_born_by():
    """{instrument_id: born-no-later-than date} from PD-CS-ONE-PERSON Appendix A (B11 and B13 members)."""
    out = {}
    for line in (REPO / POTHIER_DOCTRINE).read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and cells[0].startswith("EO:"):
            born = parse_day(cells[-2])
            if born:
                out[cells[0]] = born
    return out


def readings():
    """{instrument_id: (born_by, quote)} from READINGS.csv: facts read by hand that Pothier's appendix lacks. A reading
    counts only while its exact quote (whitespace collapsed) is still in the order's held text."""
    path = REPO / READINGS
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["instrument_id"]: (parse_day(r["born_by"]), r["quote"]) for r in csv.DictReader(fh)
                if parse_day(r["born_by"]) and r.get("quote")}


def date_in_text(day, text):
    """The order's year is legible in its held text (the signature or date line), so the date used is the text's."""
    return bool(re.search(r"(?<!\d)" + str(day.year) + r"(?!\d)", text))


def screen(text, with_age=True):
    hits = [name for name, pattern in SCREENS if pattern.search(text)]
    if with_age:
        hits += [name for name, pattern in AGE_SCREENS if pattern.search(text)]
    return hits


SIGNED_END = re.compile(r"(?:white house|roosevelt|taft|wilson|harding|coolidge|hoover|\d{4}|\[no\. [\w-]+\])\W*$", re.I)


def truncated(text):
    """The held text stops mid-sentence (a cut-off slice): it ends neither with sentence punctuation nor with a
    signature, the White House line, a year or the printed order number. False hits only narrow the class."""
    cut = re.search(r"This work is in the public domain|Retrieved from|Hidden categor|US PD-USGov", text)
    tail = (text[:cut.start()] if cut else text).rstrip(" \"'“”’")
    tail = re.sub(r"(?:\s+[\W\d]{1,4})+$", "", tail)          # page numbers and stray marks after the last word
    if not tail:
        return True
    if re.search(r"white\s*h\w{0,3}s\w{0,2}|\[\s*i?no\.?\s*[\d ,.-]+[\]\)1]", tail[-400:], re.I):
        return False                                            # signed: OCR noise after the signature block
    return not (tail[-1] in ".!?)]" or SIGNED_END.search(tail[-80:]))


def surname_anchor(persons, text):
    for person in persons:
        name = (person.get("name") if isinstance(person, dict) else str(person)) or ""
        parts = [p for p in re.findall(r"[A-Za-z][A-Za-z'’-]+", name) if len(p) > 1]
        if parts and re.search(r"\b" + re.escape(parts[-1]) + r"\b", text, re.I):
            return True
    return False


def date_band(day):
    if day is None:
        return "no exact date"
    for edge, label in ((dt.date(1904, 5, 3), "before 1904-05-03"), (dt.date(1910, 1, 1), "1904-05-03 to 1909"),
                        (dt.date(1918, 5, 3), "1910 to 1918-05-02"), (dt.date(1925, 5, 3), "1918-05-03 to 1925-05-02"),
                        (dt.date(1937, 1, 1), "1925-05-03 to 1936"), (dt.date(1965, 1, 1), "1937 to 1964")):
        if day < edge:
            return label
    return "1965 or later"


# ------------------------------------------------------------------------------------------------- the class

def blank(iid, source, typ, date, status):
    day = parse_day(date)
    return {"instrument_id": iid, "source": source, "type": typ, "date": date or "", "band": date_band(day),
            "status": status, "pothier_branch": "", "persons": "", "gate": "", "screens": "", "tier": "",
            "basis": "", "born_by": "", "bound": "", "required_age": str(required_age(day)) if day else "",
            "text_path": ""}


def gate_text(row, persons, text, with_age):
    """First failing gate for a one-person order's held text, or '' when it passes every one."""
    if len(persons) != 1:
        return "not_exactly_one_parsed_person"
    if len(text) < 80:
        return "no_usable_held_text"
    hits = screen(text, with_age)
    row["screens"] = "|".join(hits)
    if hits:
        return "screen_" + hits[0]
    if not surname_anchor(persons, text):
        return "surname_not_in_held_text"
    if truncated(text):
        return "held_text_truncated"
    return ""


def candidates():
    """One row per candidate one-person order, with the gate that keeps it out or the tier that bounds it."""
    status = ledger()
    members = {m["instrument_id"]: m for m in read_jsonl(POTHIER_MEMBERS)}
    leads = {d["instrument_id"]: d for d in read_jsonl(POTHIER_LEADS) if d.get("doctrine_id") == "PD-CS-ONE-PERSON"}
    born_by = appendix_born_by()
    read = readings()
    rows = []
    for iid, lead in sorted(leads.items()):
        m = members.get(iid, {})
        row = blank(iid, "pothier:PD-CS-ONE-PERSON", m.get("x1_type", ""), m.get("date"), status.get(iid, "undecided"))
        day = parse_day(m.get("date"))
        persons = as_list(m.get("named_persons"))
        branch = row["pothier_branch"] = lead.get("branch_id", "")
        row["persons"] = str(len(persons))
        row["text_path"] = (lead.get("order_text") or {}).get("path") or m.get("primary_text_path") or ""
        if row["status"] != "undecided":
            row["gate"] = "decided"
        elif branch in EXCLUDED_BRANCHES:
            row["gate"] = "pothier_" + branch
        elif branch not in LIFE_BRANCHES and branch != RESIDUE_BRANCH:
            row["gate"] = "pothier_other_mechanism"        # own terms, express revocation, amendment (P1/P2)
        elif day is None:
            row["gate"] = "no_exact_date"
        else:
            text = read_text(row["text_path"])
            reading = read.get(iid)
            if reading and reading[1] not in text:
                reading = None                                  # the held text changed: the reading lapses
            life = branch in LIFE_BRANCHES or reading is not None
            failed = gate_text(row, persons, text, with_age=not life)
            if not failed and not date_in_text(day, text):
                failed = "date_not_in_held_text"
            if failed:
                row["gate"] = failed
            elif life:
                a_min = LIFE_BRANCHES.get(branch) if branch in LIFE_BRANCHES else None
                born = (minus_years(day, a_min) if a_min is not None
                        else born_by.get(iid) or (reading[0] if reading else None))
                if born is None:
                    row["gate"] = "no_appendix_fact"
                else:
                    row["born_by"], row["bound"] = born.isoformat(), death_bound(born).isoformat()
                    row["basis"] = (f"pothier_{branch}" + (f"_a_min_{a_min}" if a_min is not None else "_dated_fact")
                                    if branch in LIFE_BRANCHES else "ulpian_reading_dated_fact")
                    row["gate"] = "in_class" if death_bound(born) < CUTOFF else "bound_after_cutoff"
                    row["tier"] = "quoted_fact" if row["gate"] == "in_class" else ""
            else:
                row["gate"], row["tier"] = "in_class", "required_age_reading"
        rows.append(row)
    sys.path.insert(0, str(REPO / "jobs" / "_lib"))
    import eo_identity  # noqa: E402  (index titles and dates, as Namier reads them)
    titles = eo_identity.load_dates(str(REPO))
    for link in read_jsonl(NAMIER_LINKS):
        iid = link["instrument_id"]
        if iid in leads or link.get("subject_source") != "index_title":
            continue
        row = blank(iid, "namier:index_title", link.get("type", ""), link.get("date"), status.get(iid, "undecided"))
        day = parse_day(link.get("date"))
        names = {n.get("name") for n in (link.get("names") or []) if isinstance(n, dict)}
        row["persons"] = str(len(names))
        title = str((titles.get(iid) or {}).get("title") or "")
        if row["status"] != "undecided":
            row["gate"] = "decided"
        elif day is None:
            row["gate"] = "no_exact_date"
        elif len(names) != 1:
            row["gate"] = "not_exactly_one_parsed_person"
        elif RETIREMENT_FACT.search(title):
            # A retirement exemption names a person at or near compulsory retirement age (lowest 62; Pothier B09
            # uses 61). Its held text is not linked by Namier, so it is not in the class until the text is read.
            row["gate"], row["basis"] = "needs_held_text", "retirement_age_title_a_min_61"
            row["born_by"] = minus_years(day, 61).isoformat()
            row["bound"] = bound(day, 61).isoformat()
        else:
            row["gate"] = "title_only_no_age_fact"
        rows.append(row)
    return rows


def jacquard_l1(rows):
    """Jacquard L1 rows (owner-merged 2026-10-31): the age each needs and whether it hits a screen. Reads dates and
    held texts; it does not read for quoted facts, so it says which rows need a reading, not which rows are wrong."""
    path = REPO / JACQUARD_ROWS
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8", newline="") as fh:
        l1 = [r["instrument_id"] for r in csv.DictReader(fh) if "jacquard-L1" in r.get("decision_origin", "")]
    with open(REPO / "research/excavator/jacquard-2026-10-31/LOTS.csv", encoding="utf-8", newline="") as fh:
        texts = {r["instrument_id"]: r.get("text_path", "") for r in csv.DictReader(fh)}
    dates = {link["instrument_id"]: link.get("date") for link in read_jsonl(NAMIER_LINKS)}
    out = []
    for iid in l1:
        day = parse_day(dates.get(iid))
        hits = screen(read_text(texts.get(iid, "")), with_age=True)
        out.append({"instrument_id": iid, "date": dates.get(iid) or "", "required_age": required_age(day) if day else None,
                    "screens": hits})
    need = [r for r in out if r["required_age"]]
    return {"l1_adopted": len(out),
            "need_age_above_0": len(need),
            "required_age_distribution": dict(sorted(Counter(r["required_age"] for r in need).items())),
            "need_more_than_12": sorted(r["instrument_id"] for r in need if r["required_age"] > 12),
            "hit_a_screen": sorted(r["instrument_id"] for r in need if r["screens"]),
            "no_exact_date": sorted(r["instrument_id"] for r in out if r["required_age"] is None),
            "rows": out}


def summarize(rows):
    undecided = [r for r in rows if r["status"] == "undecided"]
    tier1 = [r for r in undecided if r["tier"] == "quoted_fact"]
    tier2 = [r for r in undecided if r["tier"] == "required_age_reading"]
    return {
        "schema": "ulpian-measure/v2",
        "cutoff": CUTOFF.isoformat(),
        "life_days": LIFE_DAYS,
        "a_min_0_threshold": date_threshold(0).isoformat(),
        "candidates": len(rows),
        "candidates_undecided": len(undecided),
        "class_undecided": len(tier1) + len(tier2),
        "tier1_quoted_fact": len(tier1),
        "tier1_by_basis": dict(Counter(r["basis"] for r in tier1)),
        "tier1_by_band": dict(Counter(r["band"] for r in tier1)),
        "tier2_required_age_reading": len(tier2),
        "tier2_by_band": dict(Counter(r["band"] for r in tier2)),
        "tier2_required_age_distribution": dict(sorted(Counter(int(r["required_age"]) for r in tier2).items())),
        "tier2_required_age_at_most": {str(a): sum(int(r["required_age"]) <= a for r in tier2) for a in (5, 10, 14, 18, 21)},
        "flat_floor_would_reach": {str(a): sum(1 for r in tier2 if dt.date.fromisoformat(r["date"]) < date_threshold(a))
                                   for a in (14, 16, 18, 21)},
        "needs_held_text_retirement_titles": sum(r["gate"] == "needs_held_text" for r in undecided),
        "gates_undecided": dict(Counter(r["gate"] for r in undecided).most_common()),
        "gates_tier1_branches": dict(Counter(f"{r['pothier_branch']}:{r['gate']}" for r in undecided
                                             if r["pothier_branch"] in LIFE_BRANCHES).most_common()),
        "jacquard_l1": {k: v for k, v in jacquard_l1(rows).items() if k != "rows"},
        "inputs": [pin(p) for p in (POTHIER_MEMBERS, POTHIER_LEADS, POTHIER_DOCTRINE, NAMIER_LINKS, LEDGER,
                                    JACQUARD_ROWS, READINGS)],
        "decides": "nothing: no status, claim, codebook entry or count changes; certified stays 0",
    }


FIELDS = ["instrument_id", "source", "type", "date", "band", "status", "pothier_branch", "persons", "gate", "screens",
          "tier", "basis", "born_by", "bound", "required_age", "text_path"]


def write_measure(out):
    rows = candidates()
    out = REPO / out
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "CLASS.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})
    with open(out / "JACQUARD_L1.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["instrument_id", "date", "required_age", "screens"])
        for r in jacquard_l1(rows).get("rows", []):
            w.writerow([r["instrument_id"], r["date"], "" if r["required_age"] is None else r["required_age"],
                        "|".join(r["screens"])])
    summary = summarize(rows)
    (out / "MEASURE.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                      newline="\n")
    return summary


# ------------------------------------------------------------------------------------------------- the lock

def rule_sha():
    path = REPO / RULE
    if not path.is_file():
        raise Refused(f"rule file missing: {RULE}")
    return sha_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def rule_parameters():
    text = (REPO / RULE).read_text(encoding="utf-8").replace("\r\n", "\n")
    blocks = re.findall(r"```json\n(.*?)\n```", text, flags=re.S)
    if len(blocks) != 1:
        raise Refused("RULE.md must hold exactly one ```json parameter block")
    params = json.loads(blocks[0])
    if params.get("life_days") != LIFE_DAYS or params.get("cutoff") != CUTOFF.isoformat():
        raise Refused("RULE.md parameters disagree with this tool (life_days, cutoff)")
    return params


def committed(rel):
    def git(*args):
        return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    log = git("log", "-1", "--format=%H", "--", rel)
    status = git("status", "--porcelain", "--", rel)
    return log.returncode == 0 and bool(log.stdout.strip()) and status.returncode == 0 and not status.stdout.strip()


def owner_approval():
    """The committed Kean decision and owner-ruling file that both cite ulpian-rule-sha256:<RULE.md hash>, or refuse.

    No code can tell who wrote a file; the guard is that both reach main only by an owner merge, and that no agent
    writes either."""
    token = APPROVE + rule_sha()
    latest = {}
    for record in read_jsonl(DECISIONS):
        if record.get("rev", 0) >= latest.get(record.get("id"), {}).get("rev", -1):
            latest[record.get("id")] = record
    for record in latest.values():
        if token not in str(record.get("ruling", "")):
            continue
        for source in record.get("sources") or []:
            if isinstance(source, str) and source.startswith(RULINGS):
                full = REPO / source
                if (full.is_file() and token in full.read_text(encoding="utf-8", errors="replace")
                        and committed(source) and committed(DECISIONS)):
                    return {"decision": record.get("id"), "ruling": pin(source), "rule_sha256": rule_sha()}
    raise Refused(f"no recorded owner decision approves {RULE} ({token}); the rule is a draft "
                  "(Kean ask A-20261110-ulpian-outer-bound). Tag nothing.")


def tag(write):
    approval = owner_approval()
    params = rule_parameters()
    out = []
    for r in candidates():
        if r["status"] != "undecided" or r["tier"] != "quoted_fact":
            continue
        out.append({"schema": "ulpian-tag/v2", "instrument_id": r["instrument_id"], "lot": params["lot_id"],
                    "order_date": r["date"], "basis": r["basis"], "born_by": r["born_by"],
                    "not_later_than": r["bound"], "end_kind": params["end_kind"],
                    "end_wording": params["end_wording"].format(bound=r["bound"], born_by=r["born_by"]),
                    "use": "unknown", "text_path": r["text_path"], "approval": approval,
                    "notice": "proposal for a Respondendi lot; not a status, claim or finding; certified 0"})
    if write:
        with open(REPO / "research/ulpian/TAGS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
            for item in out:
                fh.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--out", default="research/ulpian")
    sub.add_parser("rule-sha")
    t = sub.add_parser("tag")
    t.add_argument("--write", action="store_true")
    b = sub.add_parser("bound")
    b.add_argument("date")
    b.add_argument("a_min", type=int)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "measure":
            s = write_measure(args.out)
            print(json.dumps({k: v for k, v in s.items() if k not in ("inputs", "gates_undecided")}, indent=1))
        elif args.cmd == "rule-sha":
            print(rule_sha())
        elif args.cmd == "tag":
            print(json.dumps({"tagged": len(tag(args.write))}))
        elif args.cmd == "bound":
            day = dt.date.fromisoformat(args.date)
            print(json.dumps({"order_date": args.date, "a_min": args.a_min, "latest_possible_death":
                              bound(day, args.a_min).isoformat(), "before_cutoff": bound(day, args.a_min) < CUTOFF,
                              "required_age": required_age(day)}))
    except Refused as exc:
        print(f"ulpian: refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
