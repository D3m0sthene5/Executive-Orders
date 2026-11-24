"""Classify every ProQuest unnumbered record for 1789-1936 by kind of document and match it against the census.

Input: PQ_UNNUMBERED_1789_1936.psv (cis_accession|date as printed|signed S/N|administration|title).
Census sources, all read from the repository: the reconciled inventory and findings of the Graunt audit, the
audited unnumbered series, the Lord-seeded unnumbered register and the numbered domesday register.
Output: PQ_UNNUMBERED_CLASSIFIED.psv, CANDIDATES_MISSING.csv and CLASSIFY_SUMMARY.json in this folder.
Deterministic; no network.  Run from the repository root:  python3 -I <this file>
"""
import csv, json, re, collections, datetime, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
HERE = os.path.join(ROOT, "research/petty-census-closure-2026-11-24/proquest-scan")
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                      "September", "October", "November", "December"], 1)}

# Kind codes. L and O are the kinds normally counted as executive orders; the rest are other presidential papers.
KINDS = {
    "X": "Attachment, map or correspondence filed with another record (not a separate document)",
    "L": "Land order: withdrawal, reservation, restoration, modification, land sale or land-office order",
    "O": "Other operative order, rule, regulation or directive",
    "N": "NRA code of fair competition, or its amendment, approval or exemption",
    "R": "Request to the Reconstruction Finance Corporation",
    "E": "Exception to the arms-export prohibition for one shipment",
    "V": "Commission for one private armed vessel",
    "S": "Public land sale proclamation, postponement or land-office notice",
    "Q": "Proclamation (extra session, thanksgiving and the like)",
    "I": "Interpretation of a land order (almost all not signed by the President)",
    "A": "Appointment, designation, promotion or assignment of a person",
    "P": "Pardon, commutation, remission, respite or amnesty",
    "T": "Treaty, convention, agreement or protocol",
    "F": "Approval of a fund allotment, transfer or payment",
    "M": "Pass, permit, discharge, dismissal, sentence or other action on one person",
    "C": "Letter of instruction",
    "B": "Official Bulletin compilation",
    "U": "Unclassified by the title rules",
}
RULES = [  # first match wins; patterns run against the title
    ("X", r"^\s*\[?related (map|correspondence|general orders)|: \[related (map|correspondence|general orders|documents?|papers)[^\]]*\]\s*$"),
    ("B", r"official bulletin|^miscellaneous actions"),
    ("I", r"^interpretation no"),
    ("N", r"code of fair competition|^code of|supplementary code|national industrial recovery|^approval of (the )?code|\bNRA\b|"
          r"^exemption .*code|^order .*code of fair|^modification of .*code|^stay of .*code|^termination of .*code"),
    ("R", r"reconstruction finance"),
    ("E", r"^exception to arms export"),
    ("V", r"^private armed vessel"),
    ("P", r"\bpardon|commutation|\bremission|\brespite|amnesty|^clemency|^restoration of (civil|citizenship)|"
          r"mitigat(ing|ion) .*sentence|stay of execution|suspension of (the )?(death )?sentence|"
          r"disability removal|annull?ing (the )?sentence"),
    ("T", r"\btreaty|\bconvention\b|^agreement|\bprotocol\b|^articles of|parcel post|^arbitration|money order|"
          r"^[^:\[]{2,45}: [^:\[]*, (jan|feb|mar|apr|may|june?|july?|aug|sept?|oct|nov|dec)[a-z]*\.? \d{1,2}, \d{4}$|"
          r"^declaration (between|of the)|^arrangement (between|with)|^exchange of notes|: agreement\b"),
    ("A", r"^appointment|^appoints? [a-z]+ [a-z]|^temporary appointment|^designation of (?!.*(district|lands|township|"
          r"reservation|port|ports|site))|^designating [a-z]+ [a-z]|designated to (perform|act)|^nomination|^promotion|"
          r"^assignment of|^reappointment|to (act|serve) as\b|^acting secretary|^removal of (mr\.? )?[a-z.]+ [a-z. ]+ as |"
          r"approv\w* (the )?(re-?)?appointment|^re-?appoints|^requests? (a )?commissions?|^requests a temporary|^designates|"
          r"be retired$|^transfer of .*(surgeon|clerk|officer|lieutenant|captain) |board of visitors"),
    ("M", r"^pass for|^passport for|^permit for|cotton permit|^permission for|permission to return|^discharge|dismissal|"
          r"^removal of disability|^approval of (the )?sentence|^revocation of (discharge|dismissal|dishonorable)|"
          r"^restoration to (duty|rank)|^denial of|^leave of absence for|^reinstatement of|^acceptance of resignation|"
          r"^resignation|^retirement of|^exemption of [a-z]+ [a-z]|^order for release|^release of|^refuses release|"
          r"^military record of|^orders? confining|^order concerning (mr|mrs|miss|capt|lt|gen|col|maj)"),
    ("S", r"public land sale|\bland sales?\b|^sales? at|^sale at|^sale of (alternate|public)|^announc\w* .*sale|"
          r"^postpone\w* .*sale|^defer\w* .*sale|^notice\b|^announcement of public"),
    ("Q", r"^proclamation|extra session|thanksgiving|day of (fasting|prayer|thanksgiving)"),
    ("L", r"power site|coal land|coal reserve|petroleum|phosphate|potash|oil shale|public water|reservoir site|"
          r"stock driveway|helium|water power designation|withdrawal|withdrawing|restoration|reservation|reserve\b|reserves\b|"
          r"land office|\\bland district|public lands?|order of modification|"
          r"lighthouse|light-house|bird refuge|game refuge|wildlife refuge|national monument|national forest|"
          r"naval radio|^enlargement|^reduction|^diminution|^addition to|^extension of .*(reservation|forest|reserve)|"
          r"survey(or)? general|townsite|town site|military post|cemetery|mineral lands|lead mines|^grant of land|"
          r"lands acquired|storage project|^(alaska|arizona|arkansas|california|colorado|dakota|florida|idaho|illinois|"
          r"indiana|iowa|kansas|louisiana|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new mexico|"
          r"north dakota|ohio|oklahoma|oregon|south dakota|utah|washington|wisconsin|wyoming)( territory)?\b|"
          r"^[a-z .'-]+ (river|creek|lake|reservoir), [a-z ]+$"),
    ("F", r"allotment|^approves national|^approval of (a |the )?(funds?|national security|transfer|payment|purchase|"
          r"expenditure|credit)|^transfer of (funds|appropriation)|^payment|refund|emergency fund|^apportionment|"
          r"^appropriation (of money|to account)|^approval of appropriation|credit to (the )?account|settlement of accounts"),
    ("C", r"^instructions?\b|^to (the )?[a-z]+|^letter to|^memorandum to|^message to|^[a-z]+ to [a-z.]+ [a-z.]+ ?[a-z]*, "
          r"(secretary|attorney|postmaster|director|chairman|administrator|governor)"),
    ("O", r"."),  # anything left that is a positive instruction is an operative order
]
RULES = [(k, re.compile(p, re.I)) for k, p in RULES]
NOT_OPERATIVE = re.compile(r"^(notice of|announcement of|proclamation)", re.I)  # notices are still kept as L/O; flagged

