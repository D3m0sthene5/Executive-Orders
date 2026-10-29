"""Dossier original selection: rank by representation tier, refuse contradicted identity.

Regression for the 2026-10-28 land probe, where EO 4872 carried a 1928 statute page,
EO 7509 the Water Resources Development Act of 2000, and EOs 7435 and 7510 Federal
Register issue pages that do not print the order, although APP transcriptions were held.
"""
from contextlib import redirect_stdout
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import build as B
import inputs as I

REPO = HERE.parents[1]

TREASURY = ("FEDERAL REGISTER\nNUMBER 175\nWashington, Saturday, November 14, 1936\n"
            "TREASURY DEPARTMENT.\n[Regulations 94]\nIncome Tax Under the Revenue Act of 1936\n"
            "Executive Order No. 100 is hereby revoked.\n")
STATUTE = ("SEVENTIETH CONGRESS. Sess. I. Chs. 728, 729. 1928. 729\n[Public, No. 500.]\n"
           "Executive Order No. 100 is hereby revoked.\nThe lease shall run for a period of two years.\n")
PLAW = "PUBLIC LAW 106-541—DEC. 11, 2000\nWATER RESOURCES DEVELOPMENT ACT\nOF 2000\nExecutive Order No. 7509 (December 11, 1936)\n"
FR_7373 = ("FEDERAL REGISTER\nEXECUTIVE ORDER\nESTABLISHING THE DESERT GAME RANGE\nNevada\n"
           "By virtue of the authority vested in me, it is ordered that the lands be withdrawn.\n"
           "FRANKLIN D ROOSEVELT\nTHE WHITE HOUSE,\nMay 20, 1936.\n[No. 73731\n")


def lead(url=None, page=None, archival=None, grade="held_text_lead"):
    source = {k: v for k, v in (("url", url), ("page_or_item", page), ("archival_id", archival)) if v}
    return {"grade": grade, "acceptable_as_original": False, "source": source, "text_path": "x"}


