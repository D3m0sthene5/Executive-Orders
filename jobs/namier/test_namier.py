"""Synthetic tests for Namier's name parsing and matching. Standard library only."""
import pathlib
import sys
import unittest
import tempfile
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import namier as N  # noqa: E402


class NameParsing(unittest.TestCase):
    def test_titles(self):
        cases = {
            "Exemption of John T. Crowley from Compulsory Retirement for Age": ["John", "T.", "Crowley"],
            "Authorizing the Appointment of Mrs. Ruth Hampton as Assistant Director": ["Ruth", "Hampton"],
            "appointing Ralph Whitman to position under the commission": ["Ralph", "Whitman"],
            "Authorizing the Reinstatement of Ralph Ely Stedman Without Regard to Civil Service Rules": ["Ralph", "Ely", "Stedman"],
            "Executive Order 5852—Authorizing the Appointment of Mrs. Gladys L. Knight": ["Gladys", "L.", "Knight"],
        }
        for title, want in cases.items():
            found = [N.name_parts(raw) for _, raw in N.names_from_title(title)]
            self.assertIn(want, found, title)
        self.assertEqual(N.names_from_title("Authorizing Appointments to Certain Temporary Positions"), [])

    def test_wpa_summaries(self):
        got = [N.name_parts(r) for _, r in N.names_from_summary("NellieJ. Latta made eligiblefor reinstatement as a clerk")]
        self.assertEqual(got, [["Nellie", "J.", "Latta"]])
        got = [N.name_parts(r) for _, r in N.names_from_summary(
            "William L. Hill,John Lewis May, and Leonard Magruder, exempted from compulsory retirement provisionsuntilAug. 1, 1932.")]
        self.assertEqual(got, [["William", "L.", "Hill"], ["John", "Lewis", "May"], ["Leonard", "Magruder"]])
        got = [N.name_parts(r) for _, r in N.names_from_summary(
            "Hugh A. Morrison, reading room custodian in the Li brary of Congress, further exempted from compulsory")]
        self.assertEqual(got, [["Hugh", "A.", "Morrison"]])
        self.assertEqual(N.names_from_summary("Civil Service Rules amended by promulgation of special rule to permit the appointment"), [])

    def test_rejects_office_words_and_bare_initials(self):
        self.assertIsNone(N.name_parts("Legislative Branch"))
        self.assertIsNone(N.name_parts("Alien Property Custodian"))
        self.assertIsNone(N.name_parts("H. White"))  # one initial and a surname is not a usable search key
        self.assertEqual(N.name_parts("C. M. Huntington"), ["C.", "M.", "Huntington"])
        self.assertEqual(N.name_parts("Patrick O'Brien, Jr."), ["Patrick", "O'Brien"])

    def test_own_text_gate(self):
        text = ("# EO:1: header naming Herbert Hoover\n"
                "EXEMPTION OF JOHN T. CROWLEY FROM COMPULSORY RETIREMENT FOR AGE\n"
                "John T. Crowley, Vocational Advisor, Veterans' Administration, who, during the current month, reaches "
                "the retirement age, is hereby exempted from the provisions of that section until May 31, 1933.")
        names = N.subject_names("EO:1", [text], "", "", given_names={"john"}, exclude={("herbert", "hoover")})
        self.assertEqual([n["name"] for n in names], ["John T. Crowley"])


class Matching(unittest.TestCase):
    def test_forward_and_reverse(self):
        pat = N.match_pattern(N.name_parts("John D. Campbell"))
        for text in ["John Campbell", "JOHN D. CAMPBELL", "Campbell, John D.", "john campbell", "John Davis Campbell"]:
            self.assertTrue(pat.search(text), text)
        for text in ["Johnson Pike Campbell", "Campbell John", "Johnny Campbell"]:
            self.assertFalse(pat.search(text), text)

    def test_initials_only(self):
        pat = N.match_pattern(N.name_parts("C. M. Huntington"))
        for text in ["C. M. Huntington", "C M Huntington", "Huntington, C. M."]:
            self.assertTrue(pat.search(text), text)
        self.assertFalse(pat.search("Collis Huntington"))

    def test_middle_conflict(self):
        parts = N.name_parts("Thomas L. Smith")
        self.assertTrue(N.middle_conflict(parts, "Thomas C. Smith"))
        self.assertTrue(N.middle_conflict(parts, "Smith, Thomas C"))
        for matched in ["Thomas Smith", "Thomas Lee Smith", "Thomas L Smith", "Smith, Thomas"]:
            self.assertFalse(N.middle_conflict(parts, matched), matched)

    def test_number_cited(self):
        self.assertTrue(N.number_cited("was exempted by Executive Order No. 6088, dated March 29, 1933", "EO:6088"))
        self.assertFalse(N.number_cited("was exempted by Executive Order No. 6089", "EO:6088"))


class CorpusCoverage(unittest.TestCase):
    def test_case_and_surname_spellings_reach_covered_search(self):
        cases = [
            ("John D. Campbell", "JOHN D. CAMPBELL is further exempted."),
            ("John D. Campbell", "john campbell is further exempted."),
            ("Patrick O'Brien", "Patrick O'Brien is further exempted."),
            ("John McNeir", "John McNeir is further exempted."),
        ]
        for name, text in cases:
            with self.subTest(name=name, text=text), tempfile.TemporaryDirectory() as tmp:
                path = pathlib.Path(tmp) / "actor.txt"
                path.write_text(text, encoding="utf-8")
                fragment = {"text_path": str(path), "produced_by": "test"}
                with mock.patch.object(N.E, "iter_texts", return_value=iter([("EO:2", fragment, text)])):
                    corpus = N.Corpus(tmp, {})
                subjects = {"EO:1": {"type": "retirement_exemption", "subject_source": "index_title",
                                      "title": "Exemption of " + name + " from Compulsory Retirement",
                                      "summary": ""}}
                dates = {"EO:1": {"date": "1933-01-01"}, "EO:2": {"date": "1934-01-01"}}
                links, coverage = N.search(corpus, subjects, dates)
                self.assertEqual(coverage[0]["covered"], 1)
                self.assertEqual([h["instrument_id"] for h in links[0]["hits"]], ["EO:2"])
                self.assertEqual(links[0]["hits"][0]["flags"], [])


if __name__ == "__main__":
    unittest.main()
