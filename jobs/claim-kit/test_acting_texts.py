"""Held acting texts reach the dossier as exact, hash-pinned ACTOR_TEXT records (Accursius F4).

Non-census acting instruments (public land orders, statutes, agency Federal Register documents)
keep their own identity, enter a target's dossier only when they print the target's number, and
large texts are cited by exact windows instead of an uncitable overflow pointer. A held, official,
hash-verified SUPPLEMENT excerpt that names the order is marked as a possible NO basis."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import assemble as A
import build as B
import inputs as I
import status_overlay as O
import test_build as F
import test_status_overlay as TO

write_json, write_jsonl, read_jsonl = F.write_json, F.write_jsonl, F.read_jsonl
REPO = HERE.parents[1]
FR_GRADE = ("government_printed_federal_register_issue (govinfo scan of the daily Federal Register; "
            "text is the scan's OCR layer)")
STAT_GRADE = "government_printed_statutes_at_large (govinfo digitized Statutes at Large granule PDF)"
CITER_GRADE = "fr_document_full_text (federalregister.gov full text of a Federal Register document)"

PLO_TEXT = ("PUBLIC LAND ORDER 9\n[Revoking Executive Order No. 1 in part]\nBy virtue of the authority vested in me, "
            "it is ordered as follows:\nExecutive Order No. 1 of January 1, 1990, which withdrew lands for the "
            "First Board, is hereby revoked.\nPublic Land Order 4 is not affected.\n")
STAT_TEXT = ("PUBLIC LAW 1-1\nAN ACT to provide for the Temporary Committee and for other purposes.\n"
             "Be it enacted, That the Temporary Committee shall report to Congress.\n")
FILLER = "Unrelated agency matter printed on the same pages of the Federal Register.\n"


def add_acting_sources(repo):
    """Selden-shaped outputs: SOURCES.jsonl (acting instrument first, then targets) and FRAGMENTS."""
    out = repo / "jobs/selden-fr-acting/output"
    rows, frags = [], []

    def held(name, text, actor, targets, grade, url):
        path = out / "texts" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        raw = hashlib.sha256(("pdf:" + name).encode()).hexdigest()
        rows.append({"instrument_ids": [actor] + targets, "role": "acting_instrument_text", "url": url,
                     "sha256": raw, "text_path": "texts/" + name, "grade": grade,
                     "acceptable_as_original": False, "page_or_item": "1 FR 1; PDF pages 1-2",
                     "source_id": "fr-extract:" + raw[:16]})
        return raw

    raw = held("FR_1_1.txt", PLO_TEXT, "PLO:9", ["EO:1"], FR_GRADE, "https://www.govinfo.gov/content/pkg/FR-1991/a.pdf#page=1")
    frags.append({"instrument_id": "EO:1", "kind": "later_event_candidates", "produced_by": "selden-fr-acting",
                  "data": [{"acting_id": "PLO:9", "target_id": "EO:1", "mechanism": "revocation",
                            "text_path": "texts/FR_1_1.txt", "source_sha256": raw,
                            "source_url": "https://www.govinfo.gov/content/pkg/FR-1991/a.pdf#page=1",
                            "page_or_item": "1 FR 1"}]})
    # A statute that a later-event fragment links to EO 4 but whose text never prints the number.
    held("STATUTE-1-Pg1.txt", STAT_TEXT, "STAT:1-1", ["EO:4"], STAT_GRADE, "https://www.govinfo.gov/content/pkg/STATUTE-1/pdf/STATUTE-1-Pg1.pdf")
    frags.append({"instrument_id": "EO:4", "kind": "later_event_candidates", "produced_by": "selden-statutes",
                  "data": [{"acting_id": "STAT:1-1", "target_id": "EO:4", "mechanism": "cross_reference"}]})
    # A custody row that lists EO 2 with no event fragment: the text is bound, but no pair is made.
    held("FR_2_2.txt", PLO_TEXT.replace("No. 1 ", "No. 2 "), "PLO:11", ["EO:2"], FR_GRADE, "https://www.govinfo.gov/content/pkg/FR-1992/b.pdf")
    # A large agency document (over the 50,000-byte limit) that cites EO 1 twice, far apart.
    big = ("FR Doc. 2000-1\nNotice of rescission.\n" + FILLER * 400 +
           "The rules issued under Executive Order 1 are rescinded effective March 23, 2001.\n" + FILLER * 400 +
           "See also Executive Orders 6 and 1 of 1990.\n" + FILLER * 20)
    held("fr-2000-1.txt", big, "FRDOC:2000-1", ["EO:1"], CITER_GRADE, "https://www.federalregister.gov/d/2000-1.txt")
    frags.append({"instrument_id": "EO:1", "kind": "later_event_candidates", "produced_by": "selden-fr-citers",
                  "data": [{"acting_id": "FRDOC:2000-1", "target_id": "EO:1", "mechanism": "cross_reference"}]})
    write_jsonl(out / "SOURCES.jsonl", rows)
    write_jsonl(out / "FRAGMENTS.jsonl", frags)
    return out


def grow_actor_text(repo, iid="EO:5"):
    """Push a census actor's held text past the 50,000-byte limit (the overflow case)."""
    path = repo / "jobs/future-source/data/texts" / (iid.replace(":", "_") + ".txt")
    with path.open("a", encoding="utf-8") as fh:
        fh.write("Additional context retained.\n" * 2200)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    provenance = repo / "jobs/future-source/data/PROVENANCE.json"
    data = json.loads(provenance.read_bytes())
    actor = next(r for r in data["representations"] if r["instrument_id"] == iid)
    actor["source"].update(sha256=digest, text_sha256=digest)
    write_json(provenance, data)


