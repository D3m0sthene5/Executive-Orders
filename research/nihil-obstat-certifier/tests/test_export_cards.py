"""Tests for export_cards.py: a synthetic repository (filesystem and git modes) and the committed example cards.

Run:  py -I tests/test_export_cards.py
"""
import base64
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import export_cards as X  # noqa: E402

TEXT = ("EXECUTIVE ORDER 99999\n\nSection 1. The Admin\u00adistrator shall report to the Presi-\ndent every year.\n"
        "Sec. 2. Caf\u00e9 \u20ac inspections are   suspended until June 30, 1950.\nSec. 3. This order is revoked.\n")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def make_repo(root, ready="yes", bad_claim_sha=False):
    root = pathlib.Path(root)
    (root / "texts").mkdir(parents=True)
    raw = TEXT.encode("utf-8")
    (root / "texts/EO_99999.txt").write_bytes(raw)
    src = {"url": "https://www.govinfo.gov/content/pkg/FR-1950-01-01/pdf/FR-1950-01-01.pdf", "sha256": "a" * 64,
           "page_or_item": "15 FR 1", "text_path": "texts/EO_99999.txt", "text_sha256": sha(raw),
           "char_start": 0, "char_end": len(TEXT)}
    claim = {"schema": "eo-lifecycle-claim/v1", "instrument_id": "EO:99999", "whole_order_status": "no",
             "original_representation": dict(src, quote="EXECUTIVE ORDER 99999"),
             "operative_clauses": [
                 {"scope_id": "EO:99999#s1", "original_operative_text": "The Administrator shall report to the President every year.",
                  "original_source": dict(src), "state_at_cutoff": "terminated",
                  "first_end": {"date": "1950-06-30", "actor": "EO:99999", "mechanism": "own terms",
                                "source": dict(src, quote="suspended until June 30, 1950")}, "later_events": []},
                 {"scope_id": "EO:99999#s2", "original_operative_text": "Caf\u00e9 \u20ac inspections are suspended",
                  "original_source": dict(src), "state_at_cutoff": "terminated", "later_events": []}],
             "whole_order_end": {"date": "1950-06-30", "actor": "EO:99999", "mechanism": "own terms",
                                 "source": dict(src, quote="This order is revoked.")},
             "savings_residuals": {"state": "none", "reason": "none", "source": dict(src, quote="NOT IN THE TEXT AT ALL")},
             "research_rationale": "synthetic"}
    csha = X.claim_sha(claim)
    (root / "claims.jsonl").write_text(json.dumps({"instrument_id": "EO:1"}) + "\n" + json.dumps(claim) + "\n", "utf-8")
    ck = "claims.jsonl:2"
    per = {"by_instrument": {"EO:99999": {"claim_key": ck, "claim_sha256": ("0" * 64 if bad_claim_sha else csha)}},
           "claims": [{"claim_key": ck, "file": "claims.jsonl", "line": 2, "instrument_id": "EO:99999", "claim_sha256": csha,
                       "mechanical_result": "pass", "gate_passed": True, "all_checks_passed": True,
                       "steps": {"original_text": {"checker_passed": True}}, "check_counts": {"quote_verbatim": {"pass": 5}}}]}
    (root / "jobs/readiness-tracker/output").mkdir(parents=True)
    (root / "jobs/claim-checker/output").mkdir(parents=True)
    (root / X.PER_CLAIM).write_text(json.dumps(per), "utf-8")
    (root / X.READINESS_CSV).write_text("instrument_id,ready_for_human_review,text_evidence_tier,blockers\n"
                                        f"EO:99999,{ready},original_supported,\n", "utf-8")
    (root / X.CLAIM_CHECKS).write_text("claim_key,instrument_id,effective_for_tracker,step,check,field,result,status,detail\n"
                                       f"{ck},EO:99999,yes,savings_residuals,quote_verbatim,savings_residuals.source.quote,fail,not_found,x\n", "utf-8")
    (root / "research/rev").mkdir(parents=True)
    good = {"review_id": "r1", "instrument_id": "EO:99999", "claim_sha256": csha, "reviewer": "blind-1", "model_family": "Anthropic",
            "verdict": "upheld", "reasoning": "ok", "evidence_checked": ["x"], "defects": []}
    other = dict(good, review_id="r2", claim_sha256="1" * 64)         # an older version of the claim
    second = dict(good, review_id="r3", reviewer="blind-2", model_family="OpenAI")
    (root / "research/rev/BLIND_REVIEW.jsonl").write_text("\n".join(json.dumps(r) for r in (good, other, second)) + "\n", "utf-8")
    (root / "research/rev/notes.jsonl").write_text(json.dumps(good) + "\n", "utf-8")   # name does not look like a review file
    return csha


