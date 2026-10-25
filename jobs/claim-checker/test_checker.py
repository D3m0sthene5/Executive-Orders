"""Unit tests for the claim checker. Small fixtures built in a temporary folder; no network.

The structural gate is the project's own research/stage19/code/claim_gate.py,
loaded (not copied) through a two-line shim in the fixture repo.
"""

import csv
import gzip
import hashlib
import json
import os
os.environ.setdefault("CLAIM_CHECKER_VERIFY_DOWNLOADS", "0")  # tests never use the network
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
REAL_REPO = HERE.parent.parent
REAL_GATE = REAL_REPO / "research/stage19/code/claim_gate.py"
sys.path.insert(0, str(HERE))
import checker as C  # noqa: E402
import sources as S  # noqa: E402

try:
    import pypdf  # noqa: F401
    HAVE_PYPDF = True
except ImportError:
    HAVE_PYPDF = False

ORIGINAL_TEXT = (
    "Executive Order 90001 of March 3, 1950\n"
    "Establishing the Test Board\n"
    "Section 1. There is hereby established the Test Board, which shall advise the Presi-\n"
    "dent on testing.\n"
    "Sec. 2. Executive Order No. 90002 of January 1, 1949, is superseded. The efﬁcient\n"
    "conduct of tests is the Board's duty.\n"
)
ENDING_TEXT = "Executive Order 90003\nSection 1. Executive Order 90001 is hereby revoked.\n"
OTHER_TEXT = "A different printing of the ending order.\n"
SAVINGS_TEXT = "Nothing in this order shall affect pending proceedings under Executive Order 90001."
RECORD_ONLY_TEXT = "A record-only page: the President may at any time request a report from the Test Board."


