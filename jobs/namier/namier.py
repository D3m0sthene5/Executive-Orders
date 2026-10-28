"""Namier: every held order naming the same person, found once for all one-person orders.

Named for Sir Lewis Namier, who worked out the eighteenth-century House of Commons by
collecting every record of every member (prosopography) instead of reading each man's
career on its own. This job does the same for the one-person executive orders (civil-
service waivers, retirement exemptions and similar): it parses the person each order
names, then searches every held order text once for that name, so a producer no longer
searches the corpus by hand for each order.

Everything it writes is a lead. A name match is not an identity authentication: two
people can share a name, and OCR can join or split names. An empty result covers only the
texts this job read (listed in SEARCH_COVERAGE), never the sources it does not hold.
Nothing here decides a status, a date, an ending or a count. Standard library only.
"""
from __future__ import annotations

import collections
import csv
import datetime as _dt
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "_lib"))
import eo_identity as E  # noqa: E402

SEARCH_ID = "namier:held_texts_person_name"
MECHANISM = "names_same_person"
TYPES_CSV = "jobs/x1-class-engine/output/TYPES.csv"
# Order types whose operative act concerns one named person (X1 classifier types).
SUBJECT_TYPES = {"cs_waiver_individual", "retirement_exemption"}
LEGAL_CUTOFF = "2026-10-14"
SNIPPET = 160
# A mention more than this many years after the order is kept in NAME_LINKS but not offered as a lead: the
# person named in a 1913 waiver is not the person a 1990s order lists (a memorial list, an index page).
MAX_GAP_YEARS = 60
# A person named in more orders than this (an NRA administrator, a judge designated yearly) gets no
# attached leads: the hits stay in NAME_LINKS.jsonl and the coverage note says how many there are.
MAX_LEADS_PER_SUBJECT = 40

