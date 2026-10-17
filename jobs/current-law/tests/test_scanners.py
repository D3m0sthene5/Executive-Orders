import pathlib
import unittest

import ecfr_scan
import usc_scan

FIX = pathlib.Path(__file__).parent / "fixtures"


class ReleasePoints(unittest.TestCase):
    def setUp(self):
        html = (FIX / "download.html").read_text(encoding="utf-8")
        self.points = usc_scan.parse_release_points(html, "https://uscode.house.gov/download.html")

    def test_parse(self):
        self.assertEqual([p["id"] for p in self.points], ["119-125", "119-121", "119-118"])
        p = self.points[1]
        self.assertEqual(p["date"], "2026-10-09")
        self.assertTrue(p["all_zip_url"].endswith("/119/121/xml_uscAll@119-121.zip"))
        self.assertEqual(sorted(p["title_zip_urls"]), ["03", "05a"])  # XHTML link ignored
        self.assertTrue(p["title_zip_urls"]["03"].startswith("https://uscode.house.gov/download/releasepoints/"))

    def test_choose_latest_on_or_before_cutoff(self):
        best, why, problems = usc_scan.choose_release(self.points)
        self.assertEqual(best["id"], "119-121")
        self.assertEqual(problems, [])
        self.assertEqual(usc_scan.choose_release(self.points, override="119-118")[0]["id"], "119-118")
        self.assertEqual(usc_scan.choose_release(self.points, pinned="119-121")[0]["id"], "119-121")

    def test_only_post_cutoff_points_listed(self):
        later = [p for p in self.points if p["id"] == "119-125"]
        # pinned default: built from the stable URL pattern, still dated 2026-10-09
        rp, why, problems = usc_scan.choose_release(later, pinned="119-121")
        self.assertEqual(rp["id"], "119-121")
        self.assertEqual(rp["date"], "2026-10-09")
        self.assertEqual(rp["all_zip_url"],
                         "https://uscode.house.gov/download/releasepoints/us/pl/119/121/xml_uscAll@119-121.zip")
        self.assertEqual(rp["title_zip_urls"]["05a"],
                         "https://uscode.house.gov/download/releasepoints/us/pl/119/121/xml_usc05a@119-121.zip")
        self.assertIn("stable OLRC pattern", why)
        self.assertEqual(usc_scan.usc_checked_through(rp), "2026-10-09")
        # an explicit override of an unlisted point no longer crashes
        rp2, _, _ = usc_scan.choose_release(later, override="119-121")
        self.assertEqual(rp2["id"], "119-121")
        # "auto" falls back to the post-cutoff point and says so; no checked_through date
        rp3, why3, problems3 = usc_scan.choose_release(later, override="auto")
        self.assertEqual(rp3["id"], "119-125")
        self.assertIn("NO release point", why3)
        self.assertTrue(any("AFTER the cutoff" in p for p in problems3))
        self.assertIsNone(usc_scan.usc_checked_through(rp3))
        self.assertIn("NOT evidence", usc_scan.usc_currency_note(rp3))
        # unknown point: date unknown, no checked_through, problem reported
        rp4, _, problems4 = usc_scan.choose_release(later, override="119-130")
        self.assertIsNone(rp4["date"])
        self.assertIsNone(usc_scan.usc_checked_through(rp4))
        self.assertTrue(problems4)
        rp5, _, _ = usc_scan.choose_release(later, override="119-123@2026-10-13")
        self.assertEqual(usc_scan.usc_checked_through(rp5), "2026-10-13")

    def test_newer_listed_point_reported(self):
        pts = [dict(p) for p in self.points]
        pts[0]["date"] = "2026-10-13"  # pretend 119-125 is current through a law before the cutoff
        rp, _, problems = usc_scan.choose_release(pts, pinned="119-121")
        self.assertEqual(rp["id"], "119-121")
        self.assertTrue(any("newer U.S. Code release point" in p for p in problems))

    def test_title_codes(self):
        self.assertEqual(usc_scan.norm_title_code("5"), "05")
        self.assertEqual(usc_scan.norm_title_code("05A"), "05a")
        self.assertEqual(usc_scan.norm_title_code(" 50 "), "50")

    def test_cite(self):
        self.assertEqual(usc_scan.cite("/us/usc/t5/s3301"), "5 U.S.C. 3301")
        self.assertEqual(usc_scan.cite("/us/usc/t50/ch15"), "50 U.S.C. ch. 15")
        self.assertEqual(usc_scan.cite("/us/usc/t5a/s1"), "5 App. U.S.C. 1")
        self.assertEqual(usc_scan.cite("/us/usc/t10/stA/ptII/ch57"), "10 U.S.C. subtitle A, pt. II, ch. 57")
        self.assertEqual(usc_scan.cite("/us/usc/t22/ch23/schII"), "22 U.S.C. ch. 23, subch. II")
        self.assertEqual(usc_scan.cite("/us/usc/t42/s2031 /us/usc/t42/s2032"), "42 U.S.C. 2031, 2032")
        self.assertEqual(usc_scan.cite("/us/usc/t50"), "50 U.S.C. (title level)")
        self.assertEqual(usc_scan.cite("/us/usc/t5/spt3/ptA"), "5 U.S.C. subpt. 3, pt. A")


