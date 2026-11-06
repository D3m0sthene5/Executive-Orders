"""Offline tests for Repetita (no network): parser, controls, budget, merge/dedupe, resume, failure rule, pre-1997."""
import csv
import datetime as dt
import gzip
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_lib"))
import lsa  # noqa: E402
import prewar  # noqa: E402
import repetita  # noqa: E402
from fetch_pool import FetchPool  # noqa: E402


def member(title_line, body):
    return ("<html>\n<head>\n<title>x</title>\n</head>\n<body><pre>\n[List of CFR Sections Affected (LSA), January 2018]\n"
            "[From the U.S. Government Publishing Office, <a href=\"http://www.gpo.gov\">www.gpo.gov</a>]\n\n \n"
            + title_line + "\n\n" + body + "\n\n</pre></body>\n</html>\n").encode("latin-1")


T3 = """Presidential Documents

Proclamations

9687 See Proc. 9693..............................................18-3541
9688..............................................................18-587

Executive Orders

12947 See Notice of Jan. 17, 2018................................18-2731
13099 See Notice of Jan. 17, 2018................................18-2731
13799 Revoked by EO 13820.........................................18-969
See Notice of Nov. 9, 2001....................................18-56966
13820.............................................................18-969
Jan. 22, 1912 Revoked in part by PLO 7230.......................18-3519

[[Page 8]]

13821 Amended by EO 13822; Revoked by EO 13823...................18-1507, 18-1508

Administrative Orders

Notices:
Jan. 17, 2018....................................................18-2731
Nov. 9, 2001..........................................18-57357, 18-57359"""

T32 = """Chapter I--Office of the Secretary of Defense (Parts 1--399)

57 Revised.......................................................18-2566
199.4 (c)(3)(xi)(A)(7) and (f)(10) added; (d)(3)(v) and
(f)(2)(i)(G) amended; (e)(3)(i)(A)(3) revised..............18-59338
(g)(15) revised.................................................18-629
Regulation at 62 FR 629 eff. date corrected to
2-5-97.......................................................18-3739
220 Removed. See E.O. 12958
18-4458
220.8 (k)(2) stayed and amended under Executive Order 13526...18-941"""


def make_zip(issue, members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{issue}/dip.xml", "<dip/>")
        for title, data in members.items():
            z.writestr(f"{issue}/html/{issue}-title{title}.htm", data)
            z.writestr(f"{issue}/pdf/{issue}-title{title}.pdf", b"%PDF-fake")
    return buf.getvalue()


class Resp(io.BytesIO):
    def close(self):
        pass


class Net:
    """Fake transport: routes is {exact url or prefix: (status, bytes)}."""
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, url, headers, timeout):
        self.calls.append(url)
        if url.endswith("/robots.txt"):
            return 404, {}, Resp(b"")
        if url in self.routes:
            v = self.routes[url]
            st, body = v[0], v[1]
            hd = {"content-length": str(len(body))}
            if len(v) > 2:
                hd.update(v[2])
            return st, hd, Resp(body)
        for k, (st, body) in self.routes.items():
            if k.endswith("*") and url.startswith(k[:-1]):
                return st, {"content-length": str(len(body))}, Resp(body)
        return 404, {}, Resp(b"")


def sitemap(issues):
    return ("<urlset>" + "".join(f"<url><loc>https://www.govinfo.gov/app/details/{i}</loc></url>" for i in issues) + "</urlset>").encode()


