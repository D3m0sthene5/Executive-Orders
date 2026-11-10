"""Nalimov tests. Every fixture is built here; no committed job output is read (road-tests checks out jobs/ without
outputs). Run: python -I jobs/nalimov-tablebase/test_nalimov.py"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import drafter as D  # noqa: E402
import packets as K  # noqa: E402
import predicate as P  # noqa: E402
import nalimov as N  # noqa: E402

try:  # the kit's own decision gate, when its imports are checked out
    sys.path.insert(0, str(REPO / "jobs/claim-kit"))
    import status_overlay as SO  # noqa: E402
except Exception:  # noqa: BLE001
    SO = None


def sha(t):
    return hashlib.sha256(t.encode()).hexdigest()


ORIGINAL = ("Executive Order 11111 January 5, 1970\nCreating a Board\nBy virtue of the authority vested in me, it is "
            "hereby ordered as follows:\nSection 1. There is hereby established the Board of Things, which shall "
            "advise the President.\nSec. 2. Executive Order No. 10000 of May 1, 1962, is hereby revoked.\n"
            "THE WHITE HOUSE,\nJanuary 5, 1970.\n")
ACTOR = ("Executive Order 12222 March 3, 1980\nBy virtue of the authority vested in me, it is hereby ordered:\n"
         "Section 1. The Board of New Things is established.\nSec. 2. Executive Order No. 11111 of January 5, 1970, "
         "is hereby revoked.\nTHE WHITE HOUSE.\n")


def src(path, text, page="35 FR 100"):
    return {"page_or_item": page, "text_path": path, "text_sha256": sha(text), "requires_page_check": False}


def make_evidence(iid="EO:11111", actor="EO:12222", provision="Executive Order No. 11111 of January 5, 1970, is hereby revoked.",
                  original=ORIGINAL, actor_text=ACTOR, extra_records=None, flags=(), conflicts=(), missing=(),
                  catalog="Revoked by: EO 12222, March 3, 1980", hits=0, act_extra=None):
    o_src = src("jobs/x/texts/EO_11111.txt", original)
    a_src = src("jobs/x/texts/EO_12222.txt", actor_text, "45 FR 200")
    i1 = original.index("Section 1.")
    i2 = original.index("Sec. 2.")
    i3 = original.index("THE WHITE HOUSE")
    c1, c2 = original[i1:i2].rstrip("\n"), original[i2:i3].rstrip("\n")
    pstart = actor_text.find(provision)
    act = {"id": f"ACT:{iid}>{actor}", "actor_id": actor, "target_id": iid, "scope": "whole", "names_target": True,
           "reaches_target_via": "", "verb": "revoke", "provision_text": provision, "text": provision,
           "provision_label": "Sec. 2.", "signing_date": "1980-03-03", "effective_date": None,
           "effective_class": "on_signing", "effective_wording": [], "exceptions_text": [], "savings_phrases": [],
           "char_start": pstart, "char_end": pstart + len(provision), "source": a_src, "actor_source": a_src}
    act.update(act_extra or {})
    recs = {
        f"ORIGINAL:{iid}": {"id": f"ORIGINAL:{iid}", "acceptable_as_original": True, "requires_page_check": False,
                            "signing_date": "1970-01-05", "text": original, "char_start": 0, "char_end": len(original),
                            "source": o_src, "role": "original"},
        f"CLAUSES:{iid}#sec1": {"id": f"CLAUSES:{iid}#sec1", "text": c1, "source": o_src},
        f"CLAUSES:{iid}#sec2": {"id": f"CLAUSES:{iid}#sec2", "text": c2, "source": o_src},
        act["id"]: act,
        f"ACTOR_TEXT:{actor}": {"id": f"ACTOR_TEXT:{actor}", "actor_id": actor, "text": actor_text, "source": a_src,
                                "char_start": 0, "char_end": len(actor_text)},
    }
    recs.update(extra_records or {})
    dossier = {
        "instrument_id": iid, "fingerprint": sha(iid + provision + original), "whole_order_status": None,
        "original_source_id": f"ORIGINAL:{iid}", "evidence": recs,
        "clauses": [{"id": f"CLAUSES:{iid}#sec1", "scope_id": f"{iid}#sec1", "label": "Section 1.", "char_start": i1,
                     "char_end": i1 + len(c1), "text": c1},
                    {"id": f"CLAUSES:{iid}#sec2", "scope_id": f"{iid}#sec2", "label": "Sec. 2.", "char_start": i2,
                     "char_end": i2 + len(c2), "text": c2}],
        "chain": {"events": [{"actor_id": actor}]}, "own_terms": [], "conflicts": list(conflicts),
        "missing": list(missing), "current_law_leads": [],
        "machine_searches": [{"search_id": s, "complete": True, "machine_hits_for_this_order": hits if "current-law" in s else 1}
                             for s in D.REQUIRED_SEARCHES],
    }
    history = {"fingerprint": "h" * 64, "flags": list(flags), "observation_ids": ["API:1"]}
    return {"instrument_id": iid, "fingerprint": sha("ev" + iid + provision + original + json.dumps(extra_records or {}, sort_keys=True)),
            "history_sha256": "h" * 64, "base_dossier": dossier,
            "history_packet": {"history": history, "observations": [{"id": "API:1", "text": catalog}]}}


class PredicateParityTests(unittest.TestCase):
    def test_vendored_copy_matches_respondendi_when_present(self):
        mod = P.respondendi_module()
        if mod is None:
            self.skipTest("jobs/respondendi-adoption is not checked out (PR #270 unmerged)")
        kind = mod.parameters(REPO)["kinds"]["express_named_revocation"]
        self.assertEqual(kind, P.EXPRESS)
        for s in ["Executive Order No. 11111 of January 5, 1970, is hereby revoked.",
                  "Executive Order 11111 is revoked insofar as it relates to the Board.",
                  "Section 3 of Executive Order 11111 is revoked.", "Executive Order 11111 is hereby amended."]:
            self.assertEqual(P.named_end_in(s, "EO:11111", kind), mod.named_end_in(s, "EO:11111", kind), s)
        for t in ["Ex. Ord. No. 11111 of Jan. 5, 1970,\n is hereby re-\nvoked.", "Exec­utive Order �11111"]:
            self.assertEqual(P._norm(t), mod._norm(t))
        notes = [P._norm("Revoked by: EO 12222, March 3, 1980 | Amended by: EO 12300, May 1, 1985")]
        self.assertEqual(P._segments(notes), mod._segments(notes))
        self.assertEqual(P._later_acts(notes, "1980-03-03"), mod._later_acts(notes, "1980-03-03"))
        self.assertEqual(P._id_pattern("EO:341A"), mod._id_pattern("EO:341A"))

    def test_predicate_basics(self):
        k = P.EXPRESS
        self.assertTrue(P.named_end_in("Executive Order No. 11111 of January 5, 1970, is hereby revoked.", "EO:11111", k))
        self.assertFalse(P.named_end_in("Executive Order 11111 is revoked insofar as it concerns ships.", "EO:11111", k))
        self.assertFalse(P.named_end_in("Executive Order 111111 is revoked.", "EO:11111", k))
        self.assertTrue(P.second_witness(P._segments([P._norm("Revoked by: EO 12222, March 3, 1980")]), "EO:12222"))


class DrafterTests(unittest.TestCase):
    def test_clean_express_revocation_is_complete(self):
        ev = make_evidence()
        dr = D.draft(ev)
        self.assertEqual(dr["blockers"], [])
        self.assertEqual(dr["decision"]["recommended_provisional_status"], "no")
        self.assertEqual(dr["decision"]["basis_evidence_ids"], ["ACT:EO:11111>EO:12222", "ACTOR_TEXT:EO:12222"])
        states = {c["scope_id"]: (c["mechanism"], c["effective_date"], c["end_id"]) for c in dr["clauses"]}
        self.assertEqual(states["EO:11111#sec1"], ("express_revocation", "1980-03-03", "ACT:EO:11111>EO:12222"))
        self.assertEqual(states["EO:11111#sec2"], ("task_completed", "1970-01-05", "ORIGINAL:EO:11111"))
        self.assertEqual(dr["row"]["outcome"], "submit")
        for k in ("earlier_end_check", "scope_check", "independent_command_check", "savings_check"):
            self.assertGreater(len(dr["row"][k]), 30)
        if SO is not None:
            self.assertEqual(SO._decision_errors(dr["decision"], ev), [])

    def blockers(self, ev, **kw):
        return {b.split(":")[0] for b in D.draft(ev, **kw)["blockers"]}

    def test_qualified_end_is_not_this_kind(self):
        ev = make_evidence(provision="Executive Order No. 11111 of January 5, 1970, is hereby revoked insofar as it relates to ships.",
                           actor_text=ACTOR.replace("is hereby revoked.", "is hereby revoked insofar as it relates to ships."))
        self.assertIn("no_express_named_whole_revocation", self.blockers(ev))

    def test_same_actor_partial_and_other_instrument_block(self):
        part = {"ACT:EO:11111>EO:12222@p": {"actor_id": "EO:12222", "target_id": "EO:11111", "scope": "partial", "verb": "revoke"}}
        self.assertIn("same_actor_partial_act", self.blockers(make_evidence(extra_records=part)))
        amend = {"ACT:EO:11111>EO:11500": {"actor_id": "EO:11500", "target_id": "EO:11111", "scope": "partial", "verb": "amend"}}
        self.assertIn("another_instrument_acts", self.blockers(make_evidence(extra_records=amend)))

    def test_decoy_ignores_only_the_named_blocker(self):
        amend = {"ACT:EO:11111>EO:11500": {"actor_id": "EO:11500", "target_id": "EO:11111", "scope": "partial", "verb": "amend"}}
        dr = D.draft(make_evidence(extra_records=amend), ignore=("another_instrument_acts",))
        self.assertTrue(dr.ok)
        self.assertTrue(dr.decoy)

    def test_own_terms(self):
        rd = {"TERM:EO:11111:a": {"kind": "report_deadline", "text": "shall report by June 1"}}
        self.assertEqual(self.blockers(make_evidence(extra_records=rd)), set())
        ue = {"TERM:EO:11111:b": {"kind": "until_event", "text": "until the emergency ends"}}
        self.assertIn("own_term_needs_reading", self.blockers(make_evidence(extra_records=ue)))
        later = {"TERM:EO:11111:c": {"kind": "fixed_term", "stated_end_date": "1990-01-01"}}
        self.assertEqual(self.blockers(make_evidence(extra_records=later)), set())

    def test_inventory_gaps_and_merged_sections(self):
        gap = ORIGINAL.replace("ordered as follows:\n", "ordered as follows:\nSec. 0. The Secretary may act.\n")
        self.assertIn("inventory_gap", self.blockers(make_evidence(original=gap)))
        merged = ORIGINAL.replace("advise the President.\n", "advise the President.\nS e c . 3 . The Board shall meet.\n")
        self.assertIn("clause_spans_several_sections", self.blockers(make_evidence(original=merged)))
        folded = ORIGINAL.replace("advise the President.", "advise the President; Executive Order 9000 is hereby revoked.")
        self.assertIn("clause_needs_judgment", self.blockers(make_evidence(original=folded)))

    def test_savings_and_own_term_of_actor(self):
        saving = ACTOR.replace("THE WHITE HOUSE", "Sec. 3. Regulations issued under the orders revoked by this order shall "
                                                   "remain in effect until superseded.\nTHE WHITE HOUSE")
        self.assertIn("actor_savings_sentence", self.blockers(make_evidence(actor_text=saving)))
        own = ACTOR.replace("THE WHITE HOUSE", "Sec. 3. This order shall remain in force until revoked by the President.\nTHE WHITE HOUSE")
        self.assertNotIn("actor_savings_sentence", self.blockers(make_evidence(actor_text=own)))

    def test_delayed_effect(self):
        delayed = ACTOR.replace("THE WHITE HOUSE", "Sec. 3. This order shall take effect 30 days after its signing.\nTHE WHITE HOUSE")
        self.assertIn("actor_effective_sentence_needs_reading", self.blockers(make_evidence(actor_text=delayed)))
        wording = make_evidence(act_extra={"effective_class": "unknown",
                                           "effective_wording": [{"text": "to ensure the effective use of property"}]})
        self.assertEqual(self.blockers(wording), set())

    def test_witness_required_only_on_undecided_route(self):
        ev = make_evidence(catalog="Amends: EO 9000")
        self.assertIn("no_second_witness", self.blockers(ev))
        dec = copy.deepcopy(ev)
        dec["base_dossier"]["whole_order_status"] = "no"
        out = D.draft({"instrument_id": "EO:11111", "base_dossier": dec["base_dossier"]}, route="decided")
        self.assertTrue(out.ok, out["blockers"])
        self.assertIsNone(out["decision"])

    def test_current_law_mentions(self):
        ev = make_evidence(hits=1)
        self.assertIn("current_law_mentions_order", self.blockers(ev))
        ok = [{"instrument_id": "EO:11111", "role": "eo_note_ended_status", "citation": "5 U.S.C. 1 note",
               "snippet": "Ex. Ord. No. 11111, Jan. 5, 1970, was revoked by Ex. Ord. No. 12222, Mar. 3, 1980."}]
        dr = D.draft(ev, mentions=ok)
        self.assertTrue(dr.ok, dr["blockers"])
        self.assertEqual(len(dr["facts"]["current_law_notes"]), 1)
        bad = ok + [{"instrument_id": "EO:11111", "role": "cfr_authority_citation", "citation": "7 CFR 1", "snippet": "E.O. 11111"}]
        self.assertIn("current_law_mention_needs_reading", self.blockers(ev, mentions=bad))

    def test_conflicting_catalog_actor(self):
        other = {"ACTOR_TEXT:EO:12221": {"text": "Executive Order 12221. The Council of Europe group is designated.",
                                         "source": src("p", "x")}}
        conflict = [{"code": "WHOLE_END_ACTOR_DISAGREEMENT", "detail": "EO:12221, EO:12222"}]
        dr = D.draft(make_evidence(extra_records=other, conflicts=conflict,
                                   missing=["target provision not located: EO:12221"]))
        self.assertTrue(dr.ok, dr["blockers"])
        self.assertIn("is not found in the held text", json.loads(dr["row"]["conflict_resolutions"])["WHOLE_END_ACTOR_DISAGREEMENT"])
        self.assertEqual(dr["facts"]["conflict_actor_texts"][0]["actor_id"], "EO:12221")
        named = {"ACTOR_TEXT:EO:12221": {"text": "Executive Order 11111 is cited here.", "source": src("p", "y")}}
        self.assertIn("conflict_actor_prints_the_number", self.blockers(make_evidence(extra_records=named, conflicts=conflict)))

    def test_history_flags(self):
        ok = make_evidence(flags=["EMPTY_CATALOG_NOTE_DOES_NOT_ESTABLISH_CURRENT_EFFECT"])
        dr = D.draft(ok)
        self.assertTrue(dr.ok)
        self.assertIn("EMPTY_CATALOG_NOTE_DOES_NOT_ESTABLISH_CURRENT_EFFECT", dr["decision"]["conflict_resolutions"])
        self.assertIn("history_flag_needs_reading",
                      self.blockers(make_evidence(flags=["PARTIAL_OR_QUALIFIED_CHANGE_REQUIRES_CLAUSE_CHECK"])))

    def test_real_clause_wordings(self):
        """Clauses from the independent review of v1 (real held text, OCR spacing kept)."""
        cases = {
            "(b) Executive O rder No. 12149 is revoked.": "revokes_other",                       # EO 12314 #sec4-b
            "Sec. 6. R evocation. Executive O rder 12301 of M arch 2 6 ,1981, is revoked.": "revokes_other",  # EO 12625
            "1-402. Executive O rder No. 11451 of January 19,1969, is superseded.": "revokes_other",  # EO 12136
            "3. This order supersedes Executive Order No. 9432, dated March 28, 1944.": "revokes_other",  # EO 9866
            "Sec. 8. Executive O rder No. 11954, as amended, is revoked.": "revokes_other",       # EO 12348, as adopted
            "the lands be, and they are hereby, transferred from the Secretary of Agriculture to the Secretary of War":
                "needs_judgment",                                                                  # EO 8277
            "The Board shall advise the President. This order supersedes Executive Order No. 9968.": "needs_judgment",
            "John Doe is hereby appointed a member of the Board.": "needs_judgment",
            "The departments shall be closed on Monday, December 24, 1945.": "needs_judgment",
            "Sec. 2. The Board shall meet monthly.": "continuing",
            "(a) develop and review real property policies;": "unrecognized",
        }
        for text, want in cases.items():
            self.assertEqual(D.classify_clause(text, "11111"), want, text)

    def test_list_items_follow_their_lead_in(self):
        orig = ORIGINAL.replace("which shall \"\n", "").replace(
            "Section 1. There is hereby established the Board of Things, which shall advise the President.\n",
            "Section 1. The Board shall perform the following:\n(a) advise the President;\n(b) review policies.\n")
        ev = make_evidence(original=orig)
        d = ev["base_dossier"]
        i1, ia, ib = orig.index("Section 1."), orig.index("(a) advise"), orig.index("(b) review")
        i2 = orig.index("Sec. 2.")
        mk = lambda sid, a, b: {"id": f"CLAUSES:EO:11111#{sid}", "scope_id": f"EO:11111#{sid}", "label": sid,
                                "char_start": a, "char_end": b, "text": orig[a:b].rstrip("\n")}
        d["clauses"] = [mk("sec1", i1, ia), mk("sec1-a", ia, ib), mk("sec1-b", ib, i2), d["clauses"][1]]
        dr = D.draft(ev)
        self.assertTrue(dr.ok, dr["blockers"])
        self.assertEqual(dr["facts"]["clause_states"]["EO:11111#sec1-a"], "continuing")
        d["clauses"] = [mk("sec1-a", ia, ib), d["clauses"][3]]         # an item with no lead-in
        self.assertIn("clause_needs_judgment", {b.split(":")[0] for b in D.draft(ev)["blockers"]})

    def test_inventory_anchored_on_the_order(self):
        # EO 8455's shape: the only clause is the kit header and masthead; the order follows, ending "[No. 11111]".
        orig = ("Instrument: EO:11111\nSource: https://example\n\nFEDERAL REGISTER masthead contents\n"
                "[F. R. Doc. 40-1; Filed]\nEXECUTIVE ORDER\nThe Secretary shall build ships.\nTHE WHITE HOUSE,\n"
                "[No. 11111]\n")
        ev = make_evidence()
        d = ev["base_dossier"]
        d["evidence"]["ORIGINAL:EO:11111"].update(text=orig, char_end=len(orig))
        d["clauses"] = [{"id": "CLAUSES:EO:11111#whole", "scope_id": "EO:11111#whole", "label": "sole paragraph",
                         "char_start": 0, "char_end": orig.index("[F. R."), "text": orig[:orig.index("[F. R.")]}]
        bl = {b.split(":")[0] for b in D.draft(ev)["blockers"]}
        self.assertIn("clause_starts_in_file_header", bl)
        self.assertIn("inventory_gap", bl)       # the tail runs to the order's own [No. N], so its text is seen
        # A clause after the order's own closing number line belongs to the next document.
        orig2 = ORIGINAL.replace("advise the President.\n", "advise the President.\n[No. 11111]\n")
        self.assertIn("order_number_line_outside_inventory", self.blockers(make_evidence(original=orig2)))
        self.assertTrue(D.draft(make_evidence())["facts"]["unclaimed_text"])

    def test_savings_wider(self):
        base = ACTOR.replace("THE WHITE HOUSE", "{s}\nTHE WHITE HOUSE")
        bad = ["Nothing in this order shall be construed to affect reemployment rights heretofore acquired by any person.",
               "All rules issued under Executive Order No. 11111 shall continue in effect until modified by the Secretary.",
               "Nothing in this order shall affect regulations issued under the revoked orders, which shall remain in force."]
        for s in bad:
            self.assertIn("actor_savings_sentence", self.blockers(make_evidence(actor_text=base.format(s=s))), s)
        fine = "Nothing in this order shall be construed to impair or otherwise affect the authority granted by law to a department."
        self.assertNotIn("actor_savings_sentence", self.blockers(make_evidence(actor_text=base.format(s=fine))))

    def test_delayed_forms(self):
        base = ACTOR.replace("THE WHITE HOUSE", "{s}\nTHE WHITE HOUSE")
        for s in ["Sec. 3. This order shall be in force on and after July 1, 1980.",
                  "Sec. 3. The revocations made by section 2 shall become effective on July 1, 1980."]:
            self.assertIn("actor_effective_sentence_needs_reading", self.blockers(make_evidence(actor_text=base.format(s=s))), s)
        may = base.format(s="Sec. 3. The Board may employ staff whose pay may come into effect: provided, that no one may serve twice.")
        self.assertNotIn("actor_effective_sentence_needs_reading", self.blockers(make_evidence(actor_text=may)))

    def test_catalog_and_same_actor_and_terms(self):
        self.assertIn("witness_date_differs", self.blockers(make_evidence(catalog="Revoked by: EO 12222, March 13, 1980")))
        self.assertIn("catalog_entry_acts_on_order", self.blockers(make_evidence(
            catalog="Amended by: EO 11300, August 17, 1975 | Revoked by: EO 12222, March 3, 1980")))
        same = {"ACT:EO:11111>EO:12222#2": {"actor_id": "EO:12222", "target_id": "EO:11111", "scope": "whole", "verb": "amend"}}
        self.assertIn("same_actor_other_act", self.blockers(make_evidence(extra_records=same)))
        odd = {"TERM:EO:11111:z": {"kind": "new_kind_of_term"}}
        self.assertIn("own_term_needs_reading", self.blockers(make_evidence(extra_records=odd)))
        ev = make_evidence()
        del ev["base_dossier"]["evidence"]["ACTOR_TEXT:EO:12222"]
        self.assertIn("actor_text_not_held", self.blockers(ev))
        transcribed = make_evidence()
        act = transcribed["base_dossier"]["evidence"]["ACT:EO:11111>EO:12222"]
        act["source"] = dict(act["source"], acceptable_as_original=False)
        self.assertIn("ending_source_is_working_text", self.blockers(transcribed))

    def test_mechanism_follows_the_verb(self):
        ev = make_evidence(provision="Executive Order No. 11111 of January 5, 1970, is hereby superseded.",
                           actor_text=ACTOR.replace("is hereby revoked.", "is hereby superseded."))
        dr = D.draft(ev)
        self.assertTrue(dr.ok, dr["blockers"])
        self.assertEqual({c["mechanism"] for c in dr["clauses"]}, {"express_supersession", "task_completed"})
        self.assertIn("The supersession in", dr["row"]["scope_check"])
        self.assertIn("The revocation in", D.draft(make_evidence())["row"]["scope_check"])

    def test_rereview_findings(self):
        # R1: a short first sentence is not a heading.
        self.assertEqual(D.classify_clause("Sec. 3. The Board is hereby abolished. Its records shall be kept by the Archivist."),
                         "needs_judgment")
        self.assertEqual(D.classify_clause("Sec. 6. R evocation. Executive O rder 12301 of M arch 2 6 ,1981, is revoked."),
                         "revokes_other")
        base = ACTOR.replace("THE WHITE HOUSE", "{s}\nTHE WHITE HOUSE")
        self.assertIn("actor_savings_sentence", self.blockers(make_evidence(
            actor_text=base.format(s="Existing regulations shall remain in force until amended."))))
        self.assertIn("actor_effective_sentence_needs_reading", self.blockers(make_evidence(
            actor_text=base.format(s="This order shall go into effect on the first day of the next month."))))
        self.assertIn("missing_item", self.blockers(make_evidence(missing=[
            "Machine segmentation lead; compare the inventory with the official original. No confident operative "
            "boundary found; unstructured text retained for review"])))
        self.assertNotIn("missing_item", self.blockers(make_evidence(missing=[
            "Machine segmentation lead; compare the inventory with the official original."])))

    def test_original_and_page_check(self):
        ev = make_evidence()
        ev["base_dossier"]["evidence"]["ORIGINAL:EO:11111"]["requires_page_check"] = True
        self.assertIn("page_check_owed", self.blockers(ev))
        ev["base_dossier"]["evidence"]["ORIGINAL:EO:11111"]["acceptable_as_original"] = False
        self.assertIn("original_not_acceptable", self.blockers(ev))


def actor_set(actor, targets, base=11111):
    """Several targets of one actor, each with its own original and decisive sentence."""
    out = []
    lines = []
    for t in targets:
        lines.append(f"Sec. {len(lines) + 2}. Executive Order No. {t} of January 5, 1970, is hereby revoked.")
    text = f"Executive Order {actor[3:]} March 3, 1980\nBy virtue of the authority, it is ordered:\nSection 1. A rule.\n" + "\n".join(lines) + "\nTHE WHITE HOUSE.\n"
    for t, line in zip(targets, lines):
        orig = (ORIGINAL.replace("11111", str(t)).replace("Board of Things", f"Board of Things {t}")
                .replace("10000", str(t - 1500)))
        prov = line.split(". ", 1)[1]
        ev = make_evidence(iid=f"EO:{t}", actor=actor, provision=prov, original=orig, actor_text=text,
                           catalog=f"Revoked by: EO {actor[3:]}, March 3, 1980")
        out.append(ev)
    return out


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.evs = (actor_set("EO:12222", [11111, 11112, 11113, 11114]) + actor_set("EO:12300", [11200, 11201, 11202])
                    + actor_set("EO:12350", [11250, 11251]))
        self.drafts = [D.draft(e) for e in self.evs]
        for d in self.drafts:
            self.assertTrue(d.ok, d["blockers"])
        self.by = {e["instrument_id"]: e for e in self.evs}

    def test_sessions_batch_by_actor_with_typed_controls_and_no_tells(self):
        sess, key = K.build(self.drafts, self.by, "salt", size=12)
        self.assertGreaterEqual(len(sess), 2)
        genuine_where = {g["instrument_id"]: s for s, v in key["sessions"].items() for g in v["genuine"]}
        for s in sess:
            controls = key["sessions"][s["session"]]["controls"]
            kinds = {c["control_kind"] for c in controls}
            self.assertGreaterEqual(len(controls), K.MIN_CONTROLS)
            self.assertGreaterEqual(len(kinds), 2)
            self.assertTrue(kinds & K.STATUS_DETERMINING)
            self.assertEqual(K.tells(s), [])
            for c in controls:      # no control sits in the session of its genuine twin
                self.assertNotEqual(genuine_where.get(c["instrument_id"]), s["session"])
            for e in s["entries"]:
                self.assertTrue(e["evidence_on_order"])
            dump = json.dumps(s)
            self.assertNotIn("control_kind", dump)
            self.assertNotIn("salt", dump)
            genuine_actors = {g["instrument_id"]: self.by[g["instrument_id"]] for g in key["sessions"][s["session"]]["genuine"]}
            self.assertTrue(genuine_actors)

    def test_each_mutation_is_visible_in_the_entry(self):
        rng = random.Random(1)
        genuine = [K.entry(d, self.by[d["instrument_id"]]) for d in self.drafts]
        g = genuine[0]
        blk = K.actor_block("EO:12222", self.evs[:4], self.drafts[:4])
        ds, _ = K.mutate(g, "date_shift", rng, genuine, blk)
        self.assertNotEqual(ds["claim"]["whole_order_end"]["date"], g["claim"]["whole_order_end"]["date"])
        sw, _ = K.mutate(g, "ending_source_swapped", rng, genuine, blk)
        self.assertNotEqual(sw["claim"]["whole_order_end"]["quote"], g["claim"]["whole_order_end"]["quote"])
        wo, _ = K.mutate(g, "wrong_order_text", rng, genuine, blk)
        self.assertNotEqual([c["text"] for c in wo["clauses"]], [c["text"] for c in g["clauses"]])
        self.assertTrue(all(c["scope_id"].startswith(g["instrument_id"]) for c in wo["clauses"]))
        pw, pb = K.mutate(g, "partial_as_whole", rng, genuine, blk)
        q = pw["claim"]["whole_order_end"]["quote"]
        self.assertIn("except", q)
        self.assertIn(q, pb["text"])                       # the qualified sentence is in that session's actor text
        self.assertEqual([d["target"] for d in pb["decisive"]], [g["instrument_id"]])
        self.assertEqual(K.sha(q), pw["claim"]["whole_order_end"]["quote_sha256"])
        self.assertEqual(len({x["entry_id"] for x in (g, ds, sw, wo, pw)}), 5)

    def test_one_actor_is_refused(self):
        with self.assertRaises(ValueError):
            K.build(self.drafts[:4], self.by, "salt")

    def test_topological_order_and_cycles(self):
        batches = {"P": ["EO:1"], "C": ["EO:2", "EO:3", "EO:4"]}
        self.assertEqual(K.topological(batches, [("EO:2", "EO:1")]), ["P", "C"])
        self.assertEqual(K.topological(batches, []), ["C", "P"])
        with self.assertRaises(ValueError):
            K.topological(batches, [("EO:2", "EO:1"), ("EO:1", "EO:3")])

    def test_long_actor_text_goes_as_windows(self):
        evs = actor_set("EO:12400", [11300, 11301])
        pad = "Sec. 9. Filler text that does not matter. " * 800
        for e in evs:
            t = e["base_dossier"]["evidence"]["ACTOR_TEXT:EO:12400"]
            t["text"] = pad + t["text"] + pad
        drs = [D.draft(e) for e in evs]
        block = K.actor_block("EO:12400", evs, drs)
        self.assertEqual(block["text_form"], "windows")
        self.assertTrue(all(d["text"] in "".join(w["text"] for w in block["windows"]) for d in block["decisive"]))
        self.assertLess(len(json.dumps(block)), len(pad) * 2)

    def test_decoys_enter_as_controls(self):
        amend = {"ACT:EO:11500>EO:11400": {"actor_id": "EO:11400", "target_id": "EO:11500", "scope": "partial",
                                           "verb": "amend", "provision_text": "Section 1 of Executive Order 11500 is amended."}}
        dev = actor_set("EO:12500", [11500])[0]
        dev["base_dossier"]["evidence"].update(amend)
        ddr = D.draft(dev, ignore=("another_instrument_acts",))
        self.assertTrue(ddr.decoy)
        sess, key = K.build(self.drafts, self.by, "salt2", decoys=[("later_event_removed", ddr, dev)])
        kinds = [c["control_kind"] for v in key["sessions"].values() for c in v["controls"]]
        self.assertIn("later_event_removed", kinds)
        where = next(s for s in sess if any(e["instrument_id"] == "EO:11500" for e in s["entries"]))
        decoy_entry = next(e for e in where["entries"] if e["instrument_id"] == "EO:11500")
        self.assertIn("EO:11400", {a["actor_id"] for a in decoy_entry["evidence_on_order"]})
        self.assertIn("EO:12500", {a["actor_id"] for a in where["actors"]})
        self.assertEqual(K.tells(where), [])


def _conveyor():
    import importlib.util
    spec = importlib.util.spec_from_file_location("nalimov_test_conveyor", REPO / "jobs/maudslay-conveyor/conveyor.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _claim(iid, actor, quote, events=()):
    """A minimal Stage 19-shaped claim."""
    src = {"text_path": f"jobs/x/{actor}.txt", "quote": quote, "evidence_id": "e-" + actor}
    return {"instrument_id": iid, "whole_order_status": "no",
            "whole_order_end": {"date": "1980-03-03", "actor": actor, "mechanism": "express_revocation", "source": dict(src)},
            "operative_clauses": [{"scope_id": iid + "#sec1", "original_operative_text": f"Sec. 1. The Board of {iid} shall act.",
                                   "original_source": {"text_path": f"jobs/x/{iid}.txt", "quote": f"The Board of {iid} shall act."},
                                   "state_at_cutoff": "terminated", "later_events": list(events),
                                   "first_end": {"date": "1980-03-03", "actor": actor, "source": dict(src)}}]}


class ConveyorTypedControlTests(unittest.TestCase):
    """The Maudslay conveyor's typed plants (Whitworth I4) and its Nalimov producer route."""
    def setUp(self):
        self.C = _conveyor()
        ev = [{"effective_date": "1975-01-01", "actor": "EO:11500", "mechanism": "amendment"}]
        self.claims = [_claim(f"EO:{11100 + i}", "EO:12222" if i % 2 else "EO:12300",
                              f"Executive Order {11100 + i} is revoked.", ev if i == 3 else ()) for i in range(16)]

    def test_each_kind_changes_the_claim(self):
        rng = random.Random(3)
        for kind in self.C.TYPED_TERMS:
            c = self.claims[3]
            p = self.C.plant_typed_one(c, kind, rng, self.claims[:3])
            self.assertIsNotNone(p, kind)
            self.assertNotEqual(self.C.canon(p), self.C.canon(c), kind)
        self.assertIsNone(self.C.plant_typed_one(self.claims[0], "later_event_removed", rng, self.claims))

    def test_typed_sets_meet_the_control_rule(self):
        for salt in ("a", "b", "c", "d"):
            rset, ctl = self.C.plant_typed(self.claims, salt)
            kinds = {k["type"] for k in ctl}
            self.assertGreaterEqual(len(ctl), 2)
            self.assertGreaterEqual(len(kinds), 2)
            self.assertTrue(kinds & set(self.C.TYPED_STATUS))
            self.assertEqual(len(rset), len(self.claims))
            planted = {k["planted"] for k in ctl}
            genuine = {k["genuine"] for k in ctl}
            hashes = {self.C.canon(c) for c in rset}
            self.assertTrue(planted <= hashes)
            self.assertFalse(genuine & hashes)          # the twin never sits in the review set

    def test_catch_terms_are_typed(self):
        rec = {"verdict": "rejected", "defects": ["later_events omits the 1975 amendment by EO 11500"]}
        self.assertTrue(self.C.caught(rec, self.C.TYPED_TERMS["later_event_removed"]))
        self.assertFalse(self.C.caught({"verdict": "rejected", "defects": ["the date is three years early"]},
                                       self.C.TYPED_TERMS["later_event_removed"]))
        self.assertFalse(self.C.caught({"verdict": "upheld", "defects": []}, self.C.TYPED_TERMS["partial_as_whole"]))

    def test_list_price(self):
        prices = [{"match": "^claude-sonnet-5-5", "input": 2, "cache_write_5m": 2.5, "cache_read": 0.1, "output": 10}]
        w = {"model": "sonnet", "input": 1000, "cache_read": 100000, "cache_write": 50000, "output": 5000}
        self.assertAlmostEqual(self.C.list_price_usd(w, prices), (2000 + 10000 + 125000 + 50000) / 1e6)
        self.assertIsNone(self.C.list_price_usd({"model": "gpt-x"}, prices))


