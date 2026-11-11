"""Bodley: sweep large public collections for U.S. executive orders and match them to the orders that still
lack an accepted official copy.

Named for Thomas Bodley, who rebuilt Oxford's library from copies gathered wherever they could be found.
One thread per site, each with its own polite rate and a robots.txt check. Metadata only: no image or book bytes
are downloaded. Writes only to OUTPUT_DIR; changes no status, count or other job's output. Every hit is a lead
for a person to examine, never a counted witness.
"""
import csv, gzip, json, os, pathlib, re, threading, time, traceback, urllib.parse, urllib.request, urllib.robotparser
from html import unescape

OUT = pathlib.Path(os.environ["OUTPUT_DIR"]); REPO = pathlib.Path(os.environ["REPO_ROOT"])
UA = "EO-history-research-bot/0.1 (low-rate one-off catalogue sweep; metadata only)"
NUM = re.compile(r"\b(?:Executive|Exec\.?|Ex\.)[\s_]+(?:Orders?|Ord\.?)[\s_,]+(?:No\.?|Nos\.?|Number|#)?[\s_]*(\d{1,5}(?:-?[A-Z](?![a-z]))?)\b", re.I)

def eo_numbers(*texts):
    s = set()
    for t in texts:
        for m in NUM.finditer(t or ""):
            n = m.group(1).upper().replace("-", "")
            if 1 <= int(re.match(r"\d+", n).group()) <= 14400: s.add(n)
    return sorted(s)

