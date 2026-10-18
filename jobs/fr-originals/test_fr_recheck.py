"""Unit tests for the opt-in pdfplumber recheck pass (fr_recheck.py). No network.

The layout and grading tests use synthetic word boxes and need nothing extra;
the end-to-end tests build a small positioned-text PDF and need pdfplumber
(they skip with a reason when it is not installed)."""
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "source-ladder"))
sys.path.insert(0, str(HERE))

import eo_extract  # noqa: E402
import fetch_ladder  # noqa: E402
import fr_originals  # noqa: E402
import fr_recheck  # noqa: E402
import ofr_index  # noqa: E402
import prior_output  # noqa: E402
from test_fetch_ladder import FakeTransport  # noqa: E402

HAVE_PLUMBER = fr_recheck.pdfplumber_available()


def W(text, x0, top, size=8.0, cw=4.4):
    """A pdfplumber-style word box."""
    return {"text": text, "x0": float(x0), "x1": float(x0 + cw * len(text)), "top": float(top),
            "bottom": float(top + size)}


def line(text, x0, top, size=8.0, cw=4.4):
    out, x = [], x0
    for t in text.split():
        out.append(W(t, x, top, size, cw))
        x += cw * len(t) + cw
    return out


def column(rows, x0, top0, step=10):
    words = []
    for i, r in enumerate(rows):
        if r:
            words += line(r, x0, top0 + i * step)
    return words


FILLER = ["text of the order goes on here", "and continues in this column", "with more words for the line",
          "until the column is full of it"]


def three_column_page(head, c1, c2, c3):
    words = line(head, 60, 40)
    for rows, x in ((c1, 60), (c2, 240), (c3, 420)):
        words += column(rows, x, 70)
    return words


class LayoutTests(unittest.TestCase):
    def test_columns_read_in_order_and_head_number(self):
        c1 = ["CONTENTS Continued", "Executive orders:", "10193 ............ 9031"] + FILLER
        c2 = ["end of the previous order", "[F. R. Doc. 50-1; Filed, Dec. 15, 1950]", "", "EXECUTIVE ORDER 10193",
              "Providing for the Conduct of", "the Mobilization Effort"] + FILLER
        c3 = FILLER + ["Harry S. Truman", "The White House,", "[F. R. Doc. 50-2; Filed, Dec. 16, 1950;"]
        lay = fr_recheck.layout_words(three_column_page("Tuesday, December 19, 1950 FEDERAL REGISTER 9031", c1, c2, c3), 0)
        self.assertIn(9031, lay["head_numbers"])
        texts = [ln["text"] for ln in lay["lines"] if not ln.get("running_head")]
        # column 1 entirely before column 2, column 2 before column 3
        self.assertLess(texts.index("10193 ............ 9031"), texts.index("EXECUTIVE ORDER 10193"))
        self.assertLess(texts.index("EXECUTIVE ORDER 10193"), texts.index("Harry S. Truman"))
        self.assertEqual(texts[texts.index("EXECUTIVE ORDER 10193") + 1], "Providing for the Conduct of")

    def test_heading_across_two_columns_is_not_split(self):
        words = line("FEDERAL REGISTER 100", 60, 40)
        words += line("EXECUTIVE ORDER 9999", 190, 80, cw=6.0)   # centred over the gutter at ~235
        words += column(FILLER * 2, 60, 110) + column(FILLER * 2, 240, 110)
        lay = fr_recheck.layout_words(words, 0)
        texts = [ln["text"] for ln in lay["lines"]]
        self.assertIn("EXECUTIVE ORDER 9999", texts)

    def test_signature_lines_are_not_split_into_columns(self):
        # Two short lines have aligned word gaps, but a gutter needs three rows on each side.
        words = line("FEDERAL REGISTER 100", 60, 40) + line("Harry S. Truman", 60, 70) + line("The White House,", 60, 80)
        lay = fr_recheck.layout_words(words, 0)
        self.assertEqual(lay["blocks"], 1)
        self.assertEqual([ln["text"] for ln in lay["lines"][1:]], ["Harry S. Truman", "The White House,"])


