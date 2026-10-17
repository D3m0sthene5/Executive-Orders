import unittest

import eo_refs


def nums(text):
    return [(h["number"], h["suffix"]) for h in eo_refs.find_eo_refs(text)]


class FindRefs(unittest.TestCase):
    def test_common_forms(self):
        self.assertEqual(nums("Ex. Ord. No. 10450, Apr. 27, 1953"), [(10450, "")])
        self.assertEqual(nums("see Executive Order 12291 of February 17, 1981"), [(12291, "")])
        self.assertEqual(nums("executive order No. 9066"), [(9066, "")])
        self.assertEqual(nums("under E.O. 12866, 58 FR 51735, 3 CFR, 1993 Comp., p. 638"), [(12866, "")])
        self.assertEqual(nums("E. O. 10450 applies"), [(10450, "")])
        self.assertEqual(nums("EO 13526 governs"), [(13526, "")])
        self.assertEqual(nums("Executive Order Numbered 10577"), [(10577, "")])

    def test_lists(self):
        self.assertEqual(nums("Ex. Ord. Nos. 10450 and 10491 were"), [(10450, ""), (10491, "")])
        self.assertEqual(nums("Executive Orders 12866, 13563, and 13771"), [(12866, ""), (13563, ""), (13771, "")])
        # a list stops at FR / CFR citations
        self.assertEqual(nums("E.O. 13224, 66 FR 49079"), [(13224, "")])

    def test_suffixes(self):
        self.assertEqual(nums("Ex. Ord. No. 10026-A"), [(10026, "A")])
        self.assertEqual(nums("Ex. Ord. No. 10026–A"), [(10026, "A")])
        self.assertEqual(nums("E.O. 7933a"), [(7933, "a")])

    def test_no_false_hits(self):
        self.assertEqual(nums("Executive Order 12,866"), [])
        self.assertEqual(nums("GEO 123 and video 4 and an executive order of May 1, 1905"), [])
        self.assertEqual(nums("the geo 12345 field"), [])
        self.assertEqual(nums("Reorg. Plan No. 3 of 1970"), [])
        # State orders written year-number, or with a year in brackets
        self.assertEqual(nums("Executive Orders 1991-31 and 1995-18"), [])
        self.assertEqual(nums("Executive Order No. 2 (1995), part I(C)"), [])
        # a year after "and" is not a second order number
        self.assertEqual(nums("Ex. Ord. No. 6728, and 1940 Reorg. Plan No. III"), [(6728, "")])

    def test_state_caution(self):
        text = "approved by the Governor under Executive Order 10 of the State of Vermont"
        h = eo_refs.find_eo_refs(text)[0]
        self.assertEqual(eo_refs.caution(text, h["start"], h["end"]), "possible_state_local_or_tribal_order")
        text = "Agencies shall comply with Executive Order 12866."
        h = eo_refs.find_eo_refs(text)[0]
        self.assertEqual(eo_refs.caution(text, h["start"], h["end"]), "")

    def test_universe_mapping(self):
        u = eo_refs.Universe(["EO:10450", "EO:10026A", "EO:7933a"], {"EO:10450": "no"})
        self.assertEqual(u.map(10450), ("EO:10450", "exact"))
        self.assertEqual(u.map(10026, "A")[0], "EO:10026A")
        self.assertEqual(u.map(7933, "a")[0], "EO:7933a")
        self.assertEqual(u.map(99999)[0], "")
        self.assertEqual(u.status("EO:10450"), "no")


class Events(unittest.TestCase):
    def test_revoked_status_line(self):
        line = ("Ex. Ord. No. 13199, Jan. 29, 2001, 66 F.R. 8499, as amended by Ex. Ord. No. 13498, § 1, Feb. 5, 2009, "
                "74 F.R. 6533, which established the Office, was revoked by Ex. Ord. No. 13831, § 4, May 3, 2018, 83 F.R. 20717, set out below.")
        ev = eo_refs.editorial_events(line)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["subject"]["number"], 13199)  # not the amending order
        self.assertEqual(ev[0]["verb"], "revoked")
        self.assertEqual(ev[0]["actor"]["ref"]["number"], 13831)
        self.assertEqual(ev[0]["actor"]["date"], "2018-05-03")
        self.assertEqual(ev[0]["actor"]["fr"], "83 F.R. 20717")
        self.assertEqual(eo_refs.status_line_kind(line), "ended_status_line")

    def test_semicolon_list_does_not_split_subject(self):
        line = ("Ex. Ord. No. 11230, June 28, 1965, 30 F.R. 8847, as amended by Ex. Ord. No. 11275, Mar. 31, 1966, 31 F.R. 5283; "
                "Ex. Ord. No. 11294, Aug. 4, 1966, 31 F.R. 10601, delegating functions, was superseded by Ex. Ord. No. 11609, "
                "July 22, 1971, 36 F.R. 13747.")
        ev = eo_refs.editorial_events(line)
        self.assertEqual(ev[0]["subject"]["number"], 11230)
        self.assertEqual(ev[0]["verb"], "superseded")

    def test_partial_scope(self):
        line = ("Ex. Ord. No. 11713, Apr. 21, 1973, 38 F.R. 10069, which related to delegation, was revoked by section 1-404 "
                "of Ex. Ord. No. 12215, May 27, 1980, 45 F.R. 36045.")
        ev = eo_refs.editorial_events(line)[0]
        self.assertEqual(ev["actor"]["ref"]["number"], 12215)
        self.assertIn("1-404", ev["actor"]["scope_text"])

    def test_amendments_and_printed(self):
        line = ("Ex. Ord. No. 12028, Dec. 12, 1977, 42 F.R. 62895, as amended by Ex. Ord. No. 12122, Feb. 26, 1979, "
                "44 F.R. 11197; Pub. L. 101–509, Nov. 5, 1990, 104 Stat. 1427, provided:")
        am = eo_refs.amendments_listed(line)
        self.assertEqual([a["kind"] for a in am], ["executive_order", "statute"])
        self.assertEqual(am[0]["ref"]["number"], 12122)
        self.assertEqual(am[0]["date"], "1979-02-26")
        self.assertEqual(am[1]["publ"], "Pub. L. 101-509")
        self.assertEqual(eo_refs.status_line_kind(line), "printed_text")

    def test_brackets(self):
        b = eo_refs.bracket_events("Sec. 2. [Revoked by Ex. Ord. No. 14000, § 4, Jan. 2, 2021, 86 F.R. 100.]")
        self.assertEqual(len(b), 1)
        self.assertEqual(b[0]["verb"], "revoked")
        self.assertEqual(b[0]["actor"]["ref"]["number"], 14000)
        self.assertEqual(b[0]["actor"]["date"], "2021-01-02")
        self.assertIn("Sec. 2.", b[0]["scope_text"])

    def test_dates(self):
        self.assertEqual(eo_refs.parse_date("x Sept. 30, 2015, y"), "2015-09-30")
        self.assertEqual(eo_refs.parse_date("June 5, 1951"), "1951-06-05")
        self.assertIsNone(eo_refs.parse_date("no date"))


if __name__ == "__main__":
    unittest.main()
