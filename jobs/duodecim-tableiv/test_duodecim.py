"""Offline tests for Duodecim: synthetic Table IV pages in the two real markup styles, a fake network."""
import csv
import io
import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import duodecim as D  # noqa: E402


def page(label, rows, style="old"):
    """rows: (year, month, day, no, title, section, status). style old = double quotes and no </tr> (2010 markup);
    new = single quotes with </tr> (current markup)."""
    q = '"' if style == "old" else "'"
    close = "" if style == "old" else "</tr>"
    out = [f"<html><body><p class={q}updatedthrough{q}>Tables I, II, IV, V and VI are updated through the {label}.</p>",
           f"<h2 class={q}tablename{q}>TABLE IV&mdash;EXECUTIVE ORDERS</h2>",
           f"<p class={q}tabledefinition{q}>Rep.&mdash;Repealed. ``Rep.'' in the status column.</p>",
           "<table><tr><th colspan='3'>Exec. Ord</th></tr>"]
    year = None
    for y, mo, da, no, ti, se, st in rows:
        if y != year:
            out.append(f"<tr><th colspan={q}6{q} class={q}year{q}>{y}</th></tr>")
            year = y
        out.append(f"<tr class={q}usctable4row{q}><td>{mo}</td><td>{da}</td><td>{no}</td><td>{ti}</td><td>{se}</td><td>{st}</td>{close}")
    out.append("</table></body></html>")
    return "\n".join(out).encode("latin-1")


OLD = [("1907", "Oct.", "23", "703", "16", "668dd nt", ""), ("1907", "", "", "705", "16", "668dd nt", ""),
       ("1910", "June", "23", "1216", "16", "431 nt", ""), ("1929", "Oct.", "1", "5200", "7", "452 nt", "Elim."),
       ("1933", "July", "30", "6237A", "50 App.", "12 nt", ""), ("1933", "Aug.", "28", "6260", "12", "95a nt", "Elim."),
       ("1933", "", "", "", "12", "248 nt", "Elim."), ("2009", "Dec.", "29", "13526", "50", "435 nt", "")]
NEW = [("1907", "Oct.", "23", "703", "16", "668dd nt", ""), ("1910", "June", "23", "1216", "54", "320301 nt", ""),
       ("1929", "Oct.", "1", "5200", "7", "452 nt", "Elim."), ("1933", "July", "30", "6237A", "50 App.", "12 nt", "Elim."),
       ("1933", "Aug.", "28", "6260", "12", "95a nt", "Elim."), ("2024", "Dec.", "23", "14132", "5", "5332 nt", ""),
       ("2024", "", "23", "14133", "5", "5332 nt", "")]
OLD_PAGE = page("2006 Edition and Supplement V (1/3/2012)", OLD, "old")
NEW_PAGE = page("2024 Main Edition (01/06/2025)", NEW, "new")
MID_PAGE = page("2012 Main Edition, Supplement I (01/15/2014)", OLD[:6], "new")

NL = chr(10)


def robots(*lines):
    return (NL.join(lines) + NL).encode()


WEBHARVEST_ROBOTS = robots("User-agent: *", "Allow: /", "Disallow: /nara/*/http://", "Disallow: /congress*/*/http://",
                           "Disallow: /congress*/*/https://", "Crawl-delay: 10")
UNT_TS = "20121107185129"


def unt_lines(ts=UNT_TS):
    a = {"urlkey": "k", "timestamp": ts, "url": "http://uscode.house.gov/tables/usctable4.htm", "mime": "text/html",
         "status": "200", "digest": "DIG1"}
    b = dict(a, timestamp="20130103084823", mime="warc/revisit")
    return (json.dumps(a) + NL + json.dumps(b) + NL).encode()


