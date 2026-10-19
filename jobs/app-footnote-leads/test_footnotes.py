"""Offline tests on real APP footnotes (copied verbatim from jobs/app-executive-orders/output, 2026-10-18)."""

import csv
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import footnotes as F  # noqa: E402

REFS = F.load_later_events(REPO).eo_references

REAL = {
    "EO:4601": ("1927-03-01", "Note: Executive Order 4601 was further amended by Executive Order 7962 of Aug. 22, 1938, to provide for the award of the decoration to a certain member of the U.S. Coast Guard. The Executive order was not printed in the Federal Register .\n\nEditorial Note: Executive Order 4601 was not given a formal title."),
    "EO:14096": ("2023-04-21", "NOTE: This Executive order was published in the Federal Register on April 26."),
    "EO:13293": ("2003-03-28", "Note: This Executive order will be published in the Federal Register on April 1."),
    "EO:12311": ("1981-06-29", "Note: The annexes are printed in the Federal Register of July 1, 1981.\n\nThe text of the Executive order was released by the Office of the Press Secretary on June 30."),
    "EO:11643": ("1972-02-08", "NOTE: For the President's message to Congress in which reference is made to Executive Order 11643, see page 218 of this issue."),
    "EO:11616": ("1971-08-26", "NOTE: Executive Order 11616 was released in San Clemente, Calif."),
    "EO:11408": ("1968-04-25", "NOTE: The activities formerly covered by the orders revoked by Executive Order 11408 are governed by Executive Order 11222 \"Prescribing Standards of Ethical Conduct for Government Officers and Employees\" of May 8, 1965 (3 CFR, 1964-1965 Comp., p. 306), and regulations issued thereunder.\n\nExecutive Order 11408 was not made public in the form of a White House press release."),
    "EO:8682": ("1941-02-14", "Note: Executive Order 9881 of Aug. 4, 1947, 12 FR 5325, 3 CFR, 1943-1948 Comp., p. 662, discontinued the Palmyra Island Naval Airspace Reservation and the Palmyra Island Naval Defensive Sea Area."),
    "EO:7822": ("1938-02-25", "3 FR 547, 1938 WL 3696 (Pres.)"),
    "EO:6606G": ("1934-02-17", "APP Note: The president also issued a letter to National Recovery Administrator Hugh S. Johnson on Conditions in this Executive Order. This letter can be found here: https://www.presidency.ucsb.edu/node/373380"),
    "EO:13487": ("2009-01-16", "Note: This Executive order was published in the Federal Register on January 22. This item was not received in time for inclusion in the appropriate issue."),
    "EO:13232": ("2001-10-20", "Note: This Executive order was released by the Office of the Press Secretary on October 22, and it was published in the Federal Register on October 24."),
    "EO:11255": ("1965-11-01", "NOTE: Executive Order 11255 was not filed with the Office of the Federal Register before the cutoff time of this issue. As printed above, it follows the text of the press release distributed by the Office of the White House Press Secretary at Austin, Tex."),
    "EO:9265": ("1942-11-06", "Note: Executive Order 9265 was amended by the following provisions of Executive Order 9706 of Mar. 15, 1946, which appear at 11 FR 2811, 3 CFR, 1943-1948 Comp., p. 520:\n\n1. The European-African-Middle Eastern Campaign Medal shall not be awarded for any service rendered subsequent to November 8, 1945."),
    "EO:8533": ("1940-09-06", "Note: Executive Order 8533 was amended by Executive Order 9543 of Apr. 23, 1945, 10 FR 4413, 3 CFR, 1943-1948 Comp., p. 377, and Executive Order 9774 of Sept. 3, 1946, 11 FR 9729, 3 CFR, 1943-1948 Comp., p. 566, designating the Reconstruction Finance Corporation as the agency authorized to dispose of securities with respect to loans made to certain privately owned companies. The moneys realized were to be paid to the Secretary of the Treasury for deposit to the appropriate account."),
}


def rows_for(iid):
    date, note = REAL[iid]
    out = []
    for s in F.sentences(note):
        out += [(t, f, s) for t, f in F.classify(iid, s, date, REFS)]
    return out


def types(iid):
    return [t for t, _, _ in rows_for(iid)]