class RankAndConflictTests(unittest.TestCase):
    def test_registered_working_text_outranks_leads_whatever_the_path(self):
        mirror = {"grade": "mirror_transcription", "acceptable_as_original": False, "text_path": "jobs/zzz/a.txt"}
        for grade in ("held_text_lead", "derivative_lead", "official_fr_pdf_text_layer", "mirror_transcription_app"):
            other = {"grade": grade, "acceptable_as_original": False, "text_path": "jobs/aaa/a.txt"}
            self.assertLess(B.rank_text(mirror), B.rank_text(other), grade)
        official = {"grade": "original_representation_unverified_needs_page_check",
                    "acceptable_as_original": True, "text_path": "jobs/zzz/b.txt"}
        self.assertLess(B.rank_text(official), B.rank_text(mirror))
        mirror["instrument_id"] = "EO:1"
        self.assertEqual(B.text_tier(mirror, {("EO:1", "jobs/zzz/a.txt", "mirror_transcription")}), 1)
        self.assertEqual(B.text_tier(mirror, set()), 2)  # unregistered grade label

    def test_statute_public_law_and_code_printings_are_refused_at_every_tier(self):
        for source in ({"url": "https://www.govinfo.gov/content/pkg/STATUTE-45/pdf/STATUTE-45-Pg729.pdf"},
                       {"url": "https://www.govinfo.gov/content/pkg/PLAW-106publ541/pdf/PLAW-106publ541.pdf"},
                       {"archival_id": "opus:evidence/reviews/X/cache/STAT_114_2699.pdf"},
                       {"archival_id": "opus:evidence/reviews/X/cache/stat67_29.pdf"},
                       {"url": "https://www.govinfo.gov/content/pkg/USCODE-2024-title22/pdf/x.pdf"}):
            for grade, ok in (("held_text_lead", False), ("mirror_transcription", False), ("fr_originals_high", True)):
                rec = {"grade": grade, "acceptable_as_original": ok, "source": source}
                self.assertIn("statute/public-law/Code", B.identity_conflict("EO:4872", rec, "Executive Order No. 4872 withdraws the following public lands.\n") or "", source)

    def test_text_headed_as_statute_is_refused(self):
        self.assertIn("headed as a statute", B.identity_conflict("EO:7509", lead(archival="opus:x/cache/V11.pdf"), PLAW))
        self.assertIn("headed as a statute", B.identity_conflict("EO:4872", lead(), STATUTE))
        # Citing a public law inside an order's body is not a heading.
        body = "EXECUTIVE ORDER 12517\nAll functions vested by Title IX of\nPublic Law 98-164 are delegated.\n"
        self.assertIsNone(B.identity_conflict("EO:12517", lead(), body))

    def test_fr_lead_must_print_or_name_the_order(self):
        partial = lead("https://www.govinfo.gov/content/pkg/FR-1936-11-14/pdf/FR-1936-11-14.pdf",
                       "1 FR 2150; FR-1936-11-14.pdf PDF pages 1-6 of 66 (PARTIAL: other pages not extracted)")
        self.assertIn("does not print or name EO:7510", B.identity_conflict("EO:7510", partial, TREASURY))
        whole = lead("https://www.govinfo.gov/content/pkg/FR-1936-05-22/pdf/FR-1936-05-22.pdf")
        # OCR read the closing bracket of "[No. 7373]" as a digit.
        self.assertIsNone(B.identity_conflict("EO:7373", whole, FR_7373))
        spaced = "Presidential Documents\nExecu tive O rder 12415 o f April 5, 1983\nExtension.\n"
        self.assertIsNone(B.identity_conflict("EO:12415", lead(page="48 FR 15587"), spaced))
        self.assertIn("does not print", B.identity_conflict("EO:12416", lead(page="48 FR 15587"), spaced))

    def test_text_that_prints_no_order_is_refused(self):
        for body in ("July 15, 1895.", "(this executive order was not published)", "  \n"):
            rec = {"grade": "compiled_transcription_lead", "acceptable_as_original": False, "source": {}}
            self.assertIn("prints no order", B.identity_conflict("EO:72", rec, body) or "", body)
        self.assertIsNone(B.identity_conflict("EO:72", lead(), "The Civil Service Rules are amended as follows.\n"))

    def test_only_contradictions_are_tested_outside_fr_leads(self):
        fr = "https://www.govinfo.gov/content/pkg/FR-1944-09-08/pdf/FR-1944-09-08.pdf"
        # Official and registered working texts are not refused for unread OCR numbers.
        for grade, ok in (("original_representation_unverified", True), ("mirror_transcription", False)):
            self.assertIsNone(B.identity_conflict("EO:9479", {"grade": grade, "acceptable_as_original": ok,
                                                              "source": {"url": fr}}, TREASURY))
        # Unnumbered early orders: a non-FR derivative lead need not print a number.
        self.assertIsNone(B.identity_conflict("EO:5", lead("https://example.org/richardson/vol6", grade="derivative_lead"),
                                              "The Secretary of War is directed to proceed.\n"))
        self.assertIsNone(B.identity_conflict("EO:UN:row:7", lead(fr), TREASURY))


class BuildSelectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        self.out = self.repo / "jobs/claim-kit/output"
        census = self.repo / I.UNIVERSE
        census.parent.mkdir(parents=True)
        ids = ["EO:100", "EO:4872", "EO:7373", "EO:7509", "EO:7510"]
        with census.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["id", "included_in_bibliography"])
            writer.writeheader()
            writer.writerows({"id": iid, "included_in_bibliography": "1"} for iid in ids)
        status = self.repo / I.STATUSES
        status.parent.mkdir(parents=True)
        status.write_text("instrument_id,provisional_substantive_status\n" + "".join(iid + ",no\n" for iid in ids), encoding="utf-8")
        gate = self.repo / "research/stage19/code/claim_gate.py"
        gate.parent.mkdir(parents=True)
        gate.write_bytes((REPO / "research/stage19/code/claim_gate.py").read_bytes())
        fr = "https://www.govinfo.gov/content/pkg/{0}/pdf/{0}.pdf"
        app = "https://www.presidency.ucsb.edu/documents/eo-"
        rows = [  # (id, path, text, grade, url, page, registered as a working text)
            # Path names sort the leads first, as jobs/opus-media-match and jobs/source-ladder did.
            ("EO:7510", "jobs/aaa-ladder/data/t/7510.txt", TREASURY, "held_text_lead", fr.format("FR-1936-11-14"), "1 FR 2150", False),
            ("EO:7510", "jobs/zzz-app/data/t/7510.txt", "By virtue of the authority vested in me, the Lenore Lake refuge is established.\n",
             "mirror_transcription", app + "7510", None, True),
            ("EO:4872", "jobs/aaa-opus/data/t/4872.txt", STATUTE, "held_text_lead",
             "https://www.govinfo.gov/content/pkg/STATUTE-45/pdf/STATUTE-45-Pg729.pdf", None, False),
            ("EO:7509", "jobs/aaa-opus/data/t/7509.txt", PLAW, "held_text_lead",
             "https://www.govinfo.gov/content/pkg/PLAW-106publ541/pdf/PLAW-106publ541.pdf", None, False),
            ("EO:7509", "jobs/zzz-app/data/t/7509.txt", "By virtue of the authority vested in me, the Fort Peck Game Range is established.\n",
             "mirror_transcription", app + "7509", None, True),
            ("EO:7373", "jobs/aaa-opus/data/t/7373.txt", FR_7373, "held_text_lead", fr.format("FR-1936-05-22"), None, False),
            # A working-text grade label without a producer registration is a lead.
            ("EO:7373", "jobs/aaa-cd/data/t/7373.txt", "it is ordered that the lands be withdrawn.\n",
             "mirror_transcription", app + "7373", None, False),
            ("EO:100", "jobs/aaa-ladder/data/t/100.txt", "EXECUTIVE ORDER 100\nThe Board shall perform the duties.\n",
             "held_text_lead", fr.format("FR-1937-01-02"), None, False),
            ("EO:100", "jobs/zzz-app/data/t/100.txt", "The Board shall perform the specified duties.\n",
             "mirror_transcription", app + "100", None, True),
        ]
        by_job, fragments = {}, {}
        for iid, rel, text, grade, url, page, registered in rows:
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            source = {"url": url, "sha256": digest, "text_sha256": digest}
            if page:
                source["page_or_item"] = page
            job = rel.split("/")[1]
            if registered:
                fragments.setdefault(job, []).append({"instrument_id": iid, "kind": "original_representation",
                    "data": dict(source, text_path=rel, grade=grade, acceptable_as_original=False)})
            else:
                by_job.setdefault(job, []).append(
                    {"instrument_id": iid, "text_path": rel, "grade": grade, "acceptable_as_original": False, "source": source})
        for job, declarations in by_job.items():
            target = self.repo / "jobs" / job / "data/PROVENANCE.json"
            target.write_text(json.dumps({"representations": declarations}), encoding="utf-8")
        for job, records in fragments.items():
            target = self.repo / "jobs" / job / "output/FRAGMENTS.jsonl"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")

    def dossier(self, iid):
        return json.loads((self.out / "dossiers" / (B.filename(iid) + ".json")).read_text(encoding="utf-8"))

    def test_land_probe_orders_get_their_own_text_or_none(self):
        with redirect_stdout(io.StringIO()):
            summary = B.build(self.repo, self.out)
        original = lambda iid: self.dossier(iid)["evidence"].get("ORIGINAL:" + iid, {})
        self.assertEqual(original("EO:7510")["source"]["text_path"], "jobs/zzz-app/data/t/7510.txt")
        self.assertEqual(original("EO:7509")["source"]["text_path"], "jobs/zzz-app/data/t/7509.txt")
        self.assertEqual(original("EO:100")["source"]["text_path"], "jobs/zzz-app/data/t/100.txt")
        # Both 7373 texts are leads; the FR issue page prints [No. 7373] and is not a mirror.
        self.assertEqual(original("EO:7373")["source"]["text_path"], "jobs/aaa-opus/data/t/7373.txt")
        d4872 = self.dossier("EO:4872")
        self.assertIsNone(d4872["original_source_id"])
        self.assertFalse(d4872["clauses"])
        self.assertTrue(any("refused" in m and "STATUTE-45-Pg729.pdf" in m for m in d4872["missing"]))
        # Refused texts are not this order's terms or acting provisions.
        self.assertFalse(d4872["own_terms"])
        self.assertEqual(self.dossier("EO:100")["actor_provisions"], [])
        self.assertEqual(summary["counts"]["texts_refused_as_order_text"], 3)
        # Declarations are preserved for review.
        self.assertEqual(len((self.out / "TEXT_REPRESENTATIONS.jsonl").read_text(encoding="utf-8").splitlines()), 9)


if __name__ == "__main__":
    unittest.main()