def make_transport(fail=None, live_status=200, ia_online=False, counter=None, unt_down=False):
    def transport(url, headers, timeout):
        if counter is not None:
            counter.append(url)
        p = urllib.parse.urlsplit(url)
        if unt_down and p.hostname == "webarchive.library.unt.edu":
            raise OSError("unreachable from this network")
        if p.path == "/robots.txt":
            if p.hostname == "babel.hathitrust.org":
                return 200, {}, io.BytesIO(robots("User-agent: *", "Crawl-delay: 1", "Disallow: /cgi/"))
            if p.hostname == "webharvest.gov":
                return 200, {}, io.BytesIO(WEBHARVEST_ROBOTS)
            if p.hostname == "webarchive.library.unt.edu":
                return 200, {}, io.BytesIO(robots("User-agent: ClaudeBot", "Disallow: /"))
            return 404, {}, io.BytesIO(b"")
        if fail:
            return 500, {}, io.BytesIO(b"boom")
        if p.hostname == "webharvest.gov":
            raise AssertionError("the job must never fetch webharvest.gov beyond robots.txt: " + url)
        if p.hostname == "webarchive.library.unt.edu":
            if p.path == "/eot2012/timemap/json/http://uscode.house.gov/tables/usctable4.htm":
                return 200, {}, io.BytesIO(unt_lines())
            if p.path == f"/eot2012/{UNT_TS}id_/http://uscode.house.gov/tables/usctable4.htm":
                return 200, {"content-type": "text/html"}, io.BytesIO(OLD_PAGE)
            return 404, {}, io.BytesIO(b"")
        if p.hostname == "web.archive.org":
            if "/cdx/search/cdx" in p.path:
                if not ia_online:
                    return 200, {}, io.BytesIO(b"<html>Temporarily Offline</html>")
                return 200, {}, io.BytesIO(json.dumps([
                    ["timestamp", "original", "mimetype", "statuscode", "digest"],
                    ["20141206234626", "http://uscode.house.gov/tables/usctable4.htm", "text/html", "200", "D2"],
                    ["20121107185129", "http://uscode.house.gov/tables/usctable4.htm", "text/html", "200", "D3"],
                    ["20150101000000", "http://uscode.house.gov/tables/usctable4.htm", "text/html", "200", "D4"]]).encode())
            if p.path.startswith("/web/20150101000000id_/"):  # a repeat capture: Wayback redirects to the one with the bytes
                return 302, {"location": "/web/20141206234626id_/http://uscode.house.gov/tables/usctable4.htm"}, io.BytesIO(b"")
            if p.path.startswith("/web/20141206234626id_/"):
                return 200, {"content-type": "text/html"}, io.BytesIO(MID_PAGE)
            if p.path.startswith("/web/20121107185129id_/"):
                return 200, {"content-type": "text/html"}, io.BytesIO(OLD_PAGE)
            return 404, {}, io.BytesIO(b"")
        if url == D.LIVE_URL:
            return live_status, {"content-type": "text/html", "last-modified": "Fri, 06 Nov 2026 12:46:28 GMT"}, io.BytesIO(NEW_PAGE if live_status == 200 else b"x")
        if p.hostname == "www.govinfo.gov":
            if p.path.endswith("USCODE_sitemap_index.xml"):
                return 200, {}, io.BytesIO(b"<loc>https://www.govinfo.gov/sitemap/USCODE_2018_sitemap.xml</loc>")
            if p.path.endswith("USCODE_2018_sitemap.xml"):
                return 200, {}, io.BytesIO(b"<loc>https://www.govinfo.gov/app/details/USCODE-2018-title3</loc>")
        return 404, {}, io.BytesIO(b"")
    return transport