class TargetMentionTests(unittest.TestCase):
    def names(self, iid, text, signed=None):
        return bool(B.target_mentions(iid, text, signed))

    def test_executive_forms_name_the_order(self):
        self.assertTrue(self.names("EO:8790", "lands withdrawn by Executive Order No. 8790 of June 13, 1941"))
        self.assertTrue(self.names("EO:8791", "withdrawn by Executive Orders Nos. 8790 and 8791, are"))
        self.assertTrue(self.names("EO:13355", "inserting in lieu thereof ‘‘Orders 13354 and 13355 of August 27, 2004, are"))
        self.assertTrue(self.names("EO:13354", "inserting in lieu thereof ‘‘Orders 13354 and 13355 of August 27, 2004, are"))
        self.assertTrue(self.names("EO:13024", "as amended by Ex. Ord. No. 13024, Nov. 7, 1996, 61 F.R. 58125"))
        self.assertTrue(self.names("EO:10092", "The provisions of Executive Order 10092 as made applicable"))
        self.assertTrue(self.names("EO:1", "issued under Executive Order 1 are rescinded"))
        self.assertTrue(self.names("EO:7933A", "Executive Order No. 7933A is revoked"))
        self.assertTrue(self.names("EO:5068", "issued Exec. Order No. 5068, prescribing how veterans"))

    def test_ocr_and_long_lists(self):
        self.assertTrue(self.names("EO:7734", "revoked by Execu-\ntive Order No. 7734 of"))
        self.assertTrue(self.names("EO:8979", "under Exec- utive Order No. 8979"))
        self.assertTrue(self.names("EO:10292", "Executive Or-\nder No. 10292 is"))
        self.assertTrue(self.names("EO:7794", "EXECUTIVE ORDER NO. 7 7 9 4\n"))
        self.assertTrue(self.names("EO:9019", "Executive Orders No. 8578 of Octo-\nber 29, 1940, as amended; No. 9019 of January 12,1942"))
        self.assertTrue(self.names("EO:6910", "Executive Order (E.O.) 6910 of November 26, 1934"))
        self.assertTrue(self.names("EO:7933A", "Executive Order 7933-A is revoked"))
        self.assertTrue(self.names("EO:7933A", "Executive Order No. 7933a is revoked"))
        self.assertIsNone(B.target_mentions("EO:106½", "Executive Order 106½"))
        self.assertIsNone(B.target_mentions("PLO:9", "Executive Order No. 9"))

    def test_reviewer_false_matches_are_refused(self):
        rows = [("EO:17", "Missouri Executive Order 17-03 (January 10, 2017)"),
                ("EO:17", "Initiative (Executive Order 17- 03), Missouri proposes"),
                ("EO:1991", "reorganized by Executive Order 1991-31 (Michigan)"),
                ("EO:12", "Executive Order 12, 731, requires"),
                ("EO:7", "Executive Order No. 9066, 7 F.R. 1407"),
                ("EO:58", "Executive Order 12866, 58 FR 51735"),
                ("EO:43", "Executive Order No. 6910 of November 26, 1934, as amended, 43 CFR 297"),
                ("EO:1934", "Executive Order 6910, 1934"),
                ("EO:75", "issued by Order 75-6-12 of the Board"),
                ("EO:2748", "by Order No. 2748 of the Secretary of the Interior"),
                ("EO:2509", "Secretary's Order 2508 and Order 2509"),
                ("EO:10", "required by Executive Order 10 (E.O.-10), issued by the Iowa Governor in January 2023"),
                ("EO:145", "incorporating Massachusetts Executive Order 145, Consultation with Cities"),
                ("EO:145", "the Commonwealth's Executive Order No. 145 (discussed earlier)"),
                ("EO:1266", "is not a ``significantly regulatory action'' under Executive Order 1266; (2) is not"),
                ("EO:3211", "K. Executive Order 3211\n E.O. 13211, Actions Concerning Regulations"),
                ("EO:1317", "Tribal implications as specified in Executive Order 1317(65 FR 67249, November 9, 2000)"),
                ("EO:13", "The President, through Executive Order 13, 222 of August 17, 2001"),
                ("EO:2004", "you signed Executive Order 2004-005 on January 31, 2004"),
                ("EO:200", "established by Executive Order 200-76 on July 11, 1975"),
                ("EO:6", "under Executive Order 16 of 1990"),
                ("EO:13354", "Executive Order 113354 is revoked"),
                ("EO:13354", "69 FR 13354, published"),
                ("EO:341", "Executive Order No. 341A is revoked"),
                ("EO:7933", "Executive Order 7933-A is revoked"),
                ("EO:2748", "Public Land Order 2748 revokes the withdrawal")]
        for iid, text in rows:
            with self.subTest(iid=iid, text=text):
                self.assertFalse(self.names(iid, text))

    def test_list_tails_and_spaced_digits(self):
        # A continuation number before a noun is not a list item.
        self.assertFalse(self.names("EO:8", "Executive Order 9066 and 8 other orders"))
        self.assertTrue(self.names("EO:9066", "Executive Order 9066 and 8 other orders"))
        self.assertTrue(self.names("EO:8791", "Executive Orders 8790 and 8791 are hereby revoked"))
        self.assertTrue(self.names("EO:8791", "Executive Orders 8790 and 8791, as amended, are"))
        # Spaced digits join only a fully single-spaced run of three or more digits.
        self.assertFalse(self.names("EO:12", "Executive Order 1 2 is revoked"))
        self.assertFalse(self.names("EO:866", "Executive Order 12 866 is revoked"))
        self.assertFalse(self.names("EO:12866", "Executive Order 12 866 is revoked"))
        self.assertTrue(self.names("EO:7794", "EXECUTIVE ORDER NO. 7 7 9 4\n"))

    def test_page_check_debt_blocks_basis_eligibility(self):
        ar = {"text": PLO_TEXT, "source": {"text_sha256": "h"}, "text_path": "t.txt", "role": B.ACTING_ROLE,
              "grade": FR_GRADE, "requires_page_check": True}
        evidence = {}
        B._actor_context("EO:1", "PLO:9", ar, [], evidence, [])
        record = evidence["ACTOR_TEXT:PLO:9"]
        self.assertTrue(record["prints_number_lexical"] and record["official_printing"] and record["requires_page_check"])
        self.assertFalse(record["basis_eligible"])
        ar["requires_page_check"] = False
        evidence = {}
        B._actor_context("EO:1", "PLO:9", ar, [], evidence, [])
        self.assertTrue(evidence["ACTOR_TEXT:PLO:9"]["basis_eligible"])

    def test_agency_document_state_and_unit_contexts(self):
        self.assertFalse(self.names("EO:17", "Initiative (Executive Order 17-\n03), Missouri proposes"))
        self.assertFalse(self.names("EO:72", "sections 2 and 6 of the Executive Order 72 hours after all injunctions"))
        agency = lambda iid, text: bool(B.target_mentions(iid, text, None, True))
        self.assertFalse(agency("EO:106", "OCRM received the State of Alaska's request to incorporate Executive Order 106, House Bills"))
        self.assertFalse(agency("EO:192", "The Philippines established the Bureau through the DENR, under Executive Order 192. Its"))
        self.assertFalse(agency("EO:31", "clean energy requirements within the State including Executive Order 31 on energy"))
        self.assertFalse(agency("EO:145", "the EPA is finalizing the incorporation by reference Executive Order 145 and the part of 310 CMR 7.00"))
        # The same contexts in a land order or statute are geography, not a state order.
        self.assertTrue(self.names("EO:5327", "lands in the State of Montana withdrawn by Executive Order No. 5327 dated April 15, 1930, are"))
        self.assertTrue(agency("EO:5158", "The Cedar Keys National Wildlife Refuge was established by Executive Order 5158 on July 16, 1929"))

    def test_printed_date_must_match_the_signing_year(self):
        self.assertFalse(self.names("EO:1318", "Executive Order 1318 of March 31, 1999, and", "1911-03-02"))
        self.assertFalse(self.names("EO:1322", "through Executive Order 1322 of August 17, 2001 (3 CFR", "1911-04-01"))
        self.assertTrue(self.names("EO:5158", "established by Executive Order 5158 on July 16, 1929, as a", "1929-07-16"))
        self.assertTrue(self.names("EO:101", "issued Executive Order 101 on July 27, 1897. This", "1897-07-27"))

    def test_windows_are_exact_merged_and_bounded(self):
        text = "\n".join("line %d" % n for n in range(3000))
        spans = [(100, 105), (120, 125), (15000, 15006)]
        windows = B.context_windows(text, spans)
        self.assertEqual(len(windows), 2)
        for start, end in windows:
            self.assertTrue(0 <= start < end <= len(text))
            self.assertLessEqual(end - start, B.WINDOW_MAX_CHARS)
        self.assertTrue(windows[0][0] <= 100 and windows[0][1] >= 125)
        # A text citing the order every 2,000 characters is never included whole: bytes are capped per actor,
        # and the window around a located provision late in the text is kept first.
        chunk = "Executive Order 1 applies here.\n" + ("x" * 60 + "\n") * 32
        text = chunk * 60
        act_at = len(chunk) * 55 + 3
        act = [{"actor_id": "FRDOC:x", "actor_source": {"text_sha256": "h"}, "char_start": act_at, "char_end": act_at + 10}]
        ar = {"text": text, "source": {"text_sha256": "h"}, "text_path": "t.txt", "role": B.ACTING_ROLE,
              "grade": CITER_GRADE}
        evidence, missing = {}, []
        entry = B._actor_context("EO:1", "FRDOC:x", ar, act, evidence, missing)
        self.assertLessEqual(entry["window_bytes"], B.WINDOW_BYTES)
        self.assertLessEqual(sum(len(r["text"].encode()) for r in evidence.values()), B.WINDOW_BYTES)
        self.assertTrue(all(len(r["text"]) <= B.WINDOW_MAX_CHARS for r in evidence.values()))
        first = evidence[entry["evidence_ids"][0]]
        self.assertTrue(first["char_start"] <= act_at < first["char_end"])
        self.assertGreater(entry["windows_omitted"], 0)
        self.assertTrue(missing)
        self.assertFalse(any(r["basis_eligible"] for r in evidence.values()))  # a federalregister.gov rendering