HONORIFIC = r"(?:Mrs?\.?|Miss|Ms\.?|Dr\.?|Hon\.?|Rev\.?|Col\.?|Capt\.?|Maj\.?|Lieut\.?|Lt\.?|Gen\.?|Sgt\.?|Prof\.?)"
SUFFIX = r"(?:,?\s+(?:Jr|Sr|2d|3d|II|III|IV)\.?)?"
# A name part: a capitalised word ("Crowley", "McNeir", "O'Brien") or an initial ("T.").
PART = r"(?:[A-Z][a-z]+(?:[A-Z][a-z]+)?|[A-Z]['’][A-Z][a-z]+|[A-Z]\.?)"
NAME = r"(?P<name>" + PART + r"(?:\s+" + PART + r"){1,4}" + SUFFIX + r")"
# Words that are never a given name or a surname in these orders (titles, offices, places, legal words).
STOP = set("""
Act Acts Service Services Civil Commission Commissioner Commissioners Department Departments Dept Order Orders Executive
Rule Rules Section Sections Navy Naval Treasury Office Offices Bureau Board United States State Federal President
Secretary Register Congress Stat Government Administration Veterans Division National Officer Officers Clerk Clerks
General War Interior Post Postmaster Postmasters Assistant Chief Deputy Director Supervisor Inspector Inspectors
Agriculture Commerce Labor Justice Island Islands Zone Canal Panama Alaska Hawaii Philippine Philippines Porto Puerto
Rico Columbia District Court Supreme Army Marine Corps Coast Guard Lighthouse Reclamation Indian Forest Land Lands
Public Works Engineer Engineers Engineering Survey Geological Weather Patent Patents Pension Pensions Customs Internal
Revenue Collector Carrier Carriers Rural Printing Printer Mint Mail Mails Railway Signal Ordnance Quartermaster Medical
Hospital Insane Governor Territory Territories Receiver Agent Agency Reservation Reservations Certain Persons Person Employees Employee Alien Property Custodian Plant
Industry Industries International Organization Organizations Administrator Peninsula Study Satellite
Reactors Modular Renewable Energy Petroleum Entitled Coffee Tribunal Claims Treaty Fuel Food Whereas Therefore Now Hereby Provided That Said This
Pursuant Virtue Authority Retirement Compulsory Exemption Exempted Appointment Appointments Reinstatement Transfer
Promotion Classified Competitive Unclassified Position Positions Grade Annum Vol Sec Chapter House Senate
Representative Representatives Company Corporation Bank Railroad City County Town Street Avenue Building Capitol
Arsenal Station Yard Depot Factory Shops Shop Laboratory Library Museum Institution Smithsonian Observatory Academy
School Schools College University Home Soldiers Sailors Dispensary Prison Penitentiary Jail Immigration Immigrant
Naturalization Emergency Relief Recovery Industrial Tariff Trade Mediation Mediator Reserve Reserves Fleet Militia
Volunteers Regiment Regular Retired Private Sergeant Lieutenant Captain Major Colonel Admiral Ensign Cadet Midshipman
Surgeon Nurse Teacher Matron Messenger Watchman Laborer Mechanic Foreman Draftsman Stenographer Typist Typewriter
Bookkeeper Accountant Auditor Examiner Appraiser Storekeeper Gauger Keeper Superintendent Warden Chaplain Judge
Justice Attorney Marshal Solicitor Counsel Register Recorder Collector Assessor Surveyor Translator Interpreter
Reader Librarian Curator Physician Veterinarian Chemist Botanist Geologist Statistician Economist Scientist Expert
Specialist Technical Scientific Fiscal Legislative Judicial Diplomatic Consular Foreign Domestic American British
French German Spanish Mexican Canadian Chinese Japanese Filipino Hawaiian Alaskan Porto Mr Mrs Miss Ms Dr Hon Rev
Jr Sr Esq Honorable Excellency Widow Wife Son Daughter Father Mother Brother Sister Bill Resolution Joint Statutes
Large Code Regulations Regulation Proclamation Proclamations Amendment Amendments Schedule Schedules Appendix Table
Item Case Cases Matter Number No Nos Date Dated Signed Approved Effective Expiration Term Period Year Years Month
Months Day Days Fiscal Ending Beginning Until From After Before During Within Without Under Upon Over Into Through
Between Among Against About Above Below Across Along Around Behind Beside Beyond Near Off Out Up Down Per Pro Re
Vice Acting Temporary Permanent Regard Legislative Branch Vocational Advisor Adviser Advisory Honorary Probational Probationary Original Additional Further Special Regular Ordinary Extra
The And Or Of In On At To For By With As Is Are Was Were Be Been Being It Its He She His Her They Them Their We Our
You Your Who Whom Whose Which What Where When Why How All Any Each Every Some Such Only Also Not Nor But So Yet
Chairman Member Members Committee Council Conference Convention Delegate Delegates Delegation Exhibition Exposition
Fair World Centennial Celebration Memorial Monument Park Cemetery Harbor Harbour River Lake Bay Creek Mountain Mount
Valley Fort Camp Barracks Point Cape Beach Sound Strait Channel Gulf Ocean Sea Falls Springs Hot Grand Little Big
Upper Lower North South East West Northern Southern Eastern Western Central Middle Old New Saint St Ste San Santa
Los Las Des Del De La Le Du Van Von Der
""".split())
# Capitalised words that are legitimately surnames but also common words in these texts; they count as a
# surname only together with a given name that is not in STOP, which the matcher already requires.
GIVEN_HINT_RE = re.compile(r"^(?:[A-Z][a-z]{2,}|[A-Z]\.)$")

# Cue words after the name in the order's own operative sentence or in the WPA summary.
CUE = (r"(?:is\s+hereby\s+|hereby\s+|further\s+|again\s+)?(?:may be|is hereby|shall be|be appointed|appointed|"
       r"reinstated|transferred|retained|promoted|exempted|made eligible|permitted|authorized|allowed|designated|"
       r"continued|who\b|whose\b|to be)")
PLACE_OR_TITLE = r"(?:,\s*[^,;]{1,80})?"
# Not preceded by 'the', 'of the' etc.: 'the Legislative Branch' is an office, not a person.
NOT_THE = r"(?<!\bthe )(?<!\bThe )(?<!\bof )(?<!\bin )(?<!\bat )(?<!\bto )(?<!\bfor )(?<!\bby )"
OPERATIVE_RE = re.compile(NOT_THE + r"(?<![A-Za-z])" + HONORIFIC + r"?\s*" + NAME + r"\s*" + PLACE_OR_TITLE +
                          r"\s*,?\s*" + CUE)
# A list of persons at the start of a WPA summary: 'William L. Hill, John Lewis May, and Leonard Magruder, exempted'.
LIST_RE = re.compile(r"^\s*(?P<list>" + HONORIFIC + r"?\s*" + PART + r"(?:\s+" + PART + r"){1,4}" + SUFFIX +
                     r"(?:(?:\s*,\s*(?:and\s+)?|\s+and\s+)" + HONORIFIC + r"?\s*" + PART + r"(?:\s+" + PART + r"){1,4}" + SUFFIX +
                     r"){1,12})\s*,?\s*(?:and\s+)?" + PLACE_OR_TITLE + r"\s*,?\s*" + CUE)
