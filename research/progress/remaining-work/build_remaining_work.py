"""Remaining work to reach a ready-for-human-review lifecycle account of every
executive order the American Presidency Project (APP) counts.

Reads committed outputs only (no network):
  jobs/readiness-tracker/output/READINESS_BY_ORDER.csv   per-order step state
  jobs/app-executive-orders/output/STATISTICS.csv         APP counts by president
  jobs/app-executive-orders/output/INDEX.csv              APP president per numbered EO
  jobs/numbered-early-orders/data/TARGETS.csv             WPA 1944 year for EO 1-5075
  research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv  projected year
  research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv dates of 18 unnumbered

Unit of work: one open step for one order ("order-step"). Steps are the
readiness tracker's own. Orders APP counts but the project does not hold yet
(APP count minus project orders, per president, when positive) each get one
"find and admit to the census" step plus the six core steps. Steps are not
equal effort; this measures how much is open, not hours.

Writes REMAINING_WORK.json, REMAINING_WORK_BY_PRESIDENT.csv and
REMAINING_WORK_LONG.csv (one row per president and kind of work; the two
small source-retrieval steps are folded into one kind) next to this file.
"""
import bisect, csv, json, re, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TRACKER = ROOT / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
STATS = ROOT / "jobs/app-executive-orders/output/STATISTICS.csv"
INDEX = ROOT / "jobs/app-executive-orders/output/INDEX.csv"
TARGETS = ROOT / "jobs/numbered-early-orders/data/TARGETS.csv"
PROJ = ROOT / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
NARA_UN = ROOT / "research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv"

STEPS = ["admit", "provisional_status", "original_text", "clause_inventory",
         "ending_or_current_basis", "savings_residuals", "counterevidence",
         "shared_sources", "opus_media"]
CORE = ["provisional_status", "original_text", "clause_inventory",
        "ending_or_current_basis", "savings_residuals", "counterevidence"]

# APP statistics names -> one key per president (Cleveland's terms merged,
# Trump's kept apart as APP does).
def pkey(name):
    n = re.sub(r"\s*\((?:[A-Z-]+|\d\w+ Term)\)\s*$", "", name).strip()
    n = n.replace("Harry S Truman", "Harry S. Truman").replace("Chester A. Arthur", "Chester Arthur")
    n = n.replace("James A. Garfield", "James Garfield")
    if n.startswith("Grover Cleveland"):
        return "Grover Cleveland"
    if "2nd Term" in name or n.endswith("- II"):
        return "Donald J. Trump II"
    if "1st Term" in name or n.endswith("- I") and "Trump" in n:
        return "Donald J. Trump I"
    return n

def num(iid):
    m = re.match(r"EO:(\d+)", iid)
    return int(m.group(1)) if m else None

# Start of each presidency (date of taking office).
TERMS = [("1789-04-30", "George Washington"), ("1797-03-04", "John Adams"),
         ("1801-03-04", "Thomas Jefferson"), ("1809-03-04", "James Madison"),
         ("1817-03-04", "James Monroe"), ("1825-03-04", "John Quincy Adams"),
         ("1829-03-04", "Andrew Jackson"), ("1837-03-04", "Martin van Buren"),
         ("1841-03-04", "William Henry Harrison"), ("1841-04-04", "John Tyler"),
         ("1845-03-04", "James K. Polk"), ("1849-03-05", "Zachary Taylor"),
         ("1850-07-09", "Millard Fillmore"), ("1853-03-04", "Franklin Pierce"),
         ("1857-03-04", "James Buchanan"), ("1861-03-04", "Abraham Lincoln"),
         ("1865-04-15", "Andrew Johnson"), ("1869-03-04", "Ulysses S. Grant"),
         ("1877-03-04", "Rutherford B. Hayes"), ("1881-03-04", "James Garfield"),
         ("1881-09-19", "Chester Arthur"), ("1885-03-04", "Grover Cleveland"),
         ("1889-03-04", "Benjamin Harrison"), ("1893-03-04", "Grover Cleveland"),
         ("1897-03-04", "William McKinley"), ("1901-09-14", "Theodore Roosevelt"),
         ("1909-03-04", "William Howard Taft"), ("1913-03-04", "Woodrow Wilson"),
         ("1921-03-04", "Warren G. Harding"), ("1923-08-02", "Calvin Coolidge"),
         ("1929-03-04", "Herbert Hoover"), ("1933-03-04", "Franklin D. Roosevelt"),
         ("1945-04-12", "Harry S. Truman"), ("1953-01-20", "Dwight D. Eisenhower"),
         ("1961-01-20", "John F. Kennedy"), ("1963-11-22", "Lyndon B. Johnson"),
         ("1969-01-20", "Richard Nixon"), ("1974-08-09", "Gerald R. Ford"),
         ("1977-01-20", "Jimmy Carter"), ("1981-01-20", "Ronald Reagan"),
         ("1989-01-20", "George Bush"), ("1993-01-20", "William J. Clinton"),
         ("2001-01-20", "George W. Bush"), ("2009-01-20", "Barack Obama"),
         ("2017-01-20", "Donald J. Trump I"), ("2021-01-20", "Joseph R. Biden, Jr."),
         ("2025-01-20", "Donald J. Trump II")]
