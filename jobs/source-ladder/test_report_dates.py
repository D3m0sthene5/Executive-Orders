"""PANIZZI-2 (2026-10-20): the report-date lane. No network; every document is a small fixture.

The lane returns the transmittal RECORD with hashes and verbatim dated lines. These tests also check that it never
asserts a date.
"""
import datetime as dt
import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_ladder as fl  # noqa: E402
import ladder_queue  # noqa: E402
import report_dates as rd  # noqa: E402
from test_fetch_ladder import Base, FakeResp, FakeTransport, make_pdf  # noqa: E402

H = {"content-type": "text/html"}
PDFH = {"content-type": "application/pdf"}
XMLH = {"content-type": "application/xml"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


class RangeTransport(FakeTransport):
    """Like FakeTransport, but a URL listed in `files` answers Range requests with 206 and Content-Range."""

    def __init__(self, routes, files=None, **kw):
        super().__init__(routes, **kw)
        self.files = files or {}
        self.range_calls = []

    def __call__(self, url, headers, timeout):
        if url in self.files and "Range" in headers:
            data = self.files[url]
            a, b = re.fullmatch(r"bytes=(\d+)-(\d+)", headers["Range"]).groups()
            a, b = int(a), min(int(b), len(data) - 1)
            self.range_calls.append((url, a, b))
            return 206, {"content-range": f"bytes {a}-{b}/{len(data)}", "last-modified": "Fri, 07 Jun 2019 16:44:39 GMT",
                         "content-type": "application/pdf"}, FakeResp(data[a:b + 1])
        if url in self.files:
            return 200, {"content-type": "application/pdf"}, FakeResp(self.files[url])
        return super().__call__(url, headers, timeout)


# ---------------------------------------------------------------- pure functions

class ClassifyTests(unittest.TestCase):
    POS = [
        "Actual emergency-board report submitted under EO12495, including submission date; section4 termination",
        "Emergency board report under Executive Order12085, Norfolk and Western Railway; actual submission date and any extension",
        "Presidential Emergency Board created by EO 14077 (July 15, 2022; 87 FR 43203): report to the President, date submitted (National Mediation Board)",
        "Date the National Commission on Social Security Reform (EO 12335) submitted its report to the President (report due by 1983-01-20 under EO 12402)",
        "National Advisory Commission on Food and Fiber: actual final report submission/transmittal evidence, not report deadline",
        "Board of Inquiry created by Executive Order12042 (bituminous coal industry), report and all continuation/termination records",
        "HHS report responding to Executive Order14087 section2 within90days of October14,2022; report submission date and actions",
    ]
    NEG = [
        "Text and effective date of sec. 1511 of Pub. L. 98-525 (98 Stat. 2492) establishing the Chemical Warfare Review Commission, for any statutory term and the reports it requires",
        "Railway Labor Act,44 Stat.577, actual section10 emergency-board powers/report and statutory restrictions; resolve exact effective/continuation rules",
        "3 U.S.C. 110 note ('Ex. Ord. No. 11145 ... as amended by Ex. Ord. No. 11565')",
        "87th Congress term dates (1961-01-03 to 1963-01-03) and U.S. Const. amend. XX sec. 1",
    ]

    def test_positive_and_negative(self):
        for t in self.POS:
            self.assertTrue(rd.is_report_date_request(t), t)
        for t in self.NEG:
            self.assertFalse(rd.is_report_date_request(t), t)

    def test_note_alone_can_make_the_request(self):
        c = "National Mediation Board records: emergency board established September 20, 1979 by EO 12159 for Chicago, Rock Island"
        self.assertFalse(rd.is_report_date_request(c))
        self.assertTrue(rd.is_report_date_request(c + " Discover actual board report, transmittal/receipt date"))
        spec = rd.build_spec(c, ["EO:12159"], {"12159": "1979-09-20"}, "Discover actual board report, transmittal/receipt date")
        self.assertEqual((spec["kind"], spec["lane"]), ("peb", "nmb"))

    def test_spec_for_commission_with_due_date(self):
        s = rd.build_spec("Date the National Commission on Social Security Reform (EO 12335) submitted its report to the President "
                          "(report due by 1983-01-20 under EO 12402); Public Papers of the Presidents 1983", ["EO:12335"],
                          {"12335": "1981-12-16"})
        self.assertEqual((s["kind"], s["lane"], s["due"], s["anchor"], s["year"]), ("commission", "ppp", "1983-01-20", "1983-01-20", 1983))
        self.assertEqual(s["body"], "National Commission on Social Security Reform")
        self.assertEqual(s["eo_numbers"], ["12335", "12402"])
        self.assertNotIn("report_date", s)

    def test_spec_window_and_lanes(self):
        s = rd.build_spec("Date the President's Special Review Board (Tower Commission) submitted its report to the President, from the "
                          "Public Papers; week of 1987-02-23 to 1987-03-02", ["EO:12575"])
        self.assertEqual((s["window"], s["anchor"], s["body"]), (["1987-02-23", "1987-03-02"], "1987-02-23", "President's Special Review Board"))
        w = rd.build_spec("Date the President's Commission on Mental Health (EO 11973) report transmitted; due 1997-04-01", ["EO:11973"])
        self.assertEqual(w["lane"], "wcpd")
        d = rd.build_spec("Date the President's Task Force on Aviation (EO 14000) submitted its report to the President; due 2012-04-01", ["EO:14000"])
        self.assertEqual(d["lane"], "dcpd")
        self.assertIn("report_after_2009", rd.no_route_reason(d))
        a = rd.build_spec("Dates the Secretary of the Interior actually submitted the EO 13792 interim report to the President", ["EO:13792"])
        self.assertEqual((a["kind"], a["lane"]), ("agency", "none"))
        self.assertIn("agency", rd.no_route_reason(a))

    def test_signing_date_alone_brackets_a_board_of_inquiry_but_not_a_commission(self):
        t = "Board of Inquiry created by Executive Order12042 (bituminous coal industry), report and all continuation/termination records"
        b = rd.build_spec(t, ["EO:12042"], {"12042": "1978-03-06"})
        self.assertEqual((b["kind"], b["lane"], b["window"]), ("inquiry", "ppp", ["1978-03-06", "1978-04-05"]))
        c = rd.build_spec("Actual Women in American History commission final report submission and any expiration", ["EO:13090"],
                          {"13090": "1998-06-29"})
        self.assertEqual((c["body"], c["lane"]), ("Women in American History commission", "none"))
        self.assertIn("report_date_cannot_be_bracketed", rd.no_route_reason(c))
        self.assertEqual(rd.body_name("Actual Digital Television advisory committee report submission"), "Digital Television advisory committee")

    def test_body_name(self):
        self.assertEqual(rd.body_name("Date the Committee on Selection of the Director of the FBI submitted its report"),
                         "Committee on Selection of the Director of the FBI")
        self.assertEqual(rd.body_name("Date the President's Blue Ribbon Task Group on Nuclear Weapons Program Management (EO 12499) submitted"),
                         "President's Blue Ribbon Task Group on Nuclear Weapons Program Management")
        self.assertEqual(rd.body_name("nothing here"), "")

    def test_parse_dates(self):
        self.assertEqual(rd.parse_dates("created November2,1978 and July 15, 2022; 3/31/1972; 1987-02-26; bogus 13/45/2000"),
                         ["1978-11-02", "2022-07-15", "1972-03-31", "1987-02-26"])


PEB_TABLE = """<html><body><table>
<tr><th>PEB</th><th>Carriers</th></tr>
<tr><td>250</td><td>National Carriers Conference Committee</td><td>R10</td><td>ATDA, BLET, BRS</td><td>Multiple</td><td>7/18/2022</td><td>8/16/2022</td><td></td>
    <td><a href="https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/PEB-250-Report.pdf">Report</a></td></tr>
<tr><td>206</td><td>Long Island RR</td><td>R9</td><td>BRAC/ARASA</td><td>Clerk, Station &amp; Storehouse</td><td>10/25/1984</td><td>12/24/1984</td><td>Second PEB</td>
    <td><a href="https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/PEB-206-Report-2d-PEB.pdf">Report</a></td></tr>
<tr><td>205</td><td>Long Island RR</td><td>R9</td><td>BLE</td><td>locomotive engineers</td><td>10/25/1984</td><td>12/24/1984</td><td>Second PEB</td>
    <td><a href="https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/PEB-205-Report-2d-PEB.pdf">Report</a></td></tr>
<tr><td>136</td><td>Northwest Airlines</td><td>R10</td><td>ALPA</td><td>Pilots</td><td>2/24/1961</td><td>5/24/1961</td><td></td>
    <td><a href="https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/PEB-136-Report.pdf">Report</a></td></tr>
<tr><td>77</td><td>Southern Pacific Co.</td><td>R10</td><td>BRT</td><td>Trainmen</td><td>7/20/1949</td><td>9/1/1949</td><td></td>
    <td><a href="https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/PEB-077-Report.pdf">Report</a></td></tr>
</table></body></html>"""


class PebTests(unittest.TestCase):
    def rows(self):
        return rd.parse_peb_table(PEB_TABLE)

    def test_table_parse(self):
        rows = self.rows()
        self.assertEqual([r["peb"] for r in rows], [250, 206, 205, 136, 77])
        self.assertEqual(rows[1]["craft"], "Clerk, Station & Storehouse")
        self.assertTrue(rows[0]["pdfs"][0].endswith("PEB-250-Report.pdf"))

    def spec(self, text, eo, date):
        return rd.build_spec(text, [f"EO:{eo}"], {str(eo): date})

    def test_created_within_three_days(self):
        m = rd.match_peb(self.rows(), self.spec("Presidential Emergency Board created by EO 14077: report to the President, date submitted", 14077, "2022-07-15"))
        self.assertEqual([c["peb"] for c in m], [250])
        self.assertEqual(m[0]["basis"], "created_within_3_days_of_order_date")

    def test_two_boards_created_the_same_day_are_both_returned(self):
        m = rd.match_peb(self.rows(), self.spec("Actual emergency-board report under EO12492 Long Island Rail Road, submission date", 12492, "1984-10-25"))
        self.assertEqual(sorted(c["peb"] for c in m), [205, 206])

    def test_union_named_breaks_the_tie(self):
        m = rd.match_peb(self.rows(), self.spec("Actual emergency-board report under EO12491 Long Island Rail Road locomotive engineers BLE, submission date", 12491, "1984-10-25"))
        self.assertEqual(m[0]["peb"], 205)

    def test_amending_order_inside_the_board_life_needs_the_carrier(self):
        spec = self.spec("Emergency board report under Executive Order10933 Northwest Airlines, actual submission date", 10933, "1961-03-30")
        m = rd.match_peb(self.rows(), spec)
        self.assertEqual([c["peb"] for c in m], [136])
        self.assertEqual(m[0]["basis"], "order_date_inside_board_life_and_carrier_named")
        none = rd.match_peb(self.rows(), self.spec("Emergency board report under Executive Order10933, actual submission date", 10933, "1961-03-30"))
        self.assertEqual(none, [])

    def test_front_matter_date_lines_are_verbatim_and_unlabelled(self):
        pages = [(1, "REPORT TO THE PRESIDENT\nby Emergency Board No. 250\nWashington, D.C. August 16, 2022\nThe President"),
                 (2, "Created July 18, 2022 by Executive Order 14077\nno date here")]
        leads = rd.front_matter_date_lines(pages)
        self.assertEqual(leads, [{"page": 1, "line": "Washington, D.C. August 16, 2022"},
                                 {"page": 2, "line": "Created July 18, 2022 by Executive Order 14077"}])


MODS = """<?xml version="1.0"?>
<mods xmlns="http://www.loc.gov/mods/v3" xmlns:xlink="http://www.w3.org/1999/xlink">
 <relatedItem type="constituent" ID="id-WCPD-1997-01-13-Pg11">
  <titleInfo><title>Remarks on Receiving the Final Report of the President&apos;s Commission on Mental Health</title></titleInfo>
  <location><url access="raw object">https://www.govinfo.gov/content/pkg/WCPD-1997-01-13/html/WCPD-1997-01-13-Pg11.htm</url></location>
 </relatedItem>
 <relatedItem type="constituent" ID="id-WCPD-1997-01-13-Pg7">
  <titleInfo><title>The President&apos;s Radio Address</title></titleInfo>
  <location><url access="raw object">https://www.govinfo.gov/content/pkg/WCPD-1997-01-13/html/WCPD-1997-01-13-Pg7.htm</url></location>
 </relatedItem>
 <relatedItem type="constituent" ID="id-WCPD-1997-01-13-Pg20">
  <titleInfo><title>Digest of Other White House Announcements</title></titleInfo>
  <location><url access="raw object">https://www.govinfo.gov/content/pkg/WCPD-1997-01-13/html/WCPD-1997-01-13-Pg20.htm</url></location>
 </relatedItem>
 <relatedItem type="constituent" ID="id-x"><titleInfo><title>Message on the Report of the Council of Economic Advisers</title></titleInfo>
  <location><url access="raw object">https://www.govinfo.gov/content/pkg/WCPD-1997-01-13/html/WCPD-1997-01-13-Pg30.htm</url></location></relatedItem>
</mods>"""


class WcpdTests(unittest.TestCase):
    def test_issue_dates_are_mondays_in_range_nearest_first(self):
        days = rd.wcpd_issue_dates("1997-01-10")
        self.assertTrue(all(dt.date.fromisoformat(d).weekday() == 0 for d in days))
        self.assertLessEqual(len(days), rd.MAX_WCPD_ISSUES)
        self.assertEqual(days[0], "1997-01-06")
        self.assertEqual(rd.wcpd_issue_dates("2009-06-01"), [])             # after the last issue
        self.assertTrue(all("1993-01-25" <= d for d in rd.wcpd_issue_dates("1993-02-01")))

    def test_mods_titles(self):
        items = rd.parse_wcpd_mods(MODS)
        self.assertEqual(len(items), 4)
        spec = rd.build_spec("Date the President's Commission on Mental Health submitted its report; due 1997-01-10", ["EO:1"])
        hits, digests = rd.rank_wcpd_titles(items, spec)
        self.assertEqual([h["title"][:20] for h in hits], ["Remarks on Receiving"])
        self.assertEqual(len(digests), 1)


class RangeFileTests(unittest.TestCase):
    def test_pypdf_reads_selected_pages_through_ranges_within_bounds(self):
        import pypdf
        pages = [[f"Feb. {1 + i // 10} / Administration of Ronald Reagan, 1987", f"body {i}"] for i in range(120)]
        data = make_pdf(pages)
        calls = []

        def get(a, b):
            calls.append((a, b))
            return data[a:b + 1]
        rf = rd.RangeFile(get, len(data), block=4096, max_bytes=10 ** 7, max_requests=1000)
        reader = pypdf.PdfReader(rf, strict=True)
        self.assertEqual(len(reader.pages), 120)
        self.assertIn("body 77", reader.pages[77].extract_text())
        self.assertLessEqual(rf.bytes_read, len(data))
        self.assertEqual(rf.requests, len(calls))

    def test_image_streams_are_skipped_and_text_is_unchanged(self):
        import pypdf
        # three scanned-style pages: a hidden-text layer plus a 400 KB image XObject each
        objs = [b"<< /Type /Catalog /Pages 2 0 R >>", None, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
        kids = []
        for i in range(3):
            img = b"\x01\x02" * 200_000
            objs.append(b"<< /Type /XObject /Subtype /Image /Width 400 /Height 400 /ColorSpace /DeviceGray /BitsPerComponent 8 "
                        b"/Length %d >>\nstream\n" % len(img) + img + b"\nendstream")
            img_id = len(objs)
            c = b"q 612 0 0 792 0 0 cm /Im0 Do Q BT /F1 12 Tf 40 700 Td (Remarks on Receiving the Report page %d) Tj ET" % i
            objs.append(b"<< /Length %d >>\nstream\n" % len(c) + c + b"\nendstream")
            cid = len(objs)
            objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents %d 0 R /Resources << /Font << /F1 3 0 R >> "
                        b"/XObject << /Im0 %d 0 R >> >> >>" % (cid, img_id))
            kids.append(len(objs))
        objs[1] = b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % k for k in kids) + b"] /Count 3 >>"
        out = io.BytesIO()
        out.write(b"%PDF-1.4\n")
        offs = []
        for i, body in enumerate(objs, 1):
            offs.append(out.tell())
            out.write(b"%d 0 obj\n" % i + body + b"\nendobj\n")
        xref = out.tell()
        out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
        for o in offs:
            out.write(b"%010d 00000 n \n" % o)
        out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref))
        data = out.getvalue()
        texts = {}
        for skip in (True, False):
            rf = rd.RangeFile(lambda a, b: data[a:b + 1], len(data), block=65536, max_bytes=10 ** 8, max_requests=10 ** 4,
                              skip_images=skip)
            reader = pypdf.PdfReader(rf, strict=True)
            texts[skip] = [reader.pages[i].extract_text() for i in range(3)]
            if skip:
                skipped_bytes_read, skipped = rf.bytes_read, rf.skipped_bytes
            else:
                full_bytes_read = rf.bytes_read
        self.assertEqual(texts[True], texts[False])
        self.assertIn("Receiving the Report page 2", texts[True][2])
        self.assertGreaterEqual(skipped, 3 * 400_000)
        self.assertLess(skipped_bytes_read, full_bytes_read // 3)

    def test_ceiling_raises(self):
        data = b"x" * 100000
        rf = rd.RangeFile(lambda a, b: data[a:b + 1], len(data), block=1000, max_bytes=5000, max_requests=100)
        rf.seek(0)
        with self.assertRaises(rd.RangeLimit):
            rf.read(20000)
        rf2 = rd.RangeFile(lambda a, b: data[a:b + 1], len(data), block=1000, max_bytes=10 ** 6, max_requests=3)
        with self.assertRaises(rd.RangeLimit):
            rf2.read(5000)

    def test_short_read_is_an_error(self):
        rf = rd.RangeFile(lambda a, b: b"x", 5000, block=1000)
        with self.assertRaises(IOError):
            rf.read(10)

    def test_head_date_bisect_and_scan(self):
        year = 1987
        start = dt.date(1987, 1, 2)
        texts = {}
        for i in range(300):
            if i < 8:
                texts[i] = "Title page\nContents"
            else:
                d = start + dt.timedelta(days=(i - 8) // 2)
                texts[i] = f"{d.strftime('%b')}. {d.day} / Administration of Ronald Reagan, 1987\nsome words {i}"
        texts[150] += "\nRemarks on Receiving the Final Report of the President's Special Review Board on the National Security Council"
        texts[149] += "\nthe Board was established in December"
        self.assertEqual(rd.ppp_head_date("Sept. 3 / Administration of Ronald Reagan, 1987", 1987), dt.date(1987, 9, 3))
        self.assertEqual(rd.ppp_head_date("Administration of Ronald Reagan, 1987 / June 9\nfoo", 1987), dt.date(1987, 6, 9))
        self.assertIsNone(rd.ppp_head_date("Index\nAbortion", 1987))
        target = dt.date(1987, 3, 15)               # page 8 + 2*72 = 152
        lo, hi, probes = rd.ppp_bisect(300, lambda i: texts[i], year, target)
        self.assertLessEqual(lo, 152 <= hi + 1 and 152)
        self.assertTrue(lo < 152 <= hi + 6)
        spec = {"body_words": rd.body_words("President's Special Review Board")}
        self.assertEqual(spec["body_words"], ["special", "review", "board"])
        texts[160] += "\nA review of the annual report by the board was special."       # words, but not the body
        texts[100] += "\nThe President's Special Review\nBoard filed a report on Iran."    # the body, no receiving phrase: weak
        scan = rd.ppp_scan(300, lambda i: texts[i], year, lo, hi, spec)
        self.assertEqual(scan["strong"], [150])
        self.assertNotIn(160, scan["weak"] + scan["strong"])
        # a request window scans forward from its start and stops once a running head passes the window's end
        win = rd.ppp_scan(300, lambda i: texts[i], year, lo, hi, spec, forward_first=True, fwd=100,
                          stop_after=dt.date(1987, 3, 16))
        self.assertEqual(win["strong"], [150])
        self.assertLess(len(win["scanned"]), 100)
        late = rd.ppp_scan(300, lambda i: texts[i], year, lo, hi, spec, forward_first=True, fwd=100,
                           stop_after=dt.date(1987, 3, 1), back=0)
        self.assertEqual(late["strong"], [])                                              # stopped before page 150

    def test_body_hit_phrase_order_hyphenation_and_apostrophes(self):
        w = rd.body_words("President's Special Review Board")
        self.assertEqual(rd.body_hit("the President\u2019s Special Re\u00ad\nview Board on the NSC", w), 2)
        self.assertEqual(rd.body_hit("the Board will review a special matter", w), 1)
        self.assertEqual(rd.body_hit("the Review Board", w), 0)
        self.assertEqual(rd.body_hit("anything", []), 0)


# ---------------------------------------------------------------- the lane through the ladder

def peb_report_pdf(letter_date="August 16, 2022"):
    return make_pdf([["REPORT TO THE PRESIDENT", "BY EMERGENCY BOARD NO. 250", f"Washington, D.C. {letter_date}",
                      "The President: the Emergency Board submits its report. " * 3],
                     ["Table of contents", "The Emergency Board met with the carriers and unions in the dispute. " * 3]])


class LaneThroughLadderTests(Base):
    def wanted(self, text, iid, eo_date, note=""):
        spec = rd.build_spec(text, [iid], {iid.split(":")[1]: eo_date}, note)
        return fl.Wanted(f"queue:{iid}:{text}", [iid], citation=text, extra={"report_date": spec, "queue_note": note})

    def test_peb_end_to_end_returns_record_with_hash_and_unlabelled_leads(self):
        pdf = peb_report_pdf()
        tr = FakeTransport({rd.NMB_PEB_URL: [(200, H, PEB_TABLE.encode() + b"<!-- " + b"x" * 1600 + b" -->")],
                            "https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/PEB-250-Report.pdf": [(200, PDFH, pdf)]})
        w = self.wanted("Presidential Emergency Board created by EO 14077 (July 15, 2022; 87 FR 43203): report to the President, date submitted",
                        "EO:14077", "2022-07-15")
        plan = fl.plan_routes(w)
        self.assertEqual([r.route for r in plan], ["nmb_peb_table"])
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "found", res["attempts"])
        src = res["source"]
        self.assertEqual(src["sha256"], sha(pdf))
        self.assertTrue(src["url"].endswith("PEB-250-Report.pdf"))
        self.assertIn("front matter", src["page_or_item"])
        leads = src["report_date_leads"]
        self.assertEqual(leads[0], {"page": 1, "line": "Washington, D.C. August 16, 2022"})
        self.assertEqual(src["report_date_basis"]["peb"], 250)
        self.assertEqual(src["report_date_basis"]["nmb_table_closed"], "8/16/2022")
        self.assertIn("index, not proof", src["report_date_basis"]["index_note"])
        # the job asserts no date
        self.assertFalse([k for k in src if k in ("report_date", "date", "submitted_on", "transmittal_date")])
        self.assertIn("custody only", src["notes"])
        for ln in leads:
            self.assertIn(ln["line"], res["text"])                  # verbatim from the document

    def test_peb_board_not_in_table_is_a_passing_failure_not_exhaustion(self):
        tr = FakeTransport({rd.NMB_PEB_URL: [(200, H, PEB_TABLE.encode() + b"<!-- " + b"x" * 1600 + b" -->")]})
        w = self.wanted("Presidential Emergency Board created by EO 13999: report to the President, date submitted", "EO:13999", "2020-03-03")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertIsNone(res["source"])
        self.assertEqual(res["outcome"], "retry_later")
        self.assertIn("rd_", " ".join(a.get("reject_reason") or a.get("error") or "" for a in res["attempts"]))

    def test_wrong_report_pdf_is_refused(self):
        other = make_pdf([["Annual statistics of the Railroad Retirement Board", "No emergency here at all. " * 20]])
        tr = FakeTransport({rd.NMB_PEB_URL: [(200, H, PEB_TABLE.encode() + b"<!-- " + b"x" * 1600 + b" -->")],
                            "https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/PEB-250-Report.pdf": [(200, PDFH, other)]})
        w = self.wanted("Presidential Emergency Board created by EO 14077: report to the President, date submitted", "EO:14077", "2022-07-15")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertIsNone(res["source"])

    def test_same_day_boards_the_report_naming_another_order_is_refused(self):
        # Panizzi II review: PEBs 205 and 206 were created the same day; the first PDF fetched must not be taken
        # for EO 12492 when its front matter names EO 12491.
        base = "https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/"
        r205 = make_pdf([["REPORT TO THE PRESIDENT by Emergency Board No. 205",
                          "Established by Executive Order No. 12491, October 25, 1984. Washington, D.C. December 21, 1984 " * 4]])
        r206 = make_pdf([["REPORT TO THE PRESIDENT by Emergency Board No. 206",
                          "Established by Executive Order No. 12492, October 25, 1984. Washington, D.C. December 22, 1984 " * 4]])
        tr = FakeTransport({rd.NMB_PEB_URL: [(200, H, PEB_TABLE.encode() + b"<!-- " + b"x" * 1600 + b" -->")],
                            base + "PEB-205-Report-2d-PEB.pdf": [(200, PDFH, r205)],
                            base + "PEB-206-Report-2d-PEB.pdf": [(200, PDFH, r206)]})
        w = self.wanted("Actual emergency-board report submitted under EO12492, including submission date", "EO:12492", "1984-10-25")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "found", [(a["route"], a.get("reject_reason")) for a in res["attempts"]])
        self.assertEqual(res["source"]["report_date_basis"]["peb"], 206)
        self.assertEqual(sorted(res["source"]["report_date_basis"]["equal_candidates"]), [205, 206])
        refused = [a for a in res["attempts"] if "names Executive Order 12491" in (a.get("reject_reason") or "")]
        self.assertEqual(len(refused), 1)

    def test_uppercase_title_page_dates_are_leads(self):
        # Panizzi II review: PEB 189's title page reads 'FEBRUARY 9, 1979'; leads came back empty.
        self.assertEqual(rd.front_matter_date_lines([(1, "WASHINGTON, D.C.\nFEBRUARY 9, 1979\n")]),
                         [{"page": 1, "line": "FEBRUARY 9, 1979"}])
        self.assertEqual(rd.parse_dates("DATED NOVEMBER 2, 1978"), ["1978-11-02"])

    def test_scanned_report_without_text_layer_is_a_passing_failure(self):
        blank = make_pdf([["", ""]] * 4)
        tr = FakeTransport({rd.NMB_PEB_URL: [(200, H, PEB_TABLE.encode() + b"<!-- " + b"x" * 1600 + b" -->")],
                            "https://nmb.gov/NMB_Application/wp-content/uploads/2025/05/PEB-250-Report.pdf": [(200, PDFH, blank)]})
        w = self.wanted("Presidential Emergency Board created by EO 14077: report to the President, date submitted", "EO:14077", "2022-07-15")
        res = fl.Ladder(self.fetcher(tr), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "retry_later")
        self.assertTrue(any("rd_no_meaningful_text" in (a.get("reject_reason") or "") for a in res["attempts"]),
                        [a.get("reject_reason") for a in res["attempts"]])

    def test_peb_order_mismatch_by_date(self):
        spec = {"eo_numbers": ["14125"], "eo_dates": {"14125": "2024-07-24"}, "text_dates": []}
        self.assertIn("dated 2022-07-15", rd.peb_order_mismatch("by Executive Order dated July 15, 2022.", spec))
        self.assertEqual(rd.peb_order_mismatch("by Executive Order dated July 24, 2024.", spec), "")
        self.assertEqual(rd.peb_order_mismatch("no order named here", spec), "")

    def test_wcpd_end_to_end_title_match_then_document(self):
        text = ("Date the President's Commission on Mental Health (EO 11973) submitted its report to the President "
                "(report due 1997-01-10); Weekly Compilation")
        w = self.wanted(text, "EO:11973", "1997-01-01")
        plan = fl.plan_routes(w)
        self.assertTrue(plan and all(r.kind == "wcpd_issue" for r in plan))
        self.assertFalse(any(r.kind == "cdx" for r in plan))        # no Wayback copy of an index step
        doc = ("<html><body><h1>Remarks on Receiving the Final Report of the President's Commission on Mental Health</h1>"
               "<p>January 7, 1997</p><p>The President. I want to thank the Commission on Mental Health for its report. " * 3
               + "</p></body></html>").encode()
        routes = {rd.wcpd_mods_url("1997-01-13"): [(200, XMLH, MODS.encode())],
                  "https://www.govinfo.gov/content/pkg/WCPD-1997-01-13/html/WCPD-1997-01-13-Pg11.htm": [(200, H, doc + b"<!-- " + b"x" * 1500 + b" -->")]}
        res = fl.Ladder(self.fetcher(FakeTransport(routes)), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "found", [(a["route"], a["url"][-40:], a["error"], a["reject_reason"]) for a in res["attempts"]])
        self.assertTrue(res["source"]["url"].endswith("WCPD-1997-01-13-Pg11.htm"))
        self.assertTrue(any("January 7, 1997" in l["line"] for l in res["source"]["report_date_leads"]))
        self.assertEqual(res["source"]["report_date_basis"]["issue"], "1997-01-13")

    def test_ppp_end_to_end_by_range_read(self):
        # one volume of 160 pages; running heads advance 2 pages a day from Jan. 2
        start = dt.date(1987, 1, 2)
        pages = []
        for i in range(160):
            if i < 8:
                pages.append(["Public Papers of the Presidents", "Contents"])
                continue
            d = start + dt.timedelta(days=(i - 8) // 2)
            lines = [f"{d.strftime('%b')}. {d.day} / Administration of Ronald Reagan, 1987", f"routine words for page {i}"]
            if i == 112:                                   # Feb. 26 = day 55 -> page 8 + 110 = 118; 112 is Feb. 23
                pass
            if i == 118:
                lines += ["Remarks on Receiving the Final Report of the President's Special Review Board on the National Security Council",
                          "February 26, 1987"]
            pages.append(lines)
        data = make_pdf(pages)
        book = "PPP-1987-book1"
        url = f"https://www.govinfo.gov/content/pkg/{book}/pdf/{book}.pdf"
        sitemap = ("<urlset><url><loc>https://www.govinfo.gov/app/details/PPP-1987-book1</loc></url>"
                   "<url><loc>https://www.govinfo.gov/app/details/PPP-1987-book2</loc></url></urlset>" + " " * 1600).encode()
        tr = RangeTransport({"https://www.govinfo.gov/sitemap/PPP_1987_sitemap.xml": [(200, XMLH, sitemap)]}, files={url: data})
        text = ("Date the President's Special Review Board (Tower Commission) submitted its report to the President, from the Public "
                "Papers of the Presidents (Reagan 1987, Book I); week of 1987-02-23 to 1987-03-02")
        w = self.wanted(text, "EO:12575", "1986-12-01")
        f = self.fetcher(tr, range_transport=tr)
        res = fl.Ladder(f, log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "found", [(a["route"], a["error"], a["reject_reason"]) for a in res["attempts"]])
        src = res["source"]
        self.assertIn("read by HTTP Range", src["page_or_item"])
        self.assertEqual(src["report_date_basis"]["file_content_length"], len(data))
        self.assertTrue(src["report_date_basis"]["strong_hit"])
        self.assertTrue(any("February 26, 1987" in l["line"] for l in src["report_date_leads"]))
        self.assertIn("whole file was not downloaded", res["text"])
        self.assertGreater(f.range_requests, 0)
        self.assertLessEqual(f.range_bytes, len(data) + 1)          # +1: the bytes=0-0 size probe
        self.assertEqual(f.requests, 2)                            # robots + sitemap; Range reads are counted apart
        self.assertEqual(src["sha256"], res["attempts"][-1]["sha256"])

    def test_ppp_volume_that_does_not_cover_the_date_is_skipped_then_next_book_used(self):
        def volume(first_month, n=120):
            d0 = dt.date(1987, first_month, 1)
            pg = []
            for i in range(n):
                if i < 8:
                    pg.append(["Public Papers", "Contents"])
                else:
                    d = d0 + dt.timedelta(days=(i - 8) // 2)
                    pg.append([f"{d.strftime('%b')}. {d.day} / Administration of Ronald Reagan, 1987", f"words {i}"])
            return pg
        b1 = volume(1)                                       # Jan 1 .. Mar 1
        b2 = volume(7)
        b2[60] += ["Remarks on Receiving the Final Report of the Commission on Aviation Safety", "July 28, 1987"]
        sitemap = ("<urlset><url><loc>https://www.govinfo.gov/app/details/PPP-1987-book1</loc></url>"
                   "<url><loc>https://www.govinfo.gov/app/details/PPP-1987-book2</loc></url></urlset>" + " " * 1600).encode()
        files = {f"https://www.govinfo.gov/content/pkg/PPP-1987-book{k}/pdf/PPP-1987-book{k}.pdf": make_pdf(v)
                 for k, v in ((1, b1), (2, b2))}
        tr = RangeTransport({"https://www.govinfo.gov/sitemap/PPP_1987_sitemap.xml": [(200, XMLH, sitemap)]}, files=files)
        w = self.wanted("Date the Commission on Aviation Safety (EO 12999) submitted its final report to the President; due 1987-07-31",
                        "EO:12999", "1987-03-01")
        res = fl.Ladder(self.fetcher(tr, range_transport=tr), log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "found", [(a["route"], a["error"], a["reject_reason"]) for a in res["attempts"]])
        self.assertEqual(res["source"]["report_date_basis"]["book"], "PPP-1987-book2")
        skipped = [a for a in res["attempts"] if "rd_volume_does_not_cover_date" in (a.get("reject_reason") or "")]
        self.assertEqual(len(skipped), 1)

    def test_range_budget_per_run_fails_only_the_range_route(self):
        data = make_pdf([["Contents", "x"]] * 20)
        url = "https://www.govinfo.gov/content/pkg/PPP-1987-book1/pdf/PPP-1987-book1.pdf"
        sitemap = (b"<urlset><url><loc>https://www.govinfo.gov/app/details/PPP-1987-book1</loc></url></urlset>" + b" " * 1600)
        tr = RangeTransport({"https://www.govinfo.gov/sitemap/PPP_1987_sitemap.xml": [(200, XMLH, sitemap)]}, files={url: data})
        w = self.wanted("Date the Commission on Aviation Safety (EO 12999) submitted its final report to the President; due 1987-02-01",
                        "EO:12999", "1987-01-01")
        f = self.fetcher(tr, range_transport=tr, max_range_requests=1)
        # Panizzi II review: a spent Range budget must not stop the whole run (BudgetExceeded would leave every
        # later item not_attempted_budget); the Range route fails as a passing failure and the walk ends.
        res = fl.Ladder(f, log=lambda *a: None).walk(w)
        self.assertEqual(res["outcome"], "retry_later", res["why"])
        errs = [a["error"] for a in res["attempts"] if a["route"] == "ppp_range_read"]
        self.assertTrue(errs and all(e.startswith("rd_range_budget_reached") for e in errs), errs)
        self.assertLessEqual(f.range_requests, 1)

    def test_range_read_refused_when_robots_disallow(self):
        url = "https://www.govinfo.gov/content/pkg/PPP-1987-book1/pdf/PPP-1987-book1.pdf"
        data = make_pdf([["x", "y"]] * 10)
        tr = RangeTransport({}, files={url: data}, robots={"www.govinfo.gov": "User-agent: *\nDisallow: /content/pkg/PPP"})
        f = self.fetcher(tr, range_transport=tr)
        with self.assertRaises(PermissionError):
            f.open_range(url)

    def test_server_that_ignores_range_is_not_downloaded_whole(self):
        url = "https://www.govinfo.gov/content/pkg/PPP-1987-book1/pdf/PPP-1987-book1.pdf"
        tr = FakeTransport({url: [(200, PDFH, b"%PDF-" + b"x" * 5000)]})
        f = self.fetcher(tr, range_transport=tr)
        with self.assertRaises(IOError):
            f.open_range(url)


class QueueIntegrationTests(Base):
    def test_report_date_line_is_kept_whole_with_spec_and_signing_dates(self):
        qf = self.tmp / "q.jsonl"
        lines = [
            {"instrument_id": "EO:14077", "urls": [], "citation": "Presidential Emergency Board created by EO 14077 (July 15, 2022; 87 FR 43203): "
             "report to the President, date submitted (National Mediation Board)", "step": "ending_or_current_basis",
             "requested_by": "x", "note": "Sec. 5: the Board terminates on submission of its report"},
            {"instrument_id": "EO:12502", "urls": [], "citation": "Pub. L. 98-525, 98 Stat. 2492 text of sec. 1511 establishing the Chemical Warfare Review Commission",
             "step": "ending_or_current_basis", "requested_by": "y", "note": "reports it requires"},
        ]
        qf.write_text("\n".join(json.dumps(l) for l in lines), encoding="utf-8")
        index = {"EO:14077": {"primary": {"signing_date": "2022-07-15", "citation": "87 FR 43203", "publication_date": "2022-07-20"}, "others": []}}
        items, problems = ladder_queue.read_fetch_queue(qf, index)
        self.assertEqual(problems, [])
        peb = [w for w in items if w.instrument_ids == ["EO:14077"]]
        self.assertEqual(len(peb), 1)                                  # not split into the 87 FR cite
        self.assertEqual(peb[0].extra["report_date"]["eo_dates"], {"14077": "2022-07-15"})
        self.assertEqual(peb[0].extra["report_date"]["lane"], "nmb")
        self.assertEqual(peb[0].extra["queue_note"][:6], "Sec. 5")
        other = [w for w in items if w.instrument_ids == ["EO:12502"]]
        self.assertTrue(other and all("report_date" not in w.extra for w in other))   # a statute request is not a report-date request
        self.assertTrue(all(w.extra.get("parent_citation") for w in other))            # still split into its embedded cites


if __name__ == "__main__":
    unittest.main()