# Headings in the texts: "EXEMPTION OF JOHN T. CROWLEY FROM", "APPOINTMENT OF MRS. RUTH HAMPTON AS".
HEADING_RE = re.compile(r"(?:EXEMPTION|EXEMPTING|APPOINTMENT|APPOINTING|REINSTATEMENT|REINSTATING|TRANSFER|"
                        r"RETENTION|RETAINING|PROMOTION|CONTINUANCE|CONTINUING|DESIGNATION)\s+OF\s+"
                        r"(?:(?:MRS?\.?|MISS|DR\.?|HON\.?)\s+)?(?P<name>(?:[A-Z][A-Z'’.]*\s+){1,4}[A-Z][A-Z'’]+)"
                        r"(?:,?\s+(?:JR|SR|2D|3D|II|III)\.?)?\s+(?:FROM|TO|IN|AS|WITHOUT|UNDER|FOR|AT|OF)\b")
# Titles in the indexes: "Exemption of John T. Crowley from Compulsory Retirement", "Authorizing the
# Appointment of Mrs. Ruth Hampton as Assistant Director", "appointing Ralph Whitman to position".
TITLE_RE = re.compile(r"(?i:exempt(?:ion|ing)|appoint(?:ment|ing)|reinstat(?:ement|ing)|transfer(?:ring)?|"
                      r"retention|retain(?:ing)?|promot(?:ion|ing)|continu(?:ance|ing)|designat(?:ion|ing)|"
                      r"permitting|authorizing)\s+(?:(?i:of|to)\s+)?(?:(?i:the)\s+)?" + HONORIFIC + r"?\s*" + NAME)


def unjoin(value):
    """WPA OCR joins words: 'NellieJ. Latta' -> 'Nellie J. Latta'; 'McNeir' and 'O'Brien' stay whole."""
    return re.sub(r"(?<=[a-z]{3})(?=[A-Z]\.?(?:\s|$))", " ", value or "")


def canon_text(value):
    """Collapse whitespace and split OCR-joined initials; keep punctuation."""
    return re.sub(r"\s+", " ", unjoin(value or "")).strip()


def split_joined(token):
    """WPA OCR joins words: 'NellieJ.' -> ['Nellie', 'J.']; 'McNeir' and "O'Brien" stay whole."""
    if re.fullmatch(r"[A-Z]['’][A-Z][a-z]+", token):
        return [token]
    parts = re.findall(r"[A-Z](?:[a-z]+|\.)?(?:[A-Z][a-z]+)?", token)
    out = []
    for p in parts:
        m = re.match(r"^([A-Z][a-z]+)([A-Z]\.?)$", p)
        if m and not p.startswith("Mc") and not p.startswith("Mac") and not p.startswith("O'"):
            out.extend([m.group(1), m.group(2)])
        else:
            out.append(p)
    return out or [token]


GENERATION = ("Jr", "Sr", "2d", "3d", "II", "III", "IV")


def name_parts(raw):
    """['John', 'T.', 'Crowley'] or None when the string is not a usable personal name."""
    raw = canon_text(raw).strip(" ,.;:")
    raw = re.sub(r"\s*,?\s+(Jr|Sr|2d|3d|II|III|IV)\.?$", lambda m: " " + m.group(1), raw)
    tokens = []
    for tok in raw.split(" "):
        tok = tok.strip("“”\"'(),;:")
        if not tok or re.fullmatch(HONORIFIC, tok):
            continue
        tokens.extend(split_joined(tok))
    tokens = [t for t in tokens if t]
    # Trim office or legal words the regex swept up at either end ('Ralph Ely Stedman Without Regard').
    while tokens and tokens[-1].rstrip(".") in STOP:
        tokens.pop()
    while tokens and tokens[0].rstrip(".") in STOP:
        tokens.pop(0)
    if len(tokens) < 2:
        return None
    given, surname = tokens[0], tokens[-1]
    if surname in GENERATION and len(tokens) >= 3:
        surname = tokens[-2]
    if len(surname) < 2 or surname.endswith("."):
        return None
    for n, t in enumerate(tokens[1:-1], 1):
        if t.rstrip(".") in STOP:  # 'Ralph Ely Stedman Without Regard': keep the name before the office word
            tokens = tokens[:n]
            break
    if len(tokens) < 2:
        return None
    given, surname = tokens[0], tokens[-1]
    if not re.match(r"^[A-Z]", given) or not re.match(r"^[A-Z]", surname):
        return None
    # One initial and a surname ('H. White') matches far too much to be a usable search key.
    if len(given_of(tokens)) == 1:
        return None
    return tokens