def page(i, lines_):
    """A layout dict as find_in_reading_order expects (one block per list, in order)."""
    out = [{"page": i, "block": -1, "text": f"FEDERAL REGISTER {9030 + i}", "running_head": True, "top": 40, "x0": 60}]
    for b, blk in enumerate(lines_):
        for k, t in enumerate(blk):
            out.append({"page": i, "block": b, "text": t, "top": 70 + 10 * k, "x0": 60,
                        **({"leader": True} if fr_recheck.LEADER_END.search(t) else {})})
    return {"page": i, "lines": out, "head_numbers": [9030 + i], "head_text": f"FEDERAL REGISTER {9030 + i}"}


class FindTests(unittest.TestCase):
    def test_numbered_heading_and_filing_line(self):
        lays = {1: page(1, [["CONTENTS", "Executive Order 10193 ........ 9031"],
                            ["[F. R. Doc. 50-1; Filed]", "EXECUTIVE ORDER 10193", "Providing for things"],
                            ["more text", "[F. R. Doc. 50-2; Filed, Dec. 16, 1950;"]])}
        ev = fr_recheck.find_in_reading_order(lays, "10193", 1, 3)
        self.assertEqual(ev["heading"]["text"], "EXECUTIVE ORDER 10193")
        self.assertEqual(ev["filing_line"]["text"], "[F. R. Doc. 50-2; Filed, Dec. 16, 1950;")
        self.assertTrue(ev["heading_on_cited_page"])
        self.assertEqual((ev["start_pdf_page"], ev["end_pdf_page"]), (2, 2))
        self.assertTrue(any(m["why"] == "contents" for m in ev["skipped_mentions"]))

    def test_wrapped_reference_is_not_the_heading(self):
        lays = {1: page(1, [["it is ordered that the order amending", "Executive Order 10193", "is revoked",
                             "[F. R. Doc. 50-3; Filed]"]])}
        ev = fr_recheck.find_in_reading_order(lays, "10193", 1, 3)
        self.assertIsNone(ev["heading"])

    def test_closing_tag_style_and_damaged_bracket(self):
        lays = {0: page(0, [["[F. R. Doc. 37-815; Filed]", "Executive Order", "EXCLUDING CERTAIN TRACTS",
                             "By virtue of the authority", "Franklin D Roosevelt", "[No. 75783",
                             "[P. R. Doc. 37-816; Filed, March 22, 1937]"]])}
        ev = fr_recheck.find_in_reading_order(lays, "7578", 0, 1)
        self.assertEqual(ev["heading"]["kind"], "bare_heading_then_closing_tag")
        self.assertEqual(ev["closing_tag"]["kind"], "bracket_ocr_damaged")
        self.assertIn("37-816", ev["filing_line"]["text"])

    def test_filing_line_between_heading_and_tag_is_a_conflict(self):
        lays = {0: page(0, [["Executive Order", "first order text", "[No. 7577]", "[F. R. Doc. 37-1; Filed]",
                             "second document text", "[No. 7578]", "[F. R. Doc. 37-2; Filed]"]])}
        ev = fr_recheck.find_in_reading_order(lays, "7578", 0, 1)
        self.assertIsNone(ev["heading"])
        self.assertTrue(ev["conflict"])

    def test_next_order_before_filing_line_is_a_conflict(self):
        lays = {1: page(1, [["EXECUTIVE ORDER 10193", "text without its filing line", "EXECUTIVE ORDER 10194",
                             "[F. R. Doc. 50-4; Filed]"]])}
        ev = fr_recheck.find_in_reading_order(lays, "10193", 1, 3)
        self.assertIn("10194", ev["conflict"])
        self.assertIsNone(ev["filing_line"])

    def test_tag_with_letter_suffix_is_another_order(self):
        self.assertIsNone(fr_recheck._tag_line("[No. 7700-A]", "7700"))
        self.assertEqual(fr_recheck._tag_line("[No. 7700-A]", "7700A"), "strict")
        self.assertEqual(fr_recheck._tag_line("[No. 83363", "8336"), "bracket_ocr_damaged")
        self.assertIsNone(fr_recheck._tag_line("[No. 10193]", "1019"))