class Uslm(unittest.TestCase):
    def setUp(self):
        with open(FIX / "usc_sample.xml", "rb") as f:
            self.recs = list(usc_scan.scan_uslm(f, "usc99.xml"))
        self.mentions = [r for k, r in self.recs if k == "mention"]
        self.events = [r for k, r in self.recs if k == "event"]

    def roles(self, number):
        return sorted({m["role"] for m in self.mentions if m["eo_number"] == number})

    def test_roles(self):
        self.assertIn("statutory_text_reference", self.roles(13526))
        self.assertIn("references_in_text_note", self.roles(13526))
        self.assertEqual(self.roles(12333), ["statutory_note_reference"])
        self.assertEqual(self.roles(10450), ["printed_eo_text"])
        self.assertEqual(self.roles(10491), ["amending_order_in_status_line"])
        self.assertEqual(self.roles(9835), ["mentioned_in_printed_eo_text"])
        self.assertEqual(self.roles(11230), ["eo_note_ended_status"])
        self.assertEqual(self.roles(11609), ["ending_order_in_status_line"])
        self.assertEqual(self.roles(11275), ["amending_order_in_ended_status_line"])

    def test_citations(self):
        m = next(m for m in self.mentions if m["role"] == "printed_eo_text")
        self.assertEqual(m["citation"], "99 U.S.C. 101 note")
        self.assertEqual(m["note_id"], "n-printed")
        s = next(m for m in self.mentions if m["role"] == "statutory_text_reference")
        self.assertEqual(s["citation"], "99 U.S.C. 101")
        self.assertIn("Executive Order 13526", s["snippet"])

    def test_events(self):
        got = {(e["subject_number"], e["verb"], (e["actor"] or {}).get("kind"),
                ((e["actor"] or {}).get("ref") or {}).get("number")) for e in self.events}
        self.assertIn((11230, "superseded", "executive_order", 11609), got)
        self.assertIn((10450, "amended", "executive_order", 10491), got)
        self.assertIn((10450, "amended", "statute", None), got)
        self.assertIn((10450, "revoked", "executive_order", 14000), got)   # bracketed partial revocation
        self.assertIn((9835, "revoked", "executive_order", 10450), got)    # revoked by the printed order itself
        self.assertIn((14100, "revoked", "executive_order", 14999), got)   # kept here, filtered by cutoff later

    def test_eo_note_text_kept(self):
        notes = [r for k, r in self.recs if k == "eo_note"]
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["subjects"], ["10450"])
        self.assertIn("Security Requirements", notes[0]["text"])


