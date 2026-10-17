import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from claim_gate import claim_sha, validate_claim, validate_review
from early_ranger import ROOT, fetch_loc, load_leads, routes_for, score_result
from validate_worksheet import validate as validate_worksheet


def ref(label="item"):
    return {"url":"https://www.govinfo.gov/example/"+label,"page_or_item":"p. 1","archival_id":"TEST:"+label}


def no_claim():
    return {
        "schema":"eo-lifecycle-claim/v1","instrument_id":"EO:TEST","whole_order_status":"no",
        "original_representation":ref("original"),
        "operative_clauses":[{"scope_id":"all","original_operative_text":"A substantive test directive with one operative scope.","original_source":ref("original"),"state_at_cutoff":"terminated","first_end":{"date":"1950-01-01","actor":"Congress","mechanism":"statutory transfer","source":ref("statute")},"later_events":[]}],
        "whole_order_end":{"date":"1950-01-01","actor":"Congress","mechanism":"statutory transfer","source":ref("statute")},
        "savings_residuals":{"state":"transferred_or_accrued","reason":"Prior judgments transfer and remain enforceable.","source":ref("statute")},
        "later_source_search":[{"repository":"GovInfo","query_or_scope":"later amendments and savings through cutoff","checked_on":"2026-10-17"}],
        "unresolved_material_gaps":[],
        "research_rationale":"The complete operative clause ended at the statutory transfer; later effects were separately traced."
    }


class Gates(unittest.TestCase):
    def test_no_requires_first_cause_and_review(self):
        claim=no_claim()
        self.assertEqual(validate_claim(claim,"no"),[])
        claim["operative_clauses"][0]["first_end"]["date"]="not a date"
        self.assertIn("clause_0_first_end",validate_claim(claim,"no"))
        claim=no_claim()
        review={"schema":"eo-lifecycle-review/v1","instrument_id":"EO:TEST","claim_sha256":claim_sha(claim),"reviewer":"Independent Historian","reviewer_role":"independent_human","decision":"uphold","rationale":"I checked the original order, later statute, and contrary cessation dates against the source pages.","checked_source_urls":[ref("original")["url"],ref("statute")["url"]],"reviewed_on":"2026-10-17"}
        self.assertEqual(validate_review(review,claim),[])
        review["checked_source_urls"]=[ref("original")["url"]]
        self.assertIn("unchecked_cited_source",validate_review(review,claim))
        review["checked_source_urls"].append(ref("statute")["url"])
        claim["whole_order_end"]["date"]="1950-01-02"
        self.assertIn("stale_claim_fingerprint",validate_review(review,claim))
        self.assertIn("whole_order_end_not_last_clause_end",validate_claim(claim,"no"))

    def test_yes_requires_current_predicate(self):
        claim=no_claim()
        claim["whole_order_status"]="yes"
        claim["whole_order_end"]=None
        clause=claim["operative_clauses"][0]
        clause["state_at_cutoff"]="operative"
        clause.pop("first_end")
        clause["current_predicate"]={"legal_basis":"unrevoked operative section with bounded later search","source":ref("current"),"checked_through":"2026-10-14"}
        self.assertEqual(validate_claim(claim,"yes"),[])
        claim["operative_clauses"][0].pop("current_predicate")
        self.assertIn("clause_0_current_predicate",validate_claim(claim,"yes"))

    def test_offline_archival_representation_and_later_event_date(self):
        claim=no_claim()
        claim["original_representation"]={"archival_id":"NARA:box-1","local_file_sha256":"a"*64,"page_or_item":"folio 4"}
        self.assertEqual(validate_claim(claim,"no"),[])
        claim["operative_clauses"][0]["later_events"]=[{"actor":"President","mechanism":"amendment","source":ref("amendment")}]
        self.assertIn("clause_0_later_event_evidence",validate_claim(claim,"no"))

    def test_offline_review_can_cite_archival_item(self):
        claim=no_claim()
        claim["original_representation"]={"archival_id":"NARA:box-1","local_file_sha256":"a"*64,"page_or_item":"folio 4"}
        review={"schema":"eo-lifecycle-review/v1","instrument_id":"EO:TEST","claim_sha256":claim_sha(claim),"reviewer":"Independent Historian","reviewer_role":"independent_human","decision":"uphold","rationale":"I checked the archived original and subsequent statute, including the original clause and residuals.","checked_source_urls":[ref("original")["url"],ref("statute")["url"]],"checked_archival_items":["NARA:box-1"],"reviewed_on":"2026-10-17"}
        self.assertEqual(validate_review(review,claim),[])

    def test_worksheet_is_not_certification(self):
        packet={"instrument":{"id":"EO:TEST"},"packet_fingerprint":"abc"}
        work={"schema":"eo-lifecycle-worksheet/v1","instrument_id":"EO:TEST","packet_fingerprint":"abc","reviewer":"Researcher","disposition":"hold"}
        self.assertEqual(validate_worksheet(packet,work),[])
        work["packet_fingerprint"]="old"
        self.assertIn("stale_packet_fingerprint",validate_worksheet(packet,work))
        work["packet_fingerprint"]="abc"
        work["disposition"]="research_proposal"
        self.assertIn("original_source_and_page",validate_worksheet(packet,work))


class Ranger(unittest.TestCase):
    def test_all_leads_remain_uncounted_and_have_routes(self):
        leads=load_leads()
        self.assertEqual(len(leads),1041)
        self.assertEqual(sum(bool(x["known_primary_source_url"]) for x in leads),6)
        self.assertTrue(all(x["inclusion_state"]!="included" for x in leads))
        survey=[x for x in leads if x["lead_origin"]=="systematic_18c_survey"]
        self.assertEqual(len(survey),12)
        self.assertEqual(len(routes_for(survey[0])),6)
        route=routes_for(next(x for x in leads if x["lead_id"]=="LORD-1789-10-13"))
        self.assertGreaterEqual(len(route),3)
        self.assertTrue(all(x["state"]=="planned_not_searched" for x in route))

    def test_public_loc_response_is_cached_and_only_a_candidate(self):
        lead=next(x for x in load_leads() if x["lead_id"]=="LORD-1789-10-13")
        route=routes_for(lead)[0]
        body=json.dumps({"results":[{"id":"https://www.loc.gov/item/test/","title":"Pension regulation 1789","date":"1789","description":["By command"]}],"pagination":{"of":1}}).encode()
        class Response(io.BytesIO):
            status=200
            headers={"Content-Type":"application/json"}
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        with tempfile.TemporaryDirectory(dir=ROOT / "research" / "stage19") as temp:
            with patch("early_ranger.urllib.request.urlopen",return_value=Response(body)):
                matches,failures=fetch_loc([route],{lead["lead_id"]:lead},Path(temp),1,0)
            self.assertFalse(failures)
            self.assertEqual(len(matches),1)
            self.assertEqual(matches[0]["result_state"],"search_hit_not_authenticated")
            self.assertTrue(list(Path(temp).glob("*.json")))
            self.assertGreaterEqual(score_result(lead,{"title":"Pension regulation 1789","date":"1789"}),3)


if __name__=="__main__":
    unittest.main()
