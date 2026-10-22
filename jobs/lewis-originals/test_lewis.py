"""Offline tests for Lewis with a synthetic repository. No network, no real repo data."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
import eo_identity as ident  # noqa: E402
import lewis  # noqa: E402

MINIMAL_PDF = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
               b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\nxref\n0 4\n0000000000 65535 f \n"
               b"0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\n"
               b"startxref\n160\n%%EOF\n")


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def census_row(iid, year):
    return {"id": iid, "bibliographic_class": "validated_numbered", "included_in_bibliography": "1",
            "date_effective": str(year), "year_group": "1907–1936" if year < 1937 else "1937–1989"}


def readiness_row(iid, blockers, step="open", basis=""):
    return {"instrument_id": iid, "provisional_status": "", "blockers": blockers, "step_original_text": step,
            "original_text_basis": basis}


def fragment(iid, produced_by, date="", title="", text_path=None):
    return {"instrument_id": iid, "kind": "original_representation", "produced_by": produced_by,
            "acceptable_as_original": False, "grade": "mirror_transcription",
            "sources": [{"url": f"https://example.org/{iid}", "sha256": "0" * 64, "page_or_item": "p"}],
            "data": {"app_date": date, "title": title, "text_path": text_path, "sha256": "0" * 64,
                     "url": f"https://example.org/{iid}", "needs_page_check": True, "acceptable_as_original": False}}


class SyntheticRepo(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="lewis-")
        self.out = os.path.join(self.root, "_out")
        r = self.root
        write_csv(os.path.join(r, ident.UNIVERSE), [
            census_row("EO:4", 1865), census_row("EO:7", 1868), census_row("EO:2000", 1914), census_row("EO:5100", 1929),
            census_row("EO:6000", 1932), census_row("EO:7400", 1936), census_row("EO:7543", 1937), census_row("EO:7600", 1937),
            census_row("EO:9000", 1942), census_row("EO:9100", 1942)])
        write_csv(os.path.join(r, ident.READINESS), [
            readiness_row("EO:4", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND"),
            readiness_row("EO:7", "NO_OFFICIAL_SOURCE_LOCATED"),  # no transcription lead: Clark's, not Lewis's
            readiness_row("EO:2000", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND"),
            readiness_row("EO:5100", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND"),
            readiness_row("EO:6000", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND"),
            readiness_row("EO:7400", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND"),
            readiness_row("EO:7543", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND"),
            readiness_row("EO:7600", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND"),
            readiness_row("EO:9000", "", step="done"),
            # text step met provisionally by a labeled transcription (owner ruling 2026-10-21): still Lewis's
            readiness_row("EO:9100", "", step="done", basis="transcription_provisional:mirror_transcription"),
            readiness_row("EO:UN:executive-orders-01:row:1", "NO_OFFICIAL_SOURCE_LOCATED|ONLY_COMPILED_TRANSCRIPTION_FOUND")])
        write_jsonl(os.path.join(r, "jobs/app-executive-orders/output/FRAGMENTS.jsonl"), [
            fragment("EO:4", "app-executive-orders", "1865-03-01", "Order four"),
            fragment("EO:2000", "app-executive-orders", "1914-07-28", "Amending the Civil Service Rules"),
            fragment("EO:5100", "app-executive-orders", "1929-04-01", "Hoover era"),
            fragment("EO:6000", "app-executive-orders", "1932-02-01", "GPO volume era"),
            fragment("EO:7400", "app-executive-orders", "1936-06-01", "After the first FR issue"),
            fragment("EO:7543", "app-executive-orders", "1937-01-29", "In the OFR catalog"),
            fragment("EO:7600", "app-executive-orders", "1937-03-01", "Catalog row without citation")])
        write_csv(os.path.join(r, ident.OFR_CATALOG), [
            {"id": "EO:7543", "signing_date": "1937-01-29", "citation": "2 FR 263", "title": "In the OFR catalog",
             "pdf_url": "", "html_url": "https://www.federalregister.gov/x", "raw_text_url": "", "disposition_notes": ""},
            {"id": "EO:7600", "signing_date": "1937-03-01", "citation": "", "title": "No cite",
             "pdf_url": "", "html_url": "https://www.federalregister.gov/y", "raw_text_url": "", "disposition_notes": ""}])
        rows = [{"id": "EO:4", "n": "4", "y": 1865, "pdf": "https://congressional.proquest.com/p4", "rec": "https://congressional.proquest.com/r4"},
                {"id": "EO:7", "n": "7", "y": 1868, "pdf": "https://congressional.proquest.com/p7", "rec": "https://congressional.proquest.com/r7"},
                {"id": "EO:2000", "n": "2000", "y": 1914, "pdf": "https://congressional.proquest.com/p2000", "rec": "https://congressional.proquest.com/r2000"}]
        os.makedirs(os.path.join(r, ident.PROQUEST_DIR, "_resume"))
        with open(os.path.join(r, ident.PROQUEST_LINKS), "w", encoding="utf-8") as fh:
            fh.write("<html><script>const ROWS=" + json.dumps(rows) + ";</script></html>")
        pq = os.path.join(r, ident.PROQUEST_DIR)
        for name in ("PT1-1865-EO-4.pdf", "PT1-1865-EO-4 (1).pdf"):
            with open(os.path.join(pq, name), "wb") as fh:
                fh.write(MINIMAL_PDF)
        with open(os.path.join(pq, "PT1-1868-EO-7.pdf"), "wb") as fh:
            fh.write(MINIMAL_PDF + b"\n% different bytes\n")
        with open(os.path.join(pq, "not-a-pdf.pdf"), "wb") as fh:
            fh.write(b"<html>Access is denied</html>")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_job(self):
        return lewis.run(self.root, self.out)

    def read_routes(self):
        with open(os.path.join(self.out, "ROUTES.csv"), encoding="utf-8", newline="") as fh:
            return {r["instrument_id"]: r for r in csv.DictReader(fh)}

    def test_scope_is_transcription_only_plus_handoff(self):
        s = self.run_job()
        routes = self.read_routes()
        self.assertEqual(set(routes), {"EO:4", "EO:2000", "EO:5100", "EO:6000", "EO:7400", "EO:7543", "EO:7600", "EO:9100"})
        self.assertEqual(routes["EO:9100"]["best_route"], "federal_register", "provisional transcription basis: still hunted")
        self.assertNotIn("EO:7", routes, "no transcription lead: Clark's order, not Lewis's")
        self.assertNotIn("EO:9000", routes, "original already saved")
        self.assertTrue(any("no order number" in p for p in s["problems"]), "unnumbered id reported, not routed")

    def test_ladder_picks_one_route_per_order(self):
        self.run_job()
        r = self.read_routes()
        self.assertEqual((r["EO:4"]["best_route"], r["EO:4"]["route_status"]), ("proquest_local", "file_verified_pages_unchecked"))
        self.assertEqual(r["EO:4"]["proquest_file"], "PT1-1865-EO-4.pdf")
        self.assertEqual((r["EO:2000"]["best_route"], r["EO:2000"]["route_status"]), ("proquest_supplied_link", "awaiting_acquisition"))
        self.assertEqual(r["EO:2000"]["lead_url_or_search"], "https://congressional.proquest.com/r2000")
        self.assertEqual((r["EO:7543"]["best_route"], r["EO:7543"]["route_status"]), ("federal_register", "fetch_request_proposed"))
        self.assertEqual((r["EO:7600"]["best_route"], r["EO:7600"]["route_status"]), ("federal_register", "in_ofr_catalog_no_citation"))
        self.assertEqual((r["EO:7400"]["best_route"], r["EO:7400"]["route_status"]), ("federal_register", "fr_era_not_in_ofr_catalog"))
        self.assertEqual(r["EO:5100"]["best_route"], "ofr_hoover_compilation")
        self.assertEqual(r["EO:6000"]["best_route"], "gpo_bound_volumes")
        self.assertTrue(r["EO:6000"]["lead_url_or_search"].startswith("ProQuest Congressional"))

    def test_proquest_inventory_verifies_bytes_and_marks_duplicates(self):
        s = self.run_job()
        with open(os.path.join(self.out, "PROQUEST_INVENTORY.csv"), encoding="utf-8", newline="") as fh:
            inv = {r["file"]: r for r in csv.DictReader(fh)}
        self.assertEqual(inv["PT1-1865-EO-4.pdf"]["pdf_signature"], "yes")
        self.assertEqual(inv["PT1-1865-EO-4 (1).pdf"]["duplicate_of"], "PT1-1865-EO-4.pdf")
        self.assertEqual(inv["PT1-1865-EO-4 (1).pdf"]["sha256"], inv["PT1-1865-EO-4.pdf"]["sha256"])
        self.assertEqual(inv["not-a-pdf.pdf"]["pdf_signature"], "no")
        self.assertEqual(inv["not-a-pdf.pdf"]["name_parsed"], "no")
        self.assertEqual(s["proquest_folder"]["orders_with_verified_pdf"], 2)
        self.assertEqual(s["proquest_folder"]["pdfs_for_orders_outside_lewis_scope"], 1, "EO 7 has a PDF but no transcription lead")
        self.assertEqual(s["proquest_folder"]["bad_signature"], 1)

    def test_fragments_never_claim_an_original(self):
        self.run_job()
        frags = ident.read_jsonl(os.path.join(self.out, "FRAGMENTS.jsonl"))
        self.assertEqual({f["instrument_id"] for f in frags}, {"EO:4", "EO:7"})
        for f in frags:
            self.assertIs(f["acceptable_as_original"], False)
            self.assertIs(f["data"]["needs_page_check"], True)
            self.assertIs(f["data"]["location_verified"], False)
            self.assertEqual(len(f["data"]["sha256"]), 64)
            self.assertEqual(f["produced_by"], "lewis-originals")

    def test_fetch_requests_pass_the_source_ladder_contract(self):
        s = self.run_job()
        reqs = ident.read_jsonl(os.path.join(self.out, "PROPOSED_FETCH_REQUESTS.jsonl"))
        self.assertEqual([r["instrument_id"] for r in reqs], ["EO:7543"])
        self.assertEqual(reqs[0]["citation"], "2 FR 263")
        self.assertEqual(reqs[0]["step"], "original_text")
        self.assertEqual(reqs[0]["requested_by"], "lewis-originals")
        if lewis.request_contract is not None:
            self.assertEqual(reqs[0]["_contract_errors"], [])
            self.assertEqual(s["proposed_fetch_requests"]["contract_valid"], 1)

    def test_clark_handoff_enters_scope_without_entering_the_census(self):
        write_jsonl(os.path.join(self.root, lewis.CLARK_HANDOFF), [
            {"instrument_id": "EO:7", "clark_class": "identity_unknown", "identity_evidence": "proquest_link_year_1868"},
            {"instrument_id": "EO:5862", "clark_class": "number_gap", "identity_evidence": "app_index:1932-06-23"},
            {"instrument_id": "EO:92", "clark_class": "number_gap", "identity_evidence": "cited_with_date:1896-11-02"},
            {"instrument_id": "EO:9000", "clark_class": "number_gap"},  # already done: ignored
            {"instrument_id": "EO:UN:x", "clark_class": "x"}])  # unparsable: ignored
        self.run_job()
        r = self.read_routes()
        self.assertEqual(r["EO:7"]["scope_reason"], "clark_identified")
        self.assertEqual(r["EO:7"]["best_route"], "proquest_local")
        self.assertEqual(r["EO:5862"]["scope_reason"], "clark_identified_not_in_universe")
        self.assertEqual(r["EO:5862"]["best_route"], "gpo_bound_volumes", "the GPO volumes cover 5800-8027")
        self.assertEqual(r["EO:92"]["scope_reason"], "clark_identified_not_in_universe")
        self.assertEqual(r["EO:92"]["best_route"], "proquest_phrase_search")
        self.assertNotIn("EO:9000", r)
        self.assertNotIn("EO:UN:x", r)

    def test_text_quality_screens_handwriting_noise(self):
        self.assertLess(lewis.text_quality("/ (. / 7-,t1- * Ie '(cW(J 7UJ 4/4 . r!r.f"), 0.2)
        self.assertGreater(lewis.text_quality("By virtue of the authority vested in me it is hereby ordered that the lands be reserved."), 0.8)
        self.assertEqual(lewis.text_quality(""), 0.0)

    def test_outputs_are_deterministic(self):
        self.run_job()
        first = {}
        for name in ("ROUTES.csv", "PROQUEST_INVENTORY.csv", "FRAGMENTS.jsonl", "PROPOSED_FETCH_REQUESTS.jsonl"):
            with open(os.path.join(self.out, name), "rb") as fh:
                first[name] = fh.read()
        shutil.rmtree(self.out)
        self.run_job()
        for name, data in first.items():
            with open(os.path.join(self.out, name), "rb") as fh:
                self.assertEqual(fh.read(), data, name)

    def test_missing_inputs_are_reported_not_fatal(self):
        os.remove(os.path.join(self.root, ident.READINESS))
        shutil.rmtree(os.path.join(self.root, ident.PROQUEST_DIR))
        s = self.run_job()
        self.assertEqual(s["scope"]["orders"], 0)
        self.assertTrue(any("readiness" in p for p in s["problems"]))
        self.assertEqual(s["proquest_folder"]["pdf_files"], 0)


if __name__ == "__main__":
    unittest.main()


class OnlineStage(SyntheticRepo):
    """The web stage runs after the offline routing, with an injected transport (no network)."""

    def test_online_stage_hunts_manual_leads_first_and_writes_campaign_files(self):
        sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_lib"))
        import online
        import test_eo_websearch as tw
        self.run_job()
        web = tw.FakeWeb()
        engines = [{"name": "fake_html", "kind": "html", "url": "https://engine.test/search?q={q}"}]
        import eo_websearch as w
        url = w.build_url(engines[0], '"Executive Order No. 6000"', 1932)
        web.pages[url] = (200, "text/html", b'<a href="https://docs.test/6000">Executive Order 6000 of February 1, 1932</a>')
        web.pages["https://docs.test/6000"] = (200, "text/html", b"<p>Executive Order No. 6000, February 1, 1932. It is hereby ordered. See Executive Order 5999.</p>")
        env = {"JOB_MAX_REQUESTS": "40", "JOB_MAX_TARGETS": "3", "JOB_CACHE_DIR": os.path.join(self.root, "cache")}
        s = online.run(self.root, self.out, transport=web, env=env, engines=engines)
        self.assertEqual(s["advanced_this_run"], 3)
        with open(os.path.join(self.out, "WEB_STATE.json"), encoding="utf-8") as fh:
            st = json.load(fh)["targets"]
        self.assertIn("EO:6000", st, "gpo_bound_volumes (priority 1) goes before federal_register routes")
        self.assertIn("EO:5100", st)
        self.assertNotIn("EO:7543", st, "a fetch-request route waits its turn")
        self.assertGreaterEqual(st["EO:6000"]["best_score"], 60)
        leads = ident.read_csv(os.path.join(self.out, "WEB_LEADS.csv"))
        self.assertEqual([r["instrument_id"] for r in leads], ["EO:6000"])
        self.assertIn("5999", open(os.path.join(self.out, "WEB_NUMBERS_NAMED.csv"), encoding="utf-8").read())
        self.assertIn("## Web search", open(os.path.join(self.out, "REPORT.md"), encoding="utf-8").read())