def make_repo(root):
    r = Path(root) / "repo"
    (r / "research/stage15/CENSUS").mkdir(parents=True)
    ids = ["EO:703", "EO:705", "EO:1216", "EO:5200", "EO:6237A", "EO:6260", "EO:13526", "EO:14132", "EO:14133"]
    (r / D.UNIVERSE).write_text("id,x" + NL + NL.join(f"{i},1" for i in ids) + NL)
    cl = r / "jobs/current-law/output"
    cl.mkdir(parents=True)
    note = {"member": "usc16.xml", "note_id": "n1", "citation": "16 U.S.C. 668dd note", "subjects": ["703"],
            "text": "Ex. Ord. No. 703 provided: text", "edition": "Public Law 119-121 (2026-10-09)",
            "source_id": "usc:119-121:zip"}
    (cl / "USC_EO_NOTES.jsonl").write_text(json.dumps(note) + NL)
    (cl / "SOURCES.jsonl").write_text(json.dumps({"source_id": "usc:119-121:zip", "url": "https://uscode.house.gov/x.zip",
                                                  "sha256": "ab" * 32, "bytes": 5}) + NL)
    (cl / "SUMMARY.json").write_text(json.dumps({"usc": {"label": "Public Law 119-121 (2026-10-09)",
                                                          "titles": [{"member": "usc16.xml", "sha256": "cd" * 32}]}}))
    return r


class Parse(unittest.TestCase):
    def test_label(self):
        for text, eid in (("updated through the 2006 Edition and Supplement III (2/1/2010).", "USC2006+SIII@2010-02-01"),
                          ("Updated through the 2012 Main Edition, Supplement V (01/12/2018).", "USC2012+SV@2018-01-12"),
                          ("updated through the 2024 Main Edition (01/06/2025).", "USC2024@2025-01-06")):
            self.assertEqual(D.parse_label(text)["edition_id"], eid)
        self.assertIsNone(D.parse_label("nothing here"))

    def test_both_markups_and_carry(self):
        for raw, n, elim in ((OLD_PAGE, len(OLD), 3), (NEW_PAGE, len(NEW), 3)):
            p = D.parse_table(raw)
            self.assertTrue(p["ok"])
            self.assertEqual(len(p["rows"]), n)
            self.assertEqual(p["raw_row_tags"], n)
            self.assertEqual(p["raw_elim_cells"], elim)
            self.assertEqual(p["parsed_elim"], elim)
            self.assertEqual(p["malformed"], 0)
            for r in p["rows"]:
                a, b = r["span"]
                self.assertTrue(raw[a:b].startswith(b"<tr"), raw[a:b][:20])
                self.assertTrue(raw[a:b].rstrip().endswith(b"</td>") or raw[a:b].endswith(b"</tr>"))
        p = D.parse_table(OLD_PAGE)
        carried = [r for r in p["rows"] if r["eo_number_carried"]]
        self.assertEqual([(r["eo_number"], r["section"]) for r in carried], [("6260", "248 nt")])
        self.assertEqual(p["rows"][1]["date_partial"], "1907-10-23")  # blank date cells inherit
        self.assertIn("Rep.", p["legend"])

    def test_not_a_table(self):
        self.assertFalse(D.parse_table(b"<html>Temporarily Offline</html>")["ok"])

    def test_section_kind(self):
        k = D.section_kind
        self.assertEqual(k("668dd nt"), "note")
        self.assertEqual(k("1701 nts"), "note")
        self.assertEqual(k("nt. prec. 2241"), "note_preceding")
        self.assertEqual(k("see 3321"), "see")
        self.assertEqual(k("1457"), "section_text")

    def test_map_eo(self):
        u = {"EO:6237A", "EO:703"}
        self.assertEqual(D.map_eo(u, "6237A"), "EO:6237A")
        self.assertEqual(D.map_eo(u, "703"), "EO:703")
        self.assertEqual(D.map_eo(u, "704"), "")
        self.assertEqual(D.map_eo(u, ""), "")

    def test_json_rows(self):
        self.assertEqual(len(D._json_rows(unt_lines())), 2)
        self.assertEqual(D._json_rows(b'[["a","b"],["1","2"]]'), [{"a": "1", "b": "2"}])
        self.assertEqual(D._json_rows(b"<html>Temporarily Offline</html>"), [])