class ParserTests(unittest.TestCase):
    def test_title3_entries_categories_wraps_and_refs(self):
        raw = member("TITLE 3--THE PRESIDENT", T3)
        es, st = lsa.parse_member(raw, 3)
        by = {(e.category, e.item, e.change): e for e in es}
        self.assertIn(("proclamations", "9687", "See Proc. 9693"), by)
        self.assertIn(("proclamations", "9688", ""), by)
        self.assertIn(("executive orders", "13799", "Revoked by EO 13820"), by)
        cont = by[("executive orders", "13799", "See Notice of Nov. 9, 2001")]
        self.assertTrue(cont.continuation)
        self.assertEqual(by[("executive orders", "Jan. 22, 1912", "Revoked in part by PLO 7230")].ref, "18-3519")
        multi = by[("executive orders", "13821", "Amended by EO 13822; Revoked by EO 13823")]
        self.assertEqual(multi.refs(), ["18-1507", "18-1508"])
        self.assertEqual(multi.lsa_page, 8)
        self.assertEqual(by[("notices", "Nov. 9, 2001", "")].refs(), ["18-57357", "18-57359"])
        for e in es:
            self.assertTrue(lsa.verify_entry(raw, e), e.text)
        self.assertEqual(st["entries"], len(es))
        self.assertEqual(st["leader_lines_independent"], len(es))

    def test_other_title_wrapped_continuation_and_ref_only_line(self):
        raw = member("TITLE 32--NATIONAL DEFENSE", T32)
        es, _ = lsa.parse_member(raw, 32)
        items = [(e.item, e.change, e.continuation, e.ref) for e in es]
        self.assertIn(("57", "Revised", False, "18-2566"), items)
        self.assertIn(("199.4", "(c)(3)(xi)(A)(7) and (f)(10) added; (d)(3)(v) and (f)(2)(i)(G) amended; (e)(3)(i)(A)(3) revised", False, "18-59338"), items)
        self.assertIn(("199.4", "(g)(15) revised", True, "18-629"), items)
        self.assertIn(("199.4", "Regulation at 62 FR 629 eff. date corrected to 2-5-97", True, "18-3739"), items)
        self.assertIn(("220", "Removed. See E.O. 12958", False, "18-4458"), items)  # reference alone on the next line
        for e in es:
            self.assertTrue(lsa.verify_entry(raw, e), e.text)

    def test_fr_citation(self):
        self.assertEqual(lsa.fr_citation("97-4415", 1997)[:3], (62, 4415, "yy_page"))
        self.assertEqual(lsa.fr_citation("96-37386", 1997)[:2], (61, 37386))
        self.assertEqual(lsa.fr_citation("03-4075", 2003)[:2], (68, 4075))
        self.assertEqual(lsa.fr_citation("60289", 2026), (91, 60289, "page", True))
        self.assertEqual(lsa.fr_citation("x", 2026)[2], "unparsed")

    def test_acting_and_mechanism(self):
        self.assertEqual(lsa.acting_ids("Revoked by EO 14408")[0], ["EO:14408"])
        self.assertEqual(lsa.acting_ids("Continued by Notice of Jan. 2, 1997")[0], ["NOTICE:1997-01-02"])
        self.assertEqual(lsa.acting_ids("Revoked in part by PLO 7324")[0], ["PLO:7324"])
        self.assertEqual(lsa.acting_ids("Amended by 11044"), ([], ["11044"]))
        self.assertEqual(lsa.mechanism_of("Partially revoked by EO 13526")[1:], ("revocation", "ending", "in part"))
        self.assertEqual(lsa.mechanism_of("See EO 14429")[1:3], ("cross_reference", "mention"))

    def test_row_fields(self):
        raw = member("TITLE 3--THE PRESIDENT", T3)
        es, _ = lsa.parse_member(raw, 3)
        e = next(x for x in es if x.item == "13799")
        r = lsa.row_from_entry(e, "LSA-2018-01", "2018-01-31", "html/x.htm", "ab" * 32, "18-969")
        self.assertEqual((r["eo_target"], r["acting"], r["fr_cite"], r["mechanism_class"], r["eo_mention"]),
                         ("EO:13799", "EO:13820", "83 FR 969", "ending", 1))
        held = raw[r["span_start"]:r["span_end"]].decode("latin-1")
        self.assertTrue(held.startswith("13799 Revoked by EO 13820...") and held.endswith("...18-969"), held)


