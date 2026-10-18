"""Offline tests for numbered.py (no network)."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numbered  # noqa: E402


class Dates(unittest.TestCase):
    def test_forms(self):
        text = "Tue White House, 23 February, 1916.\nby Executive order of November 30, 1915 (No. 2275).\n3d day of June, A. D. 1922"
        got = sorted(d for d, _, _ in numbered.page_dates(text))
        self.assertEqual(got, ["1915-11-30", "1916-02-23", "1922-06-03"])


class Numbers(unittest.TestCase):
    def test_forms(self):
        text = "By Executive order No. 2029, dated August 26, 1914; Executive orders of September 17, 1912 (No. 1610); E. O. 1234-A"
        got = sorted((n, s) for n, s, _, _ in numbered.page_numbers(text))
        self.assertEqual(got, [(1234, "A"), (1610, ""), (2029, "")])

    def test_citation_cue(self):
        self.assertTrue(numbered.CITED_CUE.search("This order amending Executive order "))
        self.assertFalse(numbered.CITED_CUE.search("a portion was amended by "))


class Words(unittest.TestCase):
    def test_names_and_abbreviations(self):
        words = dict(numbered.tokens("Herbert L. Halter, former clerk, Navy Dept., made eligible at Hershey, Neb."))
        self.assertTrue(words["halter"])
        self.assertFalse(words["dept"])  # an abbreviation is never a name

    def test_book_splitter(self):
        expand = numbered.book_splitter({"restriction": 0.01, "against": 0.2})
        self.assertEqual(expand(["restrictionagainst"]), ["restriction", "against"])

    def test_accept_needs_a_name_or_three_uncommon_words(self):
        entry = {"names": {"halter"}, "df": {"halter": 1, "rural": 9}}
        self.assertTrue(numbered.accept_words([("halter", 0), ("rural", 9)], entry, {}))
        self.assertFalse(numbered.accept_words([("rural", 9), ("carrier", 20)], entry, {}))


if __name__ == "__main__":
    unittest.main()
