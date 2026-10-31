"""Offline tests: python3 -I jobs/jacquard/test_jacquard.py   (or python -m unittest discover -s jobs/jacquard)"""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import jacquard as J  # noqa: E402

TYPES_COLS = ["instrument_id", "number", "year", "type", "class", "rule_id", "confidence", "sources_agreeing", "wpa_type",
              "app_type", "text_type", "evidence_source", "evidence_pattern", "evidence_match", "wpa_summary", "app_title",
              "text_path", "text_grade", "wpa_hint"]
REG_COLS = ["instrument_id", "provisional_substantive_status", "decision_origin"] + list(J.TEMPLATE_ROW)

CFG = {"schema": "x", "seed": "test-seed", "sample_size": 10, "full_review_max": 15,
       "lots": [{"lot": "A", "type": "alpha", "rule_id": "TR-A", "confidence": ["high", "medium"], "max_year": 1917},
                {"lot": "B", "type": "beta", "rule_id": "TR-B", "confidence": ["high"]}],
       "control_types": {"A": ["gamma"], "B": ["gamma"]}}


def make_repo(root, n_alpha=40, n_beta=6, n_gamma=20):
    root = Path(root)
    (root / "texts").mkdir()
    (root / "jobs/x1-class-engine/output").mkdir(parents=True)
    (root / "research/progress").mkdir(parents=True)
    rows = []

    def add(iid, typ, rule, conf="high", year="1910", text=True, header=False):
        rel = f"texts/{iid.replace(':', '_')}.txt"
        if text:
            body = f"Order {iid.split(':')[1]} body text for {typ}. " * 5
            (root / rel).write_text(("# order: %s  (WPA 1944)\n----- EXACT SLICE -----\n" % iid if header else "") + body, encoding="utf-8")
        rows.append({c: "" for c in TYPES_COLS} | {"instrument_id": iid, "number": iid.split(":")[1], "year": year, "type": typ,
                     "rule_id": rule, "confidence": conf, "text_path": rel if text else "", "app_title": "Title number " + iid.split(":")[1]})

    for i in range(n_alpha):
        add(f"EO:{100 + i}", "alpha", "TR-A", header=(i % 5 == 0))
    add("EO:900", "alpha", "TR-A", year="1925")          # too late
    add("EO:901", "alpha", "TR-A", conf="low")           # confidence out
    add("EO:902", "alpha", "TR-A", text=False)           # no text
    add("EO:903", "alpha", "TR-A")                       # in register
    for i in range(n_beta):
        add(f"EO:{300 + i}", "beta", "TR-B")
    for i in range(n_gamma):
        add(f"EO:{500 + i}", "gamma", "TR-G", conf="low")
    with open(root / J.TYPES_REL, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=TYPES_COLS)
        w.writeheader()
        w.writerows(rows)
    with open(root / J.REGISTER_REL, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=REG_COLS)
        w.writeheader()
        w.writerow({c: "x" for c in REG_COLS} | {"instrument_id": "EO:903", "provisional_substantive_status": "no"})
        w.writerow({c: "x" for c in REG_COLS} | {"instrument_id": "EO:500", "provisional_substantive_status": "yes"})


def good_review(item_id, text, **over):
    words = text.split()
    rev = {"item_id": item_id, "identity": "match", "identity_evidence": "number and date agree", "type_fits": True,
           "outliers_found": [], "status_no_supported": True, "basis": "rule", "end_or_bound": "one-time act",
           "operative_quote": " ".join(words[:4]), "notes": ""}
    rev.update(over)
    return rev


