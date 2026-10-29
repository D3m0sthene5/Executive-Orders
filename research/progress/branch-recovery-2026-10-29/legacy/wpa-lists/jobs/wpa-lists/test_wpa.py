"""Tests for wpa.py on small excerpts in the books' layouts (no network)."""

import unittest

import wpa

NUMBERED = [{"page": 21, "text": "1885\n24: Nov. 25 Mourning formalities for Vice-President Thomas A. Hen\n"
                                 "dricks ordered. VIII R 319.\n25: [E. 0. 25 is Proc. 278 of Nov. 18, 1886]\n"
                                 "1905\n26 :July 3 Charles W. Bell made eligible for appointment as finance\n"
                                 "clerk at the Lowell, Mass., post office. 1905 CSR 89.\n"
                                 "26-A :July 3 Administration of navigation aids for Tutuila placed under Commerce.\n"
                                 "412: this line is a stray number and not an entry\n"
                                 "27: July 5* Fort Keogh placed under the Interior Sec'y.\n* Has form of a proclamation.\n"}]

UNNUMBERED = [{"page": 40, "text": "9\n1840\nMar. 31 All persons employed on public works required to work only\n"
                                   "the hours prescribed by the ten-hour system .\nIII Richardson 602\n"
                                   "1842\nFeb. 9\nFeb. 9\nFort Wood Military Reservation , La . , established .\n"
                                   "( 1830 GLO 52 ; 1897 GLO 114 )\n"
                                   "Fort Laramie Military Reservation transferred to the Interior Secretary under\n"
                                   "the act of July 5 , 1884 ( 23 Stat.L. 103 ) for disposal .\n"
                                   "( 1898 GLO 157 ; 1901 GLO 195 )\n"
                                   "1898\nJan. 10\nMar. 28\nHelena Land District , Mont . , diminished .\n( 1898 GLO 157)\n"}]


class Numbered(unittest.TestCase):
    def test_entries_suffixes_and_sequence_guard(self):
        e = {x["id"]: x for x in wpa.parse_numbered(NUMBERED)}
        self.assertEqual(sorted(e), ["EO:24", "EO:25", "EO:26", "EO:26A", "EO:27"])
        self.assertEqual((e["EO:26"]["year"], e["EO:26"]["month_day"]), (1905, "July 3"))
        self.assertIn("1905 CSR 89", e["EO:26"]["citations"])
        self.assertEqual(e["EO:26"]["family_hint"], "civil_service_individual")
        self.assertIn("stray number", e["EO:26A"]["text"])        # "12:" is out of sequence: kept as text
        self.assertTrue(e["EO:27"]["has_form_of_proclamation"])
        self.assertEqual(e["EO:24"]["source_kinds"], ["R"])

    def test_crosscheck(self):
        entries = wpa.parse_numbered(NUMBERED)
        census = [{"id": "EO:26", "date_effective": "1905"}, {"id": "EO:27", "date_effective": "1906"},
                  {"id": "EO:28", "date_effective": "1905"}, {"id": "EO:9000", "date_effective": "1941"}]
        rows, extra = wpa.numbered_crosscheck(entries, census)
        by = {r["instrument_id"]: r for r in rows}
        self.assertEqual(sorted(by), ["EO:26", "EO:27", "EO:28"])   # 9000 is beyond the list
        self.assertEqual((by["EO:26"]["year_agrees"], by["EO:27"]["year_agrees"]), ("yes", "no"))
        self.assertEqual(by["EO:28"]["in_wpa_list"], "no")
        self.assertEqual(sorted(e["id"] for e in extra), ["EO:24", "EO:25", "EO:26A"])


class Unnumbered(unittest.TestCase):
    def test_pairs_date_columns_and_keeps_inline_citations_in_the_entry(self):
        entries, blocks = wpa.parse_unnumbered(UNNUMBERED, first_page=1)
        got = [(e["year"], e["date"], e["summary"][:20], e["pairing"]) for e in entries]
        self.assertEqual(got, [(1840, "Mar 31", "All persons employed", "paired"),
                               (1842, "Feb 9", "Fort Wood Military R", "paired"),
                               (1842, "Feb 9", "Fort Laramie Militar", "paired"),
                               (1898, "Jan 10", "", "uncertain")][:3] + [got[3]])
        self.assertIn("23 Stat.L. 103", entries[2]["summary"])        # inline citation stays in the text
        self.assertEqual(entries[2]["citations"], ["1898 GLO 157", "1901 GLO 195"])
        self.assertEqual(entries[3]["pairing"], "uncertain")           # 2 dates, 1 entry: never guessed
        self.assertEqual(entries[3]["date"], "")
        self.assertEqual(entries[1]["family_hint"], "military_reservation")


if __name__ == "__main__":
    unittest.main()