FAKE_CLASS_LADDER = """
import dataclasses


@dataclasses.dataclass
class Wanted:
    wanted_id: str
    instrument_ids: list
    urls: list = dataclasses.field(default_factory=list)
    citation: str = ""
    step: str = "original_text"


class Fetcher:
    def __init__(self, cache_dir, max_requests=None):
        self.cache_dir = cache_dir


class Ladder:
    def __init__(self, fetcher):
        self.fetcher = fetcher

    def walk(self, wanted):
        return {"source": {"url": wanted.urls[0], "sha256": "f" * 64, "step": wanted.step},
                "attempts": [{"tier": "given", "route": "given_url", "url": wanted.urls[0], "accepted": True}]}
"""


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def tiny_pdf(text_lines):
    """A minimal valid one-page PDF with a text layer (Helvetica)."""
    stream = "BT /F1 12 Tf 72 720 Td 14 TL " + " ".join(
        "(" + ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") '" for ln in text_lines) + " ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for n, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def build_repo(root):
    """A fixture repo shaped like the real one (only the files the checker reads)."""
    r = pathlib.Path(root)
    write_csv(r / C.P["universe"], ["id", "included_in_bibliography", "date_effective"],
              [["EO:90001", "1", "1950"], ["EO:90002", "1", "1949"], ["EO:90003", "1", "1961"],
               ["EO:90004", "1", "1955"], ["EO:3016N", "1", "1918"]])
    write_csv(r / C.P["decided"], ["instrument_id", "provisional_substantive_status", "decision_origin"],
              [["EO:90001", "no", "opus_x"], ["EO:90004", "yes", "astra"]])
    write_csv(r / C.P["crosswalk"], ["instrument_id", "signing_date_from_cached_index"],
              [["EO:90001", "1950-03-03"], ["EO:90004", "1955-06-01"]])
    gate = r / C.P["claim_gate_dir"] / "claim_gate.py"
    gate.parent.mkdir(parents=True)
    gate.write_text(
        "import importlib.util as u\n"
        f"_s = u.spec_from_file_location('real_claim_gate', {str(REAL_GATE)!r})\n"
        "_m = u.module_from_spec(_s); _s.loader.exec_module(_m); globals().update(vars(_m))\n", "utf-8")
    # Stage 21 custody: the original (a text file here) and the ending order.
    od = r / "research/stage21/original_sources"
    od.mkdir(parents=True)
    (od / "EO_90001.txt").write_bytes(ORIGINAL_TEXT.encode("utf-8"))
    (od / "EO_90003.txt").write_bytes(ENDING_TEXT.encode("utf-8"))
    pdf = tiny_pdf(["Executive Order 90004", "The Council shall continue to meet", "under section 5 of the Act."])
    (od / "EO_90004.pdf").write_bytes(pdf)
    write_csv(od / "CASE_ORIGINAL_SOURCE_CUSTODY.csv",
              ["instrument_id", "official_PDF_candidate_URL", "custody_state", "sha256_source_bytes_if_present",
               "source_repository_path", "bytes"],
              [["EO:90001", "https://www.govinfo.gov/x/EO_90001.pdf", "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED",
                sha(ORIGINAL_TEXT.encode()), "research/stage21/original_sources/EO_90001.txt", len(ORIGINAL_TEXT)],
               ["EO:90004", "https://www.govinfo.gov/x/EO_90004.pdf", "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED",
                sha(pdf), "research/stage21/original_sources/EO_90004.pdf", len(pdf)]])
    (od / "ACQUISITION_LOG.jsonl").write_text(json.dumps({
        "instrument_id": "EO:90003", "requested_url": "https://www.govinfo.gov/x/EO_90003.pdf",
        "sha256": sha(ENDING_TEXT.encode()), "bytes": len(ENDING_TEXT),
        "repository_path": "research/stage21/original_sources/EO_90003.txt"}) + "\n", "utf-8")
    # Another job's SOURCES.jsonl with extracted text; one record's bytes are in that job's cache on
    # this machine, one is a record only (cache_path null), and some lines are malformed.
    jo = r / "jobs/other-job/output"
    (jo / "text").mkdir(parents=True)
    (jo / "text/savings.txt").write_text(SAVINGS_TEXT, "utf-8")
    (jo / "text/record_only.txt").write_text(RECORD_ONLY_TEXT, "utf-8")
    cache = r / "jobs/other-job-cache/blobs"
    cache.mkdir(parents=True)
    (cache / "savings.txt").write_bytes(SAVINGS_TEXT.encode())
    good = {"source_id": "s1", "instrument_ids": ["EO:90003"], "url": "https://www.federalregister.gov/d/savings",
            "sha256": sha(SAVINGS_TEXT.encode()), "bytes": len(SAVINGS_TEXT), "content_type": "text/plain",
            "retrieved_utc": "2026-10-16T00:00:00Z", "route": "fixture", "page_or_item": "p. 1",
            "text_path": "text/savings.txt", "cache_path": "blobs/savings.txt"}
    rec_only = dict(good, source_id="s2", url="https://www.federalregister.gov/d/record-only", instrument_ids=[],
                    sha256=sha(RECORD_ONLY_TEXT.encode()), text_path="text/record_only.txt", cache_path=None)
    with open(jo / "SOURCES.jsonl", "wb") as fh:
        for line in (json.dumps(good), json.dumps(rec_only), "[1, 2]", '"just a string"', '{"sha256": 5}',
                     json.dumps(dict(good, sha256="9" * 64, text_path=["x"], cache_path=7, instrument_ids="EO:1")),
                     json.dumps(dict(good, sha256="8" * 64, text_path="../../escape.txt", cache_path="C:/x")),
                     "{broken"):
            fh.write(line.encode() + b"\n")
        fh.write(b"\xff\xfe not utf-8\n")
    # A job CSV that is not UTF-8 must not break signing-date loading.
    (r / "jobs/bad-job/output").mkdir(parents=True)
    (r / "jobs/bad-job/output/dates.csv").write_bytes(
        b"instrument_id,signing_date\nEO:3016N,1918-04-01\n\xff\xfe,\x00\n")
    # A committed Opus index in the fixture job folder.
    jd = r / "jobdir"
    (jd / "data").mkdir(parents=True)
    with gzip.open(jd / "data/opus_manifest_index.csv.gz", "wt", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=S.INDEX_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerow({"kind": "file", "sha256": "b" * 64, "bytes": "5", "path": "evidence/x.pdf", "url": "", "text_path": ""})
        w.writerow({"kind": "meta", "sha256": "c" * 64, "bytes": "9", "path": "", "url": "https://www.presidency.ucsb.edu/doc",
                    "text_path": "evidence/doc.txt"})
    (r / "research/readiness/claims").mkdir(parents=True)
    return r, jd


def ref(url, text, page="p. 1"):
    return {"url": url, "sha256": sha(text.encode()), "page_or_item": page}


def good_claim():
    orig = ref("https://www.govinfo.gov/x/EO_90001.pdf", ORIGINAL_TEXT)
    end = ref("https://www.govinfo.gov/x/EO_90003.pdf", ENDING_TEXT)
    return {
        "schema": "eo-lifecycle-claim/v1", "instrument_id": "EO:90001", "whole_order_status": "no",
        "original_representation": orig,
        "operative_clauses": [
            {"scope_id": "s1", "original_operative_text":
                "There is hereby established the Test Board, which shall advise the President on testing.",
             "original_source": orig, "state_at_cutoff": "terminated",
             "first_end": {"date": "1961-05-01", "actor": "President", "mechanism": "revocation by EO 90003",
                           "source": end, "quote": "Executive Order 90001 is hereby revoked."},
             "later_events": []},
            {"scope_id": "s2", "original_operative_text": "Executive Order No. 90002 of January 1, 1949, is superseded.",
             "original_source": orig, "state_at_cutoff": "terminated",
             "first_end": {"date": "1961-05-01", "actor": "President", "mechanism": "revocation", "source": end},
             "later_events": []},
        ],
        "whole_order_end": {"date": "1961-05-01", "actor": "President", "mechanism": "revocation", "source": end},
        "savings_residuals": {"state": "none_after_bounded_search", "reason": "no savings clause found",
                              "source": ref("https://www.federalregister.gov/d/savings", SAVINGS_TEXT)},
        "later_source_search": [{"repository": "govinfo", "query_or_scope": "EO 90001 1950-2026", "checked_on": "2026-10-16"}],
        "unresolved_material_gaps": [],
        "research_rationale": "The board was created in 1950 and revoked in full by EO 90003 in 1961; no savings.",
    }


def rows_for(rows, check, result=None):
    return [r for r in rows if r["check"] == check and (result is None or r["result"] == result)]


@unittest.skipUnless(REAL_GATE.is_file(), "research/stage19/code/claim_gate.py not checked out")
class CheckerTests(unittest.TestCase):
    def setUp(self):
        # Insulate from the caller's environment (job.py passes its own settings through).
        clean = {k: v for k, v in os.environ.items()
                 if not k.startswith("CLAIM_CHECKER_") and k not in ("JOB_LIMIT", "JOB_CACHE_DIR")}
        clean["CLAIM_CHECKER_VERIFY_DOWNLOADS"] = "0"  # tests never use the network
        patcher = mock.patch.dict(os.environ, clean, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        C._VERIFY.update(left=None, last=0.0)
        self.tmp = tempfile.mkdtemp(prefix="claim-checker-test-")
        self.repo, self.jobdir = build_repo(self.tmp)
        self.ctx = C.Context(self.repo, self.jobdir, pathlib.Path(self.tmp) / "cache",
                             today=C.dt.date(2026, 10, 17))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_good_claim_passes_everything(self):
        rows, errors, status = C.check_claim(good_claim(), self.ctx)
        self.assertEqual(errors, [])
        self.assertEqual(status, "no")
        fails = [r for r in rows if r["result"] == "fail"]
        self.assertEqual(fails, [], fails)
        src = {r["field"]: r["status"] for r in rows_for(rows, "source_held")}
        self.assertEqual(src["original_representation"], "held_bytes_verified")

        self.assertEqual(src["savings_residuals.source"], "held_bytes_verified")  # re-hashed in the job's cache
        ident = {r["field"]: r["status"] for r in rows_for(rows, "source_identity")}
        self.assertEqual(ident, {"original_representation": "recorded_for_this_order",
                                 "operative_clauses[0].original_source": "recorded_for_this_order",
                                 "operative_clauses[1].original_source": "recorded_for_this_order"})
        quotes = {r["field"]: r["status"] for r in rows_for(rows, "quote_verbatim")}
        # line-break hyphenation ("Presi-\ndent") and whitespace normalised
        self.assertEqual(quotes["operative_clauses[0].original_operative_text"], "normalised")
        self.assertEqual(quotes["operative_clauses[1].original_operative_text"], "exact")
        self.assertEqual(quotes["operative_clauses[0].first_end.quote"], "exact")
        cited = {r["detail"] for r in rows_for(rows, "order_exists", "pass")}
        self.assertTrue(any("EO:90002" in d for d in cited))
        self.assertTrue(any("EO:90003" in d for d in cited))
        summ = C.summarise_claim("k", "f", 1, good_claim(), rows, errors, status, self.ctx)
        self.assertTrue(summ["all_checks_passed"])
        self.assertTrue(all(s["checker_passed"] for s in summ["steps"].values()))

    def test_overlay_proposal_key_is_typed_metadata_not_a_second_order(self):
        claim = good_claim()
        claim["claim_kit"] = {"status_overlay": {"schema": "eo-claim-kit-working-status/v1",
                                               "proposal_id": "status-overlay:EO:90001:" + "a" * 20}}
        rows = []
        C.check_orders(claim, self.ctx, rows)
        self.assertEqual(rows_for(rows, "order_exists", "fail"), [])
        self.assertTrue(any(r["status"] == "overlay_proposal_key" for r in rows))
        for bad in ("status-overlay:EO:99999:" + "a" * 20, "status-overlay:EO:90003:" + "a" * 20,
                    "status-overlay:EO:90001:" + "a" * 19, "status-overlay:EO:90001:" + "a" * 20 + " EO:99999",
                    "EO:90001:" + "a" * 20, "status-overlay:EO:90001", "EO:90001", "not-an-id", None):
            claim["claim_kit"]["status_overlay"]["proposal_id"] = bad
            rows = []
            C.check_orders(claim, self.ctx, rows)
            self.assertTrue(rows_for(rows, "order_exists", "fail"), bad)
        claim["claim_kit"]["status_overlay"]["proposal_id"] = "status-overlay:EO:90001:" + "a" * 20
        claim["operative_clauses"][0]["first_end"]["actor"] = "EO:99999"
        rows = []
        C.check_orders(claim, self.ctx, rows)
        self.assertTrue(rows_for(rows, "order_exists", "fail"))

    def test_bad_claim_is_caught(self):
        c = good_claim()
        c["original_representation"] = dict(c["original_representation"], sha256="d" * 64)  # same URL, other bytes
        c["operative_clauses"][0]["original_operative_text"] = "The Test Board shall advise on testing."  # paraphrase
        c["operative_clauses"][0]["first_end"]["date"] = "1949-12-31"  # before signing 1950-03-03
        c["operative_clauses"][1]["first_end"]["date"] = "2026-11-01"  # after the cutoff
        c["operative_clauses"][1]["first_end"]["source"] = {"url": "https://example.gov/never", "sha256": "e" * 64,
                                                            "page_or_item": "p. 2"}
        c["operative_clauses"][0]["first_end"]["mechanism"] += " (see Executive Order 99999)"
        rows, errors, _ = C.check_claim(c, self.ctx)
        src = {r["field"]: r["status"] for r in rows_for(rows, "source_held")}
        self.assertEqual(src["original_representation"], "held_but_different_hash")
        self.assertEqual(src["operative_clauses[1].first_end.source"], "not_held")
        q = {r["field"]: (r["result"], r["status"]) for r in rows_for(rows, "quote_verbatim")}
        self.assertEqual(q["operative_clauses[0].original_operative_text"], ("fail", "not_found"))
        dates = {(r["field"], r["status"]) for r in rows if r["result"] == "fail" and r["check"].startswith("date")}
        self.assertIn(("operative_clauses[0].first_end.date", "before_signing_date"), dates)
        self.assertIn(("operative_clauses[1].first_end.date", "after_legal_cutoff"), dates)
        self.assertTrue(any("99999" in r["detail"] for r in rows_for(rows, "order_exists", "fail")))
        self.assertIn("clause_1_first_end", errors)
        summ = C.summarise_claim("k", "f", 1, c, rows, errors, "no", self.ctx)
        self.assertFalse(summ["all_checks_passed"])
        self.assertFalse(summ["steps"]["original_text"]["checker_passed"])
        self.assertTrue(summ["steps"]["savings_residuals"]["checker_passed"])

    def test_partial_claim_steps(self):
        c = good_claim()
        for k in ("whole_order_end", "savings_residuals", "later_source_search"):
            del c[k]
        for cl in c["operative_clauses"]:
            del cl["first_end"]
        rows, errors, status = C.check_claim(c, self.ctx)
        summ = C.summarise_claim("k", "f", 1, c, rows, errors, status, self.ctx)
        self.assertTrue(summ["steps"]["original_text"]["checker_passed"])
        self.assertFalse(summ["steps"]["savings_residuals"]["present"])
        self.assertEqual(summ["steps"]["savings_residuals"]["mechanical"], "absent")
        self.assertFalse(summ["gate_passed"])

    def test_unknown_instrument_and_year_only_signing(self):
        c = good_claim()
        c["instrument_id"] = "EO:12345678"
        rows, _, _ = C.check_claim(c, self.ctx)
        self.assertEqual(rows_for(rows, "order_exists", "fail")[0]["field"], "instrument_id")
        c = good_claim()
        c["instrument_id"] = "EO:90003"  # signing year 1961 only; 1961-05-01 is fine
        rows, _, _ = C.check_claim(c, self.ctx)
        st = {r["status"] for r in rows_for(rows, "date_after_signing")}
        self.assertEqual(st, {"on_or_after_index_year_only"})

    def test_opus_hash_only_and_committed_index(self):
        c = good_claim()
        c["savings_residuals"]["source"] = {"url": "https://www.presidency.ucsb.edu/doc", "sha256": "c" * 64,
                                            "page_or_item": "x"}
        c["original_representation"] = {"url": "https://example.org/opus", "sha256": "b" * 64, "page_or_item": "x"}
        rows, _, _ = C.check_claim(c, self.ctx)
        src = {r["field"]: (r["result"], r["status"]) for r in rows_for(rows, "source_held")}
        self.assertEqual(src["savings_residuals.source"], ("skip", "custody_record_only"))
        self.assertEqual(src["original_representation"], ("pass", "held_bytes_in_release_or_repo"))

    def test_gpo_published_hash_counts_as_held(self):
        c = good_claim()
        c["savings_residuals"]["source"] = {"url": "https://www.presidency.ucsb.edu/doc", "sha256": "c" * 64,
                                            "page_or_item": "x"}
        rows, _, _ = C.check_claim(c, self.ctx)
        src = {r["field"]: (r["result"], r["status"]) for r in rows_for(rows, "source_held")}
        self.assertEqual(src["savings_residuals.source"], ("skip", "custody_record_only"))
        fix = self.repo / C.GPO_MATCHED
        fix.parent.mkdir(parents=True, exist_ok=True)
        fix.write_text(json.dumps({"c" * 64: {"url": "https://www.govinfo.gov/x.pdf", "result": "match",
                                              "premis_url": "https://www.govinfo.gov/metadata/pkg/x/premis.xml",
                                              "checked_utc": "2026-10-17T00:00:00Z"},
                                   "d" * 64: {"url": "u", "result": "mismatch"}}), "utf-8")
        ctx = C.Context(self.repo, self.jobdir, pathlib.Path(self.tmp) / "cache3", today=C.dt.date(2026, 10, 17))
        self.assertNotIn("d" * 64, ctx.gpo_matched)  # only matches count
        rows, _, _ = C.check_claim(c, ctx)
        src = {r["field"]: (r["result"], r["status"]) for r in rows_for(rows, "source_held")}
        self.assertEqual(src["savings_residuals.source"], ("pass", "gpo_published_hash_match"))

    def test_verify_by_download_uses_cache_and_budget(self):
        import hashlib
        data = b"%PDF-1.4 granule"
        sha = hashlib.sha256(data).hexdigest()
        cache = pathlib.Path(self.tmp) / "vcache"
        url = "https://www.govinfo.gov/content/pkg/FR-1995-01-03/pdf/94-32388.pdf"
        self.assertIsNone(C.verify_by_download(url, sha, cache))           # budget 0, nothing cached
        store = cache / "verified" / sha[:2] / (sha + ".bin")
        store.parent.mkdir(parents=True)
        store.write_bytes(data)
        self.assertTrue(C.verify_by_download(url, sha, cache))             # cached bytes re-hashed
        self.assertFalse(C.verify_by_download(url, "0" * 64, cache) or False)
        self.assertIsNone(C.verify_by_download("https://example.org/x.pdf", sha, cache))  # other hosts: never

    def test_local_bytes_differ_from_record(self):
        (self.repo / "research/stage21/original_sources/EO_90003.txt").write_text("tampered", "utf-8")
        ctx = C.Context(self.repo, self.jobdir, pathlib.Path(self.tmp) / "cache2", today=C.dt.date(2026, 10, 17))
        rows, _, _ = C.check_claim(good_claim(), ctx)
        st = {r["status"] for r in rows_for(rows, "source_held") if "first_end" in r["field"]}
        self.assertEqual(st, {"held_record_but_local_bytes_differ"})

    def test_dates(self):
        c = good_claim()
        c["later_source_search"][0]["checked_on"] = "2026-13-01"
        c["operative_clauses"][0]["first_end"]["source"]["retrieved_utc"] = "2026-10-16T10:00:00Z"
        c["whole_order_end"]["date"] = "1961-5-1"
        rows, _, _ = C.check_claim(c, self.ctx)
        st = {(r["field"], r["status"]) for r in rows_for(rows, "date_valid")}
        self.assertIn(("later_source_search[0].checked_on", "not_iso_date"), st)
        self.assertIn(("operative_clauses[0].first_end.source.retrieved_utc", "valid_activity_date"), st)
        self.assertIn(("whole_order_end.date", "not_exact_iso_date"), st)

    @unittest.skipUnless(HAVE_PYPDF, "pypdf not installed")
    def test_pdf_quote(self):
        pdf = (self.repo / "research/stage21/original_sources/EO_90004.pdf").read_bytes()
        r = {"url": "https://www.govinfo.gov/x/EO_90004.pdf", "sha256": sha(pdf), "page_or_item": "p. 1"}
        copies = self.ctx.index.lookup_sha(sha(pdf))
        self.assertTrue(copies)
        rows = []
        C.check_quote("The Council shall continue to meet under section 5 of the Act.", "q", r, "source", self.ctx, rows)
        self.assertEqual(rows[0]["result"], "pass", rows)
        rows = []
        C.check_quote("The Council shall meet.", "q", r, "source", self.ctx, rows)
        self.assertEqual(rows[0]["status"], "not_found")
        self.assertTrue((pathlib.Path(self.tmp) / "cache/text" / f"{sha(pdf)}.json").is_file())

    def test_main_end_to_end_with_limit_and_fetch(self):
        claims = self.repo / "research/readiness/claims"
        bad = good_claim()
        bad["original_representation"]["sha256"] = "f" * 64
        (claims / "a.jsonl").write_text(json.dumps(good_claim()) + "\n" + "{not json\n", "utf-8")
        (claims / "b.jsonl").write_text(json.dumps(bad) + "\n" + json.dumps(good_claim()) + "\n", "utf-8")
        ladder = self.repo / "jobs/source-ladder/fetch_ladder.py"
        ladder.parent.mkdir(parents=True)
        ladder.write_text("def fetch_source(url, cache_dir=None):\n"
                          "    return {'url': url, 'sha256': '0'*64, 'route': 'fake'}\n", "utf-8")
        out = pathlib.Path(self.tmp) / "out"
        env = {"REPO_ROOT": str(self.repo), "OUTPUT_DIR": str(out), "JOB_CACHE_DIR": str(pathlib.Path(self.tmp) / "c"),
               "JOB_LIMIT": "3"}
        with mock.patch.dict(os.environ, env), mock.patch.object(C, "HERE", self.jobdir):
            summary = C.main(["--fetch"])
        self.assertEqual(summary["claim_lines_found"], 4)
        self.assertEqual(summary["claims_checked"], 2)
        self.assertEqual(summary["claims_parse_errors"], 1)
        per = json.loads((out / "PER_CLAIM.json").read_text("utf-8"))
        # b.jsonl line 1 is the latest checked claim for EO:90001 (limit 3 stops before b.jsonl line 2)
        self.assertEqual(per["by_instrument"]["EO:90001"]["claim_key"], "research/readiness/claims/b.jsonl:1")
        self.assertFalse(per["by_instrument"]["EO:90001"]["steps_checker_passed"]["original_text"])
        with open(out / "CLAIM_CHECKS.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertTrue(any(r["check"] == "parse" for r in rows))
        attempts = [json.loads(x) for x in (out / "FETCH_ATTEMPTS.jsonl").read_text("utf-8").splitlines()]
        self.assertEqual(attempts[0]["result"], "fetched_different_bytes")
        self.assertTrue((out / "SUMMARY.json").is_file() and (out / "REPORT.md").is_file())

    def test_fetch_with_class_based_ladder(self):
        ladder = self.repo / "jobs/source-ladder/fetch_ladder.py"
        ladder.parent.mkdir(parents=True)
        ladder.write_text(FAKE_CLASS_LADDER, "utf-8")
        out = pathlib.Path(self.tmp) / "outf"
        out.mkdir()
        r = {"url": "https://example.gov/x.pdf", "sha256": "f" * 64, "page_or_item": "60 FR 309"}
        attempts = C.run_fetch(self.ctx, [("k", "EO:90001", "whole_order_end.source", r)], out)
        self.assertEqual(attempts[0]["result"], "fetched_and_matches_claim")
        self.assertEqual(attempts[0]["source_record"]["step"], "ending_or_current_basis")
        self.assertTrue((out / "FETCH_ATTEMPTS.jsonl").is_file())

    def test_malformed_values_do_not_stop_the_run(self):
        """A list-valued scope_id makes claim_gate raise; that claim is reported and the run goes on."""
        idx = self.ctx.index
        self.assertTrue(any("ignored" in n and "other-job" in n for n in idx.notes), idx.notes)
        self.assertEqual(idx.lookup_sha("9" * 64)[0].text_path, None)  # non-string text_path ignored
        self.assertEqual(idx.lookup_sha("8" * 64)[0].text_path, None)  # path escaping the folder ignored
        self.assertEqual(self.ctx.signing["EO:3016N"]["full"], {"1918-04-01"})  # non-UTF-8 CSV still read
        claims = self.repo / "research/readiness/claims"
        bad = good_claim()
        bad["operative_clauses"][0]["scope_id"] = ["s1"]
        with open(claims / "a.jsonl", "wb") as fh:
            fh.write(json.dumps(bad).encode() + b"\n" + b"\xff\xfe{}\n" + json.dumps(good_claim()).encode() + b"\n")
        (claims / "b.jsonl").write_text(json.dumps(dict(good_claim(), instrument_id="EO:90004")) + "\n", "utf-8")
        out = pathlib.Path(self.tmp) / "out-bad"
        env = {"REPO_ROOT": str(self.repo), "OUTPUT_DIR": str(out), "JOB_CACHE_DIR": str(pathlib.Path(self.tmp) / "c"),
               "JOB_LIMIT": "x"}
        real_dates = C.check_dates

        def flaky(claim, ctx, rows):
            if claim.get("instrument_id") == "EO:90004":
                raise RuntimeError("simulated checker bug")
            return real_dates(claim, ctx, rows)

        with mock.patch.dict(os.environ, env), mock.patch.object(C, "HERE", self.jobdir), \
                mock.patch.object(C, "check_dates", flaky):
            summary = C.main([])
        self.assertEqual(summary["claims_checked"], 3)
        self.assertEqual(summary["claims_parse_errors"], 1)  # the non-UTF-8 line
        self.assertEqual(summary["claims_checker_errors"], 1)
        per = json.loads((out / "PER_CLAIM.json").read_text("utf-8"))
        first = per["claims"][0]
        self.assertEqual(first["gate_errors"], ["gate_raised_exception"])
        self.assertFalse(any(s["checker_passed"] for s in first["steps"].values()))
        self.assertIn("not valid UTF-8", per["claims"][1]["parse_error"])
        self.assertTrue(per["by_instrument"]["EO:90001"]["all_checks_passed"])  # a.jsonl line 3
        self.assertFalse(per["by_instrument"]["EO:90004"]["all_checks_passed"])
        self.assertIn("simulated checker bug", per["claims"][3]["checker_error"])
        with open(out / "CLAIM_CHECKS.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertTrue(any(r["check"] == "checker_error" for r in rows))
        self.assertTrue(any(r["status"] == "gate_raised_exception" for r in rows))
        self.assertFalse(any(r["result"] == "pass" for r in rows))  # passing rows are not written
        self.assertNotIn("claim_sha256", rows[0])
        self.assertTrue((out / "REPORT.md").is_file())

    def test_source_of_another_order(self):
        pdf = (self.repo / "research/stage21/original_sources/EO_90004.pdf").read_bytes()
        other = {"url": "https://www.govinfo.gov/x/EO_90004.pdf", "sha256": sha(pdf), "page_or_item": "p. 1"}
        c = good_claim()
        c["original_representation"] = other
        c["operative_clauses"][0]["original_source"] = other
        rows, errors, status = C.check_claim(c, self.ctx)
        ident = {r["field"]: (r["result"], r["status"]) for r in rows_for(rows, "source_identity")}
        self.assertEqual(ident["original_representation"], ("fail", "recorded_for_other_order"))
        self.assertEqual(ident["operative_clauses[0].original_source"], ("fail", "recorded_for_other_order"))
        self.assertEqual(ident["operative_clauses[1].original_source"], ("pass", "recorded_for_this_order"))
        summ = C.summarise_claim("k", "f", 1, c, rows, errors, status, self.ctx)
        self.assertFalse(summ["steps"]["original_text"]["checker_passed"])
        self.assertFalse(summ["steps"]["clause_inventory"]["checker_passed"])
        self.assertFalse(summ["all_checks_passed"])
        # No custody association: the text decides (record-only job copy whose text does not name the order).
        rows = []
        rec = {"url": "https://www.federalregister.gov/d/record-only", "sha256": sha(RECORD_ONLY_TEXT.encode())}
        C.check_identity(rec, "original_representation", "EO:90001", self.ctx, rows)
        self.assertEqual((rows[0]["result"], rows[0]["status"]), ("warn", "text_does_not_name_this_order"))
        rows = []
        C.check_identity(ref("https://www.govinfo.gov/x/EO_90001.pdf", ORIGINAL_TEXT), "original_representation",
                         "EO:90002", self.ctx, rows)  # recorded for 90001, but its text names EO 90002
        self.assertEqual(rows[0]["status"], "recorded_for_other_order_but_text_names_this_order")
        self.assertIsNotNone(C._order_number_pattern("EO:12950").search("Executive Order No. 12,950 of"))
        self.assertIsNone(C._order_number_pattern("EO:1295").search("Executive Order 12950"))
        self.assertIsNotNone(C._order_number_pattern("EO:3016N").search("EXECUTIVE ORDER 3016-N"))

    def test_too_short_quotation(self):
        c = good_claim()
        c["operative_clauses"][0]["original_operative_text"] = "the Test Board"
        rows, errors, status = C.check_claim(c, self.ctx)
        q = [r for r in rows_for(rows, "quote_verbatim") if r["field"] == "operative_clauses[0].original_operative_text"]
        self.assertEqual((q[0]["result"], q[0]["status"]), ("warn", "too_short_to_verify"))
        self.assertIn("occurs 2 time", q[0]["detail"])
        summ = C.summarise_claim("k", "f", 1, c, rows, errors, status, self.ctx)
        self.assertFalse(summ["steps"]["clause_inventory"]["checker_passed"])
        self.assertTrue(summ["steps"]["original_text"]["checker_passed"])
        self.assertEqual(summ["mechanical_result"], "pass_with_unverified")

    def test_quote_inside_a_sources_list_item(self):
        c = good_claim()
        orig = ref("https://www.govinfo.gov/x/EO_90001.pdf", ORIGINAL_TEXT)
        end = ref("https://www.govinfo.gov/x/EO_90003.pdf", ENDING_TEXT)
        c["operative_clauses"][0]["later_events"] = [{
            "effective_date": "1961-05-01", "actor": "President", "mechanism": "reprinted", "source": end,
            "sources": [dict(orig, quote="Executive Order No. 90002 of January 1, 1949, is superseded.")]}]
        rows, _, _ = C.check_claim(c, self.ctx)
        q = [r for r in rows_for(rows, "quote_verbatim") if "sources[0]" in r["field"]]
        self.assertEqual(q[0]["result"], "pass", q)
        self.assertIn("EO_90001.pdf", q[0]["detail"])
        self.assertIn(orig["sha256"][:12], q[0]["detail"])

    def test_opus_text_pack(self):
        pack = self.jobdir / S.TEXT_PACK
        with gzip.open(pack, "wt", encoding="utf-8") as fh:
            fh.write(json.dumps({"sha256": "b" * 64, "how": "html_text",
                                 "pages": ["Executive Order 90001 created the Test Board to advise on testing."]}) + "\n")
            fh.write("not json\n")
        ctx = C.Context(self.repo, self.jobdir, pathlib.Path(self.tmp) / "cache3", today=C.dt.date(2026, 10, 17))
        self.assertEqual(len(ctx.index.packed_texts), 1)
        rows = []
        C.check_quote("created the Test Board to advise on testing.", "q",
                      {"url": "https://example.org/opus", "sha256": "b" * 64}, "source", ctx, rows)
        self.assertEqual((rows[0]["result"], rows[0]["status"]), ("pass", "exact"), rows)
        self.assertIn("opus_text_pack", rows[0]["detail"])

    def test_csv_size_guard(self):
        rows = [{"claim_key": f"f:{n}", "instrument_id": "EO:1", "effective_for_tracker": "yes" if n % 2 else "no",
                 "step": "clause_inventory", "check": "quote_verbatim", "field": "x", "result": r,
                 "status": "s", "detail": "d" * 50} for n in range(40) for r in ("pass", "fail", "warn")]
        mode, kept = C.select_csv_rows(rows, 10_000_000)
        self.assertEqual((mode, len(kept)), ("non_pass_rows", 80))
        mode, kept = C.select_csv_rows(rows, 10_000_000, include_passes=True)
        self.assertEqual((mode, len(kept)), ("all_rows", 120))
        mode, kept = C.select_csv_rows(rows, 5_000)
        self.assertEqual((mode, len(kept)), ("non_pass_rows_of_effective_claims", 40))
        mode, kept = C.select_csv_rows(rows, 3_000)
        self.assertEqual((mode, len(kept)), ("fail_rows_of_effective_claims", 20))
        mode, kept = C.select_csv_rows(rows, 1_000)
        self.assertEqual(mode, "fail_rows_of_effective_claims_truncated")
        self.assertLess(len(C._csv_text(kept).encode()), 1_000)

    def test_main_with_no_claims(self):
        out = pathlib.Path(self.tmp) / "out0"
        with mock.patch.dict(os.environ, {"REPO_ROOT": str(self.repo), "OUTPUT_DIR": str(out), "JOB_LIMIT": ""}), \
                mock.patch.object(C, "HERE", self.jobdir):
            summary = C.main([])
        self.assertEqual(summary["claims_checked"], 0)
        self.assertEqual(json.loads((out / "PER_CLAIM.json").read_text("utf-8"))["claims"], [])


    def working_claim(self):
        import copy
        claim = good_claim()
        text = ORIGINAL_TEXT
        rel = 'jobs/app-executive-orders/output/texts/EO_90001.txt'
        path = self.repo / rel; path.parent.mkdir(parents=True)
        path.write_text(text, encoding='utf-8')
        source = dict(claim['original_representation'], text_path=rel, text_sha256=sha(text.encode()),
                      grade='mirror_transcription', acceptable_as_original=False, instrument_id='EO:90001',
                      char_start=0, char_end=len(text), quote=text)
        fragment = {'kind':'original_representation', 'instrument_id':'EO:90001', 'data':source}
        (path.parent.parent/'FRAGMENTS.jsonl').write_text(json.dumps(fragment)+'\n')
        claim['original_representation'] = source
        snippets = ["There is hereby established the Test Board, which shall advise the Presi-\ndent on testing.",
                    "Executive Order No. 90002 of January 1, 1949, is superseded."]
        for clause, quote in zip(claim['operative_clauses'], snippets):
            start = text.index(quote)
            clause['original_source'] = dict(source, quote=quote, char_start=start, char_end=start+len(quote))
            clause['original_operative_text'] = quote
        claim['working_text'] = C.W.blank([source])
        claim['working_text']['confirmations'][0].update(identity_confirmed=True, complete_text_confirmed=True)
        self.ctx.working_text_index = C.W.Index(self.repo)
        return claim

    def test_working_text_passes_separate_policy_without_original_upgrade(self):
        claim = self.working_claim()
        rows, errors, status = C.check_claim(claim, self.ctx)
        summary = C.summarise_claim('test', 'test.jsonl', 1, claim, rows, errors, status, self.ctx)
        self.assertTrue(summary['all_checks_passed'], summary)
        self.assertEqual(summary['text_evidence_tier'], 'transcription_dependent')
        self.assertFalse(claim['original_representation']['acceptable_as_original'])

    def test_working_text_does_not_waive_custody_only_or_missing_ending(self):
        claim = self.working_claim()
        original_sha = claim['original_representation']['sha256']
        for copy in self.ctx.index.lookup_sha(original_sha):
            copy.custody = 'record_only'
        rows, errors, status = C.check_claim(claim, self.ctx)
        summary = C.summarise_claim('test', 'test.jsonl', 1, claim, rows, errors, status, self.ctx)
        self.assertFalse(summary['steps']['original_text']['checker_passed'])
        self.assertEqual(summary['mechanical_result'], 'pass_with_unverified')
        claim['whole_order_end']['source']['sha256'] = 'e'*64
        rows, errors, status = C.check_claim(claim, self.ctx)
        summary = C.summarise_claim('test', 'test.jsonl', 1, claim, rows, errors, status, self.ctx)
        self.assertFalse(summary['steps']['ending_or_current_basis']['checker_passed'])

    def test_transcription_hash_cannot_be_laundered_through_text_path_alias(self):
        claim = self.working_claim()
        original_path = self.repo / claim['original_representation']['text_path']
        (self.repo / 'alias.txt').write_bytes(original_path.read_bytes())
        for _, ref in C.W.references(claim):
            if ref.get('acceptable_as_original') is False:
                ref.update(text_path='alias.txt', acceptable_as_original=True)
                ref.pop('grade')
        claim.pop('working_text')
        rows, errors, status = C.check_claim(claim, self.ctx)
        summary = C.summarise_claim('test', 'test.jsonl', 1, claim, rows, errors, status, self.ctx)
        self.assertFalse(summary['all_checks_passed'])
        self.assertEqual(summary['mechanical_result'], 'fail')

    def test_unlabeled_transcription_cannot_use_old_checker_success(self):
        claim = self.working_claim()
        del claim['working_text']
        for _, ref in C.W.references(claim):
            ref.pop('grade', None); ref.pop('acceptable_as_original', None)
        rows, errors, status = C.check_claim(claim, self.ctx)
        summary = C.summarise_claim('test', 'test.jsonl', 1, claim, rows, errors, status, self.ctx)
        self.assertFalse(summary['all_checks_passed'])
        self.assertFalse(summary['steps']['original_text']['checker_passed'])
        self.assertTrue(any(r['check']=='working_text_policy' and r['result']=='fail' for r in rows))

    def test_hash_spelling_and_archival_alias_cannot_hide_transcription(self):
        import copy
        original = self.working_claim()
        for spelling in ('uppercase', 'whitespace', 'archival_alias'):
            with self.subTest(spelling=spelling):
                claim = copy.deepcopy(original)
                claim.pop('working_text')
                for _, ref in C.W.references(claim):
                    if ref.get('acceptable_as_original') is not False:
                        continue
                    ref.pop('grade')
                    ref['acceptable_as_original'] = True
                    if spelling == 'uppercase':
                        ref['sha256'] = ref['sha256'].upper()
                    elif spelling == 'whitespace':
                        ref['sha256'] = ' \t' + ref['sha256'] + '\n'
                    else:
                        ref['local_file_sha256'] = ref.pop('sha256')
                        ref['archival_id'] = 'known-derivative'
                rows, errors, status = C.check_claim(claim, self.ctx)
                summary = C.summarise_claim('test', 'test.jsonl', 1, claim, rows, errors, status, self.ctx)
                self.assertFalse(summary['all_checks_passed'])
                self.assertTrue(rows_for(rows, 'working_text_policy', 'fail'))

    def test_nested_source_lists_require_transcription_disclosure(self):
        text = 'This held transcription supplies additional factual context.\n'
        path = self.repo/'jobs/app-executive-orders/output/texts/EO_90001.txt'
        path.parent.mkdir(parents=True)
        path.write_text(text)
        ref = {'sha256':sha(text.encode()), 'url':'https://example.gov/transcription',
               'text_path':path.relative_to(self.repo).as_posix(), 'text_sha256':sha(text.encode()),
               'instrument_id':'EO:90001', 'grade':'mirror_transcription',
               'acceptable_as_original':False, 'quote':text, 'char_start':0,
               'char_end':len(text), 'page_or_item':'complete text'}
        (path.parent.parent/'FRAGMENTS.jsonl').write_text(json.dumps({
            'kind':'original_representation', 'instrument_id':'EO:90001', 'data':ref})+'\n')
        self.ctx.index.add(S.HeldCopy('derivative fixture',ref['sha256'],url=ref['url'],
                                    local_path=path,text_path=path,instrument_ids=['EO:90001']))
        self.ctx.working_text_index = C.W.Index(self.repo)
        for key in ('sources', 'source_refs'):
            with self.subTest(key=key):
                claim = good_claim()
                claim['additional_context'] = [{'nested':{key:[dict(ref)]}}]
                errors, dependent = C.W.policy(claim,self.repo)
                self.assertIn('working_text:disclosure_required',errors)
                self.assertEqual(len(dependent),1)
                rows, gate_errors, status = C.check_claim(claim,self.ctx)
                summary = C.summarise_claim('test','test.jsonl',1,claim,rows,gate_errors,status,self.ctx)
                self.assertFalse(summary['all_checks_passed'])
                self.assertTrue(rows_for(rows,'working_text_policy','fail'))
                claim['working_text'] = C.W.blank([ref])
                claim['working_text']['confirmations'][0].update(identity_confirmed=True,complete_text_confirmed=True)
                rows, gate_errors, status = C.check_claim(claim,self.ctx)
                summary = C.summarise_claim('test','test.jsonl',1,claim,rows,gate_errors,status,self.ctx)
                self.assertTrue(summary['all_checks_passed'],summary)
                self.assertEqual(summary['text_evidence_tier'],'transcription_dependent')


class PureFunctionTests(unittest.TestCase):
    def test_prepared_text_is_reused(self):
        prep = C.Prepared(["The Board shall meet. ", "It shall re-\nport yearly."])
        self.assertEqual(C.find_quote("shall report yearly.", prep)[:2], ("normalised", "text page 2"))
        self.assertEqual(C.find_quote("The Board shall meet.", prep)[:2], ("exact", "text page 1"))
        self.assertEqual(prep.occurrences("shall"), 2)

    def test_find_quote(self):
        pages = ["The efﬁcient conduct of tests is the Presi-\ndent's duty.", "Second page."]
        self.assertEqual(C.find_quote("The efﬁcient conduct", pages)[0], "exact")
        self.assertEqual(C.find_quote("The efficient conduct of tests is the President's duty.", pages)[:2],
                         ("normalised", "text page 1"))
        st, _, hint = C.find_quote("THE EFFICIENT CONDUCT", pages)
        self.assertEqual(st, "not_found")
        self.assertIn("folding", hint)
        self.assertEqual(C.find_quote("self-governing body", ["a self-\ngoverning body"])[0], "normalised")
        self.assertEqual(C.find_quote("duty. Second", pages)[:2], ("normalised", "spans a page break"))
        self.assertEqual(C.find_quote("(50 U.S.C. 1701 et seq.), the", ["Act (50 U.S.C. 1701 et seq .), the"])[0],
                         "normalised")

    def test_cited_orders(self):
        def ids(t):
            return [c[0] for _, c in C.cited_orders(t)]
        self.assertEqual(ids("Executive Order No. 12826 of December 30, 1992, and Executive Order No. 12886"),
                         ["EO:12826", "EO:12886"])
        self.assertEqual(ids("Executive Orders 12826 and 12886 are revoked"), ["EO:12826", "EO:12886"])
        self.assertEqual(ids("see E.O. 9066 and EO 11000"), ["EO:9066", "EO:11000"])
        self.assertEqual(ids("Executive Order 12944, 60 FR 309"), ["EO:12944"])
        self.assertEqual(ids("Executive Order of March 3, 1903"), [])
        self.assertEqual(C.cited_orders("EO:3016-N.")[0][1], ["EO:3016-N", "EO:3016N"])
        self.assertEqual(ids("Executive Order No. 3016-N"), ["EO:3016N"])
        self.assertEqual(ids("E.O. 12,944 and Executive Order 13,000"), ["EO:12944", "EO:13000"])
        self.assertEqual(ids("Executive Orders 12944, 1995 Comp., and 12950"), ["EO:12944"])
        self.assertEqual(ids("Executive Orders 12944 and 12950, 3 CFR, 1995 Comp."), ["EO:12944", "EO:12950"])
        self.assertEqual(ids("Executive Orders 12944, 60 FR 309"), ["EO:12944"])
        self.assertEqual(ids("Executive Order 106-1"), ["EO:106-1"])
        self.assertEqual(ids("Executive Order 123456"), [])

    def test_norm_url_and_sha(self):
        self.assertEqual(S.norm_url("http://WWW.GovInfo.gov/a/b/#x"), "https://www.govinfo.gov/a/b")
        self.assertIsNone(S.sha_hex("xyz"))
        self.assertEqual(S.sha_hex("A" * 64), "a" * 64)

    def test_html_and_lfs(self):
        pages, how = S.bytes_to_pages(b"<html><body><p>Hello <b>world</b></p><script>x()</script></body></html>")
        self.assertEqual(how, "html_text")
        self.assertIn("Hello world", " ".join(pages[0].split()))
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "x.zip"
            p.write_bytes(S.LFS_MAGIC + b"\noid sha256:abc\nsize 5\n")
            self.assertTrue(S.is_lfs_pointer(p))


@unittest.skipUnless(REAL_GATE.is_file(), "research/stage19/code/claim_gate.py not checked out")
class SourceBookTests(unittest.TestCase):
    """Printed volumes committed under releases/source_books (Git LFS), named by a job's data/PROVENANCE.json."""

    setUp = CheckerTests.setUp
    tearDown = CheckerTests.tearDown

    BOOK_BYTES = b"%PDF-1.4 a printed volume of executive orders (fixture bytes, never parsed)\n"
    BOOK_TEXT = ("[page header removed]\nEXECUTIVE ORDER No. 90001\nSection 1. There is hereby established "
                 "the Test Board, which shall advise the President on testing.\n")

    def add_book(self, pointer_oid=None, real=False):
        """A book job: data/PROVENANCE.json names the volume; FRAGMENTS.jsonl cites it for EO:90001."""
        book_sha = sha(self.BOOK_BYTES)
        rel = "releases/source_books/Test_Volume.pdf"
        pdf = self.repo / rel
        pdf.parent.mkdir(parents=True, exist_ok=True)
        if real:
            pdf.write_bytes(self.BOOK_BYTES)
        else:
            pdf.write_bytes(S.LFS_MAGIC + f"\noid sha256:{pointer_oid or book_sha}\nsize 77\n".encode())
        job = self.repo / "jobs/book-job"
        (job / "data").mkdir(parents=True, exist_ok=True)
        (job / "data/PROVENANCE.json").write_text(json.dumps({"volumes": [{
            "handle_url": "https://hdl.handle.net/2027/test.volume", "pdf": rel, "pdf_sha256": book_sha,
            "pdf_bytes": len(self.BOOK_BYTES)}]}), "utf-8")
        (job / "output/texts").mkdir(parents=True, exist_ok=True)
        (job / "output/texts/EO_90001.txt").write_text(self.BOOK_TEXT, "utf-8")
        page = "Test volume (GPO 1950), printed pages 3-3, PDF pages 9-9"
        with open(job / "output/FRAGMENTS.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"instrument_id": "EO:90001", "kind": "original_representation",
                                 "produced_by": "book-job", "data": {
                                     "url": "https://hdl.handle.net/2027/test.volume", "sha256": book_sha,
                                     "page_or_item": page, "needs_page_check": False,
                                     "text_path": "texts/EO_90001.txt"}}) + "\n")
        ctx = C.Context(self.repo, self.jobdir, pathlib.Path(self.tmp) / "cache2", today=C.dt.date(2026, 10, 17))
        claim = good_claim()
        book = {"url": "https://hdl.handle.net/2027/test.volume", "sha256": book_sha, "page_or_item": page}
        claim["original_representation"] = book
        claim["operative_clauses"][0]["original_source"] = book
        return claim, ctx

    def test_committed_volume_behind_an_lfs_pointer_is_held(self):
        claim, ctx = self.add_book()
        rows, _, _ = C.check_claim(claim, ctx)
        src = {r["field"]: (r["result"], r["status"]) for r in rows_for(rows, "source_held")}
        self.assertEqual(src["original_representation"], ("pass", "held_bytes_in_release_or_repo"))
        ident = {r["field"]: r["status"] for r in rows_for(rows, "source_identity")}
        self.assertEqual(ident["original_representation"], "recorded_for_this_order")
        q = {r["field"]: r["status"] for r in rows_for(rows, "quote_verbatim")}
        # the clause is found word for word in the job's per-order OCR text of that volume
        self.assertEqual(q["operative_clauses[0].original_operative_text"], "exact")
        self.assertTrue(any("book-job: 1 committed volume(s) and 1 per-order text(s)" in n for n in ctx.index.notes))

    def test_volume_pointer_to_other_bytes_is_not_held(self):
        claim, ctx = self.add_book(pointer_oid="7" * 64)
        rows, _, _ = C.check_claim(claim, ctx)
        src = {r["field"]: r["status"] for r in rows_for(rows, "source_held")}
        self.assertEqual(src["original_representation"], "not_held")
        self.assertTrue(any("is an LFS pointer to 777777777777" in n for n in ctx.index.notes))

    def test_volume_bytes_on_this_machine_are_rehashed(self):
        claim, ctx = self.add_book(real=True)
        rows, _, _ = C.check_claim(claim, ctx)
        src = {r["field"]: r["status"] for r in rows_for(rows, "source_held")}
        self.assertEqual(src["original_representation"], "held_bytes_verified")
        (self.repo / "releases/source_books/Test_Volume.pdf").write_bytes(b"other bytes")
        ctx = C.Context(self.repo, self.jobdir, pathlib.Path(self.tmp) / "cache3", today=C.dt.date(2026, 10, 17))
        rows, _, _ = C.check_claim(claim, ctx)
        src = {r["field"]: r["status"] for r in rows_for(rows, "source_held")}
        self.assertEqual(src["original_representation"], "held_record_but_local_bytes_differ")

    def test_volume_missing_from_the_checkout_is_not_held(self):
        claim, _ = self.add_book()
        (self.repo / "releases/source_books/Test_Volume.pdf").unlink()
        ctx = C.Context(self.repo, self.jobdir, pathlib.Path(self.tmp) / "cache4", today=C.dt.date(2026, 10, 17))
        rows, _, _ = C.check_claim(claim, ctx)
        src = {r["field"]: r["status"] for r in rows_for(rows, "source_held")}
        self.assertEqual(src["original_representation"], "not_held")
        self.assertTrue(any("is not in this checkout" in n for n in ctx.index.notes))


class ReplicaFragmentTests(unittest.TestCase):
    setUp = CheckerTests.setUp
    tearDown = CheckerTests.tearDown

    def replica(self):
        raw = self.repo / 'ProQuest Pre-1937 Orders/EO_90001.pdf'
        raw.parent.mkdir(parents=True)
        raw.write_bytes(b'%PDF-1.4 retained replica fixture bytes')
        directory = self.repo / 'jobs/pinakes-proquest-ingest/output'
        directory.mkdir(parents=True)
        (directory/'text.txt').write_text(ORIGINAL_TEXT)
        self.row = {'kind':'original_representation', 'produced_by':'pinakes-proquest-ingest',
                    'instrument_id':'EO:90001', 'data':{'acceptable_as_original':False,
                    'grade':'archival_replica_scan_pending_codebook', 'sha256':sha(raw.read_bytes()),
                    'file':str(raw.relative_to(self.repo)), 'text_path':'text.txt',
                    'url':'https://example.org/proquest/90001', 'page_or_item':'p1'}}
        self.fragment = directory/'FRAGMENTS.jsonl'
        self.fragment.write_text(json.dumps(self.row)+'\n')
        return raw

    def index_replica(self):
        index = S.HeldIndex(); S.load_replica_fragments(index, self.repo)
        return index.lookup_sha(self.row['data']['sha256'])

    def test_replica_bytes_are_indexed_without_original_authentication(self):
        self.replica()
        copies = self.index_replica()
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0].custody, 'repo_file')
        self.assertTrue(self.ctx.reader.verify_bytes(copies[0]))
        self.assertIn('unverified', copies[0].note)
        self.assertFalse(self.row['data']['acceptable_as_original'])

    def test_replica_missing_bytes_remain_record_only_and_wrong_hash_fails(self):
        raw = self.replica(); raw.unlink()
        copies = self.index_replica()
        self.assertEqual(copies[0].custody, 'record_only')
        raw.write_bytes(b'wrong bytes')
        copies = self.index_replica()
        self.assertFalse(self.ctx.reader.verify_bytes(copies[0]))

    def test_replica_path_escape_is_refused(self):
        self.replica(); self.row['data']['file'] = '../outside.pdf'
        self.fragment.write_text(json.dumps(self.row)+'\n')
        self.assertEqual(self.index_replica(), [])


if __name__ == "__main__":
    unittest.main()