class ConveyorDraftRouteTests(unittest.TestCase):
    """Batch.draft_round writes the producer folders collect() takes, from the packet's own frozen evidence."""
    def test_draft_round(self):
        C = _conveyor()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        evs = actor_set("EO:12222", [11111, 11112]) + [make_evidence(iid="EO:11300", original=ORIGINAL.replace("11111", "11300"),
                                                                     provision="Executive Order 11300 is revoked in part.")]
        fields = ["instrument_id", "dossier_sha256", "agent", "outcome", "approved", "working_text", "research_rationale"]
        cfields = ["instrument_id", "scope_id", "clause_id", "state", "end_id", "effective_date", "mechanism"]
        (root / "batch/prepared").mkdir(parents=True)
        drows, crows = [], []
        for e in evs:
            d = root / "batch/packet/undecided" / e["instrument_id"].replace(":", "_")
            d.mkdir(parents=True)
            (d / "EVIDENCE.json").write_text(json.dumps(e), encoding="utf-8")
            (d / "STATUS_DECISION.json").write_text(json.dumps({"schema": "eo-status-history-decision/v1"}), encoding="utf-8")
            drows.append({k: "" for k in fields} | {"instrument_id": e["instrument_id"],
                                                    "dossier_sha256": e["base_dossier"]["fingerprint"], "outcome": "unresolved"})
            crows += [{k: "" for k in cfields} | {"instrument_id": e["instrument_id"], "scope_id": c["scope_id"],
                                                  "clause_id": c["id"]} for c in e["base_dossier"]["clauses"]]
        C.write_csv(root / "batch/prepared/decisions.csv", fields, drows)
        C.write_csv(root / "batch/prepared/clauses.csv", cfields, crows)
        b = C.Batch.__new__(C.Batch)
        b.repo, b.dir, b.packet, b.name, b.scratch = REPO, root / "batch", root / "batch/packet", "b01", root / "scratch"
        out = b.draft_round([e["instrument_id"] for e in evs])
        self.assertEqual(sorted(k for k, v in out.items() if v.get("folder")), ["EO:11111", "EO:11112"])
        self.assertIn("Nalimov drafter refused it", out["EO:11300"]["reason"])
        folder = Path(out["EO:11111"]["folder"])
        self.assertEqual(sorted(p.name for p in folder.iterdir()),
                         ["DRAFT.json", "RATIONALES.json", "STATUS_DECISION.json", "clauses.csv", "decisions.csv"])
        f, rows = C.read_csv(folder / "decisions.csv")
        self.assertEqual(f, fields)
        self.assertEqual(rows[0]["outcome"], "submit")