class Robots(unittest.TestCase):
    def test_robots_wildcards(self):
        rules = D.robots_rules(WEBHARVEST_ROBOTS.decode(), D.UA)
        self.assertFalse(D.robots_allows(rules, "/congress112th/20121211232718id_/http://uscode.house.gov/x.htm"))
        self.assertFalse(D.robots_allows(rules, "/congress112th/timemap/json/https://uscode.house.gov/x.htm"))
        self.assertTrue(D.robots_allows(rules, "/robots.txt"))
        self.assertTrue(D.robots_allows(rules, "/static/css.css"))
        named = D.robots_rules(robots("User-agent: eo-road-system", "Disallow: /a", "", "User-agent: *",
                                      "Disallow: /b").decode(), D.UA)
        self.assertFalse(D.robots_allows(named, "/a/x"))
        self.assertTrue(D.robots_allows(named, "/b/x"))  # the named group replaces *
        dollar = D.robots_rules(robots("User-agent: *", "Disallow: /x$").decode(), D.UA)
        self.assertFalse(D.robots_allows(dollar, "/x"))
        self.assertTrue(D.robots_allows(dollar, "/xy"))
        longest = D.robots_rules(robots("User-agent: *", "Disallow: /", "Allow: /pub").decode(), D.UA)
        self.assertTrue(D.robots_allows(longest, "/pub/1"))
        self.assertFalse(D.robots_allows(longest, "/other"))


class Series(unittest.TestCase):
    def editions(self):
        out = []
        for i, (raw, ts) in enumerate(((OLD_PAGE, "1"), (MID_PAGE, "2"), (NEW_PAGE, ""))):
            out.append(D.Edition(D.parse_table(raw), raw, {"url": f"u{i}", "ts": ts, "retrieved_utc": "",
                                                           "route": "olrc_live_page" if raw is NEW_PAGE else "r"}))
        return sorted(out, key=lambda e: e.date)

    def test_timeseries(self):
        eds = self.editions()
        rows, detail = D.timeseries(eds, {"EO:6237A", "EO:1216"})
        by = {r["eo_number"]: r for r in rows}
        self.assertEqual(by["6237A"]["first_edition_with_elim_row"], "2025-01-06")
        self.assertEqual(by["6237A"]["first_listed_is_left_censored"], "yes")
        self.assertEqual(by["1216"]["location_changes"], 1)
        self.assertIn("16 U.S.C. 431 nt", by["1216"]["location_change_detail"])
        self.assertEqual(by["14132"]["first_edition_listed"], "2025-01-06")
        self.assertEqual(by["14132"]["first_listed_is_left_censored"], "no")
        self.assertEqual(by["705"]["listed_in_current_edition"], "no")
        self.assertEqual(by["705"]["dropped_after_edition"], "2014-01-15")
        self.assertEqual(by["5200"]["elim_present_at_first_listing"], "yes")
        self.assertEqual(by["5200"]["elim_in_current_edition"], "all")
        self.assertEqual(by["13526"]["dropped_after_edition"], "2012-01-03")

    def test_controls_pass_and_fail(self):
        c = D.run_controls(self.editions())
        self.assertEqual(c["errors"], 0, [r for r in c["results"] if r["result"] == "FAIL"])
        self.assertGreater(c["evaluated"], 20)
        eds = self.editions()
        eds[-1].rows.append(dict(eds[-1].rows[0], eo_number="704", span=(0, 1)))  # a planted negative appears
        c = D.run_controls(eds)
        self.assertGreater(c["errors"], 0)


class Budgeting(unittest.TestCase):
    def test_caps_and_shards(self):
        with tempfile.TemporaryDirectory() as t:
            b = D.Budget(Path(t), total=1000, per_file=400)
            with self.assertRaises(D.BudgetError):
                b.write("big", b"x" * 401)
            b.write("a", b"x" * 300)
            b.write("b", b"x" * 300)
            b.write("c", b"x" * 300)
            with self.assertRaises(D.BudgetError):
                b.write("d", b"x" * 300)
            self.assertEqual(b.total(), 900)

    def test_sharding(self):
        with tempfile.TemporaryDirectory() as t:
            old = D.SHARD
            D.SHARD = 100
            try:
                b = D.Budget(Path(t))
                names = b.write_sharded("X", ".csv", [f"{i:03d},aaaaaaaaaaaaaaaaaaaa" + NL for i in range(20)], "h,h" + NL)
            finally:
                D.SHARD = old
            self.assertGreater(len(names), 2)
            self.assertEqual(names[0], "X.csv")
            self.assertEqual(names[1], "X_2.csv")
            self.assertTrue(all((Path(t) / n).read_text().startswith("h,h" + NL) for n in names))
            self.assertTrue(all(len((Path(t) / n).read_bytes()) <= 100 + 30 for n in names))