class FixesTests(unittest.TestCase):
    def test_issue_date_is_not_read_as_the_page_number(self):
        # 6 FR 1941 printed in a 1941 issue: the year in the running head must not confirm the page.
        body = column(FILLER * 2, 60, 70)
        lay = fr_recheck.layout_words(line("FEDERAL REGISTER, Thursday, April 17, 1941", 60, 40) + body, 0)
        self.assertNotIn(1941, lay["head_numbers"])
        self.assertNotIn(17, lay["head_numbers"])
        lay = fr_recheck.layout_words(line("FEDERAL REGISTER, Thursday, April 17 1941", 60, 40) + body, 0)  # comma lost
        self.assertNotIn(1941, lay["head_numbers"])
        lay = fr_recheck.layout_words(line("FEDERAL REGISTER, Thursday, April 17, 1941 1941", 60, 40) + body, 0)
        self.assertIn(1941, lay["head_numbers"])                 # a page number after the date is still read
        lay = fr_recheck.layout_words(line("1940 FEDERAL REGISTER, Thursday, April 17, 1941", 60, 40) + body, 0)
        self.assertEqual(lay["head_numbers"], [1940])
        ev = {"heading": {"pdf_page": 2, "text": "EXECUTIVE ORDER 8730", "kind": "numbered_heading"},
              "filing_line": {"pdf_page": 2, "text": "[F. R. Doc. 41-1; Filed]"}, "start_pdf_page": 2,
              "end_pdf_page": 2, "cited_pdf_page": 2, "heading_on_cited_page": True,
              "head_numbers_on_heading_page": [], "ofr_title_words_found": "3/3"}
        ok, why = fr_recheck.grade(ev, {"citation": "6 FR 1941", "publication_date": "1941-04-17"},
                                   {"sha256": "a" * 64,
                                    "url": "https://www.govinfo.gov/content/pkg/FR-1941-04-17/pdf/FR-1941-04-17.pdf"},
                                   "a" * 64)
        self.assertFalse(ok)
        self.assertTrue(any("running head" in w for w in why))

    def test_closing_tag_needs_its_opening_bracket(self):
        self.assertIsNone(fr_recheck._tag_line("No. 8792).", "8792"))
        self.assertIsNone(fr_recheck._tag_line("No. 8792]", "8792"))
        self.assertEqual(fr_recheck._tag_line("[No. 8792]", "8792"), "strict")
        self.assertEqual(fr_recheck._tag_line("[No. 8792)", "8792"), "strict")

    def test_reference_with_no_and_date_is_not_another_heading(self):
        def L(ts):
            return [{"text": t, "page": 0, "block": 0} for t in ts]
        self.assertIsNone(fr_recheck._other_document_start(
            L(["the order was issued.", "Executive Order No. 10269 of July 6, 1951"]), 1, "10461"))
        self.assertTrue(fr_recheck._other_document_start(
            L(["Title 3", "Executive Order 12890 of January 1, 1994"]), 1, "12891"))
        self.assertEqual(fr_recheck._heading_line_kind(L(["x.", "Executive Order 12890 of January 1, 1994"]), 1, "12890"),
                         "own")
        self.assertEqual(fr_recheck._heading_line_kind(L(["x.", "Executive Order No. 12890 of January 1, 1994"]), 1,
                                                       "12890"), "midline")