STOP = set("""the of and for to in a an at on by with from as or be is are its into under upon certain lands land
other its their his her this that which such all any no nos said order orders executive president united states
u s us department secretary related includes including supporting correspondence map accompanied""".split())


def iso(printed):
    m = re.match(r"(\w+) (\d+), (\d{4})", printed.strip())
    if not m or m[1] not in MONTHS:
        return ""
    return f"{m[3]}-{MONTHS[m[1]]:02d}-{int(m[2]):02d}"


def norm_date(s):
    s = (s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    return m.group(0) if m else ""


def stem(w):
    for suf in ("ings", "ing", "ions", "ion", "ed", "es", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            w = w[: -len(suf)]
            break
    return w[:6]


def tokens(s):
    s = (s or "").lower().replace("''", " ").replace('"', " ")
    return {stem(w) for w in re.findall(r"[a-z][a-z'-]{2,}|\d+", s) if w not in STOP}


def numbers(s):
    return set(re.findall(r"\bno\.?\s*(\d+)", (s or "").lower()))


LETTER = re.compile(r"^(?:to|order concerning|endorsement concerning|[a-z]+ to) [^:\[]{2,80}: \[(.+?)\]?\s*$", re.I)


def kind_of(title):
    """A letter or endorsement ("To Edwin M. Stanton: [appoints ...]") takes the kind of its bracketed summary; a
    letter whose summary gives an instruction stays a letter of instruction (C), as in the hand-coded sample."""
    m = LETTER.match(title)
    if m:
        k = kind_of(m[1])
        return "C" if k == "O" else k
    for k, rx in RULES:
        if rx.search(title):
            return k
    return "U"


def census_index():
    """date -> list of (source, id, subject) from every census layer."""
    idx = collections.defaultdict(list)

    def add(src, ident, date, subj):
        d = norm_date(date)
        if d:
            idx[d].append((src, ident, subj or ""))

    def rows(path):
        with open(os.path.join(ROOT, path), encoding="utf-8-sig", newline="") as f:
            yield from csv.DictReader(f)

    for r in rows("research/graunt-census-audit-2026-11-12/EO_reconciled_inventory.csv"):
        add("reconciled", r["id"], r["date"], r["subject"])
    for r in rows("research/graunt-census-audit-2026-11-12/FINDINGS.csv"):
        add("findings", r["Finding ID"], r["Date / date claim"], r["Subject"] + " " + r["Notes and reconciliation"][:300])
    for r in rows("jobs/domesday-register/data/GRAUNT_UNNUMBERED.csv"):
        add("graunt", r["graunt_id"], r["date"], r["subject"])
    for r in rows("jobs/domesday-register/output/UNNUMBERED.csv"):
        add("lord", r["unnumbered_id"], r["date"], r["subject"])
    for r in rows("jobs/domesday-register/output/REGISTER.csv"):
        add("numbered", r["instrument_id"], r["date"], r["title"])
    return idx


GENERIC = set("""withdrawal withdrawing withdrawn withdraw reserve reserves reserved restoration restoring restored public water
power site sites coal petroleum phosphate potash oil shale reservoir modification modifying reservation reservations
military indian lighthouse purposes establishment establishing established enlargement enlarging national forest
classification designation temporary lands sale sales office district approval approving approved amendment amending
alaska arizona arkansas california colorado dakota florida idaho illinois indiana iowa kansas louisiana michigan
minnesota mississippi missouri montana nebraska nevada new mexico north south ohio oklahoma oregon utah washington
wisconsin wyoming territory river creek county""".split())
GENERIC = {stem(w) for w in GENERIC}


SERIES = [(k, re.compile(p, re.I)) for k, p in [
    ("CLW", r"coal land withdrawal|coal withdrawal"), ("CLR", r"coal land restoration|coal restoration"),
    ("CR", r"coal reserve"), ("PRR", r"petroleum restoration"), ("PR", r"petroleum reserve"),
    ("PHRR", r"phosphate restoration"), ("PHR", r"phosphate reserve"), ("POTRR", r"potash restoration"),
    ("POTR", r"potash reserve"), ("PWRR", r"public water restoration"), ("PWR", r"public water reserve"),
    ("OSR", r"oil shale reserve"), ("RSRR", r"reservoir site restoration"), ("RSR", r"reservoir site reserve"),
    ("AW", r"alaskan? withdrawal"), ("PSC", r"power site classification"), ("WPD", r"water power designation"),
    ("TPW", r"temporary power site withdrawal"), ("PSRR", r"power[- ]site restoration|^order of restoration no"),
    ("PSM", r"power[- ]site modification"), ("PSR", r"power[- ]site reserve"), ("SD", r"stock driveway"),
    ("HR", r"helium reserve")]]
STATES = re.compile(r"\b(alaska|arizona|arkansas|california|colorado|florida|idaho|illinois|kansas|louisiana|michigan|"
                    r"minnesota|mississippi|missouri|montana|nebraska|nevada|new mexico|north dakota|south dakota|ohio|"
                    r"oklahoma|oregon|utah|washington|wisconsin|wyoming|alabama)\b", re.I)
GENERIC = set("""withdrawal withdrawing withdrawn withdraw reserve reserves reserved restoration restoring restored public water
power site sites coal petroleum phosphate potash oil shale reservoir modification modifying reservation reservations
military indian lighthouse purposes establishment establishing established enlargement enlarging national forest
classification designation temporary lands sale sales office district approval approving approved amendment amending
alaska arizona arkansas california colorado dakota florida idaho illinois indiana iowa kansas louisiana michigan
minnesota mississippi missouri montana nebraska nevada new mexico north south ohio oklahoma oregon utah washington
wisconsin wyoming territory river creek county""".split())
GENERIC = {stem(w) for w in GENERIC}


def series_keys(text):
    """[(series code, numbers that follow the series phrase)] plus the states named."""
    out = []
    for code, rx in SERIES:
        for m in rx.finditer(text):
            tail = text[m.end():m.end() + 120]
            tail = re.split(r"(?i)(?:coal|petroleum|phosphate|potash|public water|power[- ]site|reservoir|oil shale)", tail)[0]
            nums = {int(x) for x in re.findall(r"\d+", tail) if int(x) < 1789}
            if code.startswith("PS") and "identifiers" in tail:
                nums |= {int(x) for x in re.findall(r"\d+", text[m.end():]) if int(x) < 1789}
            out.append((code, nums))
    # a restoration series phrase also contains the reserve phrase ("Public Water Restoration"); keep the longest
    codes = {c for c, _ in out}
    out = [(c, n) for c, n in out if not (c + "R" in codes or (c == "PSR" and "PSRR" in codes and not n))]
    return out, {s.lower() for s in STATES.findall(text)}


def match(idx, date, title, kind="L"):
    """M: the same act is in the census.  G: the census holds an order of the same land series on that date, but not
    this one by number, so the record may be part of an order the census counts once.  D: the date carries other
    census entries.  U: nothing in the census on that date.

    Land-series records match by series and number (and state, where both name one) within seven days.  Other records
    match when the subjects share at least two distinctive words on the same date, or three within seven days.  A
    land record that shares one distinctive word with a census entry on its date is put in G.
    """
    if not date:
        return "U", ""
    sk, st_q = series_keys(title)
    t = tokens(title) - GENERIC
    same = idx.get(date, [])
    d0 = datetime.date.fromisoformat(date)
    best, group = (0, ""), ""
    for delta in range(-7, 8):
        d = (d0 + datetime.timedelta(days=delta)).isoformat()
        for src, ident, subj in idx.get(d, []):
            if sk:
                ck, st_c = series_keys(subj)
                for code, nums in sk:
                    for c2, n2 in ck:
                        if code != c2:
                            continue
                        if nums & n2 and not (st_q and st_c and not (st_q & st_c)):
                            if 10 > best[0]:
                                best = (10 - abs(delta), f"{src}:{ident}")
                        elif delta == 0 and not group:
                            group = f"{src}:{ident}"
                continue
            score = len(t & tokens(subj))
            if score >= (2 if delta == 0 else 3) and score > best[0]:
                best = (score, f"{src}:{ident}")
            elif score == 1 and delta == 0 and kind == "L" and not group:
                group = f"{src}:{ident}"
    if best[0]:
        return "M", best[1]
    if group:
        return "G", group
    if sk and any(c.startswith("PS") for c, _ in sk) and any(re.search(r"power", s, re.I) for _, _, s in same):
        return "G", next(f"{a}:{b}" for a, b, s in same if re.search(r"power", s, re.I))
    return ("D", "") if same else ("U", "")


def main():
    src = os.path.join(HERE, "PQ_UNNUMBERED_1789_1936.psv")
    recs = [l.rstrip("\n").split("|", 4) for l in open(src, encoding="utf-8") if l.strip() and not l.startswith("cis_accession|")]
    idx = census_index()
    out, seen_order = [], {}
    for acc, printed, signed, admin, title in recs:
        date = iso(printed)
        k = kind_of(title)
        dup_of = ""
        key = (date, re.sub(r":\s*\[[^\]]*\]\s*$", "", title).lower().strip(" .")) if k != "X" else None
        if key:
            sk, sts = series_keys(title)
            key2 = (date, frozenset((c, frozenset(n)) for c, n in sk), frozenset(sts)) if sk and any(n for _, n in sk) else None
            for kk in (key, key2):
                if kk and kk in seen_order:
                    dup_of = seen_order[kk]
                    break
            for kk in (key, key2):
                if kk and kk not in seen_order:
                    seen_order[kk] = dup_of or acc
        m, via = match(idx, date, title, k) if k in "LO" and not dup_of else ("", "")
        out.append(dict(acc=acc, date=date, signed=signed, admin=admin, kind=k, dup_of=dup_of, match=m, via=via,
                        notice="y" if NOT_OPERATIVE.search(title) else "", title=title))
    with open(os.path.join(HERE, "PQ_UNNUMBERED_CLASSIFIED.psv"), "w", encoding="utf-8") as f:
        f.write("cis_accession|date|signed|administration|kind|second_copy_of|match|matched_census_id|notice|title\n")
        for r in out:
            f.write("|".join(r[c] for c in ["acc", "date", "signed", "admin", "kind", "dup_of", "match", "via",
                                            "notice", "title"]) + "\n")
    cand = [r for r in out if r["kind"] in "LO" and not r["dup_of"] and r["match"] in ("D", "U")]
    with open(os.path.join(HERE, "CANDIDATES_MISSING.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cis_accession", "date", "signed_by_president", "administration", "kind", "census_on_date",
                    "notice_only", "title"])
        for r in cand:
            w.writerow([r["acc"], r["date"], r["signed"], r["admin"], r["kind"],
                        "other entries" if r["match"] == "D" else "none", r["notice"], r["title"]])
    # summary
    era = lambda d: "1789-1861" if d < "1862" else ("1862-1906" if d < "1907" else "1907-1936")
    S = {"records_read": len(out), "kinds": {}, "lo_by_era": {}, "kind_labels": KINDS}
    for k in KINDS:
        sel = [r for r in out if r["kind"] == k]
        S["kinds"][k] = {"records": len(sel), "signed": sum(r["signed"] == "S" for r in sel),
                         "second_copies": sum(bool(r["dup_of"]) for r in sel)}
    for e in ["1789-1861", "1862-1906", "1907-1936"]:
        sel = [r for r in out if r["kind"] in "LO" and not r["dup_of"] and r["date"] and era(r["date"]) == e]
        c = collections.Counter((r["match"], r["signed"]) for r in sel)
        S["lo_by_era"][e] = {f"{m}_{s}": c[(m, s)] for m in "MGDU" for s in "SN"}
    tot = collections.Counter((r["match"], r["signed"], r["kind"]) for r in out if r["kind"] in "LO" and not r["dup_of"])
    S["lo_totals"] = {f"{k}_{m}_{s}": tot[(m, s, k)] for k in "LO" for m in "MGDU" for s in "SN"}
    S["candidates_missing"] = {"all": len(cand), "signed": sum(r["signed"] == "S" for r in cand),
                               "signed_not_notice": sum(r["signed"] == "S" and not r["notice"] for r in cand)}
    json.dump(S, open(os.path.join(HERE, "CLASSIFY_SUMMARY.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in S.items() if k != "kind_labels"}, indent=1))


if __name__ == "__main__":
    main()