def given_of(parts):
    """The searchable given name: the first spelled-out name, else the run of initials ('C. M.')."""
    core = [t for t in parts if t not in GENERATION]
    for t in core[:-1]:
        if len(t.rstrip(".")) > 1:
            return t.rstrip(".")
    return " ".join(t.rstrip(".") for t in core[:-1])


def surname_of(parts):
    core = [t for t in parts if t not in GENERATION]
    return core[-1]


def middle_of(parts):
    """Middle names or initials between the searchable given name and the surname, lower-cased."""
    core = [t for t in parts if t not in GENERATION]
    given = given_of(parts)
    if " " in given:  # initials only: nothing in between
        return []
    mids = []
    seen_given = False
    for t in core[:-1]:
        if not seen_given:
            if t.rstrip(".") == given:
                seen_given = True
            continue
        mids.append(t.rstrip(".").lower())
    return mids


def name_key(parts):
    """Case-insensitive (given, surname) key used to merge the same person's spellings."""
    return (given_of(parts).lower(), surname_of(parts).lower())


def body_only(text):
    """Drop the '# ' provenance header lines the text producers prepend (they name the president and volume)."""
    return "\n".join(line for line in text.split("\n") if not line.startswith("#"))


def names_from_text(text, limit=4000):
    """Candidate names from an order's own heading and operative sentences (first `limit` chars)."""
    head = body_only(text)[:limit]
    found = []
    for m in HEADING_RE.finditer(head):
        found.append(("heading", m.group("name").title()))
    body = canon_text(head)
    for m in OPERATIVE_RE.finditer(body):
        found.append(("operative", m.group("name")))
    return found


def names_from_title(title):
    out = []
    for m in TITLE_RE.finditer(canon_text(title)):
        out.append(("title", m.group("name")))
    return out


def names_from_summary(summary):
    """Names from a WPA summary: a leading list of persons, else the first operative-sentence name."""
    out = []
    s = canon_text(summary).lstrip("* ")
    m = LIST_RE.match(s)
    if m:
        for raw in re.split(r"\s*,\s*(?:and\s+)?|\s+and\s+", m.group("list")):
            if raw.strip():
                out.append(("wpa_summary", raw))
        return out
    for m in OPERATIVE_RE.finditer(s):
        out.append(("wpa_summary", m.group("name")))
    return out


def subject_names(iid, texts, title, summary, given_names=None, exclude=()):
    """Merged personal names for one order with where each came from; [] when none parsed.

    A parsed name counts when it carries an initial or an honorific, or its given name is one the
    project's indexes use for some one-person order (`given_names`); otherwise office phrases such as
    'Vocational Advisor' or 'Treaty Claims' would pass as persons."""
    cands = names_from_title(title) + names_from_summary(summary)
    for t in texts:
        cands += names_from_text(t)
    merged = collections.OrderedDict()
    for where, raw in cands:
        parts = name_parts(raw)
        if not parts or name_key(parts) in exclude:
            continue
        if given_names is not None:
            has_initial = any(len(t.rstrip(".")) == 1 for t in parts)
            has_honorific = bool(re.match(r"^\s*" + HONORIFIC + r"\s", canon_text(raw)))
            if not (has_initial or has_honorific or given_of(parts).lower() in given_names):
                continue
        key = name_key(parts)
        entry = merged.setdefault(key, {"name": " ".join(parts), "sources": [], "spellings": []})
        if where not in entry["sources"]:
            entry["sources"].append(where)
        spelled = " ".join(parts)
        if spelled not in entry["spellings"]:
            entry["spellings"].append(spelled)
    return list(merged.values())


# Given names common in these orders, so that a name with no initial ('Edna May') still passes the gate.
SEED_GIVEN = set("""
john william james george charles frank joseph thomas henry robert edward harry walter arthur fred albert samuel david
louis joe charlie clarence richard andrew daniel ernest will jesse oscar lewis peter benjamin frederick willie alfred sam
francis michael herbert elmer carl paul ralph lee earl roy patrick eugene raymond herman howard harold leo martin edwin
jacob ray alexander luther anthony julius guy leonard chester otto philip floyd milton hugh ira lawrence max archie
mary anna emma elizabeth minnie margaret ida alice bertha sarah annie clara ella florence cora martha laura nellie grace
carrie maude mabel bessie jennie gertrude julia hattie edith mattie rose catherine lillian ada lillie helen jessie louise
ethel lula myrtle eva frances lena lucy edna maggie pearl daisy fannie josephine dora rosa nora agnes marie lizzie ellen
mamie nettie esther hannah lottie amelia belle susan stella sadie katie blanche charlotte ruth ruby emily virginia isabel
""".split())