class ActingCorpusTests(unittest.TestCase):
    def setUp(self):
        F.BuildIntegrationTests.setUp(self)
        add_acting_sources(self.repo)

    run_build, dossier = F.BuildIntegrationTests.run_build, F.BuildIntegrationTests.dossier

    def test_corpus_keeps_honest_non_census_identities(self):
        corpus = I.load_corpus(self.repo)
        actors = {r["instrument_id"] for r in corpus["acting_texts"]}
        self.assertEqual(actors, {"PLO:9", "PLO:11", "STAT:1-1", "FRDOC:2000-1"})
        self.assertFalse(any(r["instrument_id"] in actors for r in corpus["texts"]))
        for row in corpus["acting_texts"]:
            self.assertEqual(row["role"], I.ACTING_ROLE)
            self.assertFalse(row["acceptable_as_original"])
            self.assertEqual(row["source"]["instrument_id"], row["instrument_id"])
        self.assertTrue(I.NON_EO_ACTOR.fullmatch("FRDOC:2000-1"))
        pairs = {(p["target_id"], p["actor_id"]) for p in corpus["pairs"]}
        self.assertTrue({("EO:1", "PLO:9"), ("EO:4", "STAT:1-1"), ("EO:1", "FRDOC:2000-1")} <= pairs)
        # A custody row is not a pair: PLO:11 lists EO 2 but no event fragment links them.
        self.assertNotIn(("EO:2", "PLO:11"), pairs)
        plo = next(r for r in corpus["acting_texts"] if r["instrument_id"] == "PLO:9")
        self.assertEqual(plo["producer_role"], "acting_instrument_text")
        self.assertFalse(plo["requires_page_check"])

    def test_named_acting_texts_become_exact_actor_text_records(self):
        self.run_build()
        d = self.dossier("EO:1")
        plo = d["evidence"]["ACTOR_TEXT:PLO:9"]
        self.assertEqual(plo["text"], PLO_TEXT)
        self.assertTrue(plo["prints_number_lexical"])
        self.assertTrue(plo["basis_eligible"])
        self.assertEqual(plo["actor_kind"], B.NON_CENSUS_ACTOR)
        self.assertEqual(plo["source"]["text_sha256"], hashlib.sha256(PLO_TEXT.encode()).hexdigest())
        self.assertNotIn("Acting identity absent from census: PLO:9", d["missing"])
        # The large agency document is cited by exact windows around each printed number.
        context = next(c for c in d["actor_contexts"] if c["actor_id"] == "FRDOC:2000-1")
        self.assertNotIn("overflow", context)
        self.assertEqual(len(context["evidence_ids"]), 2)
        held = (self.repo / context["held_text_path"]).read_text(encoding="utf-8")
        for eid in context["evidence_ids"]:
            self.assertTrue(eid.startswith("ACTOR_TEXT:FRDOC:2000-1@"))
            record = d["evidence"][eid]
            self.assertEqual(held[record["char_start"]:record["char_end"]], record["text"])
            self.assertTrue(record["prints_number_lexical"])
            self.assertFalse(record["basis_eligible"])  # federalregister.gov text: a lead, not a basis
            self.assertLess(len(record["text"]), 5000)
        self.assertNotIn("ACTOR_TEXT:FRDOC:2000-1", d["evidence"])
        O._source_pins(self.repo, d, {})
        # A non-census instrument never becomes an order: no dossier, no own-text representation.
        self.assertFalse((self.out / "dossiers" / (B.filename("PLO:9") + ".json")).exists())
        clauses = [r for r in read_jsonl(self.out / "CLAUSES.jsonl") if r["instrument_id"] == "PLO:9"]
        self.assertEqual(len(clauses), 1)
        self.assertEqual(clauses[0]["clauses"], [])
        self.assertEqual(clauses[0]["role"], I.ACTING_ROLE)

    def test_number_not_found_is_a_lead_note_not_a_finding(self):
        self.run_build()
        lead = next(r for r in read_jsonl(self.out / "STATUS_LEADS.jsonl") if r["instrument_id"] == "EO:4")
        note = ("Acting text of STAT:1-1: " + B.NOT_FOUND_LEXICAL +
                "jobs/selden-fr-acting/output/texts/STATUTE-1-Pg1.txt")
        self.assertIn(note, lead["missing"])
        self.assertFalse(any("D-20261021" in m for m in lead["missing"]))
        overlay = next(r for r in read_jsonl(self.out / "OVERLAY_INPUTS.jsonl") if r["instrument_id"] == "EO:4")
        self.assertNotIn("STAT:1-1", overlay["known_actor_ids"])
        self.assertFalse(any(r["instrument_id"] in ("STAT:1-1", "PLO:11") for r in read_jsonl(self.out / "CLAUSES.jsonl")))
        self.assertNotIn("ACTOR_TEXT:PLO:11", self.dossier("EO:2")["evidence"])

    def test_census_overflow_actor_text_gets_window_ids_and_keeps_pointer(self):
        grow_actor_text(self.repo)
        self.run_build()
        d = self.dossier("EO:1")
        context = next(c for c in d["actor_contexts"] if c["actor_id"] == "EO:5")
        self.assertEqual(context["overflow"], "actor-texts/EO_5.json")
        self.assertTrue(context["evidence_ids"])
        for eid in context["evidence_ids"]:
            self.assertTrue(eid.startswith("ACTOR_TEXT:EO:5@"))
            self.assertIn("Executive Order 1", d["evidence"][eid]["text"])
            self.assertTrue(d["evidence"][eid]["prints_number_lexical"])
            self.assertNotIn("basis_eligible", d["evidence"][eid])
        self.assertNotIn("ACTOR_TEXT:EO:5", d["evidence"])
        self.assertIn("Large actor context must be read at actor-texts/EO_5.json before deciding scope/savings.", d["missing"])
        O._source_pins(self.repo, d, {})

    def test_small_census_actor_text_is_unchanged_but_marked(self):
        self.run_build()
        d = self.dossier("EO:1")
        record = d["evidence"]["ACTOR_TEXT:EO:5"]
        self.assertEqual(record["char_start"], 0)
        self.assertTrue(record["prints_number_lexical"])
        self.assertNotIn("actor_kind", record)
        self.assertNotIn("basis_eligible", record)


