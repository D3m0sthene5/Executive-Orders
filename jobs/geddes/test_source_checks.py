"""Source-bound checks: identity, boundary, quote and integrity controls."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_checks


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class SourceChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.own = ("Executive Order 12345\nCreating an Emergency Board\n"
                    "Whereas, a hearing was held by the Board.\n"
                    "The Board shall report within thirty days.\n"
                    "FRANKLIN D. ROOSEVELT\nThe White House,\nOctober 16, 1934.\n")
        self.neighbor = ("Executive Order 12346\nAnother Order\n"
                         "A standstill is ordered; status quo shall remain.\n"
                         "FRANKLIN D. ROOSEVELT\nThe White House,\nOctober 17, 1934.\n")
        self.full = self.own + self.neighbor
        (self.repo / "held.txt").write_text(self.full)
        source = {"text_path": "held.txt", "text_sha256": sha(self.full), "instrument_id": "EO:12345"}
        a = self.own.index("Whereas")
        b = self.own.index("FRANKLIN")
        parent = {"id": "ORIGINAL:EO:12345", "source": source, "text": self.full,
                  "char_start": 0, "char_end": len(self.full)}
        clause = {"id": "CLAUSES:EO:12345#whole", "scope_id": "EO:12345#whole", "source": source,
                  "text": self.full[a:b], "char_start": a, "char_end": b}
        self.dossier = {"instrument_id": "EO:12345", "original_source_id": parent["id"],
                        "evidence": {parent["id"]: parent}, "clauses": [clause]}
        self.claim = {"instrument_id": "EO:12345", "research_rationale": "",
                      "operative_clauses": [{"judgment_reason": "", "later_events": []}]}

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, claim=None, dossier=None, cache=None):
        return source_checks.check(claim or self.claim, dossier or self.dossier, self.repo, cache=cache)

    def test_recital_inside_own_body_and_neighbor_excluded(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "This order's recitals describe hearings."
        claim["operative_clauses"][0]["judgment_reason"] = "The order's standstill sentence is spent."
        row = self.check(claim)
        self.assertEqual([f["concept"] for f in row["flags"]], ["standstill"])
        self.assertEqual(row["flags"][0]["source"]["boundary"], "numbered")

    def test_claimed_status_quo_and_nonderogation_absent(self):
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0]["judgment_reason"] = "The status-quo sentence and non-derogation sentence are both parts of this order."
        self.assertEqual({f["concept"] for f in self.check(claim)["flags"]}, {"status_quo", "non_derogation"})

    def test_concept_tolerates_soft_hyphen_and_line_break(self):
        text = self.own.replace("The Board shall report", "No change shall be made in the conditions.\nThe Board shall re\u00ad\nport")
        (self.repo / "held.txt").write_text(text)
        dossier = copy.deepcopy(self.dossier)
        dossier["evidence"]["ORIGINAL:EO:12345"].update(text=text, char_end=len(text))
        dossier["evidence"]["ORIGINAL:EO:12345"]["source"]["text_sha256"] = sha(text)
        start = text.index("Whereas"); end = text.index("FRANKLIN")
        dossier["clauses"][0].update(text=text[start:end], char_start=start, char_end=end)
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0]["judgment_reason"] = "The standstill is spent; the Board shall report."
        self.assertEqual(self.check(claim, dossier)["flags"], [])

    def test_quote_verbatim_case_and_not_legal_paraphrase(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "The order sets a report date ('The board shall report within thirty days')."
        self.assertIn("attributed_quote_not_verbatim", {x["code"] for x in self.check(claim)["flags"]})
        claim["research_rationale"] = "The order sets a report date ('The Board shall report within thirty days')."
        self.assertEqual(self.check(claim)["flags"], [])
        claim["research_rationale"] = "The statute's phrase 'a report within thirty days' is relevant."
        self.assertEqual(self.check(claim)["flags"], [])

    def test_verified_override_replaces_contaminated_dossier_inventory(self):
        dossier = copy.deepcopy(self.dossier)
        neighbor_start = self.full.index("A standstill")
        dossier["clauses"].append({"id": "CLAUSES:EO:12345#bad", "scope_id": "EO:12345#bad",
             "source": dossier["clauses"][0]["source"], "text": self.full[neighbor_start:neighbor_start+24],
             "char_start": neighbor_start, "char_end": neighbor_start+24})
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0]["judgment_reason"] = "The order's standstill sentence has ended."
        self.assertEqual(self.check(claim, dossier)["flags"], [])
        self.assertIn("own_order_body_unverified", {x["code"] for x in self.check(claim, dossier)["coverage_gaps"]})
        claim["claim_kit"] = {"inventory_overrides": [{"scope_id": "EO:12345#whole", "source_id": "ORIGINAL:EO:12345",
             "char_start": 0, "char_end": self.own.index("FRANKLIN"), "reason": "Corrected whole printed order"}]}
        self.assertEqual([f["concept"] for f in self.check(claim, dossier)["flags"]], ["standstill"])

    def test_changed_bytes_with_restored_stat_fail_closed(self):
        cache = {}
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0]["judgment_reason"] = "The order's standstill sentence has ended."
        self.assertEqual(len(self.check(claim, cache=cache)["flags"]), 1)
        p = self.repo / "held.txt"; st = p.stat()
        p.write_text("X" + self.full[1:]); os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
        row = self.check(claim, cache=cache)
        self.assertEqual(row["flags"], [])
        self.assertEqual(row["coverage_gaps"][0]["reason"], "source_hash_mismatch")

    def test_app_item_requires_publisher_identity_and_spans(self):
        item = ("An application was made after a hearing.\n"
                "Executive Order 12344 is mentioned in this recital.\n"
                "I hereby establish the Board, which shall report.\n"
                "FRANKLIN D. ROOSEVELT\nThe White House,\nOctober 16, 1934.\n")
        (self.repo / "held.txt").write_text(item)
        dossier = copy.deepcopy(self.dossier)
        parent = dossier["evidence"]["ORIGINAL:EO:12345"]
        parent.update(text=item, char_end=len(item))
        parent["source"].update(text_sha256=sha(item), archival_id="app:node/123",
            page_or_item="Executive Order 12345—Creating a Board; October 16, 1934",
            url="https://www.presidency.ucsb.edu/documents/executive-order-1234-creating-board")
        dossier["clauses"] = [{"id": "CLAUSES:EO:12345#whole", "scope_id": "EO:12345#whole",
            "source": parent["source"], "text": item, "char_start": 0, "char_end": len(item)}]
        index = self.repo / "jobs/app-executive-orders/output/INDEX.jsonl"
        index.parent.mkdir(parents=True)
        index.write_text(json.dumps({"instrument_id": "EO:12345", "title": "Executive Order 12345—Creating a Board",
            "date": "1934-10-16", "url": parent["source"]["url"]}) + "\n")
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "This order's recitals describe a hearing."
        claim["operative_clauses"][0]["judgment_reason"] = "The status-quo sentence is spent."
        self.assertEqual([f["concept"] for f in self.check(claim, dossier)["flags"]], ["status_quo"])
        parent["source"]["url"] = "https://www.presidency.ucsb.edu/documents/executive-order-12346-creating-board"
        self.assertEqual(self.check(claim, dossier)["flags"], [])
        self.assertEqual(self.check(claim, dossier)["coverage_gaps"][0]["reason"], "order_heading_unresolved")
        parent["source"]["url"] = "https://www.presidency.ucsb.edu/documents/executive-order-1234-creating-board"
        index.write_text(json.dumps({"instrument_id": "EO:99999", "title": "Executive Order 12345—Creating a Board",
            "date": "1934-10-16", "url": parent["source"]["url"]}) + "\n")
        self.assertEqual(self.check(claim, dossier)["flags"], [])
        self.assertEqual(self.check(claim, dossier)["coverage_gaps"][0]["reason"], "order_heading_unresolved")

    def test_app_abbreviated_signature_date_and_appended_material(self):
        item = ("Whereas, a hearing was held.\nI hereby create the Board.\n"
                "FRANKLIN D. ROOSEVELT\nThe White House,\nOct. 16, 1934.\n")
        p = self.repo / "held.txt"; p.write_text(item)
        dossier = copy.deepcopy(self.dossier)
        parent = dossier["evidence"]["ORIGINAL:EO:12345"]
        parent.update(text=item, char_end=len(item))
        parent["source"].update(text_sha256=sha(item), archival_id="app:node/123",
            page_or_item="Executive Order 12345—Creating a Board; October 16, 1934",
            url="https://www.presidency.ucsb.edu/documents/executive-order-1234-creating-board")
        dossier["clauses"] = [{"id": "CLAUSES:EO:12345#whole", "scope_id": "EO:12345#whole",
            "source": parent["source"], "text": item, "char_start": 0, "char_end": len(item)}]
        index = self.repo / "jobs/app-executive-orders/output/INDEX.jsonl"
        index.parent.mkdir(parents=True)
        index.write_text(json.dumps({"instrument_id": "EO:12345", "title": "Executive Order 12345—Creating a Board",
            "date": "1934-10-16", "url": parent["source"]["url"]}) + "\n")
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0]["judgment_reason"] = "This order contains a status-quo sentence."
        self.assertEqual([f["concept"] for f in self.check(claim, dossier)["flags"]], ["status_quo"])
        appended = item + "Committee report dated October 15, 1934.\n"
        p.write_text(appended)
        parent.update(text=appended, char_end=len(appended))
        parent["source"]["text_sha256"] = sha(appended)
        dossier["clauses"][0].update(text=appended, char_end=len(appended))
        self.assertEqual(self.check(claim, dossier)["flags"], [])
        self.assertEqual(self.check(claim, dossier)["coverage_gaps"][0]["reason"], "order_heading_unresolved")

    def test_later_event_quote_is_verbatim_in_its_own_source_span(self):
        later = "Executive Order 12347. The Board shall report to the President."
        (self.repo / "later.txt").write_text(later)
        event_source = {"text_path": "later.txt", "text_sha256": sha(later),
                        "char_start": 23, "char_end": len(later),
                        "quote": "The Board shall report to the President."}
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0]["later_events"] = [{"source": event_source}]
        self.assertEqual(self.check(claim)["flags"], [])
        event_source["quote"] = "The board shall report to the President."
        flags = self.check(claim)["flags"]
        self.assertEqual([f["code"] for f in flags], ["later_event_quote_not_in_cited_source"])
        self.assertEqual(flags[0]["source"]["text_path"], "later.txt")
        (self.repo / "later.txt").write_text(later.replace("Board", "board"))
        row = self.check(claim)
        self.assertEqual(row["flags"], [])
        self.assertIn("cited_quote_source_unverified", {x["code"] for x in row["coverage_gaps"]})

    def test_original_operative_quote_and_first_end_actor_have_separate_sources(self):
        own_quote = "The Board shall report within thirty days."
        own_start = self.full.index(own_quote)
        actor = "Executive Order 12347. The board is dissolved."
        (self.repo / "later.txt").write_text(actor)
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0].update({
            "original_operative_text": own_quote,
            "original_source": {"text_path": "held.txt", "text_sha256": sha(self.full),
                "char_start": own_start, "char_end": own_start+len(own_quote), "quote": own_quote},
            "first_end": {"source": {"text_path": "later.txt", "text_sha256": sha(actor),
                "char_start": 0, "char_end": len(actor), "quote": "The board is dissolved."}}})
        self.assertEqual(self.check(claim)["flags"], [])
        claim["operative_clauses"][0]["original_operative_text"] = own_quote.lower()
        claim["operative_clauses"][0]["first_end"]["source"]["quote"] = "The Board is dissolved."
        self.assertEqual({f["code"] for f in self.check(claim)["flags"]},
                         {"quotation_not_verbatim", "first_end_quote_not_in_cited_source"})
        (self.repo / "later.txt").write_text(actor.replace("dissolved", "replaced "))
        row = self.check(claim)
        self.assertNotIn("first_end_quote_not_in_cited_source", {f["code"] for f in row["flags"]})
        self.assertIn("cited_quote_source_unverified", {x["code"] for x in row["coverage_gaps"]})


if __name__ == "__main__":
    unittest.main()