def index_given_names(subjects):
    """Given names the index titles use, plus any given name two or more one-person orders share (for the gate)."""
    from_title, counts = set(), collections.Counter()
    for iid, info in subjects.items():
        seen = set()
        for where, raw in names_from_title(info["title"]) + names_from_summary(info["summary"]):
            parts = name_parts(raw)
            if not parts or len(given_of(parts)) <= 1 or " " in given_of(parts):
                continue
            g = given_of(parts).lower()
            if where == "title":
                from_title.add(g)
            if g not in seen:
                seen.add(g)
                counts[g] += 1
    return SEED_GIVEN | from_title | {g for g, n in counts.items() if n >= 2}


def match_pattern(parts):
    """Regex for 'Given [middle...] Surname' and 'Surname, Given' in another text, OCR-tolerant.

    Only the given name and surname are case-insensitive; a middle part must start with a capital,
    so 'John' never reaches 'Campbell' through 'Johnson Pike' and 'son' is never a middle name."""
    given = given_of(parts)
    sur = surname_of(parts)
    if " " in given:  # initials only: 'C. M. Huntington' / 'Huntington, C. M.'
        g = r"\s*".join(r"(?i:" + re.escape(x) + r")\.?" for x in given.split(" "))
        mids = ""
    else:
        g = r"(?i:" + re.escape(given) + r")(?![a-z])\.?"
        mids = r"(?:[A-Z][a-z]*\.?\s*){0,3}"
    s = r"(?i:" + re.escape(sur).replace(r"\'", r"['’]") + r")(?![a-z])"
    forward = r"(?<![A-Za-z])" + g + r"\s*" + mids + s
    reverse = r"(?<![A-Za-z])" + s + r"\s*,\s*" + g + r"(?:\s*[A-Z][a-z]*\.?){0,3}(?![a-z])"
    return re.compile("(?:" + forward + ")|(?:" + reverse + ")")


INDEX_RE = re.compile(r"_{3,}|-{4,}|\.{5,}")


def middle_conflict(parts, matched):
    """True when both the subject name and the matched text give a middle initial or name and they differ."""
    mids = middle_of(parts)
    if not mids:
        return False
    given, sur = given_of(parts).lower(), surname_of(parts).lower()
    toks = [t.rstrip(".").lower() for t in re.findall(r"[A-Za-z][a-z'’]*\.?", matched)]
    if not toks:
        return False
    if toks[0] == sur:  # 'Surname, Given M.'
        between = toks[2:] if len(toks) > 1 and toks[1] == given else toks[1:]
    else:
        try:
            between = toks[toks.index(given) + 1:toks.index(sur)]
        except ValueError:
            return False
    between = [t for t in between if t]
    if not between:
        return False
    return between[0][0] != mids[0][0]


def surname_token(parts):
    return surname_of(parts).lower()


def number_cited(text, iid):
    """True when the text cites the subject order by its own number (reachable by number-based tools)."""
    num, suffix = E.parse_eo_id(iid)
    if not num:
        return False
    for m in E.MENTION_RE.finditer(text):
        for n in E._NUM_RE.finditer(m.group("run")):
            if n.group(1).replace(",", "") == str(num):
                return True
    return False


TITLE_SUBJECT_RE = re.compile(r"compulsory retirement|without (?:regard|reference) to (?:the )?civil[- ]service", re.I)


def load_subjects(root, fragments, dates):
    """{iid: {'type', 'summary', 'title', ...}} for every one-person order.

    Two sources: the X1 type table (pre-1937 orders typed cs_waiver_individual or retirement_exemption),
    and, for the rest of the census, any order whose index title names a person in an exemption,
    appointment, reinstatement, transfer, retention or designation phrase, or mentions compulsory
    retirement or a civil-service waiver (post-1936 retirement exemptions and waivers are not in X1)."""
    out = {}
    path = os.path.join(root, TYPES_CSV)
    for r in E.read_csv(path):
        if r.get("type") in SUBJECT_TYPES:
            out[r["instrument_id"]] = {"type": r["type"], "confidence": r.get("confidence", ""),
                                       "summary": r.get("wpa_summary", ""), "app_title": r.get("app_title", ""),
                                       "subject_source": "x1_type_table"}
    for iid, info in out.items():
        info["title"] = (dates.get(iid) or {}).get("title") or info["app_title"]
    universe = E.load_universe(root)
    given = index_given_names(out)
    for iid in universe:
        if iid in out:
            continue
        title = (dates.get(iid) or {}).get("title") or ""
        named = bool(subject_names(iid, [], title, "", given))
        if named or TITLE_SUBJECT_RE.search(title):
            out[iid] = {"type": "title_one_person_order" if named else "title_retirement_or_waiver",
                        "confidence": "title", "summary": "", "app_title": title, "title": title,
                        "subject_source": "index_title"}
    return out


