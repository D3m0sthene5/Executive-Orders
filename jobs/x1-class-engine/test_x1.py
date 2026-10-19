"""Offline tests: python -m unittest discover -s jobs/x1-class-engine -v"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classify, cluster, sheets, taxonomy as tx  # noqa: E402


def top(text, year=1925):
    h = tx.matches(text, year)
    return h[0][0] if h else "unknown"


class Taxonomy(unittest.TestCase):
    def test_wpa_summaries(self):
        cases = {
            "George W. Pitts made eligiblefor appointment as a clerk in the Treasury Dept. without regard to CivilService Rules.": "cs_waiver_individual",
            "Charles R. Torbert exempted from compulsory retire ment provisions.": "retirement_exemption",
            "Code of Fair Competition for the Ice Industry approved. I NRA Codes 529.": "nra_code_approval",
            "Public Water Reserve No. 151,Calif.,established.": "public_water_reserve",
            "Mourning formalitiesfor Admiral George Dewey ordered.": "closing_mourning",
            "Certain described lands in Wyoming withdrawn pending township resurvey.": "land_withdrawal_general",
            "Lighthouse tender Palmetto, with equipment and person nel,transferredfrom the Commerce Dept.": "property_transfer",
            "CivilService Rule V [pertainingto age limitations],Sec tion 4, amended. 1901 CSR 294.": "cs_rules_amendment",
        }
        for text, want in cases.items():
            self.assertEqual(top(text), want, text)

    def test_war_dept_is_not_wwi(self):
        self.assertNotEqual(top("Civil Service Rules, Schedule A, Subdivision IV [on War Dept. positions] amended", 1918), "wwi_emergency")

    def test_wwi_is_date_gated(self):
        self.assertEqual(top("War Trade Board authorized to disburse unexpended funds", 1919), "wwi_emergency")
        self.assertNotEqual(top("War Trade Board authorized to disburse unexpended funds", 1930), "wwi_emergency")

    def test_next_entry_is_cut(self):
        m = classify.NEXT_ENTRY.search("Board on Geographic Names established. 28-1:Jan. 30 * Mourning formalities", 10)
        self.assertIsNotNone(m)


class Decide(unittest.TestCase):
    def test_text_never_overrides_summary(self):
        hits = {"wpa": [("organization_agency", "p", "board")], "text": [("land_withdrawal_general", "p", "publicdomain")]}
        self.assertEqual(classify.decide(hits)[0], "organization_agency")

    def test_agreement_is_high(self):
        hits = {"wpa": [("cs_waiver_individual", "p", "x")], "text": [("cs_waiver_individual", "p", "y")]}
        self.assertEqual(classify.decide(hits)[2], "high")

    def test_nothing_is_unknown(self):
        self.assertEqual(classify.decide({"wpa": []})[:3], ("unknown", "unknown", "none"))


class Clone(unittest.TestCase):
    def doc(self, text):
        toks = [(m.group(0), m.start(), m.end()) for m in cluster.TOKEN.finditer(text)]
        return {"tokens": toks, "raw": text, "path": "t", "text_sha256": "h", "truncated": False, "spans_ok": True,
                "clauses": [{"scope_id": "EO:1#whole", "char_start": 0, "char_end": len(text), "tok_from": 0, "tok_to": len(toks)}]}

    def test_names_and_places_are_slots(self):
        a = self.doc("It is hereby ordered that the lands in Utah described below are withdrawn from settlement.")
        b = self.doc("It is hereby ordered that the lands in Nevada described below are withdrawn from settlement.")
        out, diffs, why = cluster.clone(a, b, None)
        self.assertEqual(why, "")
        self.assertEqual(len(out), 1)

    def test_operative_word_drops_out(self):
        a = self.doc("It is hereby ordered that the lands described below are withdrawn from settlement.")
        b = self.doc("It is hereby ordered that the lands described below are not withdrawn from settlement.")
        out, diffs, why = cluster.clone(a, b, None)
        self.assertTrue(why.startswith("non_slot_difference"))
        self.assertEqual(out, [])

    def test_clause_count_mismatch_drops_out(self):
        a = self.doc("It is hereby ordered that the lands are withdrawn.")
        b = self.doc("It is hereby ordered that the lands are withdrawn.")
        b["clauses"] = b["clauses"] * 2
        self.assertTrue(cluster.clone(a, b, None)[2].startswith("own_segmentation"))


class Review(unittest.TestCase):
    def test_risk_tiered_review_is_off_by_default(self):
        self.assertFalse(sheets.risk_tiered())
        self.assertEqual(sheets.review_tier({"clone_status": "cloned", "instrument_id": "EO:1"}), "full")


if __name__ == "__main__":
    unittest.main()