class Classify(unittest.TestCase):
    def test_amended_by_with_date_and_not_printed(self):
        rows = rows_for("EO:4601")
        self.assertEqual([t for t, _, _ in rows], ["amended_by", "not_published", "other"])
        self.assertEqual(rows[0][1]["referenced_eo"], ["EO:7962"])
        self.assertEqual(rows[0][1]["actors"][0]["date"], "1938-08-22")
        self.assertEqual(rows[0][1]["qualifier"], "")  # "further" is not a scope qualifier; "in part" would be
        part = F.classify("EO:1", "Executive Order 1 was revoked in part by Executive Order 2.", "1900-01-01", REFS)
        self.assertEqual([(t, f["qualifier"], f["referenced_eo"]) for t, f in part], [("revoked_by", "in part", ["EO:2"])])

    def test_two_amending_orders_and_their_fr_cites_are_not_this_orders_citation(self):
        rows = rows_for("EO:8533")
        self.assertEqual([t for t, _, _ in rows], ["amended_by", "other"])
        self.assertEqual(rows[0][1]["referenced_eo"], ["EO:9543", "EO:9774"])
        self.assertNotIn("fr_citation", types("EO:9265"))
        self.assertEqual(rows_for("EO:9265")[0][1]["referenced_eo"], ["EO:9706"])

    def test_this_order_as_the_revoker_is_not_revoked_by(self):
        self.assertEqual(types("EO:11408"), ["other", "other"])
        self.assertEqual(rows_for("EO:11408")[1][1]["detail"], "press_release")

    def test_a_note_about_another_order_is_other(self):
        rows = rows_for("EO:8682")
        self.assertEqual([t for t, _, _ in rows], ["other"])
        self.assertEqual(rows[0][1]["referenced_eo"], ["EO:9881"])

    def test_fr_publication_notes_and_inferred_dates(self):
        rows = rows_for("EO:14096")
        self.assertEqual([t for t, _, _ in rows], ["fr_citation"])
        self.assertEqual(rows[0][1]["fr_publication_date_inferred"], "2023-04-26")
        future = rows_for("EO:13293")[0][1]
        self.assertEqual((future["detail"], future["fr_publication_date_inferred"]),
                         ("future tense: announced publication", "2003-04-01"))
        annex = rows_for("EO:12311")
        self.assertEqual([t for t, _, _ in annex], ["fr_citation", "other"])
        self.assertEqual(annex[0][1]["detail"], "publication note (attachments)")
        self.assertEqual(annex[0][1]["fr_publication_date_inferred"], "1981-07-01")
        both = rows_for("EO:13232")
        self.assertEqual([t for t, _, _ in both], ["fr_citation"])
        self.assertEqual(both[0][1]["fr_publication_date_inferred"], "2001-10-24")

    def test_year_rolls_over_after_a_december_signing(self):
        self.assertEqual(F.infer_date("January 3", "2008-12-30"), "2009-01-03")
        self.assertEqual(F.infer_date("Febr 30", "2008-12-30"), "")

    def test_bare_fr_citation(self):
        rows = rows_for("EO:7822")
        self.assertEqual([t for t, _, _ in rows], ["fr_citation"])
        self.assertEqual((rows[0][1]["fr_volume"], rows[0][1]["fr_page"]), ("3", "547"))

    def test_weekly_compilation_timing_is_not_not_published(self):
        rows = rows_for("EO:11255")
        self.assertNotIn("not_published", [t for t, _, _ in rows])
        self.assertEqual(rows[0][1]["detail"], "weekly_compilation_timing")
        self.assertEqual([t for t, _, _ in rows_for("EO:13487")], ["fr_citation", "other"])
        self.assertEqual(rows_for("EO:13487")[1][1]["detail"], "weekly_compilation_timing")

    def test_other_kinds(self):
        self.assertEqual(rows_for("EO:11643")[0][1]["detail"], "cross_reference")
        self.assertEqual(rows_for("EO:11616")[0][1]["detail"], "release_place")
        self.assertEqual({f["detail"] for _, f, _ in rows_for("EO:6606G")}, {"app_editorial_note"})

    def test_sentences_keep_abbreviations_and_are_exact_pieces(self):
        for iid, (_, note) in REAL.items():
            collapsed = " ".join(" ".join(p.split()) for p in note.split("\n"))
            for s in F.sentences(note):
                self.assertIn(s, collapsed, iid)
        self.assertEqual(len(F.sentences(REAL["EO:8533"][1])), 2)


class Run(unittest.TestCase):
    def test_job_outputs_and_edges_shape(self):
        repo = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        le = repo / "jobs" / "later-events"
        le.mkdir(parents=True)
        shutil.copy(REPO / "jobs" / "later-events" / "later_events.py", le / "later_events.py")
        src = repo / F.SOURCE_OUT
        src.mkdir(parents=True)
        recs = [{"instrument_id": iid, "date": d, "footnote": n, "path": f"/documents/{iid}", "app_node": "1",
                 "url": f"https://www.presidency.ucsb.edu/documents/{iid}", "sha256": "a" * 64}
                for iid, (d, n) in REAL.items()]
        with open(src / "DOCUMENTS.jsonl", "w", encoding="utf-8") as fh:
            fh.writelines(json.dumps(r) + "\n" for r in recs)
        with open(src / "MIRROR_DOCUMENTS.jsonl", "w", encoding="utf-8") as fh:  # same note, second lane
            fh.write(json.dumps(dict(recs[0], capture={"archive": "common-crawl", "captured_utc": "2025-01-01"})) + "\n")
        with open(src / "MIRROR_FAILURES.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"instrument_id": "EO:9457", "path": "/documents/x", "reason": "no_usable_text",
                                 "archive": "common-crawl", "capture_timestamp": "20260123022801"}) + "\n")
        out = repo / "out"
        s, leads, edges = F.run(repo, out)
        self.assertEqual(s["distinct_footnotes"], len(REAL))
        self.assertEqual(s["sentence_rows_by_type"]["amended_by"], 3)
        self.assertEqual(s["sentence_rows_by_type"]["not_published"], 2)
        self.assertEqual(s["later_order_edges"], 4)
        lanes = next(r["lanes"] for r in leads if r["instrument_id"] == "EO:4601")
        self.assertEqual(lanes, "live|common-crawl 2025-01-01")
        with open(out / "EDGES.csv", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(list(rows[0]), F.EDGE_COLUMNS)
        self.assertEqual({(r["acting_id"], r["target_id"], r["mechanism"]) for r in rows},
                         {("EO:7962", "EO:4601", "amendment"), ("EO:9543", "EO:8533", "amendment"),
                          ("EO:9774", "EO:8533", "amendment"), ("EO:9706", "EO:9265", "amendment")})
        self.assertTrue(all(r["evidence_type"] == "app_footnote_on_target" for r in rows))
        self.assertTrue(all("lead_only_never_an_ending" in r["date_flags"] for r in rows))


if __name__ == "__main__":
    unittest.main()