class Ecfr(unittest.TestCase):
    def test_bulk_xml(self):
        with open(FIX / "ecfr_sample.xml", "rb") as f:
            recs = list(ecfr_scan.scan_ecfr_xml(f, 99))
        self.assertEqual(recs[0], ("amddate", "2026-10-15"))
        ms = [r for k, r in recs if k == "mention"]
        got = {(m["eo_number"], m["role"], m["citation"]) for m in ms}
        self.assertIn((12866, "cfr_authority_citation", "99 CFR part 10"), got)
        self.assertIn((12372, "cfr_text_reference", "99 CFR 10.1"), got)
        self.assertIn((12416, "cfr_text_reference", "99 CFR 10.1"), got)
        self.assertIn((14410, "cfr_source_citation", "99 CFR 10.1"), got)
        self.assertIn((13563, "cfr_text_reference", "99 CFR 10.2"), got)
        self.assertIn((13224, "cfr_appendix_text_reference", "99 CFR part 10, Appendix A to Part 10"), got)
        sec = next(m for m in ms if m["eo_number"] == 12372)
        self.assertEqual(sec["human_url"], "https://www.ecfr.gov/on/2026-10-14/title-99/section-10.1")
        # the CITA text is not double counted as section text
        self.assertFalse(any(m["eo_number"] == 14410 and m["role"] == "cfr_text_reference" for m in ms))

    def test_search_page(self):
        meta, hits = ecfr_scan.parse_search_page((FIX / "search_page.json").read_bytes())
        self.assertEqual(meta["total_pages"], 1)
        self.assertEqual(hits[0]["section"], "10.1")
        ms = ecfr_scan.search_hit_mentions(hits[0])
        self.assertEqual(sorted(m["eo_number"] for m in ms), [12372, 12416])
        self.assertEqual(ms[0]["citation"], "99 CFR 10.1")
        self.assertEqual(sorted(m["eo_number"] for m in ecfr_scan.search_hit_mentions(hits[1])), [10577, 99999])

    def test_versions(self):
        secs, parts, rows = ecfr_scan.changed_after((FIX / "versions.json").read_bytes())
        self.assertEqual(secs, {"10.2"})  # 10.7 changed ON the cutoff: in force that day
        self.assertEqual(parts, {"10"})
        self.assertEqual(rows, 1)

    def test_currency_flag(self):
        rows = ecfr_scan.version_rows((FIX / "versions.json").read_bytes())
        f = ecfr_scan.currency_flag
        self.assertEqual(f({"section": "10.2", "part": "10"}, rows, "2026-10-15"), "yes")
        self.assertEqual(f({"section": "10.1", "part": "10"}, rows, "2026-10-15"), "no")
        # bulk file older than a version in force on the cutoff
        self.assertEqual(f({"section": "10.7", "part": "10"}, rows, "2026-10-01"), "file_older_than_cutoff_version")
        self.assertEqual(f({"section": "", "part": "10"}, rows, "2026-10-15"), "part_has_changes")
        self.assertTrue(f({"section": "10.1", "part": "10"}, None, "2026-10-15").startswith("unknown"))

    def test_state_plan_parts_flagged(self):
        self.assertEqual(ecfr_scan.state_program_part("40", "52"), "state_plan_approval_part")
        self.assertEqual(ecfr_scan.state_program_part("30", "913"), "state_plan_approval_part")
        self.assertEqual(ecfr_scan.state_program_part("5", "1"), "")
        self.assertEqual(ecfr_scan.state_program_part("40", ""), "")

    def test_search_url_is_point_in_time(self):
        u = ecfr_scan.search_url('"Executive Order"', 2)
        self.assertIn("date=2026-10-14", u)
        self.assertIn("page=2", u)
        self.assertTrue(u.startswith("https://www.ecfr.gov/api/search/v1/results?"))


if __name__ == "__main__":
    unittest.main()