class ActingOverlayTests(unittest.TestCase):
    """The frozen undecided dossier selects the same held acting texts, verifies them, and a NO may cite them."""

    history_packet = TO.OverlayTests.history_packet
    accepted_review = TO.OverlayTests.accepted_review

    def setUp(self):
        self.fixture = F.BuildIntegrationTests("test_whole_population_including_yes_no_undecided_and_missing")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.repo, self.out = self.fixture.repo, self.fixture.out
        add_acting_sources(self.repo)
        grow_actor_text(self.repo)
        self.fixture.status.write_text("instrument_id,provisional_substantive_status\nEO:2,no\nEO:3,yes\nEO:5,no\nEO:6,no\n",
                                       encoding="utf-8")
        code = self.repo / "jobs/claim-kit"
        code.mkdir(parents=True)
        for name in O.CODE_FILES:
            (code / name).parent.mkdir(parents=True, exist_ok=True)
            (code / name).write_bytes((HERE / name).read_bytes())
        history = self.repo / "jobs/status-history/history.py"
        history.parent.mkdir(parents=True)
        history.write_bytes((REPO / "jobs/status-history/history.py").read_bytes())
        self.fixture.run_build()
        self.packet = self.history_packet()
        self.evidence = O.freeze_evidence(self.repo, self.out, self.packet)
        self.decision = O.extend_decision(self.packet, self.evidence, "synthetic-producer")
        self.decision.update(approved=True, identity_confirmed=True, basis_review_confirmed=True,
                             earlier_endings_checked=True, partial_scope_checked=True, savings_checked=True,
                             recommended_provisional_status="no", material_gaps=[],
                             observations_reviewed=["OBS:synthetic-1"], basis_evidence_ids=["ACTOR_TEXT:PLO:9"],
                             rationale="The synthetic public land order prints this order's number and revokes it; read in full.")
        self.ending = "ACTOR_TEXT:PLO:9"
        self.review = self.accepted_review(self.decision)

    def test_frozen_evidence_holds_non_census_and_window_records(self):
        base = self.evidence["base_dossier"]
        self.assertIn("ACTOR_TEXT:PLO:9", base["evidence"])
        self.assertTrue(any(k.startswith("ACTOR_TEXT:FRDOC:2000-1@") for k in base["evidence"]))
        self.assertTrue(any(k.startswith("ACTOR_TEXT:EO:5@") for k in base["evidence"]))
        self.assertNotIn("No compiled selected actor text located: PLO:9", base["missing"])
        self.assertIn("jobs/selden-fr-acting/output/texts/FR_1_1.txt", self.evidence["source_fingerprints"])
        self.assertTrue(O.validate_evidence(self.repo, self.evidence))
        # Batch freezing gives the same evidence.
        many = O.prepare_evidence_many(self.repo, self.out, ["EO:1"])
        self.assertEqual(A.canonical_sha(many["EO:1"]), A.canonical_sha(O.prepare_evidence(self.repo, self.out, "EO:1")))

    def test_no_may_cite_a_named_non_census_actor_text(self):
        proposal = O.propose(self.repo, self.decision, self.review, self.evidence)
        self.assertEqual(proposal["recommended_provisional_status"], "no")
        self.assertFalse(proposal["owner_acceptance"]["accepted"])

    def test_no_may_cite_an_overflow_window(self):
        window = next(k for k in self.evidence["base_dossier"]["evidence"] if k.startswith("ACTOR_TEXT:EO:5@"))
        self.decision["basis_evidence_ids"] = [window]
        self.ending = window
        self.review = self.accepted_review(self.decision)
        self.assertEqual(O.propose(self.repo, self.decision, self.review, self.evidence)["recommended_provisional_status"], "no")

    def test_non_census_lead_is_refused_as_a_basis(self):
        window = next(k for k in self.evidence["base_dossier"]["evidence"] if k.startswith("ACTOR_TEXT:FRDOC:2000-1@"))
        self.decision["basis_evidence_ids"] = [window]
        self.ending = window
        self.review = self.accepted_review(self.decision)
        with self.assertRaisesRegex(ValueError, "non_census_actor_text_is_a_lead_not_a_basis:" + window):
            O.propose(self.repo, self.decision, self.review, self.evidence)

    def test_census_actor_text_behaves_as_on_main(self):
        # A census actor text with no lexical mark (an OCR-missed or date-cited provision) remains citable.
        window = next(k for k in self.evidence["base_dossier"]["evidence"] if k.startswith("ACTOR_TEXT:EO:5@"))
        self.evidence["base_dossier"]["evidence"][window].pop("prints_number_lexical", None)
        base = self.evidence["base_dossier"]
        base["fingerprint"] = A.canonical_sha(base)
        O._seal(self.evidence)
        self.decision["evidence_sha256"] = self.evidence["fingerprint"]
        self.decision["basis_evidence_ids"] = [window]
        self.ending = window
        self.review = self.accepted_review(self.decision)
        self.assertEqual(O.propose(self.repo, self.decision, self.review, self.evidence)["recommended_provisional_status"], "no")

    def test_changed_acting_text_is_stale(self):
        path = self.repo / "jobs/selden-fr-acting/output/texts/FR_1_1.txt"
        path.write_bytes(path.read_bytes() + b"tampered\n")
        with self.assertRaisesRegex(ValueError, "stale_held_source"):
            O.validate_evidence(self.repo, self.evidence)

    def supplement(self, record):
        base = self.evidence["base_dossier"]
        base["evidence"]["SUPPLEMENT:s1"] = record
        base["fingerprint"] = A.canonical_sha(base)
        O._seal(self.evidence)
        self.decision["evidence_sha256"] = self.evidence["fingerprint"]
        self.decision["basis_evidence_ids"] = ["SUPPLEMENT:s1"]
        self.ending = "SUPPLEMENT:s1"
        self.review = self.accepted_review(self.decision)

    def test_supplement_basis_needs_the_eligibility_mark(self):
        plo = deepcopy(self.evidence["base_dossier"]["evidence"]["ACTOR_TEXT:PLO:9"])
        record = {"id": "SUPPLEMENT:s1", "source": plo["source"], "text": plo["text"], "char_start": 0,
                  "char_end": len(plo["text"]), "actor_id": "PLO:9", "role": "unreviewed_source_excerpt"}
        self.supplement(dict(record))
        with self.assertRaisesRegex(ValueError, "snapshot_only_or_missing_ending_basis"):
            O.propose(self.repo, self.decision, self.review, self.evidence)
        self.supplement(dict(record, basis_eligible=True))
        self.assertEqual(O.propose(self.repo, self.decision, self.review, self.evidence)["recommended_provisional_status"], "no")