class Run(unittest.TestCase):
    def run_job(self, root, transport, env=None, prior=None, name="out", cache="cache"):
        repo = Path(root) / "repo" if (Path(root) / "repo").exists() else make_repo(root)
        out = Path(root) / name
        e = {"JOB_UNT_COLLECTIONS": "eot2008,eot2012", "JOB_RETRIES": "2", "JOB_MIN_EDITIONS": "2", "JOB_BACKOFF": "0", "JOB_SMOKE": "",
             "JOB_PRIOR_OUTPUT_DIR": str(prior or (Path(root) / "no_prior"))}
        e.update(env or {})
        s = D.main(repo, out, Path(root) / cache, transport=transport, env=e, sleep=lambda s: None,
                   intervals={h: 0 for h in ("webharvest.gov", "uscode.house.gov", "www.govinfo.gov",
                                             "babel.hathitrust.org", "web.archive.org", "webarchive.library.unt.edu")})
        return s, out

    def test_full_run(self):
        with tempfile.TemporaryDirectory() as t:
            s, out = self.run_job(t, make_transport())
            self.assertEqual(s["editions_parsed"], 2)
            self.assertEqual(s["editions_parsed_by_source"], {"unt_end_of_term_id_replay": 1, "olrc_live_page": 1})
            self.assertEqual(s["routes"]["library_of_congress_scans"][:22], "pending owner decision")
            self.assertEqual(s["controls_errors"], 0)
            self.assertEqual(s["control_error_rate"], 0.0)
            for f in ("SOURCES.jsonl", "FRAGMENTS.jsonl", "FRAGMENTS_HISTORY.jsonl", "TABLE_IV_ROWS.csv", "TIMESERIES.csv",
                      "CONTROLS.json", "SUMMARY.json", "BUDGET.json", "EDITIONS.csv", "CURRENT_NOTE_HOLDINGS.csv",
                      "SOURCE_COVERAGE.json", "FETCH_LOG.jsonl"):
                self.assertTrue((out / f).is_file(), f)
            srcs = [json.loads(x) for x in (out / "SOURCES.jsonl").read_text().splitlines()]
            self.assertEqual(len(srcs), 2)
            for r in srcs:
                self.assertEqual(len(r["sha256"]), 64)
                self.assertEqual(r["instrument_ids"], [])
                self.assertIsNone(r["cache_path"])
                self.assertFalse(r["acceptable_as_original"])
            self.assertFalse(list(out.glob("*.html")))
            frags = [json.loads(x) for x in (out / "FRAGMENTS.jsonl").read_text().splitlines()]
            self.assertEqual({f["kind"] for f in frags}, {"current_predicate_candidates"})
            ids = {f["instrument_id"] for f in frags}
            self.assertIn("EO:703", ids)
            self.assertNotIn("EO:5200", ids)  # Elim. rows are not emitted as current-basis leads
            f703 = next(f for f in frags if f["instrument_id"] == "EO:703")
            e = f703["data"][0]
            self.assertEqual(e["note_text_held"]["status"], "yes_exact_citation")
            self.assertEqual(e["note_text_held"]["note_id"], "n1")
            self.assertEqual(e["source"]["sha256"], srcs[-1]["sha256"])
            self.assertNotIn("text_path", e)
            hist = [json.loads(x) for x in (out / "FRAGMENTS_HISTORY.jsonl").read_text().splitlines()]
            self.assertEqual({h["kind"] for h in hist}, {"table_iv_history_candidates"})
            h = next(h for h in hist if h["instrument_id"] == "EO:6237A")
            codes = [d["event_code"] for d in h["data"]]
            self.assertIn("elim_marker_first_seen", codes)
            ent = next(d for d in h["data"] if d["event_code"] == "elim_marker_first_seen")
            self.assertIn("caution", ent)
            a, b = map(int, ent["row_span"].split("-"))  # a span reads back the row in the held bytes
            self.assertIn(b"6237A", NEW_PAGE[a:b])
            with open(out / "CURRENT_NOTE_HOLDINGS.csv", newline="", encoding="utf-8") as fh:
                holdings = list(csv.DictReader(fh))
            self.assertEqual(next(r for r in holdings if r["eo_number"] == "703")["note_text_held"], "yes_exact_citation")
            self.assertEqual(next(r for r in holdings if r["eo_number"] == "1216")["note_text_held"], "no_printed_note_in_current_law")
            bud = json.loads((out / "BUDGET.json").read_text())
            self.assertLess(bud["total_bytes"], D.MAX_TOTAL)
            cov = json.loads((out / "SOURCE_COVERAGE.json").read_text())
            self.assertEqual(cov["sources"]["govinfo_uscode_collection"]["years_with_packages"], [2018])
            self.assertIs(cov["sources"]["hathitrust_full_view"]["robots_allows_automated_fetch"], False)
            ia = cov["sources"]["internet_archive_wayback"]
            self.assertEqual(ia["captures_listed"], 0)
            self.assertFalse(ia["used"])
            self.assertEqual(cov["sources"]["library_of_congress_scans"]["status"], "pending owner decision")
            self.assertEqual(cov["sources"]["library_of_congress_scans"]["requests_made_by_job"], 0)
            wh = cov["sources"]["webharvest_gov"]
            self.assertFalse(wh["used"])
            self.assertTrue(all(v is False for v in wh["replay_and_timemap_paths_allowed"].values()))

    def test_smoke(self):
        with tempfile.TemporaryDirectory() as t:
            s, out = self.run_job(t, make_transport(), env={"JOB_SMOKE": "1"})
            self.assertEqual(s["editions_parsed"], 2)
            self.assertTrue(s["smoke_mode"])
        caps = [{"i": i} for i in range(9)]
        self.assertEqual(D.smoke_pick(caps), [{"i": 0}, {"i": 4}, {"i": 8}])

    def test_never_fetches_webharvest_or_loc(self):
        seen = []
        with tempfile.TemporaryDirectory() as t:
            self.run_job(t, make_transport(counter=seen))
        hosts = {urllib.parse.urlsplit(u).hostname for u in seen}
        self.assertNotIn("www.loc.gov", hosts)
        self.assertNotIn("webarchive.loc.gov", hosts)
        self.assertEqual([u for u in seen if "webharvest.gov" in u], ["https://webharvest.gov/robots.txt"])

    def test_internet_archive_leg_when_online(self):
        with tempfile.TemporaryDirectory() as t:
            s, out = self.run_job(t, make_transport(ia_online=True), env={"JOB_MIN_EDITIONS": "3"})
            self.assertEqual(s["editions_parsed"], 3)
            self.assertEqual(s["editions_parsed_by_source"], {"olrc_live_page": 1, "unt_end_of_term_id_replay": 1,
                                                              "internet_archive_id_replay": 1})
            self.assertEqual(s["captures_discovered_internet_archive"], 3)
            srcs = {}
            for x in (out / "SOURCES.jsonl").read_text().splitlines():
                srcs[json.loads(x)["edition_id"]] = json.loads(x)
            dup = srcs["USC2006+SV@2012-01-03"]
            self.assertEqual(len(dup["duplicate_captures_with_identical_rows"]), 1)  # IA copy of the UNT capture
            mid = srcs["USC2012+SI@2014-01-15"]
            self.assertEqual(len(mid["duplicate_captures_with_identical_rows"]), 1)  # the redirected repeat capture
            self.assertTrue(dup["url"].startswith("https://webarchive.library.unt.edu/"))
            self.assertEqual(s["routes"]["internet_archive_wayback"], "used")

    def test_unreachable_host_is_tried_once_and_does_not_fail_the_run(self):
        seen = []
        with tempfile.TemporaryDirectory() as t:
            s, out = self.run_job(t, make_transport(unt_down=True, ia_online=True, counter=seen),
                                  env={"JOB_MIN_EDITIONS": "2"})
            self.assertEqual(s["editions_parsed_by_source"], {"olrc_live_page": 1, "internet_archive_id_replay": 2})
            self.assertEqual(len([u for u in seen if "unt.edu" in u]), 1)  # robots.txt once, then the breaker holds
            self.assertEqual(s["problems"], [])

    def test_time_budget_stops_archive_captures(self):
        with tempfile.TemporaryDirectory() as t:
            s, out = self.run_job(t, make_transport(ia_online=True), env={"JOB_TIME_BUDGET_MIN": "0.0000001", "JOB_MIN_EDITIONS": "1"})
            self.assertEqual(s["editions_parsed_by_source"], {"olrc_live_page": 1})
            self.assertTrue(all(f["error"] == "time_budget_exhausted" for f in s["capture_failures"]))
            self.assertGreaterEqual(len(s["capture_failures"]), 2)

    def test_429_slows_the_host(self):
        calls = {"n": 0}

        def transport(url, headers, timeout):
            if url.endswith("/robots.txt"):
                return 404, {}, io.BytesIO(b"")
            calls["n"] += 1
            return (429, {}, io.BytesIO(b"slow down")) if calls["n"] < 3 else (200, {}, io.BytesIO(b"ok"))
        with tempfile.TemporaryDirectory() as t:
            f = D.Fetcher(Path(t), transport=transport, intervals={"example.org": 0.01}, sleep=lambda s: None, retries=4, backoff=0)
            r = f.get("https://example.org/x")
            self.assertEqual(r["status"], 200)
            self.assertAlmostEqual(f.pool("example.org").min_interval, 0.04)  # doubled twice

    def test_fails_when_most_requests_fail(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(SystemExit) as cm:
                self.run_job(t, make_transport(fail=True))
            self.assertTrue("failed" in str(cm.exception) or "edition" in str(cm.exception))

    def test_resumes_from_prior_when_current_page_is_down(self):
        with tempfile.TemporaryDirectory() as t:
            s, out1 = self.run_job(t, make_transport(), name="out1")
            # second run: the live page is down; the prior output carries it, flagged, and the run still passes
            s2, out2 = self.run_job(t, make_transport(live_status=503), prior=out1, name="out2", cache="cache2",
                                    env={"JOB_SMOKE": ""})
            self.assertEqual(s2["editions_parsed"], 2)
            self.assertTrue(any(e["carried_forward"] for e in s2["editions"]))
            self.assertTrue(s2["capture_failures"][0]["carried_forward_from_prior_output"])
            self.assertEqual(s2["controls_errors"], 0)
            with open(out2 / "EDITIONS.csv", newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(sum(1 for r in rows if r["carried_forward"] == "yes"), 1)
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(SystemExit) as cm:  # no prior: the current page is missing, so the run fails
                self.run_job(t, make_transport(live_status=503))
            self.assertIn("current Table IV page", str(cm.exception))

    def test_budget_stop_writes_budget_file(self):
        with tempfile.TemporaryDirectory() as t:
            old = D.MAX_FILE
            try:
                D.MAX_FILE = 50
                with self.assertRaises(SystemExit) as cm:
                    self.run_job(t, make_transport())
            finally:
                D.MAX_FILE = old
            self.assertIn("budget stop", str(cm.exception))
            self.assertTrue(json.loads((Path(t) / "out" / "BUDGET.json").read_text())["stopped"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
