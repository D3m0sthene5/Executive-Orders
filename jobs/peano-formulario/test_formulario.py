import csv
import gzip
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["FORMULARIO_TACTIC"] = "0"  # tests never search the web
import formulario as F  # noqa: E402


class Kernel(unittest.TestCase):
    def test_locate_tolerates_case_quotes_dashes_whitespace(self):
        text = "Sec. 2. Executive Order No. 7234 of\nNovember 25, 1935, is hereby “revoked” — in full."
        a, b, tier = F.locate('executive order no. 7234 of November 25, 1935, is hereby "revoked" - in full', text)
        self.assertEqual(tier, "spaced")
        self.assertTrue(text[a:b].startswith("Executive Order No. 7234"))

    def test_locate_alnum_tier_and_hyphenation(self):
        text = "the Bureau of Light-\nhouses is a bol ished"
        self.assertEqual(F.locate("the Bureau of Lighthouses is abolished", text)[2], "alnum")

    def test_locate_refuses_short_or_absent(self):
        self.assertIsNone(F.locate("revoked", "revoked"))
        self.assertIsNone(F.locate("is hereby revoked in its entirety", "is hereby amended in part"))

    def test_binding_requires_the_counterparty_number(self):
        self.assertTrue(F.names_number("Revoked by EO 7234 of Nov. 25, 1935", "EO:7234"))
        self.assertTrue(F.names_number("Executive O rder 7 6 7 7 -A", "EO:7677A"))
        self.assertTrue(F.names_number("see Pub. L. 95-495", "PL:95-495"))
        self.assertFalse(F.names_number("revokes EO 7235", "EO:7234"))
        self.assertFalse(F.names_number("revoked by regulations", "Department of X regulations"))

    def test_ofr_page_rendered_one_record_per_order(self):
        page = {"results": [{"executive_order_number": 7234, "citation": "", "signing_date": "1935-11-25",
                             "disposition_notes": "Revokes: EO 2040\nSee: EO 3761"},
                            {"executive_order_number": 7235, "disposition_notes": "Amends: EO 1"}]}
        text, err = F.text_of(json.dumps(page).encode())
        src = {"_text": text}
        a, b = F.record_span(src, "7234")
        self.assertIn("See: EO 3761", text[a:b])  # a multi-line note stays inside its record
        self.assertNotIn("7235", text[a:b])

    def test_html_text(self):
        text, _ = F.text_of(b"<html><script>x()</script><p>Sec. 1. Abolished.</p></html>")
        self.assertIn("Sec. 1. Abolished.", text)
        self.assertNotIn("x()", text)


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


class FakePool:
    def __init__(self, pages):
        self.pages, self.calls = pages, []

    def fetch(self, url):
        self.calls.append(url)
        if url not in self.pages:
            raise RuntimeError("HTTP 404")
        body = self.pages[url]
        return {"url": url, "body": body, "sha256": F.sha256(body), "bytes": len(body)}