class SupplementEligibilityTests(unittest.TestCase):
    def setUp(self):
        F.BuildIntegrationTests.setUp(self)
        add_acting_sources(self.repo)

    def entry(self, name, start=0, end=None, ids=("EO:1",)):
        import source_supplement as S
        out = self.repo / "jobs/selden-fr-acting/output"
        row = next(r for r in read_jsonl(out / "SOURCES.jsonl") if r["text_path"] == "texts/" + name)
        local = self.repo / "jobs/selden-fr-acting/output/captures" / (name + ".pdf")
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(b"pdf bytes " + name.encode())
        text_path = "jobs/selden-fr-acting/output/texts/" + name
        text = (self.repo / text_path).read_text(encoding="utf-8")
        source = {"url": row["url"], "sha256": hashlib.sha256(local.read_bytes()).hexdigest(),
                  "text_path": text_path, "text_sha256": hashlib.sha256((self.repo / text_path).read_bytes()).hexdigest(),
                  "page_or_item": row["page_or_item"], "local_path": local.relative_to(self.repo).as_posix()}
        return S, source, text, {"alias": "s1", "instrument_ids": list(ids), "actor_id": row["instrument_ids"][0],
                                 "reason": "Held acting text printed in the Federal Register.", "source": source,
                                 "char_start": start, "char_end": end or len(text)}

    def test_official_named_excerpt_is_marked_eligible(self):
        S, source, text, entry = self.entry("FR_1_1.txt")
        # The declared local bytes are the producer's capture: the declaration's raw hash must match them.
        rows = read_jsonl(self.repo / "jobs/selden-fr-acting/output/SOURCES.jsonl")
        for r in rows:
            if r["text_path"] == "texts/FR_1_1.txt":
                r["sha256"] = source["sha256"]
        write_jsonl(self.repo / "jobs/selden-fr-acting/output/SOURCES.jsonl", rows)
        mark = S.basis_mark(self.repo, source, text, 0, len(text), "EO:1")
        self.assertTrue(mark["basis_eligible"])
        self.assertTrue(mark["prints_number_lexical"])
        self.assertEqual(mark["official_declaration"]["declaration_path"], "jobs/selden-fr-acting/output/SOURCES.jsonl")
        unnamed = S.basis_mark(self.repo, source, text, 0, len(text), "EO:4")
        self.assertFalse(unnamed["basis_eligible"])
        self.assertIsNone(unnamed["prints_number_lexical"])
        # Naming is read on the whole text: an excerpt cut to start at "Order 4" inside "Public Land Order 4"
        # does not name EO 4, and an excerpt that holds no mention is not eligible.
        start = text.index("Order 4 is not")
        self.assertFalse(S.basis_mark(self.repo, source, text, start, len(text), "EO:4")["basis_eligible"])
        first = text.index("No. 1 in part")
        self.assertFalse(S.basis_mark(self.repo, source, text, 0, first - 4, "EO:1")["basis_eligible"])
        self.assertTrue(S.basis_mark(self.repo, source, text, first - 20, first + 8, "EO:1")["basis_eligible"])
        # A page check owed on the official declaration is carried into the mark.
        for r in rows:
            if r["text_path"] == "texts/FR_1_1.txt":
                r["needs_page_check"] = True
        write_jsonl(self.repo / "jobs/selden-fr-acting/output/SOURCES.jsonl", rows)
        owed = S.basis_mark(self.repo, source, text, 0, len(text), "EO:1")
        self.assertTrue(owed["official_declaration"]["requires_page_check"])
        self.assertFalse(owed["basis_eligible"])

    def test_unofficial_or_unmatched_excerpt_is_not_eligible(self):
        S, source, text, entry = self.entry("fr-2000-1.txt")
        self.assertFalse(S.basis_mark(self.repo, source, text, 0, len(text), "EO:1")["basis_eligible"])  # raw hash differs
        rows = read_jsonl(self.repo / "jobs/selden-fr-acting/output/SOURCES.jsonl")
        for r in rows:
            if r["text_path"] == "texts/fr-2000-1.txt":
                r["sha256"] = source["sha256"]
        write_jsonl(self.repo / "jobs/selden-fr-acting/output/SOURCES.jsonl", rows)
        mark = S.basis_mark(self.repo, source, text, 0, len(text), "EO:1")
        self.assertTrue(mark["prints_number_lexical"])
        self.assertFalse(mark["basis_eligible"])  # federalregister.gov text is not the official edition


if __name__ == "__main__":
    unittest.main()