class GradeTests(unittest.TestCase):
    def ev(self, **kw):
        e = {"heading": {"pdf_page": 2, "text": "EXECUTIVE ORDER 10193", "kind": "numbered_heading"},
             "filing_line": {"pdf_page": 2, "text": "[F. R. Doc. 50-2; Filed]"}, "start_pdf_page": 2,
             "end_pdf_page": 2, "cited_pdf_page": 2, "heading_on_cited_page": True,
             "head_numbers_on_heading_page": [9031], "ofr_title_words_found": "3/3"}
        e.update(kw)
        return e

    rec = {"citation": "15 FR 9031", "publication_date": "1950-12-19"}
    src = {"sha256": "a" * 64, "url": "https://www.govinfo.gov/content/pkg/FR-1950-12-19/pdf/FR-1950-12-19.pdf"}

    def test_full_evidence_upgrades(self):
        ok, why = fr_recheck.grade(self.ev(), self.rec, self.src, "a" * 64)
        self.assertTrue(ok, why)

    def test_every_missing_piece_blocks_the_upgrade(self):
        cases = [
            (self.ev(), dict(self.rec), "b" * 64),                                         # bytes changed
            (self.ev(heading_on_cited_page=False), dict(self.rec), "a" * 64),               # wrong page
            (self.ev(head_numbers_on_heading_page=[]), dict(self.rec), "a" * 64),           # page number unread
            (self.ev(), dict(self.rec, publication_date="1950-12-18"), "a" * 64),           # other issue
            (self.ev(filing_line=None, end_pdf_page=None), dict(self.rec), "a" * 64),       # no end
            (self.ev(conflict="another document starts"), dict(self.rec), "a" * 64),
            (self.ev(ofr_title_words_found="0/6"), dict(self.rec), "a" * 64),
        ]
        for ev, rec, sha in cases:
            ok, why = fr_recheck.grade(ev, rec, self.src, sha)
            self.assertFalse(ok, ev)
            self.assertTrue(why)

    def test_exact_printed_page_match_stands_in_for_an_unread_running_head(self):
        ok, _ = fr_recheck.grade(self.ev(head_numbers_on_heading_page=[], base_exact_printed_page_match=True),
                                 self.rec, self.src, "a" * 64)
        self.assertTrue(ok)


# ---------------------------------------------------------------------------
# End to end with a real (tiny) PDF: needs pdfplumber
# ---------------------------------------------------------------------------

def positioned_pdf(pages):
    """pages: list of [(x, top, text)] on a 612x792 page, 8 pt Helvetica."""
    objs = [None, None, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for items in pages:
        parts = []
        for x, top, text in items:
            esc = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            parts.append(f"BT /F1 8 Tf 1 0 0 1 {x} {792 - top - 8} Tm ({esc}) Tj ET")
        cb = "\n".join(parts).encode("latin-1")
        objs.append(b"<< /Length %d >>\nstream\n" % len(cb) + cb + b"\nendstream")
        cid = len(objs)
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents %d 0 R "
                    b"/Resources << /Font << /F1 3 0 R >> >> >>" % cid)
        kids.append(len(objs))
    objs[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[1] = b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % k for k in kids) + b"] /Count %d >>" % len(kids)
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offs = []
    for i, body in enumerate(objs, 1):
        offs.append(out.tell())
        out.write(b"%d 0 obj\n" % i + body + b"\nendobj\n")
    x = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1))
    for o in offs:
        out.write(b"%010d 00000 n \n" % o)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x))
    return out.getvalue()


def col(rows, x, top0=70):
    return [(x, top0 + 11 * i, r) for i, r in enumerate(rows) if r]