class Site:
    def __init__(self, name, base, delay, robots=False):
        # robots=True for HTML page scraping; documented APIs (MediaWiki, SPARQL, IA scrape, Google Books, loc.gov JSON)
        # follow their own API etiquette: identified User-Agent, low rate, back-off on 429/maxlag.
        self.name, self.base, self.delay, self.robots = name, base, delay, robots
        self.calls = 0; self.leads = []; self.errors = []; self.notes = []; self.log = []
        self.rp = urllib.robotparser.RobotFileParser(); self.rp.set_url(base.rstrip("/") + "/robots.txt")
        if robots:
            try: self.rp.read()
            except Exception as e: self.notes.append(f"robots.txt unreadable: {e}")
    def allowed(self, url):
        if not self.robots: return True
        try: return self.rp.can_fetch(UA, url)
        except Exception: return True
    def get(self, url, kind="json", tries=8):
        if not self.allowed(url):
            self.notes.append(f"robots.txt disallows {url[:120]}"); return None
        wait = 20
        for i in range(tries):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json" if kind == "json" else "*/*"}), timeout=90) as r:
                    body = r.read().decode("utf-8", "replace")
                self.calls += 1; time.sleep(self.delay)
                return json.loads(body) if kind == "json" else body
            except urllib.error.HTTPError as e:
                if e.code in (400, 403, 404, 410): self.errors.append(f"{e.code} {url[:160]}"); time.sleep(self.delay); return None
                self.say(f"retry {i} {e.code}"); time.sleep(wait); wait = min(wait * 2, 600)
            except Exception as e:
                self.say(f"retry {i} {str(e)[:80]}"); time.sleep(wait); wait = min(wait * 2, 600)
        self.errors.append(f"gave up {url[:160]}"); return None
    def say(self, msg):
        line = f"[{self.name}] {msg}"; self.log.append(line); print(line, flush=True)
    def lead(self, **kw):
        kw.setdefault("eo_numbers", eo_numbers(kw.get("title", ""), kw.get("description", "")[:400]))
        kw["site"] = self.name; self.leads.append(kw)

# ---------------- Wikimedia Commons ----------------
def commons(S):
    api = "https://commons.wikimedia.org/w/api.php?"
    q = lambda **p: S.get(api + urllib.parse.urlencode(dict(p, format="json", formatversion=2, maxlag=5)))
    files, cats = {}, set()
    def walk(cat, depth):
        if cat in cats or depth < 0: return
        cats.add(cat); cont = {}
        while True:
            d = q(action="query", list="categorymembers", cmtitle=cat, cmlimit=500, cmtype="file|subcat", **cont)
            if not d: return
            for m in d["query"]["categorymembers"]:
                if m["ns"] == 14: walk(m["title"], depth - 1)
                elif m["ns"] == 6: files.setdefault(m["title"], cat)
            if "continue" not in d: break
            cont = {"cmcontinue": d["continue"]["cmcontinue"]}
    for c in ["Category:Executive orders of the United States", "Category:US National Archives series: Executive Orders, 1862 - 2016",
              "Category:US National Archives Record Group 11: General Records of the United States Government, 1778 - 2006"]:
        walk(c, 4); S.say(f"{c}: {len(files)} files, {len(cats)} categories")
    for s in ['intitle:"Executive Order"', 'intitle:"Executive Orders"', '"executive order" filemime:application/pdf',
              '"executive orders" filemime:image/vnd.djvu', '"Presidential executive orders"', '"Record Group 11" "executive order"']:
        off = 0
        while True:
            d = q(action="query", list="search", srsearch=s, srnamespace=6, srlimit=500, sroffset=off)
            if not d: break
            for r in d["query"]["search"]: files.setdefault(r["title"], "search: " + s)
            if "continue" not in d or off >= 9500: break
            off = d["continue"]["sroffset"]
        S.say(f"search {s}: {len(files)} files")
    titles = sorted(files)
    for i in range(0, len(titles), 50):
        d = q(action="query", prop="imageinfo", titles="|".join(titles[i:i + 50]), iiprop="url|mime|size|extmetadata",
              iiextmetadatafilter="ImageDescription|DateTimeOriginal|Credit")
        for p in (d or {}).get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata") or {}
            v = lambda k: re.sub(r"<[^>]+>", " ", unescape((md.get(k) or {}).get("value", "")))[:500]
            S.lead(id=p["title"], title=p["title"], url=ii.get("descriptionurl", ""), date=v("DateTimeOriginal"),
                   kind="volume" if ii.get("mime") in ("application/pdf", "image/vnd.djvu") else "image",
                   mime=ii.get("mime", ""), description=v("ImageDescription") + " " + v("Credit"), found_by=files[p["title"]])

# ---------------- Internet Archive ----------------
def internet_archive(S):
    queries = ['title:("executive order" OR "executive orders")', 'subject:("executive orders")', '"presidential executive orders"',
               'title:("proclamations and executive orders")', '"M1118"', '"Record Group 11" AND "executive"',
               'title:("executive orders relating")', 'title:("official U.S. bulletin")', 'title:("civil service act and rules")',
               'creator:("United States. President") AND mediatype:texts AND date:[1862-01-01 TO 1945-12-31]']
    seen = set()
    for qq in queries:
        cursor = None
        for page in range(40):
            p = {"q": qq, "fields": "identifier,title,date,mediatype,collection,description,subject", "count": 1000}
            if cursor: p["cursor"] = cursor
            d = S.get("https://archive.org/services/search/v1/scrape?" + urllib.parse.urlencode(p))
            if not d: break
            for it in d.get("items", []):
                if it["identifier"] in seen: continue
                seen.add(it["identifier"]); txt = lambda k: " ".join(it[k]) if isinstance(it.get(k), list) else str(it.get(k, ""))
                S.lead(id=it["identifier"], title=txt("title"), url="https://archive.org/details/" + it["identifier"],
                       date=txt("date"), kind="volume" if txt("mediatype") == "texts" else txt("mediatype"),
                       mime=txt("mediatype"), description=(txt("description")[:400] + " | " + txt("subject")[:200]), found_by=qq,
                       collection=txt("collection")[:200])
            cursor = d.get("cursor")
            if not cursor: break
        S.say(f"{qq}: {len(seen)} items")

# ---------------- Library of Congress ----------------
def loc(S):
    seen = set()
    for qq in ["executive order", "executive orders", "presidential executive orders", "executive order no", "proclamations and executive orders"]:
        for sp in range(1, 41):
            d = S.get("https://www.loc.gov/search/?" + urllib.parse.urlencode({"q": qq, "fo": "json", "c": 100, "sp": sp, "at": "results,pagination"}))
            if not d or not d.get("results"): break
            for r in d["results"]:
                u = r.get("id") or r.get("url") or ""
                if u in seen: continue
                seen.add(u); title = r.get("title", "") if isinstance(r.get("title"), str) else " ".join(r.get("title") or [])
                desc = " ".join(r.get("description") or []) if isinstance(r.get("description"), list) else str(r.get("description", ""))
                fmt = " ".join(r.get("original_format") or [])
                S.lead(id=u, title=title, url=u, date=str(r.get("date", "")), kind="volume" if "book" in fmt.lower() else (fmt or "item"),
                       mime=fmt, description=desc[:400], found_by=qq, collection=" ".join(r.get("partof") or [])[:200] if isinstance(r.get("partof"), list) else "")
            if not (d.get("pagination") or {}).get("next"): break
        S.say(f"{qq}: {len(seen)} items")

# ---------------- Google Books (public full-view only) ----------------
def google_books(S):
    seen = set()
    for qq in ['intitle:"executive orders"', 'intitle:"executive order"', '"executive order no"', 'intitle:"proclamations and executive orders"',
               'intitle:"executive orders relating"', 'intitle:"civil service act and rules"', 'inauthor:"United States. President" "executive order"']:
        for start in range(0, 400, 40):
            d = S.get("https://www.googleapis.com/books/v1/volumes?" + urllib.parse.urlencode({"q": qq, "filter": "full", "maxResults": 40, "startIndex": start, "printType": "books"}))
            if not d or not d.get("items"): break
            for it in d["items"]:
                if it["id"] in seen: continue
                seen.add(it["id"]); vi = it.get("volumeInfo", {})
                S.lead(id=it["id"], title=(vi.get("title", "") + " " + vi.get("subtitle", "")).strip(), url=vi.get("infoLink", ""),
                       date=vi.get("publishedDate", ""), kind="volume", mime="book", description=(vi.get("description") or "")[:400],
                       found_by=qq, collection=", ".join(vi.get("authors") or [])[:200])
        S.say(f"{qq}: {len(seen)} volumes")

# ---------------- HathiTrust catalog (full view only; robots-checked) ----------------
def hathitrust(S):
    seen = set()
    for qq, typ in [("executive orders", "title"), ("executive order", "title"), ("proclamations executive orders", "title"),
                    ("United States. President. Executive orders", "all"), ("presidential executive orders", "all")]:
        for page in range(1, 31):
            url = "https://catalog.hathitrust.org/Search/Home?" + urllib.parse.urlencode({"lookfor": qq, "type": typ, "ft": "ft", "page": page})
            h = S.get(url, kind="text")
            if not h: break
            recs = re.findall(r'href="/Record/(\d+)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{3,300})<', h)
            if not recs: break
            new = 0
            for rid, title in recs:
                if rid in seen: continue
                seen.add(rid); new += 1
                S.lead(id=rid, title=unescape(title).strip(), url="https://catalog.hathitrust.org/Record/" + rid, date="", kind="volume",
                       mime="catalog record (full view)", description="", found_by=f"{typ}: {qq}")
            if not new: break
        S.say(f"{qq}: {len(seen)} records")

# ---------------- Wikidata ----------------
def wikidata(S):
    qids = set()
    for term in ["United States executive order", "executive order of the President of the United States", "executive order"]:
        d = S.get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({"action": "wbsearchentities", "search": term, "language": "en", "type": "item", "limit": 10, "format": "json"}))
        for e in (d or {}).get("search", []):
            if "executive order" in (e.get("label", "") + " " + e.get("description", "")).lower(): qids.add(e["id"])
    S.notes.append(f"classes tried: {sorted(qids)}")
    for qid in sorted(qids):
        sparql = f"""SELECT ?item ?itemLabel ?ord ?date ?scan ?ws ?full ?img WHERE {{ ?item wdt:P31 wd:{qid} .
          OPTIONAL {{ ?item wdt:P1545 ?ord }} OPTIONAL {{ ?item wdt:P577 ?date }} OPTIONAL {{ ?item wdt:P996 ?scan }}
          OPTIONAL {{ ?item wdt:P1957 ?ws }} OPTIONAL {{ ?item wdt:P953 ?full }} OPTIONAL {{ ?item wdt:P18 ?img }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }} LIMIT 20000"""
        d = S.get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": sparql, "format": "json"}))
        rows = (d or {}).get("results", {}).get("bindings", [])
        for b in rows:
            g = lambda k: b.get(k, {}).get("value", "")
            title = g("itemLabel"); nums = eo_numbers(title)
            if not nums and g("ord").isdigit() and "executive order" in title.lower(): nums = [g("ord")]
            links = " ".join(x for x in [g("scan"), g("ws"), g("full"), g("img")] if x)
            S.lead(id=g("item"), title=title, url=g("item"), date=g("date")[:10], kind="item" + (" with scan/text link" if links else ""),
                   mime="wikidata", description=links, found_by=f"P31 {qid}", eo_numbers=nums)
        S.say(f"class {qid}: {len(rows)} rows")

SITES = [("commons", "https://commons.wikimedia.org", 1.5, commons), ("internet_archive", "https://archive.org", 1.0, internet_archive),
         ("loc", "https://www.loc.gov", 3.5, loc), ("google_books", "https://www.googleapis.com", 1.0, google_books),
         ("hathitrust", "https://catalog.hathitrust.org", 4.0, hathitrust, True), ("wikidata", "https://www.wikidata.org", 2.0, wikidata)]

if os.environ.get("BODLEY_SITES"):  # local testing: a comma list of site names
    SITES = [x for x in SITES if x[0] in os.environ["BODLEY_SITES"].split(",")]

def run(S, fn):
    t0 = time.time()
    try: fn(S)
    except Exception: S.errors.append(traceback.format_exc()[-800:])
    S.seconds = round(time.time() - t0)

sites = []
threads = []
for spec in SITES:
    name, base, delay, fn = spec[:4]
    S = Site(name, base, delay, robots=len(spec) > 4 and spec[4]); sites.append(S)
    t = threading.Thread(target=run, args=(S, fn)); t.start(); threads.append(t)
for t in threads: t.join()

# ---------------- filter non-U.S.-presidential hits and mark what the project already knows ----------------
NOT_US = re.compile(r"philippin|govph|governor[- ]general|civil governor|\bnovel\b|clancy|podcast|state of (?!the union)|"
                    r"illinois|texas|california|new york state|puerto ric|hawaii|guam|royal|crown|canad|australia|"
                    r"\bindia\b|ontario|obama|trump|biden|bush|clinton", re.I)
def foreign(l):
    blob = " ".join(str(l.get(k, "")) for k in ("title", "collection", "description", "mime"))
    return bool(NOT_US.search(blob)) or l.get("mime") in ("audio", "movies", "etree")
known_text = []
for folder in ["research/pre-1937-sources", "research/mabillon", "research/photius", "research/montfaucon", "research/niebuhr",
               "research/dagron", "jobs/photius-free-printings", "jobs/tischendorf-originals", "jobs/hathi-gpo-orders"]:
    for f in (REPO / folder).rglob("*"):
        if f.is_file() and f.suffix in (".md", ".json", ".csv", ".txt", ".py", ".jsonl") and f.stat().st_size < 30_000_000 and "/output/" not in str(f):
            try: known_text.append(f.read_text(errors="ignore"))
            except Exception: pass
known_blob = "\n".join(known_text)
known_tokens = set(re.split(r"[^A-Za-z0-9_.:\-]+", known_blob))
def is_known(l):
    key = str(l.get("id", ""))
    if len(key) <= 5: return False
    cands = {key, key.rsplit("/", 1)[-1], key.replace("File:", ""), str(l.get("url", "")).rstrip("/").rsplit("/", 1)[-1]}
    if any(c and c in known_tokens for c in cands): return True
    if l["site"] == "commons":
        u = key.replace("File:", "").replace(" ", "_")[:40]
        return u in known_blob or key.replace("File:", "")[:40] in known_blob
    return False
print(f"known-source text: {len(known_blob):,} chars, {len(known_tokens):,} tokens", flush=True)
for S in sites:
    for l in S.leads:
        l["not_us_presidential_likely"] = foreign(l)
        l["already_in_project"] = is_known(l)
        if l["not_us_presidential_likely"]: l["eo_numbers_raw"] = l["eo_numbers"]; l["eo_numbers"] = []

# ---------------- match against the gaps ----------------
need = {}
with open(REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", newline="") as fh:
    for r in csv.DictReader(fh):
        m = re.fullmatch(r"EO:(\d+[A-Z]?)", r["instrument_id"])
        if m:
            bl = {x.split(":")[0] for x in r["blockers"].split("|") if x}
            need[m.group(1)] = {"tier": r["text_evidence_tier"], "provisional": r["provisional_status"],
                                "needs_copy": bool(bl & {"NO_OFFICIAL_SOURCE_LOCATED", "ONLY_COMPILED_TRANSCRIPTION_FOUND", "ORIGINAL_FOUND_NEEDS_PAGE_CHECK"})}
reel = {}
with gzip.open(REPO / "jobs/dagron-collection-manifest/output/nyu-film709/MANIFEST.jsonl.gz", "rt") as fh:
    for line in fh:
        r = json.loads(line); m = re.fullmatch(r"EO:(\d+[A-Z]?)", r.get("instrument_id") or "")
        if m: reel[m.group(1)] = r.get("likely_unit")

by_num = {}
for S in sites:
    (OUT / S.name).mkdir(exist_ok=True)
    with open(OUT / S.name / "LEADS.jsonl", "w") as fh:
        for l in S.leads: fh.write(json.dumps(l, ensure_ascii=False) + "\n")
    for l in S.leads:
        for n in l["eo_numbers"]: by_num.setdefault(n, []).append(l)
rows = []
for n, ls in sorted(by_num.items(), key=lambda kv: (int(re.match(r"\d+", kv[0]).group()), kv[0])):
    s = need.get(n, {})
    rows.append({"eo": n, "in_tracker": bool(s), "needs_official_copy": s.get("needs_copy", False), "text_tier": s.get("tier", ""),
                 "provisional": s.get("provisional", ""), "film709_reel": reel.get(n, ""), "leads": len(ls),
                 "sites": ";".join(sorted({l["site"] for l in ls})), "kinds": ";".join(sorted({l["kind"] for l in ls})),
                 "new_to_project": any(not l["already_in_project"] for l in ls),
                 "example": ls[0]["url"], "example_title": ls[0]["title"][:150]})
with open(OUT / "ORDERS.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["eo"]); w.writeheader(); w.writerows(rows)
needed = [r for r in rows if r["needs_official_copy"]]
volumes = [l for S in sites for l in S.leads if l["kind"] == "volume" and not l["not_us_presidential_likely"]]
summary = {"sites": {S.name: {"calls": S.calls, "seconds": getattr(S, "seconds", None), "leads": len(S.leads),
                              "leads_with_eo_number": sum(1 for l in S.leads if l["eo_numbers"]),
                              "volumes": sum(1 for l in S.leads if l["kind"] == "volume" and not l["not_us_presidential_likely"]),
                              "new_volumes": sum(1 for l in S.leads if l["kind"] == "volume" and not l["not_us_presidential_likely"] and not l["already_in_project"]),
                              "filtered_not_us": sum(1 for l in S.leads if l["not_us_presidential_likely"]),
                              "errors": len(S.errors), "notes": S.notes[:10], "first_errors": S.errors[:5]} for S in sites},
           "distinct_eo_numbers": len(rows), "in_tracker": sum(r["in_tracker"] for r in rows),
           "needing_official_copy_with_a_lead": len(needed),
           "needing_official_copy_with_a_new_lead": sum(1 for r in needed if r["new_to_project"]),
           "needed_by_site": {S.name: sum(1 for r in needed if S.name in r["sites"].split(";")) for S in sites},
           "needed_by_film709_reel": {str(k): sum(1 for r in needed if r["film709_reel"] == k) for k in sorted({r["film709_reel"] for r in needed}, key=str)},
           "total_needing_official_copy": sum(1 for v in need.values() if v["needs_copy"])}
(OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
with open(OUT / "VOLUMES.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["site", "already_in_project", "title", "date", "url", "found_by"], extrasaction="ignore"); w.writeheader()
    for l in sorted(volumes, key=lambda l: (l["site"], l["title"])): w.writerow(l)
rep = ["# Bodley: sweep of large public collections for executive orders", "",
       "Leads only. A hit is examined by a person before it counts as any witness; nothing here changes a status or count.", "",
       "```json", json.dumps(summary, indent=2), "```", "", "## Orders still needing an official copy that have a lead", "",
       "| EO | reel | new | sites | kinds | example |", "|---|---|---|---|---|---|"]
rep += [f"| {r['eo']} | {r['film709_reel']} | {'yes' if r['new_to_project'] else ''} | {r['sites']} | {r['kinds']} | {r['example']} |" for r in needed[:600]]
rep += ["", "## New volumes (books and scans not yet named anywhere the project tracks sources)", ""]
rep += [f"- {l['site']}: [{l['title'][:140]}]({l['url']}) {l.get('date','')}" for l in sorted(volumes, key=lambda l: (l['site'], l['title'])) if not l['already_in_project']][:500]
(OUT / "REPORT.md").write_text("\n".join(rep) + "\n")
print(json.dumps(summary, indent=2))
