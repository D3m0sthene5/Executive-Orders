"""LAMBERTINI tests (standard library only).  Run:  python3 -I jobs/lambertini/test_lambertini.py

Claims proved: the class rules route every unsafe case to a reader (S0 only when the acting text is held,
names the order and holds no savings or transfer wording); one packet is built per acting order and shared by
all its targets; short numbers are not "named" by page numbers; WPA OCR cites ('E. 0. [9]') are found;
coverage is counted; outputs never contain a claim or an EXHAUSTED line; the probe draw is deterministic.
"""
import contextlib, io, json, os, sys, tempfile, unittest
sys.dont_write_bytecode = True
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lambertini as L  # noqa: E402

STEPS = ["provisional_status", "original_text", "clause_inventory", "ending_or_current_basis",
         "savings_residuals", "counterevidence", "shared_sources", "opus_media"]


def put(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def readiness(rows):
    cols = ["instrument_id", "provisional_status", "ready_for_human_review", "blockers"] + ["step_" + s for s in STEPS]
    out = [",".join(cols)]
    for iid, st, ready, bl, open_ in rows:
        out.append(",".join([iid, st, ready, bl] + ["open" if s in open_ else "done" for s in STEPS]))
    return "\n".join(out) + "\n"


def draft(iid, status, actor=None, lead=False, conflict=False, later=False):
    ends = [{"proposal": {"actor": actor, "date": "1986-02-25", "mechanism": "revocation"}}] if actor else []
    return json.dumps({"instrument_id": iid, "_draft": {"provisional_status": status, "conflicts":
                       [{"code": "X"}] if conflict else [], "proposals": {
                           "whole_order_end": ends, "savings_leads": [{"phrase": "x"}] if lead else [],
                           "later_events": [{"x": 1}] if later else []}}})


def frag(iid, path):
    return json.dumps({"instrument_id": iid, "kind": "original_representation", "data": {
        "needs_page_check": False, "text_path": path, "url": "https://www.govinfo.gov/x.pdf",
        "sha256": "a" * 64, "page_or_item": "51 FR 1, PDF page 1", "signing_date": "1986-02-25"}})


CLAIM_STEPS = {"clause_inventory", "ending_or_current_basis", "savings_residuals"}


def make_repo(root):
    put(root, L.P["readiness"], readiness([
        ("EO:9001", "no", "no", "A", CLAIM_STEPS),             # named by EO:12553, clean -> S0
        ("EO:9002", "no", "no", "A", CLAIM_STEPS),             # named near a savings phrase -> S2
        ("EO:9003", "no", "no", "A", CLAIM_STEPS),             # acting text not held -> S8
        ("EO:9004", "no", "no", "A", CLAIM_STEPS),             # conflict -> S4
        ("EO:36", "no", "no", "NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE", CLAIM_STEPS | {"counterevidence"}),
        ("EO:40", "no", "no", "NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE", CLAIM_STEPS | {"counterevidence"}),
        ("EO:9500", "yes", "no", "A", {"clause_inventory", "ending_or_current_basis", "savings_residuals"}),
        ("EO:9600", "no", "yes", "", set()),                   # ready: calibration only
        ("EO:12553", "no", "no", "A", CLAIM_STEPS),
    ]))
    put(root, L.P["drafts"], "\n".join([
        draft("EO:9001", "no", "EO:12553"), draft("EO:9002", "no", "EO:12553"),
        draft("EO:9003", "no", "EO:13000"), draft("EO:9004", "no", "EO:12553", conflict=True),
        draft("EO:36", "no", "EO:12553"), draft("EO:40", "no"), draft("EO:9500", "yes"),
        draft("EO:9600", "no", "EO:12553"), draft("EO:12553", "no")]) + "\n")
    body = ("Executive Order 12553. Revocation of certain orders. Executive Order No. 9001 of 1942 is revoked. "
            + "x" * 3000 + " Executive Order No. 9002 is revoked; rights accrued thereunder shall not be affected "
            "and pending proceedings shall continue. " + "y" * 3000 + " Executive Order No. 9004 is revoked. "
            "Executive Order No. 9600 is revoked. Page 36 of the register.")
    put(root, L.P["fr_dir"] + "/texts/EO_12553.txt", body.replace("shall not be affected", "shall not affect"))
    put(root, L.P["fr_dir"] + "/texts/EO_9001.txt", "The Secretary shall prescribe rules.")
    put(root, L.P["fr_fragments"], frag("EO:12553", "texts/EO_12553.txt") + "\n" + frag("EO:9001", "texts/EO_9001.txt") + "\n")
    put(root, "research/readiness/claims/claude-x.jsonl", json.dumps(
        {"instrument_id": "EO:9600", "savings_residuals": {"state": "none_after_bounded_search"}}) + "\n")
    put(root, L.P["le_edges"], "edge_id,acting_id,target_id,mechanism,date_candidate,evidence_type\n"
                               "LE-1,EO:7000,EO:36,revocation,1936-01-01,order_text\n")
    put(root, L.P["le_scan"], "acting_id,source_id\n" + "".join("EO:%d,s\n" % n for n in range(37, 7532, 2)))
    put(root, L.P["cl_orders"], "instrument_id,usc_mentions,ecfr_mentions\nEO:40,0,0\n")
    put(root, L.P["wpa"], "id,number,suffix,year,month_day,page,family_hint,has_form_of_proclamation,"
                          "source_kinds_joined,citations_joined,text\n"
                          "EO:36,36,,1894,Nov 2,22,x,False,,,Civil Service Rules amended.\n"
                          "EO:40,40,,1894,Dec 5,22,x,False,,,Rules for posts.\n"
                          "EO:41,41,,1895,Jan 3,22,x,False,,,\"E. 0. [36] of Nov. 2, 1894, amended to except a clerk.\"\n")
    put(root, L.P["le_status"], json.dumps({"finished_utc": "2026-10-19T18:34:58Z"}))
    put(root, L.P["cl_status"], json.dumps({"finished_utc": "2026-10-17T20:28:32Z"}))


class Pure(unittest.TestCase):
    base = dict(actors={"EO:12553"}, acting_held=True, named=True, savings_anywhere=False, savings_near=False,
                transfer_near=False, own_transfer=False, own_lead=False, conflict=False)

    def cls(self, **kw):
        return L.classify_no(dict(self.base, **kw))

    def test_s0_only_when_everything_clean(self):
        self.assertEqual(self.cls(), ("S0_none_candidate", "none_after_bounded_search"))
        for kw, want in [({"actors": set()}, "S9_no_end_candidate"), ({"actors": {"EO:1", "EO:2"}}, "S9_multiple_acting"),
                         ({"actors": {"PLO:5"}}, "S8_acting_not_EO"), ({"acting_held": False}, "S8_acting_text_not_held"),
                         ({"named": False}, "S8_acting_text_does_not_name_order"), ({"conflict": True}, "S4_conflict"),
                         ({"own_lead": True}, "S3_own_savings_lead"), ({"savings_near": True, "savings_anywhere": True},
                                                                       "S2_savings_phrase_near"),
                         ({"savings_anywhere": True}, "S2b_savings_phrase_elsewhere_in_acting"),
                         ({"transfer_near": True}, "S1_transfer_wording"), ({"own_transfer": True}, "S1_transfer_wording")]:
            c, sug = self.cls(**kw)
            self.assertEqual(c, want, kw)
            self.assertNotEqual(sug, "none_after_bounded_search", kw)

    def test_yes(self):
        f = dict(conflict=False, own_lead=False, later_events=False)
        self.assertEqual(L.classify_yes(f)[0], "Y0_no_later_events")
        self.assertEqual(L.classify_yes(dict(f, later_events=True))[1], "review")

    def test_mentions_and_ocr_cites(self):
        t = "Executive Order No. 9001 revoked. Page 36."
        self.assertTrue(L.mention_spans(t, 9001)[0]["strict"])
        self.assertFalse(L.mention_spans(t, 36)[0]["strict"])
        self.assertEqual(L.mention_spans("No. 90011", 9001), [])
        self.assertTrue(L.names_number("E. 0. [9] of Jan. 17, 1873, amended", 9))
        self.assertTrue(L.names_number("E. 0.s [983 and 1624] of Nov. 30, 1908", 1624))
        self.assertFalse(L.names_number("E. 0. [19] of Jan. 17, 1873", 9))
        self.assertTrue(L.wpa_date_regex((1905, 10, 13)).search("of Oct. 13,1905,prohibiting"))
        self.assertTrue(L.wpa_date_regex((1873, 1, 17)).search("of January 17, 1873"))
        self.assertIsNone(L.parse_wpa_date("1894", "Nov"))
        self.assertEqual(L.parse_wpa_date("1894", "Sept. 2"), (1894, 9, 2))

    def test_coverage(self):
        c = L.scan_coverage(7529, {7530, 7531})
        self.assertEqual((c["numbered_orders_after_it_before_1937"], c["texts_scanned"]), (2, 2))
        self.assertIsNone(L.scan_coverage(8000, set()))
        self.assertEqual(L.eo_number("EO:1234-A"), 1234)
        self.assertIsNone(L.eo_number("EO:UN:x"))


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = cls.tmp.name
        make_repo(cls.root)
        cls.out = os.path.join(cls.root, "out")
        with contextlib.redirect_stdout(io.StringIO()):
            cls.summary = L.build(cls.root, cls.out)
        cls.pre = {r["instrument_id"]: r for r in L.read_csv(os.path.join(cls.out, "SAVINGS_PREFILL.csv"))}
        cls.packets = list(L.jsonl(os.path.join(cls.out, "SAVINGS_PACKETS.jsonl")))
        cls.recs = {r["instrument_id"]: r for r in L.jsonl(os.path.join(cls.out, "COUNTEREVIDENCE_RECORDS.jsonl"))}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_one_packet_shared_by_targets(self):
        self.assertEqual([p["acting_id"] for p in self.packets], ["EO:12553"])
        p = self.packets[0]
        self.assertEqual(set(p["targets"]), {"EO:9001", "EO:9002", "EO:9004", "EO:36", "EO:9600"})
        self.assertEqual(len(p["text"]["text_sha256"]), 64)
        self.assertTrue(p["savings_phrases"])
        for k in ("source_url", "source_sha256", "page_or_item"):
            self.assertTrue(p["text"][k])

    def test_classes(self):
        c = {i: r["savings_class"] for i, r in self.pre.items()}
        self.assertEqual(c["EO:9001"], "S2b_savings_phrase_elsewhere_in_acting")  # the packet holds a savings phrase
        self.assertEqual(c["EO:9002"], "S2_savings_phrase_near")
        self.assertEqual(c["EO:9003"], "S8_acting_text_not_held")
        self.assertEqual(c["EO:9004"], "S4_conflict")
        self.assertEqual(c["EO:36"], "S8_acting_text_does_not_name_order")  # 'Page 36' is not a citation
        self.assertEqual(c["EO:40"], "S9_no_end_candidate")
        self.assertEqual(c["EO:9500"], "Y0_no_later_events")
        self.assertEqual(self.pre["EO:9600"]["claim_savings_state"], "none_after_bounded_search")
        self.assertIn("calibration_on_ready_claims", self.summary)

    def test_counterevidence_records(self):
        self.assertEqual(set(self.recs), {"EO:36", "EO:40"})
        r36, r40 = self.recs["EO:36"], self.recs["EO:40"]
        self.assertTrue(r36["draft_not_claim"])
        self.assertEqual(r36["counter_class"], "C1_contrary_or_wpa_lead")
        self.assertEqual(r36["leads"]["wpa"][0]["wpa_entry"], "EO:41")
        self.assertEqual(r40["counter_class"], "C0_no_lead_found")
        self.assertEqual(r40["coverage"]["numbered_orders_after_it_before_1937"], 7491)
        for e in r40["later_source_search_draft"]:
            self.assertTrue(e["repository"] and e["query_or_scope"] and e["checked_on"])
        self.assertTrue(r40["not_searched"])
        self.assertIn("owner ruling", r40["adequacy"])

    def test_pools_and_no_claims_written(self):
        lambc = Path(self.out, "POOL_LAMBC.txt").read_text().split()
        self.assertEqual(lambc, ["EO:40"])
        self.assertEqual(Path(self.out, "POOL_LAMBS.txt").read_text().split(), [])
        names = set(os.listdir(self.out))
        self.assertFalse({n for n in names if "claim" in n.lower() or "EXHAUSTED" in n})
        self.assertEqual(Path(self.root, "research/readiness/claims/claude-x.jsonl").read_text().count("\n"), 1)
        self.assertFalse(Path(self.root, "research/readiness/EXHAUSTED.jsonl").exists())

    def test_probe_deterministic(self):
        Path(self.out, "POOL_LAMBS.txt").write_text("EO:9001\nEO:9002\nEO:9004\n")
        runs = []
        for k in range(2):
            d = os.path.join(self.root, "probe%d" % k)
            with contextlib.redirect_stdout(io.StringIO()):
                L.main(["--repo", self.root, "--output", self.out, "probe", "--pool", "LAMBS", "--n", "2",
                        "--seed", "s1", "--out", d])
            runs.append(json.loads(Path(d, "PROBE_BATCH_LAMBS.json").read_text()))
        self.assertEqual([i["instrument_id"] for i in runs[0]["items"]], [i["instrument_id"] for i in runs[1]["items"]])
        self.assertEqual(runs[0]["n"], 2)
        self.assertTrue(all(i["packet"] for i in runs[0]["items"]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