def run(root, *extra, git_ref=None):
    out = pathlib.Path(tempfile.mkdtemp())
    args = [str(root), "--ids", "99999", "--out", str(out)] + list(extra)
    if git_ref:
        args += ["--git-ref", git_ref]
    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    try:
        X.main(args)
    finally:
        sys.stdout = old
    return json.loads((out / "cards/EO_99999.json").read_text("utf-8")), out


class Normalisation(unittest.TestCase):
    def test_exact_and_normalised_offsets_map_back_to_the_original(self):
        status, hits = X.find_occurrences("President every year.", TEXT)
        self.assertEqual(status, "normalised")                       # the source has "Presi-\ndent"
        a, b = hits[0]
        self.assertTrue(TEXT[a:b].startswith("Presi-\ndent"))
        self.assertTrue(TEXT[a:b].endswith("year."))
        status, hits = X.find_occurrences("Administrator shall", TEXT)  # soft hyphen inside the word
        self.assertEqual(status, "normalised")
        self.assertEqual(TEXT[hits[0][0]:hits[0][1]], "Admin\u00adistrator shall")
        self.assertEqual(X.find_occurrences("inspections are suspended", TEXT)[0], "normalised")  # three spaces collapsed
        self.assertEqual(X.find_occurrences("This order is revoked.", TEXT)[0], "exact")
        self.assertEqual(X.find_occurrences("not there", TEXT), ("not_found", []))
        self.assertEqual(X.find_occurrences("   ", TEXT), ("not_found", []))

    def test_byte_offsets_are_utf8(self):
        i = TEXT.index("Caf\u00e9")
        (a, b), = X.byte_offsets(TEXT, [(i, i + 6)], False)
        raw = TEXT.encode("utf-8")
        self.assertEqual(raw[a:b].decode("utf-8"), "Caf\u00e9 \u20ac")
        self.assertEqual(b - a, 4 + 1 + 1 + 3)

    def test_claim_sha_is_the_gate_function(self):
        self.assertEqual(X.canonical({"b": 1, "a": "\u00e9"}), '{"a":"\u00e9","b":1}')