TERM_DATES = [d for d, _ in TERMS]
MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}

def by_date(iso):
    return TERMS[bisect.bisect_right(TERM_DATES, iso) - 1][1]

def by_year(y):
    """President in office for most of year y."""
    return by_date(f"{y}-07-01")

def wpa_date(year, month_day):
    m = re.match(r"([A-Za-z]+)\.?\s*(\d+)", month_day or "")
    if not (year.isdigit() and m and m.group(1)[:3].lower() in MONTHS):
        return None
    return f"{year}-{MONTHS[m.group(1)[:3].lower()]:02d}-{int(m.group(2)):02d}"

def main():
    tracker = list(csv.DictReader(open(TRACKER)))
    stats = [r for r in csv.DictReader(open(STATS)) if r["term"] == "Total"]
    app = collections.Counter()
    order = []
    for r in stats:
        k = pkey(r["president"])
        if k not in app:
            order.append(k)
        app[k] += int(r["total_orders"].replace(",", ""))

    # President per project order, best evidence first: APP's own attribution;
    # an exact date (WPA 1944 list, NARA codification row, Lord row id); the
    # nearest numbered neighbours when both sides agree (numbers run in date
    # order); the year alone.
    pres, how = {}, {}
    for r in csv.DictReader(open(INDEX)):
        if r["instrument_id"] and r["instrument_id"] not in pres:
            pres[r["instrument_id"]] = pkey(r["president"]); how[r["instrument_id"]] = "app_index"
    exact, year = {}, {}
    for r in csv.DictReader(open(PROJ)):
        if r["date_effective"].isdigit():
            year[r["id"]] = int(r["date_effective"])
    for r in csv.DictReader(open(TARGETS)):
        if r["year"].isdigit():
            year[r["instrument_id"]] = int(r["year"])
        d = wpa_date(r["year"], r["month_day"])
        if d:
            exact[r["instrument_id"]] = d
    for r in csv.DictReader(open(NARA_UN)):
        exact[r["instrument_id"]] = r["reference_date"]
    for r in tracker:
        m = re.search(r"(\d{4}-\d{2}-\d{2})$", r["instrument_id"])
        if m:
            exact.setdefault(r["instrument_id"], m.group(1))
    for r in tracker:
        iid = r["instrument_id"]
        if iid not in pres and iid in exact:
            pres[iid] = by_date(exact[iid]); how[iid] = "exact_date"
    anchored = sorted((num(i), i) for i in pres if num(i) is not None)
    keys = [n for n, _ in anchored]
    for r in tracker:
        iid = r["instrument_id"]; n = num(iid)
        if iid in pres or n is None:
            continue
        i = bisect.bisect_left(keys, n)
        lo = pres[anchored[i - 1][1]] if i > 0 else None
        hi = pres[anchored[i][1]] if i < len(keys) else None
        if lo and lo == hi:
            pres[iid] = lo; how[iid] = "numbered_neighbours"
        elif iid in year:
            pres[iid] = by_year(year[iid]); how[iid] = "year_only"
        else:
            pres[iid] = lo or hi; how[iid] = "nearest_neighbour"
    for r in tracker:
        if r["instrument_id"] not in pres:
            pres[r["instrument_id"]] = "Unattributed"; how[r["instrument_id"]] = "none"
    source = collections.Counter(how[r["instrument_id"]] for r in tracker)

    work = collections.defaultdict(collections.Counter)   # president -> step -> open count
    done = collections.Counter()
    held = collections.Counter(); ready = collections.Counter(); prov = collections.Counter()
    for r in tracker:
        p = pres[r["instrument_id"]]
        held[p] += 1
        ready[p] += r["ready_for_human_review"] == "yes"
        prov[p] += r["provisional_status"] in ("yes", "no")
        for s in STEPS[1:]:
            if r["step_" + s] == "open":
                work[p][s] += 1
            elif r["step_" + s] == "done":
                done[p] += 1
    gap = {}
    for p in order:
        g = max(0, app[p] - held[p])
        gap[p] = g
        if g:
            work[p]["admit"] += g
            for s in CORE:
                work[p][s] += g

    rows = []
    for p in order + [p for p in held if p not in app]:
        rows.append({"president": p, "app_count": app.get(p, 0), "project_orders": held[p],
                     "not_yet_in_project": gap.get(p, 0),
                     "project_above_app": max(0, held[p] - app.get(p, 0)),
                     "provisional_status": prov[p], "ready_for_human_review": ready[p],
                     "open_steps": {s: work[p][s] for s in STEPS if work[p][s]},
                     "open_total": sum(work[p].values()), "done_total": done[p]})
    out = {
        "built_from": {k: str(v.relative_to(ROOT)) for k, v in
                       dict(tracker=TRACKER, app_statistics=STATS, app_index=INDEX,
                            wpa_years=TARGETS, projected_years=PROJ).items()},
        "president_attribution": dict(source),
        "app_total": sum(app.values()),
        "project_orders": len(tracker),
        "not_yet_in_project": sum(gap.values()),
        "ready_for_human_review": sum(ready.values()),
        "provisional_status": sum(prov.values()),
        "open_steps_by_kind": {s: sum(w[s] for w in work.values()) for s in STEPS},
        "open_total": sum(sum(w.values()) for w in work.values()),
        "done_total": sum(done.values()),
        "presidents": rows,
    }
    (HERE / "REMAINING_WORK.json").write_text(json.dumps(out, indent=1) + "\n")
    with open(HERE / "REMAINING_WORK_BY_PRESIDENT.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["president", "app_count", "project_orders", "not_yet_in_project",
                    "project_above_app", "has_provisional_status", "ready_for_human_review",
                    "open_total", "done_total"] + ["open_" + s_ for s_ in STEPS])
        for r in rows:
            w.writerow([r[k] for k in ["president", "app_count", "project_orders",
                        "not_yet_in_project", "project_above_app", "provisional_status",
                        "ready_for_human_review", "open_total", "done_total"]]
                       + [r["open_steps"].get(s, 0) for s in STEPS])
    kinds = {"admit": "Find and admit to the census",
             "provisional_status": "First yes/no on whether in effect",
             "original_text": "Save an official copy of the text",
             "clause_inventory": "List every operative clause",
             "ending_or_current_basis": "Prove how it ended or what keeps it in force",
             "savings_residuals": "Close parts that outlive it",
             "counterevidence": "Search later law for contrary sources",
             "shared_sources": "Retrieve cited sources and evidence images",
             "opus_media": "Retrieve cited sources and evidence images"}
    with open(HERE / "REMAINING_WORK_LONG.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["president_order", "president", "step_order", "kind", "open_steps",
                    "app_count", "project_orders", "ready_for_human_review"])
        for i, r in enumerate(rows, 1):
            merged = collections.Counter()
            for s_ in STEPS:
                merged[kinds[s_]] += r["open_steps"].get(s_, 0)
            for j, k in enumerate(dict.fromkeys(kinds.values()), 1):
                if merged[k]:
                    w.writerow([i, r["president"], j, k, merged[k], r["app_count"],
                                r["project_orders"], r["ready_for_human_review"]])
    print(json.dumps({k: v for k, v in out.items() if k != "presidents"}, indent=1))

if __name__ == "__main__":
    main()