class ControlTests(unittest.TestCase):
    def test_planted_controls_pass_on_real_shaped_member(self):
        res = lsa.plant_controls(member("TITLE 3--THE PRESIDENT", T3))
        self.assertTrue(res and all(c["ok"] for c in res), res)

    def test_planted_controls_detect_a_broken_parser(self):
        # a member whose structure the parser cannot read as entries must fail the planted positive
        res = lsa.plant_controls(b"<html><body>no pre block here</body></html>")
        self.assertFalse(all(c["ok"] for c in res))

    def test_known_fact_and_negatives(self):
        z = make_zip("LSA-2018-01", {3: member("TITLE 3--THE PRESIDENT", T3), 32: member("TITLE 32--X", T32)})
        r = lsa.process_zip("LSA-2018-01", z, "t")
        self.assertEqual(r["errors"], [])
        known = [c for c in r["controls"] if c["name"].startswith("known_fact")]
        self.assertEqual([c["ok"] for c in known], [True])
        self.assertTrue(all(c["ok"] for c in r["controls"]), r["controls"])
        rows = r["rows"]
        self.assertTrue(all(c["ok"] for c in lsa.negative_controls(rows)))
        # a made-up entry planted into the final rows is caught
        bad = rows + [{"title": 3, "category": "executive orders", "item": "99999", "change": "", "fr_ref": "1"}]
        self.assertFalse(all(c["ok"] for c in lsa.negative_controls(bad)))
        # EO mention outside Title 3 is kept; others are not
        self.assertEqual([x["item"] for x in rows if x["title"] == 32], ["220", "220.8"])
        self.assertEqual(sorted({x["fr_ref"] for x in rows if x["title"] == 32}), ["18-4458", "18-941"])

    def test_zip_without_title3_fails_its_control(self):
        r = lsa.process_zip("LSA-2018-01", make_zip("LSA-2018-01", {32: member("TITLE 32--X", T32)}), "t")
        self.assertFalse(all(c["ok"] for c in r["controls"]))

    def test_bad_zip(self):
        self.assertTrue(lsa.process_zip("LSA-2018-01", b"not a zip", "t")["errors"])


class BudgetTests(unittest.TestCase):
    def test_budget_refuses_over_file_and_total(self):
        with tempfile.TemporaryDirectory() as d:
            b = lsa.Budget(Path(d), total=100, per_file=60)
            self.assertTrue(b.write("a", b"x" * 50))
            self.assertFalse(b.write("big", b"x" * 61))
            self.assertFalse(b.write("c", b"x" * 55))
            self.assertTrue(b.write("d", b"x" * 40))
            self.assertEqual(b.used(), 90)
            self.assertEqual([r["file"] for r in b.refused], ["big", "c"])

    def test_sharding_by_year_when_one_file_is_too_big(self):
        with tempfile.TemporaryDirectory() as d:
            b = lsa.Budget(Path(d), total=10_000, per_file=3000)
            rows = [{"first_issue": f"LSA-{y}-01", "v": "x" * 400} for y in (1997, 1998) for _ in range(3)]
            names = lsa.write_sharded(b, "R", ".jsonl", rows, lsa.jsonl_bytes, lambda r: r["first_issue"][4:8])
            self.assertEqual(names, ["R.1997.jsonl", "R.1998.jsonl"])


def run_main(tmp, routes, env=None, prior=None, today=dt.date(2018, 4, 5)):
    out = Path(tmp) / "out"
    if out.exists():
        import shutil
        shutil.rmtree(out)
    net = Net(routes)
    e = {"JOB_SKIP_PRE1997": "1", "JOB_WORKERS": "2", "JOB_SMOKE": "0"}
    e.update(env or {})
    s = repetita.main(Path(tmp), out, Path(tmp) / "cache", env=e, transport=net, today=today, prior_dir=prior or (Path(tmp) / "none"))
    return s, out, net


def routes_for(issues, with_missing=()):
    r = {lsa.SITEMAP_INDEX: (200, b"<x>https://www.govinfo.gov/sitemap/LSA_2018_sitemap.xml</x>"),
         "https://www.govinfo.gov/sitemap/LSA_2018_sitemap.xml": (200, sitemap(issues))}
    for i in issues:
        if i in with_missing:
            continue
        t3 = T3 if i == "LSA-2018-01" else T3.replace("13820.............................................................18-969\n", "")
        r[lsa.PKG_ZIP.format(issue=i)] = (200, make_zip(i, {3: member("TITLE 3--THE PRESIDENT", t3), 32: member("TITLE 32--X", T32)}))
        r[lsa.MEMBER_URL.format(issue=i, title=3)] = (200, member("TITLE 3--THE PRESIDENT", t3))
    return r