class Corpus:
    """Every held text, read once, indexed by lower-cased capitalised word."""

    def __init__(self, root, fragments):
        self.root = root
        self.texts = {}  # (iid, text_path) -> text
        self.meta = {}  # (iid, text_path) -> fragment summary
        self.by_iid = collections.defaultdict(list)
        self.index = collections.defaultdict(set)  # word -> set of (iid, text_path)
        self.unreadable = 0
        for iid, frag, text in E.iter_texts(fragments):
            key = (iid, os.path.relpath(frag["text_path"], root))
            self.texts[key] = text
            self.meta[key] = frag
            self.by_iid[iid].append(key)
            for tok in set(re.findall(r"[A-Z][a-z]+", text)):
                self.index[tok.lower()].add(key)

    def own_texts(self, iid):
        return [self.texts[k] for k in self.by_iid.get(iid, [])]


def search(corpus, subjects, dates):
    """For each subject order and each parsed name, every other held text containing the name."""
    links = []
    coverage = []
    given = index_given_names(subjects)
    presidents = set()
    for d in dates.values():
        parts = name_parts(d.get("president", "")) if d.get("president") else None
        if parts:
            presidents.add(name_key(parts))
    for iid in sorted(subjects, key=E.parse_eo_id):
        info = subjects[iid]
        names = subject_names(iid, corpus.own_texts(iid), info["title"], info["summary"], given, presidents)
        own_held = bool(corpus.by_iid.get(iid))
        date = (dates.get(iid) or {}).get("date", "")
        if not names:
            coverage.append({"instrument_id": iid, "search_id": SEARCH_ID, "covered": 0,
                             "note": "no personal name parsed from the order's title, WPA summary"
                                     + (" or held text" if own_held else "; no held text")})
            links.append({"instrument_id": iid, "type": info["type"], "subject_source": info["subject_source"],
                          "date": date, "names": [], "hits": [], "searchable": False})
            continue
        hits = []
        seen = set()
        for entry in names:
            parts = entry["name"].split(" ")
            pat = match_pattern(parts)
            for key in sorted(corpus.index.get(surname_token(parts), ())):
                other, path = key
                if other == iid:
                    continue
                text = corpus.texts[key]
                m = pat.search(text)
                if not m:
                    continue
                if (other, entry["name"]) in seen:
                    continue
                seen.add((other, entry["name"]))
                odate = (dates.get(other) or {}).get("date", "")
                if date and odate:
                    rel = "later" if odate[:10] > date[:10] else ("earlier" if odate[:10] < date[:10] else "same_date")
                    if len(date) == 4 or len(odate) == 4:
                        rel = rel if date[:4] != odate[:4] else "same_year_order_unknown"
                else:
                    rel = "undated"
                frag = corpus.meta[key]
                start, end = max(0, m.start() - SNIPPET), min(len(text), m.end() + SNIPPET)
                flags = []
                if middle_conflict(parts, text[m.start():m.end()]):
                    flags.append("middle_name_conflict")
                if INDEX_RE.search(text[max(0, m.start() - 60):m.end() + 60]):
                    flags.append("index_or_table_context")
                cautions = []
                n_self, n_other = E.parse_eo_id(iid)[0], E.parse_eo_id(other)[0]
                if n_self and n_other and abs(int(n_self) - int(n_other)) <= 3:
                    cautions.append("adjacent_order_number_check_slice_boundary")
                if date and odate and len(date) >= 4 and len(odate) >= 4:
                    gap = int(odate[:4]) - int(date[:4])
                    if gap > MAX_GAP_YEARS:
                        flags.append(f"later_by_more_than_{MAX_GAP_YEARS}_years")
                hits.append({
                    "flags": flags, "cautions": cautions,
                    "instrument_id": other, "date": odate, "relation": rel, "name": entry["name"],
                    "matched": text[m.start():m.end()], "char_start": m.start(), "char_end": m.end(),
                    "snippet": canon_text(text[start:end]),
                    "cites_subject_number": number_cited(text, iid),
                    "source": {"text_path": path, "text_sha256": sha_file(os.path.join(corpus.root, path)),
                               "sha256": frag.get("sha256", ""), "url": frag.get("url", ""),
                               "page_or_item": frag.get("page_or_item", ""), "grade": frag.get("grade", ""),
                               "produced_by": frag.get("produced_by", "")},
                })
        hits.sort(key=lambda h: (h["date"] or "9999", h["instrument_id"], h["source"]["text_path"]))
        coverage.append({"instrument_id": iid, "search_id": SEARCH_ID, "covered": 1,
                         "note": "searched for " + "; ".join(e["name"] for e in names)})
        links.append({"instrument_id": iid, "type": info["type"], "subject_source": info["subject_source"],
                      "date": date, "names": names, "hits": hits, "searchable": True})
    return links, coverage