ISSUE_URL = "https://www.govinfo.gov/content/pkg/FR-1950-12-19/pdf/FR-1950-12-19.pdf"
BODY = ["text of the order goes on", "and continues in this col", "with more words in a line", "until the end of it"]
ISSUE = positioned_pdf([
    [(60, 40, "9030 FEDERAL REGISTER, December 19, 1950")] + col(BODY * 3, 60) + col(BODY * 3, 250)
    + col(BODY * 3, 440),
    # The cited page 9031: contents in column 1, the order in column 2, its end in column 3.
    [(60, 40, "Tuesday, December 19, 1950 FEDERAL REGISTER 9031")]
    + col(["CONTENTS Continued", "Executive orders:", "10193 .......... 9031"] + BODY * 2, 60)
    + col(["the previous order ends", "[F. R. Doc. 50-1; Filed, Dec. 15]", "", "EXECUTIVE ORDER 10193",
           "Providing for the Conduct of", "the Mobilization Effort"] + BODY * 2, 250)
    + col(BODY * 2 + ["Harry S. Truman", "The White House,", "[F. R. Doc. 50-2; Filed, Dec. 16, 1950;",
                      "12:47 p. m.]"], 440),
    [(60, 40, "9032 FEDERAL REGISTER, December 19, 1950")] + col(BODY * 3, 60) + col(BODY * 3, 250)
    + col(BODY * 3, 440),
])


def rec(num, citation, pub, **kw):
    r = {"executive_order_number": num, "citation": citation, "publication_date": pub, "signing_date": pub,
         "title": "Providing for the Conduct of the Mobilization Effort", "pdf_url": None, "document_number": None,
         "not_received_for_publication": None}
    r.update(kw)
    return r


