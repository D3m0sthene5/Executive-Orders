import csv
import gzip
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dagron  # noqa: E402

SPEC = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "collections", "nyu-film709.json")))


class Units(unittest.TestCase):
    def test_reel_bounds(self):
        u = lambda n, s="": dagron.unit_for(SPEC, n, s)[0]  # noqa: E731
        self.assertEqual(u("1"), 1)
        self.assertEqual(u("707"), 1)
        self.assertEqual(u("708"), 2)
        self.assertEqual(u("6925"), 10)
        self.assertEqual(u("6925", "A"), 11)
        self.assertEqual(u("6925", "B"), 11)
        self.assertEqual(u("7403"), 11)
        self.assertIsNone(u("7404"))
        self.assertIsNone(u(""))

    def test_boundary_notes(self):
        self.assertIn("variant of reel 1", dagron.unit_for(SPEC, "707", "A")[1])
        self.assertEqual(dagron.unit_for(SPEC, "707", "A")[0], 1)
        self.assertIn("last item of reel 10", dagron.unit_for(SPEC, "6925", "")[1])
        self.assertIn("first number of reel 2", dagron.unit_for(SPEC, "708", "")[1])

    def test_designation_keeps_suffix(self):
        self.assertEqual(dagron.designation("106", "½"), "EO 106½")
        self.assertEqual(dagron.designation("8", "-1"), "EO 8-1")
        self.assertEqual(dagron.designation("", ""), "(unnumbered)")

    def test_lfs_pointer(self):
        sha = "3bce4d490526a69516217faf43b66b62adf565a388b622f6d1e9225faffdcdf5"
        ptr = f"version https://git-lfs.github.com/spec/v1\noid sha256:{sha}\nsize 68508824\n"
        self.assertEqual(dagron.LFS.match(ptr).group(1), sha)


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


class EndToEnd(unittest.TestCase):
    """A five-order fixture covering each group, built from files only (no git)."""

    def test_groups_and_evidence(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as out:
            ready = lambda i, step, tier: {"instrument_id": i, "step_original_text": step, "text_evidence_tier": tier,  # noqa: E731
                                           "blockers": "NO_OFFICIAL_SOURCE_LOCATED", "provisional_status": "",
                                           "claim_present": "no", "ready_for_human_review": "no",
                                           "original_copy_replacement_required": "no", "provisional_text_grade": "",
                                           "informational_flags": "", "generation_id": "g"}
            write_csv(f"{root}/{dagron.P['readiness']}", [
                ready("EO:10", "open", "missing"), ready("EO:20", "done", "original_supported"),
                ready("EO:8-1", "open", "missing"), ready("EO:UN:x", "open", "missing"),
                ready("EO:7500", "open", "missing"), ready("EO:9000", "open", "missing")])
            reg = lambda i, n, s, d: {"instrument_id": i, "number": n, "suffix": s, "date": d, "date_source": "app_index",  # noqa: E731
                                      "title": "t", "president": "p", "census_class": "c", "best_held": "nothing",
                                      "proquest_link_supplied": "no", "proquest_pdf_file": ""}
            write_csv(f"{root}/{dagron.P['domesday']}", [
                reg("EO:10", "10", "", "1870-01-01"), reg("EO:20", "20", "", "1880-01-01"),
                reg("EO:8-1", "8", "-1", "1873-03-14"), reg("EO:UN:x", "", "", "1898-08-12"),
                reg("EO:7500", "7500", "", "1936-10-01"), reg("EO:9000", "9000", "", "1941-12-08")])
            write_csv(f"{root}/{dagron.P['candidates']}", [{"instrument_id": "EO:27A", "number": "27", "suffix": "A",
                                                            "named_by": "cited_by:EO:399", "dates_seen": "", "titles_seen": "",
                                                            "strength": "cited", "example_source": "", "note": ""}])
            os.makedirs(f"{root}/jobs/wikisource-texts/output/texts")
            open(f"{root}/jobs/wikisource-texts/output/texts/EO_20.txt", "w").write("x")
            write_jsonl(f"{root}/jobs/ofr-compilations/output/FRAGMENTS.jsonl", [
                {"kind": "original_representation", "instrument_id": "EO:20",
                 "data": {"needs_page_check": False, "text_path": "texts/EO_20.txt", "sha256": "ab", "url": "u"}}])
            os.makedirs(f"{root}/jobs/ofr-compilations/output/texts")
            open(f"{root}/jobs/ofr-compilations/output/texts/EO_20.txt", "w").write("x")
            write_jsonl(f"{root}/jobs/wikisource-texts/output/FRAGMENTS.jsonl", [
                {"kind": "original_representation", "instrument_id": "EO:10", "acceptable_as_original": False,
                 "data": {"text_path": "texts/EO_10.txt", "sha256": "cd", "url": "https://en.wikisource.org/x"}}])
            write_jsonl(f"{root}/research/acquisitions/nyu-film709/PROVENANCE.jsonl", [
                {"instrument_id": "EO:10", "collection": "hein", "file": "f.pdf", "sha256": "ee",
                 "witness_kind_observed": "official_printed_copy", "observed_number": "10", "retrieved_utc": "t"}])
            spec = dict(SPEC)
            dagron.main([root, out, os.path.join(os.path.dirname(os.path.abspath(__file__)), "collections", "nyu-film709.json")])
            rows = [json.loads(l) for l in gzip.open(f"{out}/nyu-film709/MANIFEST.jsonl.gz", "rt")]
            by = {r["instrument_id"] or r["proposed_id_not_in_census"]: r for r in rows}
            self.assertEqual(by["EO:10"]["manifest_group"], "1_missing_accepted_original_witness")
            self.assertEqual(by["EO:10"]["likely_unit"], 1)
            self.assertTrue(by["EO:10"]["missing"]["has_transcription_only"])
            self.assertEqual(by["EO:10"]["held"]["transcriptions"][0]["witness_class"], "transcription")
            self.assertEqual(len(by["EO:10"]["staged_acquisitions"]), 1)
            self.assertNotIn("EO:20", by)  # counted original with its text
            self.assertEqual(by["EO:8-1"]["manifest_group"], "3_unnumbered_or_ambiguous_identity")
            self.assertEqual(by["EO:UN:x"]["manifest_group"], "3_unnumbered_or_ambiguous_identity")
            self.assertEqual(by["EO:27A"]["manifest_group"], "3_unnumbered_or_ambiguous_identity")
            self.assertEqual(by["EO:27A"]["instrument_id"], "")
            self.assertEqual(by["EO:7500"]["manifest_group"], "4_edge_numbered_after_last_unit_within_dates")
            self.assertNotIn("EO:9000", by)
            s = json.load(open(f"{out}/nyu-film709/SUMMARY.json"))
            self.assertEqual(s["staged_orders"], 1)
            self.assertEqual(s["tracker_measures"]["step_original_text_open"]["not_in_manifest_by_reason"],
                             {"numbered above the last unit, outside the dates": 1})
            with gzip.open(f"{out}/nyu-film709/MANIFEST.csv.gz", "rt") as fh:
                self.assertEqual(len(list(csv.DictReader(fh))), len(rows))


if __name__ == "__main__":
    unittest.main()