_sha_cache = {}


def sha_file(path):
    if path not in _sha_cache:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        _sha_cache[path] = h.hexdigest()
    return _sha_cache[path]


def coverage_entry(corpus, fragments, subjects, coverage, checked_on):
    """The one machine-search record claim-drafts and claim-kit carry into every covered dossier."""
    held = len(corpus.by_iid)
    universe = len(E.load_universe(corpus.root))
    producers = sorted({m.get("produced_by", "") for m in corpus.meta.values()})
    unparsed = sum(1 for c in coverage if not c["covered"])
    return {
        "search_id": SEARCH_ID,
        "complete": True,
        "scope_note": "",
        "entry": {
            "repository": f"held order texts in this repository ({len(corpus.texts)} text files for {held} of "
                          f"{universe} census orders, produced by {', '.join(p for p in producers if p)})",
            "query_or_scope": "the full name of the person this order concerns (given name, any middle names or "
                              "initials, surname; also 'Surname, Given'), case-insensitive, in every other held "
                              f"order text; {universe - held} census orders have no held text and were not "
                              f"searched; {unparsed} of {len(subjects)} one-person orders had no parsable name "
                              "and were not searched (SEARCH_COVERAGE.csv); a match is a name match, not an "
                              "identity authentication",
            "checked_on": checked_on,
            "searched_by": "jobs/namier (machine search)",
        },
    }