class PipelineTests(unittest.TestCase):
    def test_run_dedupes_across_a_cumulative_year_and_writes_everything(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues = ["LSA-2018-01", "LSA-2018-02", "LSA-2018-03"]
            s, out, _ = run_main(tmp, routes_for(issues))
            self.assertEqual((s["issues_read_ok"], s["issues_failed"]), (3, 0))
            rows = list(csv.DictReader(open(out / "LSA_EO_ROWS.csv", newline="", encoding="utf-8")))
            keys = {(r["title"], r["category"], r["item"], r["change"], r["fr_ref"]) for r in rows}
            self.assertEqual(len(keys), len(rows))  # one row per distinct entry in the year
            r13799 = next(r for r in rows if r["item"] == "13799" and r["change"].startswith("Revoked"))
            self.assertEqual((r13799["first_issue"], r13799["last_issue"], r13799["n_issues"]), ("LSA-2018-01", "LSA-2018-03", "3"))
            self.assertEqual(r13799["fr_cite"], "83 FR 969")
            frags = [json.loads(x) for x in open(out / "FRAGMENTS.jsonl", encoding="utf-8")]
            f = next(x for x in frags if x["data"][0]["acting_id"] == "EO:13820")
            self.assertEqual((f["instrument_id"], f["kind"], f["data"][0]["mechanism_class"]), ("EO:13799", "later_event_candidates", "ending"))
            # quote_span re-slices from the held member bytes
            held = member("TITLE 3--THE PRESIDENT", T3)
            a, b = map(int, f["data"][0]["quote_span"].split("-"))
            self.assertIn("13799 Revoked by EO 13820", held[a:b].decode("latin-1"))
            self.assertEqual(f["data"][0]["source_sha256"], lsa.sha256(held))
            srcs = [json.loads(x) for x in open(out / "SOURCES.jsonl", encoding="utf-8")]
            self.assertTrue(all(x["instrument_ids"] == [] and len(x["sha256"]) == 64 for x in srcs))
            ctl = json.loads((out / "CONTROLS.json").read_text())
            self.assertEqual(ctl["control_error_rate"], 0.0)
            self.assertEqual(ctl["member_url_hash"]["failures"], 0)
            bj = json.loads((out / "BUDGET.json").read_text())
            self.assertFalse(bj["truncated"])
            self.assertLessEqual(bj["committed_bytes_total_with_this_file"], 20 * 1024 * 1024)
            self.assertEqual(s["eo_mention_rows_outside_title3"], 2)

    def test_resume_carries_prior_issues_without_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues = ["LSA-2018-01", "LSA-2018-02", "LSA-2018-03", "LSA-2018-04"]
            s1, out1, _ = run_main(tmp, routes_for(issues, with_missing=("LSA-2018-03", "LSA-2018-04")),
                                   today=dt.date(2018, 5, 5))
            self.assertEqual((s1["issues_read_ok"], s1["issues_not_found_speculative"]), (2, 0))
            prior = Path(tmp) / "prior"
            import shutil
            shutil.copytree(out1, prior)
            s2, out2, net2 = run_main(tmp, routes_for(issues), prior=prior, today=dt.date(2018, 5, 5))
            zips = [u for u in net2.calls if u.endswith(".zip")]
            # 01 and 02 are carried; 03 and 04 are read (the newest two are always re-read)
            self.assertNotIn(lsa.PKG_ZIP.format(issue="LSA-2018-01"), zips)
            self.assertNotIn(lsa.PKG_ZIP.format(issue="LSA-2018-02"), zips)
            self.assertEqual(s2["issues_carried_forward"], 2)
            rows = list(csv.DictReader(open(out2 / "LSA_EO_ROWS.csv", newline="", encoding="utf-8")))
            r = next(x for x in rows if x["item"] == "13799" and x["change"].startswith("Revoked"))
            self.assertEqual((r["first_issue"], r["last_issue"], r["n_issues"]), ("LSA-2018-01", "LSA-2018-04", "4"))
            frags = [json.loads(x) for x in open(out2 / "FRAGMENTS.jsonl", encoding="utf-8")]
            self.assertEqual(len([x for x in frags if x["data"][0]["acting_id"] == "EO:13820"]), 1)

    def test_job_fails_when_most_requests_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues = ["LSA-2018-01", "LSA-2018-02", "LSA-2018-03"]
            routes = routes_for(issues, with_missing=issues[:])
            for i in issues:
                routes[lsa.PKG_ZIP.format(issue=i)] = (500, b"boom")
            with self.assertRaises(SystemExit) as cm:
                import repetita as r
                r.time.sleep = lambda s: None  # no waiting on retries in the test
                run_main(tmp, routes, today=dt.date(2018, 4, 5))
            self.assertIn("failed", str(cm.exception))

    def test_govinfo_error_redirect_is_not_found_not_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            routes = routes_for(["LSA-2018-01"])
            routes[lsa.PKG_ZIP.format(issue="LSA-2018-02")] = (302, b"", {"location": "https://www.govinfo.gov/error"})
            routes["https://www.govinfo.gov/error"] = (200, b"<html>error page</html>")
            s, out, _ = run_main(tmp, routes, today=dt.date(2018, 3, 5))
            self.assertEqual((s["issues_read_ok"], s["issues_failed"], s["issues_not_found_speculative"]), (1, 0, 1))

    def test_key_handling_never_uses_demo_for_full_run_and_never_prints_key(self):
        self.assertEqual(lsa.api_key({"API_DATA_GOV_KEY": "abc", "GOVINFO_API_KEY": "zzz"}), ("abc", "real", "API_DATA_GOV_KEY"))
        self.assertEqual(lsa.api_key({"GOVINFO_API_KEY": "abc"}), ("abc", "real", "GOVINFO_API_KEY"))
        self.assertEqual(lsa.api_key({"GOVINFO_API_KEY": "DEMO_KEY"})[1], "demo")
        self.assertEqual(lsa.api_key({})[1], "none")
        calls = []

        class R(io.BytesIO):
            def __enter__(s):
                return s

            def __exit__(s, *a):
                pass

        def opener(req, timeout=0):
            calls.append((req.full_url, req.get_header("X-api-key")))
            return R(json.dumps({"packages": [{"packageId": "LSA-2018-01"}, {"packageId": "LSA-2018-02"}], "nextPage": None}).encode())
        with tempfile.TemporaryDirectory() as tmp:
            issues = ["LSA-2018-01", "LSA-2018-02"]
            s, out, _ = run_main(tmp, routes_for(issues), env={"GOVINFO_API_KEY": "DEMO_KEY", "_API_OPENER": opener})
            self.assertEqual(s["route"]["api_key_kind"], "demo_refused_for_full_run")
            self.assertFalse(s["route"]["api_crosscheck"]["attempted"])
            self.assertEqual(calls, [])
            s, out, _ = run_main(tmp, routes_for(issues), env={"API_DATA_GOV_KEY": "SECRETKEY", "_API_OPENER": opener})
            self.assertEqual(s["route"]["api_crosscheck"]["api_issues"], 2)
            self.assertEqual(calls[0][1], "SECRETKEY")
            self.assertNotIn("SECRETKEY", calls[0][0])
            for f in out.iterdir():
                self.assertNotIn(b"SECRETKEY", f.read_bytes())

    def test_speculative_404_is_not_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            routes = routes_for(["LSA-2018-01"])
            routes["https://www.govinfo.gov/sitemap/LSA_2018_sitemap.xml"] = (200, sitemap(["LSA-2018-01"]))
            s, out, _ = run_main(tmp, routes, today=dt.date(2018, 3, 5))  # Feb 2018 is speculative and 404
            self.assertEqual((s["issues_read_ok"], s["issues_failed"], s["issues_not_found_speculative"]), (1, 0, 1))


class PreWarTests(unittest.TestCase):
    def hathi_gz(self):
        def line(htid, access, title, desc, year, bib="100", gov="1"):
            f = [htid, access, "pd", bib, desc, "MIU", "1", "555", "", "", "", title, "Washington", "bib", "2020-01-01", gov,
                 str(year), "dcu", "eng", "BK", "MIU", "umich", "umich", "google", "google", "US"]
            return "\t".join(f)
        rows = [line("uc1.a", "allow", "List of CFR sections affected", "1973-1985 v.3", 1985),
                line("uc1.b", "deny", "List of CFR sections affected", "1986", 1986),
                line("uc1.c", "allow", "List of CFR sections affected", "1998", 1998, bib="101"),
                line("uc1.d", "allow", "Code of Federal Regulations", "Title 3 1949", 1949, bib="102"),
                line("uc1.e", "allow", "Code of Federal Regulations", "Title 21 1949", 1949, bib="102"),
                line("uc1.f", "allow", "Codification of presidential proclamations and executive orders", "1945-1989", 1989, bib="103"),
                line("uc1.g", "allow", "Moby Dick", "", 1851)]
        return gzip.compress(("\n".join(rows) + "\n").encode())

    def test_scan_hathifile(self):
        gz = self.hathi_gz()

        class R(io.BytesIO):
            status = 200
        rows, st = prewar.scan_hathifile(lambda u, ua: R(gz), "u", "ua")
        ids = {r["id"]: r for r in rows}
        self.assertEqual(sorted(ids), ["uc1.a", "uc1.b", "uc1.d", "uc1.f"])  # not 1998+, not Moby Dick, not a Title 21 CFR volume
        self.assertEqual((ids["uc1.a"]["series"], ids["uc1.a"]["access"]), ("lsa", "allow"))
        self.assertEqual(ids["uc1.b"]["access"], "deny")
        self.assertEqual(st["lsa_full_view"], 1)
        self.assertEqual(st["year_1997_or_later"], 1)
        self.assertEqual(len(st["sha256"]), 64)

    def test_scan_rejects_a_changed_layout(self):
        gz = gzip.compress(b"a\tb\tc\n")

        class R(io.BytesIO):
            status = 200
        with self.assertRaises(Exception):
            prewar.scan_hathifile(lambda u, ua: R(gz), "u", "ua")

    def test_hathifile_blocked_falls_back_to_bib_api_and_records_survey_leads(self):
        bib = json.dumps({"records": {"x": {"titles": ["LSA, list of CFR sections affected"], "oclcs": ["1"], "lccns": ["sn1"], "publishDates": ["1977"]}},
                          "items": [{"htid": "inu.1", "itemURL": "https://babel.hathitrust.org/cgi/pt?id=inu.1", "rightsCode": "pd", "enumcron": "1985", "usRightsString": "Full view"},
                                    {"htid": "inu.2", "itemURL": "u2", "rightsCode": "ic", "enumcron": "1990", "usRightsString": "Limited (search-only)"},
                                    {"htid": "inu.3", "itemURL": "u3", "rightsCode": "pd", "enumcron": "1999", "usRightsString": "Full view"}]}).encode()
        routes = {"https://catalog.hathitrust.org/api/volumes/brief/recordnumber/*": (200, bib),
                  prewar.IA_SEARCH + "*": (200, json.dumps({"response": {"docs": []}}).encode())}
        # the hathifile list is answered with a challenge page (403): robots cannot be read and nothing is evaded
        routes[prewar.HATHI_LIST] = (403, b"challenge")
        with tempfile.TemporaryDirectory() as tmp:
            pool = FetchPool(Path(tmp), transport=Net(routes), min_interval=0)
            prewar.SEED_DIR = Path(tmp) / "no-seed"
            rows, summ = prewar.build(pool, "ua", log=lambda *a: None, wait=0)
        self.assertIn("error", summ["hathi"])
        self.assertEqual(summ["hathi"]["fallback"]["failed"], 0)
        ids = {r["id"]: r for r in rows}
        self.assertEqual(sorted(ids), ["inu.1", "inu.2"])  # 1999 is not pre-1997
        self.assertEqual((ids["inu.1"]["access"], ids["inu.2"]["access"]), ("allow", "deny"))
        self.assertIn("heinonline", [x["id"] for x in summ["survey_leads"]])
        self.assertTrue(summ["hathi_read_check"]["attempted"])  # robots verdict recorded, page never read

    def test_hathifile_blocked_uses_committed_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            seed = Path(tmp) / "seed"
            seed.mkdir()
            row = {c: "" for c in prewar.MANIFEST_COLUMNS}
            row.update(source="hathitrust", id="uc1.z", series="lsa", access="allow", year="1985")
            with open(seed / "MANIFEST.csv", "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=prewar.MANIFEST_COLUMNS, lineterminator="\n")
                w.writeheader()
                w.writerow(row)
            (seed / "SCAN.json").write_text(json.dumps({"made_utc": "x"}))
            prewar.SEED_DIR = seed
            routes = {prewar.HATHI_LIST: (403, b"challenge"), prewar.IA_SEARCH + "*": (200, json.dumps({"response": {"docs": []}}).encode())}
            pool = FetchPool(Path(tmp) / "c", transport=Net(routes), min_interval=0)
            rows, summ = prewar.build(pool, "ua", log=lambda *a: None, wait=0)
        self.assertEqual([r["id"] for r in rows], ["uc1.z"])
        self.assertEqual(summ["hathi"]["seed"]["rows"], 1)
        self.assertNotIn("fallback", summ["hathi"])

    def test_build_with_fake_hosts(self):
        gz = self.hathi_gz()
        ia = json.dumps({"response": {"docs": [
            {"identifier": "micro_X1", "title": "List of CFR Sections Affected, 1973-1985. Volume III", "date": "1985-01-01T00:00:00Z", "publisher": ["GPO"]},
            {"identifier": "later", "title": "List of CFR Sections Affected 1999", "date": "1999-01-01T00:00:00Z"}]}}).encode()
        meta = json.dumps({"metadata": {"publisher": "GPO"}, "files": [{"name": "micro_X1_djvu.txt"}]}).encode()
        txt = b"LIST OF CFR SECTIONS AFFECTED\nTitle 3\nExecutive Order 11111 amended\nE.O. 2222\n"
        bib = json.dumps({"items": [{"htid": "uc1.a", "usRightsString": "Full view"}, {"htid": "uc1.b", "usRightsString": "Limited (search-only)"}]}).encode()
        listing = json.dumps([{"filename": "hathi_full_20260101.txt.gz", "full": True, "size": len(gz),
                               "url": "https://www.hathitrust.org/files/hathifiles/hathi_full_20260101.txt.gz"}]).encode()
        routes = {prewar.HATHI_LIST: (200, listing), "https://catalog.hathitrust.org/api/volumes/brief/recordnumber/*": (200, bib),
                  prewar.IA_SEARCH + "*": (200, ia), prewar.IA_META.format(id="micro_X1"): (200, meta),
                  prewar.IA_TEXT.format(id="micro_X1"): (200, txt)}

        class R(io.BytesIO):
            status = 200
        with tempfile.TemporaryDirectory() as tmp:
            pool = FetchPool(Path(tmp), transport=Net(routes), min_interval=0)
            rows, summ = prewar.build(pool, "ua", opener=lambda u, ua: R(gz), log=lambda *a: None)
        ia_rows = [r for r in rows if r["source"] == "internet_archive"]
        self.assertEqual([r["id"] for r in ia_rows], ["micro_X1"])  # 1999 volume is not pre-1997
        self.assertTrue(summ["smoke_read_internet_archive"]["ok"])
        self.assertEqual(summ["smoke_read_internet_archive"]["executive_order_mentions"], 2)
        self.assertEqual(summ["hathi"]["bib_api"]["disagree"], 0)
        self.assertEqual(summ["hathi"]["bib_api"]["agree"], 2)
        self.assertEqual(summ["manifest_by_source_series_access"]["hathitrust:lsa:full_view"], 1)
        self.assertEqual(summ["manifest_by_source_series_access"]["hathitrust:lsa:not_full_view"], 1)
        self.assertIn("1985", summ["lsa_full_view_years"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