@unittest.skipUnless(HAVE_PLUMBER, "pdfplumber is not installed (pip install -r jobs/fr-originals/requirements.txt)")
class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        eo_extract._TEXT_CACHE.clear()
        self.index = ofr_index.build_index([rec("10193", "15 FR 9031", "1950-12-19"),
                                            rec("10192", "15 FR 9030", "1950-12-19")])
        self.plan = fr_originals.build_plan(self.repo, self.index)
        self.sha = hashlib.sha256(ISSUE).hexdigest()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ctx(self, transport, cache="cache"):
        c = self.tmp / cache
        f = fetch_ladder.Fetcher(c, transport=transport, sleep=lambda s: None, clock=lambda: 0.0, log=lambda *a: None)
        return {"repo": self.repo, "fetcher": f, "ladder": None, "custody": {}, "crosswalk": {},
                "state_dir": c / "state", "state_texts": c / "state" / "texts", "issue_blobs": set()}

    def seed(self, ctx):
        """States as the default locator left them: EO 10193 low (needs a page check), EO 10192 high."""
        for p in self.plan:
            num = p["instrument_id"].split(":")[1]
            conf = "low" if num == "10193" else "high"
            src = {"source_id": f"fr-originals:{p['instrument_id']}:{self.sha[:12]}", "instrument_ids": [p["instrument_id"]],
                   "url": ISSUE_URL, "requested_url": ISSUE_URL, "sha256": self.sha, "bytes": len(ISSUE),
                   "content_type": "application/pdf", "retrieved_utc": "2026-10-17T00:00:00Z",
                   "route": "official/govinfo_fr_issue_pdf", "page_or_item": f"{p['record']['citation']}, PDF pages 1-1",
                   "text_path": f"texts/EO_{num}.txt", "cache_path": None, "notes": "test",
                   "location_confidence": conf}
            st = {"state_version": fr_originals.STATE_VERSION, "instrument_id": p["instrument_id"], "status": "found",
                  "permanent": True, "source": src, "not_found": None, "attempts": [], "text_file": f"EO_{num}.txt",
                  "fragment": fr_originals.fragment_for(p, src, fr_originals.confidence_note({"confidence": conf}, True))}
            ctx["state_texts"].mkdir(parents=True, exist_ok=True)
            (ctx["state_texts"] / f"EO_{num}.txt").write_text("old text\n", encoding="utf-8")
            fr_originals.write_state(ctx["state_dir"], st)

    def transport(self):
        return FakeTransport({ISSUE_URL: [(200, {"content-type": "application/pdf"}, ISSUE)]})

    def test_default_outputs_unchanged_without_recheck(self):
        ctx = self.ctx(self.transport())
        self.seed(ctx)
        states, info = fr_originals.run(ctx, self.plan, log=lambda *a: None)
        out = self.tmp / "plain"
        s = fr_originals.write_outputs(out, ctx, self.plan, states, info)
        self.assertNotIn("recheck_upgrades_applied", s)
        self.assertFalse((out / "RECHECK.jsonl").exists())
        frags = [json.loads(x) for x in (out / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(frags, [states[p["instrument_id"]]["fragment"] for p in self.plan])

    def test_upgrade_overlay_carry_forward_and_never_touch_high(self):
        t = self.transport()
        ctx = self.ctx(t)
        self.seed(ctx)
        states, info = fr_originals.run(ctx, self.plan, limit=0, log=lambda *a: None)
        rows, rinfo = fr_recheck.run_recheck(ctx, self.plan, states, log=lambda *a: None)
        self.assertEqual([r["instrument_id"] for r in rows], ["EO:10193"])   # the high order is never rechecked
        r = rows[0]
        self.assertEqual(r["result"], "upgraded", r["reasons"])
        self.assertEqual(r["page_or_item"], "15 FR 9031, PDF pages 2-2")
        self.assertEqual(r["evidence"]["heading"]["text"], "EXECUTIVE ORDER 10193")
        self.assertTrue(r["evidence"]["cited_page_number_in_running_head"])
        out = self.tmp / "out"
        s = fr_originals.write_outputs(out, ctx, self.plan, states, info)
        rs = fr_recheck.write_recheck_outputs(out, ctx, self.plan, states, rinfo)
        self.assertEqual((rs["upgraded_to_high"], rs["stayed"]), (1, 0))
        self.assertEqual(s["recheck_upgrades_applied"], 1)
        self.assertEqual(s["found_by_confidence"], {"low": 1, "high": 1})            # SOURCES: the locator's record
        self.assertEqual(s["found_by_confidence_after_recheck"], {"high": 2})
        frags = {f["instrument_id"]: f for f in map(json.loads, (out / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines())}
        d = frags["EO:10193"]["data"]
        self.assertEqual((d["location_confidence"], d["needs_page_check"], d["location_verified"]), ("high", False, False))
        self.assertEqual(d["recheck_evidence"]["base"]["location_confidence"], "low")
        self.assertEqual(d["text_path"], "texts/EO_10193.recheck.txt")
        self.assertIn("EXECUTIVE ORDER 10193", (out / d["text_path"]).read_text(encoding="utf-8"))
        self.assertEqual(frags["EO:10192"], states["EO:10192"]["fragment"])          # high result untouched
        srcs = {x["instrument_ids"][0]: x for x in map(json.loads, (out / "SOURCES.jsonl").read_text(encoding="utf-8").splitlines())}
        self.assertEqual(srcs["EO:10193"]["location_confidence"], "low")
        self.assertEqual(srcs["EO:10193"]["recheck"]["location_confidence"], "high")
        self.assertTrue((out / "texts" / "EO_10193.txt").is_file())                 # the locator's text is kept

        # Resume: nothing is rechecked or fetched again.
        calls = len(t.calls)
        rows2, _ = fr_recheck.run_recheck(ctx, self.plan, states, log=lambda *a: None)
        self.assertEqual((rows2, len(t.calls)), ([], calls))

        # A fresh machine carries the upgrade forward from the committed output.
        ctx2 = self.ctx(FakeTransport({}), cache="cache2")
        prior = prior_output.PriorOutput.from_folder(out)
        fr_originals.carry_forward(ctx2, self.plan, [prior], log=lambda *a: None)
        self.assertEqual(fr_recheck.carry_forward_recheck(ctx2, self.plan, [prior], log=lambda *a: None), 1)
        states2, info2 = fr_originals.run(ctx2, self.plan, limit=0, log=lambda *a: None)
        out2 = self.tmp / "out2"
        fr_originals.write_outputs(out2, ctx2, self.plan, states2, info2)
        fr_recheck.write_recheck_outputs(out2, ctx2, self.plan, states2)
        for name in ("FRAGMENTS.jsonl", "SOURCES.jsonl", "texts/EO_10193.recheck.txt", "texts/EO_10193.txt"):
            self.assertEqual((out2 / name).read_bytes(), (out / name).read_bytes(), name)
        # The carried state is the base (low) result; the upgrade is only the overlay from its record,
        # and the record (carried too) means it is not rechecked again.
        self.assertEqual(states2["EO:10193"]["fragment"], states["EO:10193"]["fragment"])
        self.assertNotIn("recheck", states2["EO:10193"]["source"])
        self.assertEqual(fr_recheck.eligible(states2["EO:10193"]), (True, ""))
        todo, skipped = fr_recheck.select(ctx2, self.plan, states2)
        self.assertEqual((todo, skipped.get("already rechecked")), ([], 1))

    def _upgraded_output(self):
        ctx = self.ctx(self.transport())
        self.seed(ctx)
        states, info = fr_originals.run(ctx, self.plan, limit=0, log=lambda *a: None)
        _, rinfo = fr_recheck.run_recheck(ctx, self.plan, states, log=lambda *a: None)
        out = self.tmp / "out"
        fr_originals.write_outputs(out, ctx, self.plan, states, info)
        fr_recheck.write_recheck_outputs(out, ctx, self.plan, states, rinfo)
        return out, states

    def _carry(self, out, cache):
        ctx2 = self.ctx(FakeTransport({}), cache=cache)
        prior = prior_output.PriorOutput.from_folder(out)
        fr_originals.carry_forward(ctx2, self.plan, [prior], log=lambda *a: None)
        fr_recheck.carry_forward_recheck(ctx2, self.plan, [prior], log=lambda *a: None)
        states2, info2 = fr_originals.run(ctx2, self.plan, limit=0, log=lambda *a: None)
        out2 = self.tmp / (cache + "_out")
        s2 = fr_originals.write_outputs(out2, ctx2, self.plan, states2, info2)
        return ctx2, states2, out2, s2

    def assert_back_to_base(self, states, states2, out2, s2):
        frags = {f["instrument_id"]: f for f in map(json.loads, (out2 / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines())}
        self.assertEqual(frags["EO:10193"], states["EO:10193"]["fragment"])   # the base low fragment again
        d = frags["EO:10193"]["data"]
        self.assertEqual((d["location_confidence"], d["needs_page_check"]), ("low", True))
        self.assertNotIn("recheck_evidence", d)
        self.assertTrue((out2 / d["text_path"]).is_file())
        self.assertFalse((out2 / "texts" / "EO_10193.recheck.txt").exists())
        srcs = {x["instrument_ids"][0]: x for x in map(json.loads, (out2 / "SOURCES.jsonl").read_text(encoding="utf-8").splitlines())}
        self.assertNotIn("recheck", srcs["EO:10193"])
        self.assertNotIn("recheck_upgrades_applied", s2)
        self.assertEqual(s2["found_by_confidence"], {"low": 1, "high": 1})
        self.assertEqual(fr_recheck.eligible(states2["EO:10193"]), (True, ""))

    def test_upgrade_is_withdrawn_when_its_record_is_gone(self):
        out, states = self._upgraded_output()
        (out / "RECHECK.jsonl").unlink()
        (out / "RECHECK_SUMMARY.json").unlink()
        ctx2, states2, out2, s2 = self._carry(out, "cache_norecord")
        self.assert_back_to_base(states, states2, out2, s2)
        todo, _ = fr_recheck.select(ctx2, self.plan, states2)
        self.assertEqual([i["instrument_id"] for i in todo], ["EO:10193"])   # eligible for recheck again

    def test_upgrade_is_withdrawn_when_recheck_version_changes(self):
        out, states = self._upgraded_output()
        rows = [json.loads(x) for x in (out / "RECHECK.jsonl").read_text(encoding="utf-8").splitlines()]
        for r in rows:
            r["recheck_version"] = fr_recheck.RECHECK_VERSION - 1
        (out / "RECHECK.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        _, states2, out2, s2 = self._carry(out, "cache_oldversion")
        self.assert_back_to_base(states, states2, out2, s2)

    def test_upgrade_is_withdrawn_when_its_text_is_missing(self):
        out, states = self._upgraded_output()
        (out / "texts" / "EO_10193.recheck.txt").unlink()
        _, states2, out2, s2 = self._carry(out, "cache_notext")
        self.assert_back_to_base(states, states2, out2, s2)

    def test_a_cache_state_with_a_baked_in_upgrade_is_read_as_the_base(self):
        # A cache seeded by the earlier code could hold the upgraded fragment as state.
        out, states = self._upgraded_output()
        frags = {f["instrument_id"]: f for f in map(json.loads, (out / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines())}
        srcs = {x["instrument_ids"][0]: x for x in map(json.loads, (out / "SOURCES.jsonl").read_text(encoding="utf-8").splitlines())}
        self.assertIn("recheck_evidence", frags["EO:10193"]["data"])
        ctx3 = self.ctx(FakeTransport({}), cache="cache_baked")
        st = dict(states["EO:10193"], fragment=frags["EO:10193"], source=srcs["EO:10193"])
        fr_originals.write_state(ctx3["state_dir"], st)
        got = fr_originals.load_state(ctx3["state_dir"], "EO:10193")
        self.assertEqual(got["fragment"], states["EO:10193"]["fragment"])
        self.assertEqual(got["source"], states["EO:10193"]["source"])

    def test_a_forged_upgrade_never_overwrites_a_high_result(self):
        ctx = self.ctx(self.transport())
        self.seed(ctx)
        states, info = fr_originals.run(ctx, self.plan, limit=0, log=lambda *a: None)
        self.assertEqual(fr_recheck.eligible(states["EO:10192"]), (False, "already high (never rechecked)"))
        frag = json.loads(json.dumps(states["EO:10192"]["fragment"]))
        frag["data"]["page_or_item"] = "15 FR 9030, PDF pages 9-9"
        fr_recheck.save_recheck(ctx, {"recheck_version": fr_recheck.RECHECK_VERSION, "instrument_id": "EO:10192",
                                      "result": "upgraded", "base_sha256": self.sha, "fragment": frag,
                                      "text_file": None})
        self.assertEqual(fr_recheck.overlay(ctx, self.plan, states), {})

    def test_bytes_changed_means_no_upgrade(self):
        other = positioned_pdf([[(60, 40, "nothing")]])
        ctx = self.ctx(FakeTransport({ISSUE_URL: [(200, {"content-type": "application/pdf"}, other)]}))
        self.seed(ctx)
        states, _ = fr_originals.run(ctx, self.plan, limit=0, log=lambda *a: None)
        rows, _ = fr_recheck.run_recheck(ctx, self.plan, states, log=lambda *a: None)
        self.assertEqual(rows[0]["result"], "stays")
        self.assertTrue(any("sha256" in x for x in rows[0]["reasons"]))


class NoPlumberTests(unittest.TestCase):
    def test_missing_pdfplumber_degrades_cleanly(self):
        orig = fr_recheck.pdfplumber_available
        fr_recheck.pdfplumber_available = lambda: False
        try:
            tmp = Path(tempfile.mkdtemp())
            ctx = {"state_dir": tmp / "state", "fetcher": None}
            msgs = []
            rows, info = fr_recheck.run_recheck(ctx, [], {}, log=msgs.append)
            self.assertEqual(rows, [])
            self.assertEqual(info["stopped"], "pdfplumber not installed")
            self.assertTrue(msgs and "pdfplumber is not installed" in msgs[0])
            shutil.rmtree(tmp, ignore_errors=True)
        finally:
            fr_recheck.pdfplumber_available = orig


if __name__ == "__main__":
    unittest.main()