def write_outputs(out, root, links, coverage, search_record, corpus, dates, started):
    os.makedirs(out, exist_ok=True)
    counts = collections.Counter()
    for rec in links:
        if rec:
            counts["subjects"] += 1
            counts["subjects_by_type:" + rec["type"]] += 1
            counts["subjects_by_source:" + rec["subject_source"]] += 1
            if rec["searchable"]:
                counts["subjects_searchable"] += 1
            later = [h for h in rec["hits"] if h["relation"] == "later" and not h["flags"]]
            counts["hits_flagged"] += sum(1 for h in rec["hits"] if h["flags"])
            if rec["hits"]:
                counts["subjects_with_any_hit"] += 1
            if later:
                counts["subjects_with_later_hit"] += 1
                counts["subjects_with_later_hit_by_type:" + rec["type"]] += 1
                if not any(h["cites_subject_number"] for h in later):
                    counts["subjects_with_later_hit_not_citing_number"] += 1
            counts["hits"] += len(rec["hits"])
            counts["hits_later"] += len(later)
    # One row per distinct (subject, other order) with a later-or-undated match: claim-kit's pair input.
    edges = []
    frag_items = collections.defaultdict(list)
    for rec in links:
        seen = set()
        offered = [h for h in rec["hits"] if h["relation"] != "earlier" and not h["flags"]]
        if len({h["instrument_id"] for h in offered}) > MAX_LEADS_PER_SUBJECT:
            counts["subjects_with_too_many_leads_to_attach"] += 1
            rec["leads_not_attached"] = (f"{len({h['instrument_id'] for h in offered})} other orders name this person; "
                                         f"more than {MAX_LEADS_PER_SUBJECT}, so none is attached as a lead; read NAME_LINKS.jsonl")
            for c in coverage:
                if c["instrument_id"] == rec["instrument_id"]:
                    c["note"] += "; " + rec["leads_not_attached"]
            continue
        for h in offered:
            if h["instrument_id"] in seen:
                continue
            seen.add(h["instrument_id"])
            qualifier = (f"names {h['name']}" + ("; cites this order by number" if h["cites_subject_number"] else
                                                "; does not cite this order by number") +
                         f"; relation by date: {h['relation']}" +
                         ("; " + ", ".join(h["cautions"]) if h["cautions"] else ""))
            edges.append({
                "edge_id": "NM-" + hashlib.sha256((rec["instrument_id"] + ">" + h["instrument_id"]).encode()).hexdigest()[:12],
                "acting_id": h["instrument_id"], "target_id": rec["instrument_id"], "target_in_universe": "yes",
                "mechanism": MECHANISM, "qualifier": qualifier, "date_candidate": h["date"],
                "date_basis": "acting order date from the project's date indexes (eo_identity.load_dates)",
                "evidence_type": "held_text_name_match", "source_url": h["source"]["url"],
                "source_sha256": h["source"]["sha256"], "text_path": h["source"]["text_path"],
                "text_sha256": h["source"]["text_sha256"], "page_or_item": h["source"]["page_or_item"],
                "quote_kind": "verbatim_text_snippet", "quote_span": f"{h['char_start']}-{h['char_end']}",
                "quote": h["snippet"],
            })
            frag_items[rec["instrument_id"]].append({
                "actor": h["instrument_id"], "date_candidate": h["date"], "mechanism": MECHANISM,
                "qualifier": qualifier, "date_basis": ["acting order date from the project's date indexes"],
                "edge_ids": [edges[-1]["edge_id"]], "evidence_types": ["held_text_name_match"],
                "flags": ["name_match_lead", "text_only_unverified"] + ([] if h["cites_subject_number"] else ["does_not_cite_subject_number"]),
                "quote": h["snippet"], "quote_kind": "verbatim_text_snippet",
                "matched_name": h["matched"], "char_start": h["char_start"], "char_end": h["char_end"],
                "source": {"sha256": h["source"]["sha256"], "url": h["source"]["url"],
                           "page_or_item": h["source"]["page_or_item"], "text_path": h["source"]["text_path"],
                           "text_sha256": h["source"]["text_sha256"], "grade": h["source"]["grade"]},
            })
    cols = ["edge_id", "acting_id", "target_id", "target_in_universe", "mechanism", "qualifier", "date_candidate",
            "date_basis", "evidence_type", "source_url", "source_sha256", "text_path", "text_sha256", "page_or_item",
            "quote_kind", "quote_span", "quote"]
    with open(os.path.join(out, "NAME_LINKS.jsonl"), "w", encoding="utf-8") as fh:
        for rec in links:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    with open(os.path.join(out, "SEARCH_COVERAGE.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["instrument_id", "search_id", "covered", "note"])
        w.writeheader()
        w.writerows(coverage)
    with open(os.path.join(out, "EDGES.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(edges)
    note = ("Machine name-match leads: the acting order's held text contains the full name of the person this "
            "order concerns. It may extend, modify, revoke, confirm or merely mention that person, or concern a "
            "different person of the same name. date_candidate is the acting order's indexed date, not an effective "
            "date. Read the cited text at the quoted span before using it; it is never an ending by itself.")
    with open(os.path.join(out, "FRAGMENTS.jsonl"), "w", encoding="utf-8") as fh:
        for iid in sorted(frag_items, key=E.parse_eo_id):
            fh.write(json.dumps({"instrument_id": iid, "kind": "later_event_candidates", "produced_by": "namier",
                                 "confidence_note": note, "data": frag_items[iid]}, ensure_ascii=False) + "\n")
    counts["edges"] = len(edges)
    counts["orders_with_fragments"] = len(frag_items)
    summary = {
        "job": "namier", "generated_utc": started, "legal_cutoff": LEGAL_CUTOFF,
        "subject_types": sorted(SUBJECT_TYPES), "subjects_source": [TYPES_CSV, "index titles (eo_identity.load_dates)"],
        "texts_read": len(corpus.texts), "orders_with_held_text": len(corpus.by_iid),
        "counts": dict(sorted(counts.items())),
        "machine_searches": [search_record],
        "legal_conclusions": 0, "statuses_changed": 0, "network_requests": 0,
        "notice": "Leads only. A name match is not an identity authentication, a date, an ending or a status.",
    }
    with open(os.path.join(out, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
    return summary


def run(root, out):
    started = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    print("namier: loading fragments and dates", flush=True)
    fragments = E.load_fragments(root)
    dates = E.load_dates(root, fragments)
    print(f"namier: reading held texts for {len(fragments)} orders", flush=True)
    corpus = Corpus(root, fragments)
    print(f"namier: {len(corpus.texts)} texts for {len(corpus.by_iid)} orders; indexing done", flush=True)
    subjects = load_subjects(root, fragments, dates)
    print(f"namier: {len(subjects)} one-person orders to search", flush=True)
    links, coverage = search(corpus, subjects, dates)
    record = coverage_entry(corpus, fragments, subjects, coverage, started[:10])
    summary = write_outputs(out, root, links, coverage, record, corpus, dates, started)
    print(json.dumps(summary["counts"], indent=1), flush=True)
    return summary


if __name__ == "__main__":
    run(os.environ.get("REPO_ROOT", os.path.join(HERE, "..", "..")),
        os.environ.get("OUTPUT_DIR", os.path.join(HERE, "output")))