class Export(unittest.TestCase):
    def check_card(self, card, csha):
        self.assertEqual(card["claim_sha256"], csha)
        self.assertEqual(X.claim_sha(card["claim"]), csha)
        self.assertEqual(len(card["sources"]), 1)
        src = card["sources"][0]
        raw = src["text"].encode("utf-8")
        self.assertEqual(sha(raw), src["text_sha256_export"])
        self.assertTrue(src["text_sha256_matches_claim"])
        by = {s["claim_path"]: s for s in card["spans"]}
        s = by["operative_clauses[0].original_operative_text"]
        self.assertEqual(s["status"], "normalised")
        self.assertIn("Presi-\ndent", raw[s["byte_start"]:s["byte_end"]].decode("utf-8"))
        s = by["operative_clauses[1].original_operative_text"]
        self.assertTrue(raw[s["byte_start"]:s["byte_end"]].decode("utf-8").startswith("Caf\u00e9"))
        s = by["whole_order_end.source.quote"]
        self.assertEqual((s["status"], raw[s["byte_start"]:s["byte_end"]].decode("utf-8")), ("exact", "This order is revoked."))
        self.assertTrue(s["in_declared_span"])
        self.assertEqual(by["savings_residuals.source.quote"]["status"], "not_found")
        self.assertEqual({s["element"] for s in card["spans"]}, {"original", "clause:0", "clause:1", "ending", "savings"})
        # only reviews that name this exact hash; the file name filter keeps notes.jsonl out
        self.assertEqual(sorted(r["review_id"] for r in card["ai_reviews"]), ["r1", "r3"])
        self.assertTrue(card["ai_review_gate"]["met"])
        self.assertEqual(card["ai_review_gate"]["model_families"], ["Anthropic", "OpenAI"])
        self.assertEqual(card["checker"]["non_passing_rows"][0]["status"], "not_found")
        self.assertEqual(card["elements"][1]["label"], "Clause 1: EO:99999#s1")

    def test_filesystem_repo(self):
        root = tempfile.mkdtemp()
        csha = make_repo(root)
        card, out = run(root)
        self.check_card(card, csha)
        man = json.loads((out / "manifest.json").read_text("utf-8"))
        data = (out / "cards/EO_99999.json").read_bytes()
        self.assertEqual(man["cards"][0]["sha256"], sha(data))

    def test_git_repo_mode_gives_the_same_card(self):
        root = tempfile.mkdtemp()
        csha = make_repo(root)

        def g(*a):
            return subprocess.run(["git", "-C", root, "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True, capture_output=True)
        g("init", "-q")
        g("add", "-A")
        g("commit", "-q", "-m", "x")
        a, _ = run(root)
        b, _ = run(root, git_ref="HEAD")
        for c in (a, b):
            c.pop("exported_utc")
        self.assertEqual(a, b)
        self.check_card(b, csha)

    def test_refuses_stale_claim_hash(self):
        root = tempfile.mkdtemp()
        make_repo(root, bad_claim_sha=True)
        with self.assertRaises(SystemExit) as cm:
            run(root)
        self.assertIn("changed since the checker ran", str(cm.exception))

    def test_refuses_orders_not_ready_unless_allowed(self):
        root = tempfile.mkdtemp()
        make_repo(root, ready="no")
        with self.assertRaises(SystemExit):
            run(root)
        card, _ = run(root, "--allow-not-ready")
        self.assertEqual(card["readiness"]["ready_for_human_review"], "no")

    def test_text_over_the_cap_is_not_embedded(self):
        root = tempfile.mkdtemp()
        make_repo(root)
        card, _ = run(root, "--max-text-bytes", "50")
        src = card["sources"][0]
        self.assertFalse(src["text_embedded"])
        self.assertNotIn("text", src)
        self.assertIn("attach", src["text_note"])
        self.assertTrue(all("byte_start" in s for s in card["spans"] if s["status"] != "not_found"))

    def test_path_traversal_in_text_path_is_ignored(self):
        self.assertIsNone(X.safe_rel("../../etc/passwd"))
        self.assertIsNone(X.safe_rel("/abs/path"))
        self.assertIsNone(X.safe_rel("C:/x"))
        self.assertEqual(X.safe_rel("a/./b.txt"), "a/b.txt")


class CommittedExamples(unittest.TestCase):
    """The five example cards are real filed claims; re-check every invariant a certifier relies on."""

    def cards(self):
        return sorted((HERE / "example_cards/cards").glob("*.json"))

    def test_five_cards_under_2_mib(self):
        files = self.cards()
        self.assertEqual(len(files), 5)
        self.assertLess(sum(f.stat().st_size for f in files), 2 * 1024 * 1024)

    def test_every_card_verifies(self):
        for f in self.cards():
            card = json.loads(f.read_text("utf-8"))
            self.assertEqual(card["schema"], X.CARD_SCHEMA)
            self.assertEqual(X.claim_sha(card["claim"]), card["claim_sha256"], f.name)
            self.assertEqual(card["readiness"]["ready_for_human_review"], "yes")
            self.assertTrue(card["ai_reviews"], f.name)
            srcs = {s["source_key"]: s for s in card["sources"]}
            for s in srcs.values():
                self.assertTrue(s["text_embedded"])
                raw = s["text"].encode("utf-8") if "text" in s else base64.b64decode(s["text_b64"])
                self.assertEqual(sha(raw), s["text_sha256_export"])
                self.assertTrue(s["text_sha256_matches_claim"], f"{f.name} {s['url']}")
            for sp in card["spans"]:
                s = srcs[sp["source_key"]]
                raw = s["text"].encode("utf-8")
                self.assertEqual(sp["status"], "exact", f"{f.name} {sp['claim_path']}")
                self.assertEqual(raw[sp["byte_start"]:sp["byte_end"]].decode("utf-8"), sp["quote"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