class Build(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as out, \
                tempfile.TemporaryDirectory() as prior:
            # later-events: one order-text edge (proved from a retained text), one OFR note edge, one unbound edge
            os.makedirs(f"{root}/jobs/fr-originals/output/texts")
            with open(f"{root}/jobs/fr-originals/output/texts/EO_7234.txt", "w") as fh:
                fh.write("Executive Order No. 2040 of September 1, 1914, is hereby revoked.")
            with open(f"{root}/jobs/fr-originals/output/SOURCES.jsonl", "w") as fh:
                fh.write(json.dumps({"sha256": "aa" * 32, "text_path": "texts/EO_7234.txt"}) + "\n")
            api = "https://www.federalregister.gov/api/v1/documents.json?x=1"
            edge = lambda i, act, tgt, ev, q, url="", sha="": {  # noqa: E731
                "edge_id": i, "acting_id": act, "acting_label": "", "target_id": tgt, "target_label": "",
                "mechanism": "revocation", "qualifier": "", "date_candidate": "1935-11-25", "date_basis": "",
                "date_flags": "", "evidence_type": ev, "stated_on": act, "source_url": url, "source_sha256": sha,
                "page_or_item": "", "quote": q}
            write_csv(f"{root}/{F.LATER_EDGES}", [
                edge("LE-1", "EO:7234", "EO:2040", "order_text_fr_originals",
                     "Executive Order No. 2040 of September 1, 1914, is hereby revoked", "u", "aa" * 32),
                edge("LE-2", "EO:7234", "EO:3761", "ofr_note_on_acting", "See: EO 3761", api),
                edge("LE-3", "EO:7234", "EO:9999", "ofr_note_on_acting", "Revokes: EO 2040", api)])
            page = json.dumps({"results": [{"executive_order_number": 7234, "disposition_notes": "Revokes: EO 2040\nSee: EO 3761"}]}).encode()
            proc = b"%PDF-"  # unreadable PDF: kernel must leave the axiom sorry
            pool = FakePool({api: page, "https://www.govinfo.gov/proc.pdf": proc,
                             "https://www.govinfo.gov/a.html": b"<html><p>All Executive orders under Title I shall cease to be in effect.</p></html>"})
            here = F.HERE
            try:
                F.HERE = root
                os.makedirs(f"{root}/axioms")
                with open(f"{root}/axioms/t.jsonl", "w") as fh:
                    fh.write("# comment\n")
                    fh.write(json.dumps({"axiom_id": "A1", "instrument": "Act X", "instrument_kind": "statute", "date": "1935-06-14",
                                         "url": "https://www.govinfo.gov/a.html", "quote": "All Executive orders under Title I shall cease to be in effect",
                                         "relation": "terminates", "targets_named": [], "class_scope": "orders under Title I",
                                         "census_families_hint": ["PD-CLASS-EVENTS"]}) + "\n")
                    fh.write(json.dumps({"axiom_id": "A2", "instrument": "Proc Y", "instrument_kind": "proclamation", "date": "1946",
                                         "url": "https://www.govinfo.gov/proc.pdf", "quote": "hostilities have terminated in full",
                                         "relation": "other", "targets_named": ["EO 9066"], "class_scope": ""}) + "\n")
                write_csv(f"{root}/{F.TYPES}", [{"instrument_id": "EO:6000", "type": "nra_code_approval"}])
                os.makedirs(f"{root}/research/pothier/doctrines")
                with open(f"{root}/research/pothier/doctrines/PD-CLASS-EVENTS.json", "w") as fh:
                    json.dump({"doctrine_id": "PD-CLASS-EVENTS", "members": {"field": "x1_type", "in": ["nra_code_approval"]}}, fh)
                idx = F.build(root, out, prior, pool, {"fetches": 10, "bytes": 10 ** 7})
            finally:
                F.HERE = here
            self.assertEqual(idx["lemmas"], 5)
            self.assertEqual(idx["class_lemmas"], {"proved": 1, "sorry": 0})
            by = {}
            for path in os.listdir(f"{out}/lemmas"):
                with gzip.open(f"{out}/lemmas/{path}", "rt") as fh:
                    for line in fh:
                        lm = json.loads(line)
                        by[lm["origin"].get("edge_id") or lm["origin"].get("axiom_id")] = lm
            self.assertEqual(by["LE-1"]["status"], "proved")
            self.assertEqual(by["LE-2"]["status"], "proved")
            self.assertEqual(by["LE-2"]["proof"]["binding"]["counterparty_named"], "EO:3761")
            self.assertEqual(by["LE-3"]["status"], "sorry")  # quote names 2040, not the counterparty 9999
            self.assertEqual(by["A1"]["status"], "proved")
            self.assertEqual(by["A2"]["status"], "sorry")
            self.assertEqual(pool.calls.count(api), 1)  # one retained copy, fetched once
            r = F.exact("EO:2040", "end", out)
            self.assertEqual([lm["origin"]["edge_id"] for lm in r["instances"]], ["LE-1"])
            r = F.exact("EO:6000", "end", out)
            self.assertEqual([lm["origin"]["axiom_id"] for lm in r["class_candidates"]], ["A1"])
            sup = F.supplement([by["LE-1"]["lemma_id"], by["A2"]["lemma_id"]], out)
            self.assertEqual(len(sup["entries"]), 1)
            e = sup["entries"][0]
            with open(f"{root}/{e['source']['text_path']}") as fh:
                text = fh.read()
            self.assertEqual(text[e["char_start"]:e["char_end"]], "Executive Order No. 2040 of September 1, 1914, is hereby revoked")
            with open(f"{out}/SOURCES.jsonl") as fh:
                srcs = [json.loads(l) for l in fh]
            self.assertEqual(len(srcs), 2)  # the unreadable PDF proves nothing and is not kept
            for s in srcs:
                with open(os.path.join(out, s["cache_path"]), "rb") as fh:
                    self.assertEqual(F.sha256(fh.read()), s["sha256"])

    def test_carry_forward_without_refetch(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            url = "https://www.govinfo.gov/a.html"
            pool = FakePool({url: b"<p>All orders under Title I shall cease to be in effect today.</p>"})
            lib = F.Library(F.Repo(root), a, None, pool)
            lib.retain(url, {"fetches": 1, "bytes": 10 ** 6})
            lib.add({"lemma_id": "F-x", "kind": "class", "statement": {"objects": [], "relation": "terminates",
                     "families": [], "subject": "s", "class_scope": "c"}, "status": "proved", "sorry_reason": "",
                     "proof": {"source": {"url": url}}, "origin": {"from": "axioms/t"}})
            F.write(lib, F.Repo(root), a, {})
            lib2 = F.Library(F.Repo(root), b, a, FakePool({}))
            rec = lib2.retain(url, {"fetches": 0, "bytes": 0})
            self.assertTrue(rec["retrieved_from_prior"])


if __name__ == "__main__":
    unittest.main()