def write_reviews(reviews_dir, packets_dir, key, overrides=None, kinds_caught=True):
    """Write a reviewer's answers: right on everything (controls caught) unless overridden per item_id."""
    overrides = overrides or {}
    for lot in key["lots"]:
        for bdir in sorted((Path(packets_dir) / lot).glob("batch-*")):
            lines = []
            for line in (bdir / "items.jsonl").read_text().splitlines():
                it = json.loads(line)
                iid = it["item_id"]
                text = (bdir / "texts" / f"{iid}.txt").read_text()
                kind = key["items"][iid]["kind"]
                rev = good_review(iid, text)
                if kind == "intruder" and kinds_caught:
                    rev.update(type_fits=False, status_no_supported=False)
                if kind == "text_swap" and kinds_caught:
                    rev.update(identity="mismatch", status_no_supported=False, operative_quote="")
                rev.update(overrides.get(iid, {}))
                if rev is not None:
                    lines.append(json.dumps(rev))
            out = Path(reviews_dir) / lot
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{bdir.name}.jsonl").write_text("\n".join(lines) + "\n")


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.repo, self.out, self.packets, self.keyf, self.reviews = t / "repo", t / "out", t / "packets", t / "key/CONTROL_KEY.json", t / "reviews"
        self.repo.mkdir()
        make_repo(self.repo)
        J.step_select(self.repo, self.out, CFG)
        self.samples = J.step_sample(self.out, CFG)

    def tearDown(self):
        self.tmp.cleanup()

    def packets_and_key(self):
        key, errors, warnings = J.step_packets(self.repo, self.out, CFG, self.packets, self.keyf)
        return key, errors, warnings

    # -- selection
    def test_selection_filters(self):
        members, counts, cal = J.select_lots(self.repo, CFG)
        ids = [r["instrument_id"] for r in members["A"]]
        self.assertEqual(len(ids), 40)
        for bad in ("EO:900", "EO:901", "EO:902", "EO:903"):
            self.assertNotIn(bad, ids)
        self.assertEqual((counts["A"]["year_excluded"], counts["A"]["confidence_excluded"], counts["A"]["text_missing"],
                          counts["A"]["already_in_register"]), (1, 1, 1, 1))
        self.assertEqual(len(members["B"]), 6)
        row = [c for c in cal if c["lot"] == "A"][0]
        self.assertEqual((row["in_register"], row["register_no"], row["register_yes"]), (1, 1, 0))

    # -- sampling
    def test_sampling_deterministic_and_modes(self):
        ids = [f"EO:{i}" for i in range(100)]
        a, b = J.sample_lot(CFG, "A", ids), J.sample_lot(CFG, "A", list(reversed(ids)))
        self.assertEqual(a, b)
        self.assertEqual(a["mode"], "sampled")
        self.assertEqual(len(set(a["sampled_ids"])), 10)
        self.assertNotEqual(a["sampled_ids"], J.sample_lot(CFG, "B", ids)["sampled_ids"])
        self.assertNotEqual(a["sampled_ids"], J.sample_lot(dict(CFG, seed="other"), "A", ids)["sampled_ids"])
        small = J.sample_lot(CFG, "B", ids[:15])
        self.assertEqual((small["mode"], small["sample_n"]), ("full", 15))
        self.assertEqual(self.samples["lots"]["A"]["mode"], "sampled")
        self.assertEqual(self.samples["lots"]["B"]["mode"], "full")

    def test_real_config_sample_size_and_draw_is_repeatable(self):
        cfg = J.load_config()
        ids = [f"EO:{i}" for i in range(858)]
        s = J.sample_lot(cfg, "L1", ids)
        self.assertEqual(s["sample_n"], 59)
        self.assertEqual(s, J.sample_lot(cfg, "L1", ids))

    # -- statistics
    def test_clopper_pearson(self):
        self.assertLess(J.cp_upper(0, 59), 0.05)
        self.assertAlmostEqual(J.cp_upper(0, 59), 1 - 0.05 ** (1 / 59), places=12)
        self.assertGreater(J.cp_upper(0, 58), 0.05)
        import math
        p1 = J.cp_upper(1, 59)                      # defining property: P(X <= 1 | n=59, p) = 0.05
        self.assertAlmostEqual(sum(math.comb(59, i) * p1 ** i * (1 - p1) ** (59 - i) for i in range(2)), 0.05, places=9)
        self.assertEqual(J.cp_upper(5, 5), 1.0)

    # -- quote normalization
    def test_quote_normalization(self):
        text = "The  President\n\tdirects that\r\nJohn   Doe be   exempted."
        self.assertTrue(J.quote_in_text("directs that John Doe", text))
        self.assertTrue(J.quote_in_text("  The President directs ", text))
        self.assertFalse(J.quote_in_text("John Roe", text))
        self.assertFalse(J.quote_in_text("   ", text))

    def test_strip_preamble(self):
        raw = "# order: EO:28 (WPA)\n# x\n----- EXACT SLICE -----\nbody line\n"
        self.assertEqual(J.strip_preamble(raw), "body line\n")
        raw2 = "# Copy: x\n# Source: y\n----- EXACT SOURCE TEXT -----\nExecutive Order 5077\n"
        self.assertEqual(J.strip_preamble(raw2), "Executive Order 5077\n")
        self.assertEqual(J.strip_preamble("plain text\n# not a header\n"), "plain text\n# not a header\n")

    # -- packets
    def test_packets_blinded_and_structured(self):
        key, errors, warnings = self.packets_and_key()
        self.assertEqual(errors, [])
        a = key["lots"]["A"]
        self.assertEqual((a["genuine"], a["controls"], a["batches"]), (10, J.control_count(10), 1))
        self.assertEqual(key["lots"]["B"]["controls"], 2)
        kinds = [v["kind"] for v in key["items"].values() if v["lot"] == "A"]
        self.assertEqual(sorted(set(kinds)), ["genuine", "intruder", "text_swap"])
        # blinding: no listed word and no answer-key instrument id anywhere under the packets directory
        for p in self.packets.rglob("*"):
            self.assertIsNone(__import__("re").search("control|intruder|swap|planted", str(p.relative_to(self.packets)), 2))
            if p.is_file():
                body = p.read_text()
                for w in J.FORBIDDEN_WORDS:
                    self.assertNotIn(w, body.lower(), f"{w} in {p}")
                self.assertNotIn("EO:", body)           # preamble with 'order: EO:n' was stripped
        self.assertFalse(self.keyf.resolve().is_relative_to(self.packets.resolve()))
        for v in key["items"].values():
            if v["kind"] == "text_swap":
                self.assertNotEqual(v["instrument_id"], v["text_instrument_id"])
            if v["kind"] == "intruder":
                self.assertEqual(v["instrument_id"], v["text_instrument_id"])
                self.assertEqual(v["instrument_id"].split(":")[1][0], "5")        # gamma pool
        self.assertNotIn("EO:500", {v["instrument_id"] for v in key["items"].values()})   # in register: not eligible

    def test_packets_batches_and_truncation(self):
        cfg = dict(CFG, sample_size=10, full_review_max=15)
        (self.repo / "texts/EO_100.txt").write_text("x " * 10000)
        J.step_packets(self.repo, self.out, cfg, self.packets, self.keyf)
        key = json.loads(self.keyf.read_text())
        hit = [i for i, v in key["items"].items() if v["lot"] == "A" and v["instrument_id"] == "EO:100" and v["kind"] != "intruder"]
        for iid in hit:
            if key["items"][iid]["text_instrument_id"] == "EO:100":
                t = (self.packets / "A" / key["items"][iid]["batch"] / "texts" / f"{iid}.txt").read_text()
                self.assertIn("[TRUNCATED: original 20000 characters]", t)
                self.assertLess(len(t), 12100)
        # lot of 40 with sample_size > 20 gives several batches of at most 20
        bigcfg = dict(CFG, sample_size=30, full_review_max=15)
        J.step_sample(self.out, bigcfg)
        key, errors, _ = J.step_packets(self.repo, self.out, bigcfg, self.packets, self.keyf)
        self.assertEqual(errors, [])
        sizes = [len(list((self.packets / "A").glob("batch-*"))), key["lots"]["A"]["items"]]
        self.assertEqual(sizes, [2, 32])
        for b in (self.packets / "A").glob("batch-*"):
            self.assertLessEqual(len((b / "items.jsonl").read_text().splitlines()), 20)
        # a text swap never shares a batch with its own twins when several batches exist
        for v in key["items"].values():
            if v["kind"] == "text_swap" and v["lot"] == "A":      # lot B fits in one batch: separation impossible
                self.assertTrue(v["twins_in_other_batches"])
            if v["kind"] == "text_swap" and v["lot"] == "B":
                self.assertFalse(v["twins_in_other_batches"])

    def test_packets_deterministic(self):
        k1, _, _ = self.packets_and_key()
        k2, _, _ = J.step_packets(self.repo, self.out, CFG, self.packets, self.keyf)
        self.assertEqual(k1, k2)

    # -- verify
    def verify(self, overrides=None, **kw):
        key, _, _ = self.packets_and_key()
        write_reviews(self.reviews, self.packets, key, overrides, **kw)
        return key, J.step_verify(self.reviews, self.keyf, self.packets, self.out)

    def first(self, key, lot, kind):
        return sorted(i for i, v in key["items"].items() if v["lot"] == lot and v["kind"] == kind)[0]

    def test_all_caught_batch_valid(self):
        key, res = self.verify()
        self.assertEqual({b["status"] for b in res["lots"]["A"]["batches"].values()}, {"valid"})
        self.assertEqual(res["lots"]["A"]["failures"], [])
        self.assertEqual(len(res["lots"]["A"]["upheld"]), 10)

    def test_caught_intruder_by_either_signal(self):
        key = self.packets_and_key()[0]
        iid = self.first(key, "A", "intruder")
        for over in ({"type_fits": False}, {"status_no_supported": False}):
            write_reviews(self.reviews, self.packets, key, {iid: dict(over, type_fits=over.get("type_fits", True),
                          status_no_supported=over.get("status_no_supported", True))})
            res = J.step_verify(self.reviews, self.keyf, self.packets, self.out)
            self.assertEqual(res["lots"]["A"]["batches"]["batch-01"]["controls"][iid]["caught"], True)

    def test_missed_swap_invalidates_batch(self):
        key = self.packets_and_key()[0]
        swap = self.first(key, "A", "text_swap")
        write_reviews(self.reviews, self.packets, key, {swap: {"identity": "match", "status_no_supported": True,
                      "operative_quote": "Order"}})
        res = J.step_verify(self.reviews, self.keyf, self.packets, self.out)["lots"]["A"]
        self.assertEqual(res["batches"]["batch-01"]["status"], "invalid")
        self.assertEqual(res["batches"]["batch-01"]["missed_controls"], [swap])
        self.assertEqual(res["rereview_batches"], ["batch-01"])
        self.assertEqual((res["upheld"], res["failures"]), ([], []))        # genuine reviews discarded
        self.assertEqual(len(res["discarded_genuine_items"]), 10)

    def test_missed_intruder_invalidates_batch(self):
        key = self.packets_and_key()[0]
        iid = self.first(key, "B", "intruder")
        write_reviews(self.reviews, self.packets, key, {iid: {"type_fits": True, "status_no_supported": True}})
        res = J.step_verify(self.reviews, self.keyf, self.packets, self.out)["lots"]["B"]
        self.assertEqual(res["batches"]["batch-01"]["status"], "invalid")

    def test_structural_errors_make_batch_incomplete(self):
        key = self.packets_and_key()[0]
        write_reviews(self.reviews, self.packets, key)
        f = self.reviews / "A" / "batch-01.jsonl"
        lines = f.read_text().splitlines()
        f.write_text("\n".join(lines[1:] + [lines[2]]) + "\n")             # one missing, one duplicated
        res = J.step_verify(self.reviews, self.keyf, self.packets, self.out)["lots"]["A"]
        self.assertEqual(res["batches"]["batch-01"]["status"], "incomplete")
        (self.reviews / "B" / "batch-01.jsonl").unlink()
        res = J.step_verify(self.reviews, self.keyf, self.packets, self.out)["lots"]["B"]
        self.assertEqual(res["batches"]["batch-01"]["status"], "incomplete")

    def test_genuine_failure_reasons(self):
        key = self.packets_and_key()[0]
        gen = sorted(i for i, v in key["items"].items() if v["lot"] == "A" and v["kind"] == "genuine")
        over = {gen[0]: {"operative_quote": "words that are not in the text"}, gen[1]: {"outliers_found": ["odd"]},
                gen[2]: {"identity": "cannot_tell"}, gen[3]: {"type_fits": "yes"}, gen[4]: {"status_no_supported": False}}
        write_reviews(self.reviews, self.packets, key, over)
        res = J.step_verify(self.reviews, self.keyf, self.packets, self.out)["lots"]["A"]
        fails = {f["item_id"]: " ".join(f["reasons"]) for f in res["failures"]}
        self.assertEqual(set(fails), set(gen[:5]))
        self.assertIn("operative_quote_not_in_text", fails[gen[0]])
        self.assertIn("outliers_flagged", fails[gen[1]])
        self.assertIn("identity_cannot_tell", fails[gen[2]])
        self.assertIn("schema", fails[gen[3]])
        self.assertEqual(len(res["upheld"]), 5)

    def test_quote_with_changed_whitespace_passes(self):
        key = self.packets_and_key()[0]
        gen = self.first(key, "A", "genuine")
        text = (self.packets / "A" / key["items"][gen]["batch"] / "texts" / f"{gen}.txt").read_text()
        quote = "  ".join(text.split()[:3]) + "\n"
        write_reviews(self.reviews, self.packets, key, {gen: {"operative_quote": quote}})
        res = J.step_verify(self.reviews, self.keyf, self.packets, self.out)["lots"]["A"]
        self.assertIn(gen, [u["item_id"] for u in res["upheld"]])

    # -- acceptance
    def accept(self, overrides=None, **kw):
        key, _ = self.verify(overrides, **kw)
        return key, J.step_accept(self.out)

    def test_sampled_zero_failures_accepts_all_members(self):
        key, acc = self.accept()
        a = acc["lots"]["A"]
        self.assertEqual((a["status"], a["mode"], a["failures"]), ("accepted", "sampled", 0))
        self.assertLess(a["upper_bound_95"], 0.31)       # n=10: 1 - 0.05**0.1
        self.assertEqual(len(a["adoptable_ids"]), 40)
        self.assertEqual(a["adoption_route"], "sampled")

    def test_sampled_one_failure_rejects_lot(self):
        key = self.packets_and_key()[0]
        gen = self.first(key, "A", "genuine")
        key, acc = self.accept({gen: {"outliers_found": ["unusual"]}})
        a = acc["lots"]["A"]
        self.assertEqual((a["status"], a["failures"]), ("rejected", 1))
        self.assertEqual(len(a["adoptable_ids"]), 9)      # only individually upheld sampled members
        self.assertNotIn(key["items"][gen]["instrument_id"], a["adoptable_ids"])
        rows = list(csv.DictReader(open(self.out / "INDIVIDUAL_REVIEW.csv")))
        self.assertEqual([r["instrument_id"] for r in rows], [key["items"][gen]["instrument_id"]])

    def test_full_mode_individual_adoption(self):
        key = self.packets_and_key()[0]
        gen = self.first(key, "B", "genuine")
        key, acc = self.accept({gen: {"status_no_supported": False}})
        b = acc["lots"]["B"]
        self.assertEqual((b["status"], b["mode"], b["failures"]), ("full_review_complete", "full", 1))
        self.assertEqual(len(b["adoptable_ids"]), 5)
        self.assertEqual(b["individual_review_ids"], [key["items"][gen]["instrument_id"]])

    def test_missed_control_makes_lot_pending(self):
        key = self.packets_and_key()[0]
        swap = self.first(key, "A", "text_swap")
        key, acc = self.accept({swap: {"identity": "match"}})
        self.assertEqual(acc["lots"]["A"]["status"], "pending_rereview")
        self.assertEqual(acc["lots"]["A"]["adoptable_ids"], [])
        self.assertEqual(acc["lots"]["B"]["status"], "full_review_complete")

    # -- proposal
    def test_proposed_rows(self):
        self.accept()
        rows, skipped = J.step_propose(self.repo, self.out)
        self.assertEqual((len(rows), skipped), (46, []))
        text = (self.out / "PROPOSED_STATUS_ROWS.csv").read_text()
        reg_header = (self.repo / J.REGISTER_REL).read_text().splitlines()[0]
        self.assertEqual(text.splitlines()[0], reg_header)
        got = list(csv.DictReader(open(self.out / "PROPOSED_STATUS_ROWS.csv")))
        r = [x for x in got if x["instrument_id"] == "EO:100"][0]
        self.assertEqual(r["provisional_substantive_status"], "no")
        self.assertEqual(r["decision_origin"], "jacquard-A-2026-10-31:ai_class_status (sampled review "
                         "research/excavator/jacquard-2026-10-31/A; ruling 2026-10-31-jacquard-and-working-texts)")
        self.assertEqual((r["human_certified_by_this_release"], r["stage17_assessment"]), ("no", "none"))
        self.assertIn("full review", [x for x in got if x["instrument_id"] == "EO:300"][0]["decision_origin"])
        self.assertNotIn("EO:903", {x["instrument_id"] for x in got})
        self.assertEqual(sorted(x["instrument_id"] for x in got), sorted({x["instrument_id"] for x in got}))


if __name__ == "__main__":
    unittest.main()
