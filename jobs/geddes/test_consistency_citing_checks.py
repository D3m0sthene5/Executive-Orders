"""Synthetic fixtures for the consistency and citing checks."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import citing_checks as CIT
import consistency_checks as CON
import name_checks as N


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


OWN = ("Executive Order 12345\nAmending Executive Order No. 9000\n"
       "By virtue of the authority vested in me by section 6386(c) of title 10 of the United States Code, "
       "paragraph 3 of Executive Order No. 9000 is hereby amended for one employee.\n"
       "This reservation shall be known £ts the Alpha Lake Migratory Waterfowl Refuge.\n"
       "The Board shall investigate certain labor disputes between the railroads and their employees.\n"
       "FRANKLIN D. ROOSEVELT\nThe White House,\nMarch 8, 1939.\n")
LIST = ("Executive Order 12553\nRevocation of Various Executive Orders\n"
        "The following Executive Orders are revoked:\n"
        "12345 Creating a board to investigate labor disputes affecting the railroads\n"
        "12346 Creating an emergency board to investigate an airline labor dispute\n"
        "RONALD REAGAN\nThe White House,\nFebruary 25, 1986.\n")


def dossier_and_claim(repo):
    (repo / "own.txt").write_text(OWN)
    (repo / "list.txt").write_text(LIST)
    own_src = {"text_path": "own.txt", "text_sha256": sha(OWN), "instrument_id": "EO:12345", "signing_date": "1939-03-08"}
    list_src = {"text_path": "list.txt", "text_sha256": sha(LIST), "instrument_id": "EO:12553"}
    a, b = OWN.index("By virtue"), OWN.index("FRANKLIN")
    parent = {"id": "ORIGINAL:EO:12345", "source": own_src, "text": OWN, "char_start": 0, "char_end": len(OWN)}
    clause = {"id": "CLAUSES:EO:12345#whole", "scope_id": "EO:12345#whole", "source": own_src,
              "text": OWN[a:b], "char_start": a, "char_end": b}
    actor = {"actor_id": "EO:12553", "target_id": "EO:12345", "source": list_src}
    dossier = {"instrument_id": "EO:12345", "signing_date": "1939-03-08", "original_source_id": parent["id"],
               "evidence": {parent["id"]: parent, "ACT:EO:12345>EO:12553": actor}, "clauses": [clause]}
    end = {"actor": "EO:12553", "date": "1986-02-25", "mechanism": "express_revocation",
           "source": {"evidence_id": "ACT:EO:12345>EO:12553", "text_path": "list.txt", "text_sha256": sha(LIST)}}
    claim = {"instrument_id": "EO:12345", "whole_order_status": "no", "whole_order_end": copy.deepcopy(end),
             "research_rationale": "", "later_source_search": [],
             "operative_clauses": [{"scope_id": "EO:12345#whole", "judgment_reason": "", "first_end": copy.deepcopy(end), "later_events": []}]}
    return dossier, claim


class Consistency(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.dossier, self.claim = dossier_and_claim(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def codes(self, claim):
        return [f["code"] for f in CON.check(claim, self.dossier, self.repo)["flags"]]

    def test_end_bound_must_cover_claimed_end(self):
        claim = copy.deepcopy(self.claim)
        claim["later_source_search"] = [{"query_or_scope": "coverage cannot matter for an order whose end is shown in 1980 or earlier"}]
        self.assertEqual(self.codes(claim), ["stated_end_bound_contradicts_claimed_end"])
        claim["later_source_search"][0]["query_or_scope"] = "cannot matter for an order whose end is shown in 1986 or earlier"
        self.assertEqual(self.codes(claim), [])

    def test_stated_end_date_and_conditional_reading(self):
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0]["judgment_reason"] = "No held record shows an earlier end, so the first end is 1985-01-01."
        self.assertEqual(self.codes(claim), ["stated_end_date_mismatch"])
        claim["operative_clauses"][0]["judgment_reason"] = "If a reviewer reads the parent as controlling, the first end is 1985-01-01 instead."
        self.assertEqual(self.codes(claim), [])

    def test_event_cannot_precede_order(self):
        claim = copy.deepcopy(self.claim)
        claim["operative_clauses"][0]["later_events"] = [{"actor": "EO:9000", "date": "1938-01-01"}]
        self.assertEqual(self.codes(claim), ["event_precedes_order"])

    def test_row_count_and_entity_words_bind_to_held_row(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 12553's table lists 12345, whose subject line describes a board to investigate a labor dispute."
        row = CON.check(claim, self.dossier, self.repo)["flags"]
        self.assertEqual([f["code"] for f in row], ["attributed_row_wording_mismatch"])
        self.assertEqual(row[0]["source"]["text_sha256"], sha(LIST))
        self.assertIn("12345 Creating", row[0]["source"]["quote"])
        claim["research_rationale"] = "EO 12553's table lists 12345, whose subject line describes a board to investigate labor disputes affecting railroads."
        self.assertEqual(self.codes(claim), [])
        claim["research_rationale"] = "EO 12553's table lists 12345, whose subject line describes a board on airline labor disputes."
        self.assertEqual(self.codes(claim), ["attributed_row_wording_mismatch"])

    def test_order_description_and_statute_citation(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "The order concerns a labor dispute on the railroads."
        self.assertEqual(self.codes(claim), ["attributed_order_wording_mismatch"])
        claim["research_rationale"] = "The text of 10 U.S.C. 5711(b) and 6386(c), which the order cites as its authority, is not held."
        row = CON.check(claim, self.dossier, self.repo)["flags"]
        self.assertEqual([f["code"] for f in row], ["attributed_order_citation_absent"])
        self.assertIn("5711(b)", row[0]["detail"])
        self.assertNotIn("6386", row[0]["detail"])

    def test_only_transcription_statement_checked_against_dossier_grade(self):
        rel = "jobs/fr-originals/output/texts/EO_14010.txt"
        (self.repo / rel).parent.mkdir(parents=True)
        (self.repo / rel).write_text("Executive Order 14010 amends Executive Order 12345.")
        self.dossier["evidence"]["ACT:EO:12345>EO:14010"] = {"actor_id": "EO:14010", "source": {
            "text_path": rel, "text_sha256": sha((self.repo / rel).read_text()), "page_or_item": "24 FR 1"}}
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "The dossier holds only an American Presidency Project transcription row for 14010 as a located provision."
        self.assertEqual(self.codes(claim), ["dossier_source_grade_misdescribed"])
        self.dossier["evidence"]["ACT:EO:12345>EO:14010"]["source"]["grade"] = "mirror_transcription"
        self.assertEqual(self.codes(claim), [])

    def test_stated_sha256_shape_and_adjacent_file(self):
        claim = copy.deepcopy(self.claim)
        good = sha(LIST)
        claim["research_rationale"] = f"The list is held (list.txt, text sha256 {good[:-1]})."
        self.assertEqual(self.codes(claim), ["stated_sha256_malformed"])
        rel = "jobs/source-ladder/output/texts/act.txt"
        (self.repo / rel).parent.mkdir(parents=True)
        (self.repo / rel).write_text("National Emergencies Act")
        claim["research_rationale"] = f"The act is held ({rel}, text sha256 {good})."
        self.assertEqual(self.codes(claim), ["stated_sha256_mismatch"])
        claim["research_rationale"] = f"The act is held ({rel}, text sha256 {sha('National Emergencies Act')})."
        self.assertEqual(self.codes(claim), [])
        claim["original_representation"] = {"sha256": "ABC"}
        self.assertEqual(self.codes(claim), ["stated_sha256_malformed"])

    def test_unverified_source_is_a_gap_not_a_flag(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 12553's table lists 12345, whose subject line describes a board on a labor dispute."
        (self.repo / "list.txt").write_text(LIST.replace("disputes", "dispute"))
        row = CON.check(claim, self.dossier, self.repo)
        self.assertEqual(row["flags"], [])
        self.assertEqual(row["coverage_gaps"][0]["code"], "row_description_source_unverified")


class Citing(unittest.TestCase):
    APP = "jobs/app-executive-orders/output/texts/"
    FR = "jobs/fr-originals/output/"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.dossier, self.claim = dossier_and_claim(self.repo)
        self.index, self.sources = [], []
        self.app_item("14000", "1959-02-12", "Delegating authority",
                      "Sec. 2. Executive Order No. 9000 of May 10, 1946; and Executive Order No. 9500 of June 1, 1950, are revoked except as to vested rights.")
        self.app_item("12553", "1986-02-25", "Revocation of Various Executive Orders",
                      "The following Executive Orders are revoked:\n9999 Something else\n12000 Other subject\n")
        self.app_item("6444", "1933-11-25", "Restoring Drill Sites to Naval Petroleum Reserve", "Drill sites are restored.")
        self.app_item("6444A", "1933-11-26", "Approval of Code of Fair Competition for the Distilled Spirits Industry", "The code is approved.")
        self.app_item("14002", "1950-01-01", "Amending Executive Order No. 9000", "Executive Order No. 9000 is hereby amended by striking a word.")
        proclamation = ("Changing the Names of Certain Federal Wildlife Refuges\nBY THE PRESIDENT\nA PROCLAMATION\n"
                        "I do proclaim that the names of the Federal wildlife refuges listed below are hereby changed as indicated:\n"
                        "Alpha Lake Migratory Waterfowl\nRefuge\nAlpha Lake National Wildlife Refuge\n[No. 2416]\n"
                        "[F. R. Doc. 40-3124; Filed, July 27, 1940]\n"
                        "Executive Order 14001\nAnother order\nIt is ordered.\nFRANKLIN D. ROOSEVELT\nThe White House,\nJuly 26, 1940.\n")
        self.write(self.FR + "texts/EO_14001.txt", proclamation)
        self.sources.append({"instrument_ids": ["EO:14001"], "text_path": "texts/EO_14001.txt",
                             "url": "https://www.govinfo.gov/content/pkg/FR-1940-07-30/pdf/FR-1940-07-30.pdf"})
        self.write("jobs/current-law/output/MENTIONS.csv",
                   "mention_id,system,citation,instrument_id,snippet\n"
                   'usc:1,usc,42 U.S.C. 7101 note,EO:12345,"Ex. Ord. No. 9000, as amended by Ex. Ord. No. 12345, was revoked"\n'
                   'ecfr:1,ecfr,19 CFR 204.2,EO:7233,"[27 FR 12345]"\n')
        self.write("jobs/later-events/output/EDGES.csv", "edge_id,acting_id,target_id,evidence_type,quote\n"
                   "LE-1,EO:12345,EO:9000,ofr_note_on_acting,Amends: EO 9000\n")
        report = ("Wanted: report\nCited by: EO:12345\n\n=== PDF page 1 ===\nReport \nTO \nTHE PRESIDENT \nBY TIlE \nEMERGENCY BOARD \n"
                  "APPOINTED BY EXECUTIVE ORDER I2345 DATED \nMARCH 8, 1939, PURSUANT TO SECTION 10 \nWASHINGTON, D. C. \nAPRIL 15, 1939 \n")
        self.write("jobs/source-ladder/output/texts/queue_report.txt", report)
        self.commit()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def app_item(self, number, date, subject, body):
        slug = f"executive-order-{number.lower()}-{subject.lower().replace(' ', '-')}"
        label = number[:-1] + "-" + number[-1] if number[-1].isalpha() else number
        self.write(self.APP + slug + ".txt", body)
        self.index.append({"instrument_id": "EO:" + number, "date": date, "path": "/documents/" + slug,
                           "title": f"Executive Order {label}—{subject}"})

    def commit(self):
        self.write("jobs/app-executive-orders/output/INDEX.jsonl", "".join(json.dumps(r) + "\n" for r in self.index))
        self.write(self.FR + "SOURCES.jsonl", "".join(json.dumps(r) + "\n" for r in self.sources))
        self.write("jobs/fr-originals/data/full_run/SOURCES.jsonl", "")
        for args in (("init", "-q"), ("add", "."), ("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")):
            subprocess.run(["git", *args], cwd=self.repo, capture_output=True, check=True)

    def check(self, claim):
        with N.Snapshot(self.repo) as cache:
            return CIT.check(claim, self.dossier, self.repo, None, cache)

    def codes(self, claim):
        return sorted(f["code"] for f in self.check(claim)["flags"])

    def test_parent_revocation_not_mentioned(self):
        flags = [f for f in self.check(self.claim)["flags"] if f["code"] == "unaddressed_citing_instrument"]
        self.assertEqual([f["source"]["instrument_id"] for f in flags], ["EO:14000"])
        self.assertEqual(flags[0]["source"]["text_sha256"], sha((self.repo / flags[0]["source"]["text_path"]).read_text()))
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 14000 revoked the parent subject to savings; addressed below."
        self.assertNotIn("unaddressed_citing_instrument", self.codes(claim))

    def test_amendment_of_parent_is_not_a_revocation(self):
        flags = [f for f in self.check(self.claim)["flags"] if f["code"] == "unaddressed_citing_instrument"]
        self.assertNotIn("EO:14002", [f["source"]["instrument_id"] for f in flags])

    def test_held_report_contradicts_negative(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 14000 is addressed. No board report for this order is held in the packet."
        flags = [f for f in self.check(claim)["flags"] if f["code"] == "held_board_report_unaddressed"]
        self.assertEqual(len(flags), 1)
        self.assertIn("APRIL 15, 1939", flags[0]["detail"])
        self.assertEqual(flags[0]["source"]["text_path"], "jobs/source-ladder/output/texts/queue_report.txt")
        self.dossier["instrument_id"] = claim["instrument_id"] = "EO:12346"
        self.assertNotIn("held_board_report_unaddressed", self.codes(claim))

    def test_created_name_changed_later(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 14000 is addressed. No earlier named instrument was found."
        flags = [f for f in self.check(claim)["flags"] if f["code"] == "created_name_changed_by_later_instrument"]
        self.assertEqual(len(flags), 1)
        self.assertIn("Proclamation No. 2416", flags[0]["detail"])
        self.assertEqual(flags[0]["source"]["date"], "1940-07-30")
        claim["research_rationale"] += " Proclamation 2416 renamed the refuge; recorded as a later event."
        self.assertNotIn("created_name_changed_by_later_instrument", self.codes(claim))

    def test_reference_instrument_must_cite_order(self):
        claim = copy.deepcopy(self.claim)
        claim["whole_order_end"] = claim["operative_clauses"][0]["first_end"] = None
        claim["research_rationale"] = "EO 14000 is addressed. Catalog notes: the revocation note on this order and the matching note on EO 12553."
        self.assertIn("reference_instrument_does_not_cite_order", self.codes(claim))
        (self.repo / self.APP).joinpath("executive-order-12553-revocation-of-various-executive-orders.txt").write_text(
            "The following Executive Orders are revoked:\n12345 Creating a board\n")
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qam", "cite"],
                       cwd=self.repo, capture_output=True, check=True)
        self.assertNotIn("reference_instrument_does_not_cite_order", self.codes(claim))

    def test_suffix_sibling_matches_stated_date(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 14000 is addressed. The code was approved by EO 6444 (November 26, 1933)."
        flags = [f for f in self.check(claim)["flags"] if f["code"] == "reasoning_order_suffix_sibling_mismatch"]
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0]["source"]["instrument_id"], "EO:6444A")
        claim["research_rationale"] = "EO 14000 is addressed. EO 6444 (November 25, 1933) restored drill sites; EO 6444-A of November 26, 1933 approved the code."
        self.assertNotIn("reasoning_order_suffix_sibling_mismatch", self.codes(claim))

    def test_unpinned_held_source(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 14000 is addressed. Its source is the held text of EO 14002, which is not one of the cited sources of this claim."
        self.assertIn("held_source_left_unpinned", self.codes(claim))

    def test_reported_empty_search_checked_against_retained_output(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 14000 is addressed. current-law:usc and current-law:ecfr recorded no hit."
        flags = [f for f in self.check(claim)["flags"] if f["code"] == "reported_empty_search_has_hit"]
        self.assertEqual([f["source"]["citation"] for f in flags], ["42 U.S.C. 7101 note"])
        self.assertIn("as amended by Ex. Ord. No. 12345", (self.repo / flags[0]["source"]["text_path"]).read_text()[flags[0]["source"]["char_start"]:flags[0]["source"]["char_end"]])
        claim["research_rationale"] = "EO 14000 is addressed. The Federal Register catalog notes show 0 hits; eCFR (no hit)."
        self.assertNotIn("reported_empty_search_has_hit", self.codes(claim))
        claim["research_rationale"] = "EO 14000 is addressed. The U.S. Code shows no hit for this order that contradicts the ending."
        self.assertNotIn("reported_empty_search_has_hit", self.codes(claim))

    def test_reference_discussed_elsewhere_is_not_compared(self):
        claim = copy.deepcopy(self.claim)
        claim["research_rationale"] = "EO 14000 is addressed. Searches: a full read of EO 12553. EO 12553 is discussed as the revoker of a sibling."
        self.assertNotIn("reference_instrument_does_not_cite_order", self.codes(claim))

    def test_changed_metadata_withholds_identity(self):
        (self.repo / "jobs/app-executive-orders/output/INDEX.jsonl").write_text("")
        row = self.check(self.claim)
        self.assertEqual(row["flags"], [])
        self.assertTrue(any(g["code"] == "citing_identity_metadata_unavailable" for g in row["coverage_gaps"]))

    def test_without_git_inventory_is_a_gap(self):
        row = CIT.check(self.claim, self.dossier, Path(tempfile.gettempdir()) / "no-such-geddes-repo")
        self.assertEqual(row["flags"], [])
        self.assertEqual(row["coverage_gaps"][0]["code"], "citing_corpus_unavailable")


if __name__ == "__main__":
    unittest.main()