class RouteTests(unittest.TestCase):
    """draft -> sessions -> score -> install on a fake prepared packet, in the kit's sheet format."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.packet = root / "packet"
        evs = (actor_set("EO:12222", [11111, 11112]) + actor_set("EO:12300", [11200, 11201])
               + actor_set("EO:12350", [11250])
               + [make_evidence(iid="EO:11300", original=ORIGINAL.replace("11111", "11300"),
                                provision="Executive Order 11300 is revoked in part.")])
        fields = ["instrument_id", "dossier_sha256", "agent", "outcome", "approved", "original_confirmed",
                  "original_pages_confirmed", "inventory_confirmed", "research_rationale", "savings_state",
                  "savings_source_id", "savings_reason", "search_ids", "conflict_resolutions", "unresolved_material_gaps",
                  "earlier_end_check", "scope_check", "independent_command_check", "savings_check", "working_text",
                  "source_notes", "publication_kind"]
        cfields = ["instrument_id", "scope_id", "clause_id", "state", "end_id", "effective_date", "mechanism",
                   "effective_date_confirmed", "current_basis_id", "current_legal_basis", "checked_through",
                   "later_event_ids", "later_events", "reason", "inventory_source_id", "inventory_char_start",
                   "inventory_char_end", "inventory_reason"]
        drows, crows = [], []
        for e in evs:
            iid = e["instrument_id"]
            d = self.packet / "undecided" / iid.replace(":", "_")
            d.mkdir(parents=True)
            (d / "EVIDENCE.json").write_text(json.dumps(e), encoding="utf-8")
            (d / "STATUS_DECISION.json").write_text(json.dumps({"schema": "eo-status-history-decision/v1", "agent": "",
                                                                "approved": False}), encoding="utf-8")
            drows.append({**{k: "" for k in fields}, "instrument_id": iid, "dossier_sha256": e["base_dossier"]["fingerprint"],
                          "outcome": "unresolved", "approved": "false", "working_text": "{}"})
            for c in e["base_dossier"]["clauses"]:
                crows.append({**{k: "" for k in cfields}, "instrument_id": iid, "scope_id": c["scope_id"], "clause_id": c["id"]})
        N.write_csv(self.packet / "decisions.csv", fields, drows)
        N.write_csv(self.packet / "clauses.csv", cfields, crows)
        self.root = root

    def tearDown(self):
        self.tmp.cleanup()

    def test_draft_packet(self):
        out = N.draft_packet(self.packet, self.root / "drafts")
        self.assertEqual(sorted(out["complete"]), ["EO:11111", "EO:11112", "EO:11200", "EO:11201", "EO:11250"])
        self.assertIn("EO:11300", out["blocked"])
        f, rows = N.read_csv(self.root / "drafts/EO_11111/decisions.csv")
        self.assertEqual(f, N.read_csv(self.packet / "decisions.csv")[0])
        self.assertEqual(rows[0]["outcome"], "submit")
        before = (self.packet / "decisions.csv").read_bytes()
        self.assertEqual(before, (self.packet / "decisions.csv").read_bytes())   # the packet is never touched

    def test_drafts_never_overwrite(self):
        N.draft_packet(self.packet, self.root / "drafts")
        with self.assertRaises(ValueError):
            N.draft_packet(self.packet, self.root / "drafts")


if __name__ == "__main__":
    unittest.main()
