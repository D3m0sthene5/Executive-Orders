"""Arm A: explicit per-order decisions through the existing blank_sheet/assemble API.

Experimental proposals only. Reads exactly the six frozen A dossiers, their
declared source text files, and the existing assembler. No canonical writes.
"""
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import sys

REPO = Path(__file__).resolve().parents[7]
HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "dossiers"
NUMBERS = [12720, 12813, 12734, 12817, 12696, 12722]
AGENT = "matched-a-independent-producer"


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


spec = importlib.util.spec_from_file_location("existing_claim_kit_assemble", REPO / "jobs/claim-kit/assemble.py")
assemble = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assemble)


def corrected_inventory(dossier, spans):
    original = dossier["evidence"][dossier["original_source_id"]]
    text = original["text"]
    overrides = []
    for label, start, end in spans:
        while end > start and text[end-1].isspace():
            end -= 1
        overrides.append({"scope_id": dossier["instrument_id"] + "#" + label,
                          "source_id": dossier["original_source_id"],
                          "char_start": start, "char_end": end,
                          "reason": "Producer read the complete held original; restore this operative section/subsection boundary omitted or conflated by OCR segmentation. Page furniture and signatures are not independent commands."})
    clauses, evidence, errors = assemble.derive_inventory(dossier, overrides)
    if errors:
        raise ValueError(errors)
    return overrides, clauses


def source_integrity(dossier):
    records = []
    seen = set()
    for evidence_id, record in dossier["evidence"].items():
        source = record.get("source", {})
        path = source.get("text_path")
        if not path or path in seen:
            continue
        seen.add(path)
        p = REPO / path
        item = {"text_path": path, "exists": p.is_file(), "declared_text_sha256": source.get("text_sha256")}
        if p.is_file():
            content = p.read_bytes()
            item["actual_text_sha256"] = hashlib.sha256(content).hexdigest()
            item["hash_matches"] = item["actual_text_sha256"] == source.get("text_sha256")
        records.append(item)
    return records


def decision_for(d):
    n = int(d["instrument_id"].split(":")[1])
    s = assemble.blank_sheet(d, AGENT)
    s["producer_review_scope"] = "Experimental owner-reviewable proposal; no human certification, canonical publication, or status change."
    s["source_review_method"] = "Read full frozen original text and full relevant actor legal bodies. Original page-image confirmation remains false; frozen original evidence marks requires_page_check=false. EO13350 body pages 1-3 independently rendered and viewed."
    s["legal_cutoff_reviewed"] = "2026-10-14"
    s["original_pages_confirmed"] = False
    s["current_cutoff_limits"] = "U.S. Code machine coverage ends 2026-10-09 and is not used as a current operative predicate. eCFR search is point-in-time 2026-10-14; catalog/disposition search includes 6,938 catalog records and 7,619 held order texts. These are bounded negative searches, not a claim of exhaustive worldwide coverage."
    # Every decision below is individual; no family approval is used.
    if n == 12720:
        spans = [("sec1-a",1047,1263),("sec1-b",1264,1364),("sec2-a",1365,1547),
                 ("sec2-b",1548,1778),("sec3-a",1779,2061),("sec3-b",2062,2430),
                 ("sec3-c",2431,2797),("sec3-d",2798,3145),("sec3-e",3308,3402)]
        # End the FACA delegation before page furniture, at the last word of its sentence.
        text = d["evidence"][d["original_source_id"]]["text"]
        delegation_end = text.index("General Services.",2798) + len("General Services.")
        spans[7] = ("sec3-d",2798,delegation_end)
        overrides, inventory = corrected_inventory(d, spans)
        s["inventory_overrides"] = overrides
        end_id, date = "ACTOR_TEXT:EO:12783", "1993-01-16"
        reasons = {
            "sec1-a":"Council creation and membership cap operate only while the Council exists; amended section 3(e) ends it January 16, 1993.",
            "sec1-b":"Appointment of the Council's Chairman and Vice Chairman depends on the continuing Council, ended January 16, 1993.",
            "sec2-a":"Advice to the President and Economic Policy Council is the Council's function, not an independent post-Council mandate.",
            "sec2-b":"Continuing reviews are expressly the Council's advisory duties and cease with its amended sunset.",
            "sec3-a":"Executive-agency information duty runs to this Council solely to carry out its functions; it does not command an independent rural-development program after sunset.",
            "sec3-b":"Uncompensated service and travel entitlement concern work on the Council. No new Council service is authorized after sunset; any already accrued travel claims are residuals.",
            "sec3-c":"Farmers Home Administration support and Agriculture funding are expressly for Council operations/functions and have no separate prospective object after the Council ends.",
            "sec3-d":"The FACA delegation is limited to functions applicable to this Council and expressly excludes reporting to Congress. It creates no independent annual report command that survives the Council.",
            "sec3-e":"EO12783 replaces the original two-year sunset with the express date January 16, 1993. This is the amended sunset of the Council, not an inferred amendment signing-date onset or a reporting deadline."
        }
        rationale = "EO12720 establishes only the Council and its appointments, advice, reviews, information, travel, support/funding and Council-specific FACA administration. EO12783 expressly substitutes January 16, 1993 for the original two-year sunset, so July 16, 1992 does not control. All independent-looking agency duties are expressly tied to that Council. The amended Council sunset supplies the first cessation of those functions; the later express revocation in EO12869 section 4(c), effective September 30, 1993 by its section 6, is cleanup rather than the first functional ending. No exact onset date for EO12783 is inferred from its signing date."
        savings = "Council service and travel already earned may leave accrued reimbursement rights under section 3(b); no occurrence or pending claim is asserted. Such liabilities are residual, not a new advisory, support, funding or reporting command. EO12869 contains no savings giving this Council continuing independent functions."
    elif n == 12813:
        spans = [("sec1",1190,1546),("sec2",1547,1994),("sec3-a",1995,2129),
                 ("sec3-b",2130,2468),("sec3-c",2469,2662),("sec3-d",2663,2797),
                 ("sec4-a",2798,3158),("sec4-b",3159,3228)]
        text = d["evidence"][d["original_source_id"]]["text"]
        spans[-1] = ("sec4-b",3159,text.index("THE WHITE HOUSE",3159))
        overrides, inventory = corrected_inventory(d, spans)
        s["inventory_overrides"] = overrides
        end_id, date = "ACTOR_TEXT:EO:12815", "1992-12-31"
        reasons = {
            "sec1":"Establishment, five private-sector members and designation of the Chairman are all features of the Commission that terminates under amended section 4(b).",
            "sec2":"Advice to AID and progress reports to the Deputy Secretary of State are Commission functions. The prior statutory commission's May 16, 1992 end is contextual, not this Commission's ending.",
            "sec3-a":"AID funding is specifically funding for this Commission and has no separate prospective authorization once it ends.",
            "sec3-b":"Uncompensated service and statutory travel expenses are tied to work on the Commission. Existing travel claims may accrue; no new Commission work follows the amended sunset.",
            "sec3-c":"Reimbursable administrative services require this Commission's Chairman's request and AID's judgment, so the prospective authority depends on this Commission.",
            "sec3-d":"Procurement authority belongs to the Commission Chairman through AID and concerns temporary/intermittent services; it does not set up a continuing independent procurement program.",
            "sec4-a":"The FACA delegation to AID is expressly for functions applicable to this Commission and ceases prospectively with that body.",
            "sec4-b":"EO12815 expressly substitutes December 31, 1992 for September 30, 1992. The substituted not-later-than sunset closes the Commission absent evidence of a legally earlier ending; no report date or amendment signing date is used as an end."
        }
        rationale = "The machine's lone whole clause is only header material, so all eight operative sections/subsections are reconstructed from the frozen complete original exact spans. EO12815 changes section 4(b)'s September 30 date to December 31, 1992. Neither the earlier statutory predecessor commission nor the original superseded September date ends this Commission. No earlier termination act is held or identified by the bounded later-event search; December 31 is the amended self-executing outer sunset. Advice, progress reporting, funding, travel, support, procurement and FACA administration all attach to this Commission. EO12869 section 4(b), effective September 30, 1993 under section 6, subsequently revokes the order but does not establish its first functional ending."
        savings = "Already accrued travel reimbursements and liabilities from properly procured Commission services may persist; no particular transaction is asserted. They are residual accrued matters. The original and EO12869 provide no independent continuing AID advisory, reporting or administrative command for this Commission after its amended sunset."
    elif n == 12734:
        inventory = d["clauses"]
        end_id, date = "ACT:EO:12734>EO:13350", "2004-07-30"
        reasons = {"whole":"The complete unnumbered command invokes 10 USC 2808 emergency-construction authority for Defense and military departments and requires immediate effectiveness/transmittal/publication. EO13350 expressly revokes EO12734, and section 10 supplies July 30, 2004 at 12:01 a.m. EDT. No earlier own-term sunset or distinct continuing command appears in the original. Completed transmission/publication is an ancillary historical execution, not an independent current command."}
        rationale = "EO12734's complete text invokes 10 USC 2808 in relation to the EO12722 Iraq emergency. Its citations of EO12722 and the original emergency are predicates rather than earlier revocations of an order that did not yet exist; the machine missing-target-provision entries for EO12722 and EO12724 do not identify a post-EO12734 contrary act. EO13350 expressly names and revokes EO12734 and terminates the predicate emergency. Its section 10 expressly sets 12:01 a.m. EDT July 30, 2004, distinct from July 29 signing. Section 1 preserves completed actions, proceedings and matured rights/duties rather than prospective construction authority under EO12734. No earlier legal termination is identified within the held named-actor chain or bounded corpus searches."
        savings = "EO13350 section 1 preserves prior actions, pending proceedings, actions based on prior acts, matured rights/duties and incurred penalties. Those accrued matters may concern construction already undertaken; this proposal asserts no particular project completion. Section 1's continued blocking rule expressly concerns EO12722/12724 property, not an independent prospective construction command in EO12734."
    elif n == 12817:
        spans = [("sec1",1551,2291),("sec2",2292,2930),("sec3",2931,3504),
                 ("sec4",3505,4636),("sec5",4637,5481),("sec6",5482,6032),
                 ("sec7",6033,6308),("sec8",6309,6451)]
        overrides, inventory = corrected_inventory(d, spans)
        s["inventory_overrides"] = overrides
        end_id, date = "ACT:EO:12817>EO:13350", "2004-07-30"
        reasons = {
            "sec1":"Treasury implementation authority for Resolution 778 and repaid assets is prospective authority revoked expressly by EO13350; no factual completion date is inferred from a transfer program.",
            "sec2":"The financial-institution transfer command is conditional on Treasury determinations and directions and is revoked prospectively by EO13350. Receipt of one transfer would not prove every potential transfer completed.",
            "sec3":"New York Federal Reserve receipt, holding, investment and onward transfers are continuing commands until revoked, with accrued obligations addressed as residuals.",
            "sec4":"Discharge, good-faith protection and preservation of pre-transfer rights are assessed expressly: protection for transactions already performed can remain accrued, but it supplies no independent command to make new transfers after revocation.",
            "sec5":"The financial-institution definition serves the transfer/implementation commands and has no independent prospective operation after those commands are revoked.",
            "sec6":"Treasury rulemaking, redelegation and all-agency implementation duties implement this order and are expressly revoked with it; preserved prior actions and matured duties are residual matters.",
            "sec7":"The no-private-right clause limits enforcement of this order and is ancillary to the order's implementation; it does not supply an independent ongoing asset-transfer mandate.",
            "sec8":"Immediate effectiveness and transmittal/publication concern enactment and notice of this order; completed notice is not a current independent obligation. The last prospective authority is expressly revoked effective July 30, 2004, 12:01 a.m. EDT under EO13350 section 10."
        }
        rationale = "The original complete text has eight sections. OCR conflates sections 1/2 and invents a standalone empty section 8; exact overrides restore the complete inventory. EO13350 expressly revokes EO12817 and section 10 sets July 30, 2004 at 12:01 a.m. EDT, not its July 29 signing date. No unproved occurrence of Treasury determinations, transfers, UN repayments, or exhaustion of asset accounts is used as an earlier end. Section 4 discharge/good-faith protection and preservation of pre-transfer rights remain accrued consequences; the no-private-right provision is ancillary. EO13350 section 1 saves prior actions, pending proceedings and matured rights/duties. Its continuing blocking language is expressly for EO12722/12724, not fresh EO12817 transfer authority. No independent original command survives the express revocation within the bounded evidence."
        savings = "EO12817 section 4 gives completed-transfer acquittance, good-faith protection and preservation of pre-transfer rights, debts and claims. EO13350 section 1 saves prior actions/proceedings and matured rights/duties/penalties. Such accrued legal consequences are retained, without asserting a particular transfer occurred; no new transfer, investment, repayment or rulemaking command continues independently under EO12817."
    else:
        return unable_decision(s, d, n)

    s["original_confirmed"] = True
    s["inventory_confirmed"] = True
    s["approved"] = True
    s["unresolved_material_gaps"] = []
    s["search_ids"] = ["current-law:usc", "current-law:ecfr", "later-events:ofr_catalog"]
    s["research_rationale"] = rationale + " The selected original text is complete on its face and its bytes/provenance are pinned; page-image authentication is not claimed. Searches are accepted only for the bounded contrary-evidence task through the specified cutoff, not as substantive proof of an operative current predicate."
    s["savings"] = {"state":"transferred_or_accrued", "source_id":d["original_source_id"] if n in (12720,12813) else "ACTOR_TEXT:EO:13350", "reason":savings}
    s["clauses"] = []
    formal = "ACT:EO:" + str(n) + ">EO:12869"
    for c in inventory:
        label = c["scope_id"].split("#",1)[1]
        row = {"scope_id":c["scope_id"],"state":"terminated","end_id":end_id,
               "effective_date":date,"effective_date_confirmed":True,
               "mechanism":"own_terms_fixed_term_as_amended" if n in (12720,12813) else "express_revocation",
               "current_basis_id":None,"current_legal_basis":"","checked_through":None,
               "later_event_ids":[],"later_events":[],"reason":reasons[label]}
        if not s["inventory_overrides"]:
            row["clause_id"] = c["id"]
        if n in (12720,12813):
            row["later_events"] = [{"id":formal,"effective_date":"1993-09-30","effective_date_confirmed":True,"mechanism":"formal_revocation_after_amended_council_sunset"}]
            row["later_event_ids"] = [formal]
        s["clauses"].append(row)
    s["earlier_endings_and_partial_scope"] = (
        "The amendment's substitution of the sunset text is read as continuation of the same sunset scope in amended form. Its date of onset is not asserted. The explicit final sunset is the first end of the Council/Commission functions; later formal revocation is recorded separately."
        if n in (12720,12813) else
        "No original own-term sunset. Do not infer completion/exhaustion or termination from a report or publication deadline. All held actual later change provisions and independent original commands were reviewed."
    )
    s["material_gaps_resolved"] = list(d.get("missing",[]))
    if n == 12734:
        s["missing_lead_dispositions"] = {"target provision not located: EO:12722":"Original emergency predates EO12734; source text read as predicate, no nonexistent prospective target provision required.", "target provision not located: EO:12724":"Held actor also predates EO12734 and does not alter its later construction invocation; this is a machine relationship gap, not missing later ending evidence."}
    return s


def unable_decision(s, d, n):
    s["approved"] = False
    s["search_ids"] = []
    if n == 12696:
        s["original_confirmed"] = False
        s["inventory_confirmed"] = False
        gaps = ["Selected frozen ORIGINAL:EO:12696 recheck text stops after section 3(c) at the page-12 FR Doc line. The fully read alternate text jobs/fr-originals/output/texts/EO_12696.txt, cited by frozen own-terms evidence, holds section 3(d), section 4(a) and section 4(b) outside this selected original. The existing derive_inventory interface may only select spans inside the selected original, so it cannot reconstruct those absent clauses against the exact frozen dossier.",
                "Inspect official original pages 54 FR 47507-47508 (PDF pages 11-12) to satisfy the alternate representation's requires_page_check=true, reconcile the erroneous truncated recheck selection, and issue a corrected separately frozen dossier. The alternate full OCR is held; this is not evidence exhaustion or a claim that no text exists."]
        s["research_rationale"] = "Independent review finds a real frozen original-selection/inventory blocker, despite the selected source's requires_page_check=false and dossier missing=[] fields. The full alternate original cited by own-terms evidence was then read: section 3(d) requires departments/agencies to provide information requested for Council functions; section 4(a) delegates Council-specific FACA functions to the ONDCP Director and excepts Congress reporting; section 4(b) has the 24-month sunset. These are Council-dependent commands, not an identified independent program. EO12756 section 1 expressly continues the Council until November 13, 1993, superseding the original November 13, 1991 candidate, and section 2 merely raises section 1(a)'s membership cap 30 to 35. EO12869 section 4(d) expressly revokes EO12696 effective September 30, 1993 by section 6, before the extension's end. The likely final date is not promoted because selected-original spans cannot supply a complete frozen inventory and the alternate requires official page inspection."
        s["earlier_endings_and_partial_scope"] = "Original 24-month sunset is a candidate only and cannot bypass EO12756's express continuation. Membership amendment is partial. September 30, 1993 is explicitly EO12869's effective revocation date, not a date inferred from signing; no complete-order finding is approved."
        s["savings"] = {"state":None,"source_id":"ACTOR_TEXT:EO:12869","reason":"The full alternate original shows only Council-dependent advice, support, information, travel and FACA administration (with Congress reporting excepted); accrued travel reimbursement may survive. Held revoker has no target-specific savings continuing those functions. Source-selection/page reconciliation is still required before a complete frozen claim can be approved."}
        for c in s["clauses"]:
            c["reason"] = "Visible Council clause reviewed; no state/first-end is approved because the selected complete-original inventory is materially incomplete. See precise gaps and candidate chronology."
    else:
        s["original_confirmed"] = True
        s["inventory_confirmed"] = False
        gaps = ["CONFLICT NO_ORDER_CITED_IN_CURRENT_LAW remains unresolved: full attributable cutoff-valid text of 31 CFR 576.201(b) and the 50 USC 1701 'Iraq Sanctions' note is missing from frozen legal evidence; snippets do not establish continuation, repeal or savings scope.",
                "EO12724 section 6 revokes EO12722 only to the extent inconsistent and continues administrative actions under EO12724. A provision-by-provision inconsistency determination is required to establish each first end; a single 2004 revocation date cannot replace this earlier partial scope analysis.",
                "Restore original inventory boundaries: the national-emergency declaration precedes the machine lead clause; split section 2(h) from the definition and section 4 from the final transmission command. Exact spans are available but approving the legal state still requires partial-revocation/current-law closure.",
                "Establish cutoff currency of the statutory Iraq Sanctions note for 2026-10-10 through 2026-10-14, not merely release-point 119-121's 2026-10-09 coverage."]
        s["research_rationale"] = "The full original and held actor texts were read. EO12724 section 6 is an actual partial revocation with savings, effective immediately under its section 4; it needs clause-by-clause inconsistency analysis. EO12771 section 1 revokes Kuwaiti orders 12723/12725 and expressly leaves the EO12722 emergency unaffected, so the machine whole-revocation link is not a legal end here. EO12743 invokes military authorities in furtherance of the emergency without a located repeal of EO12722. EO12817 implements asset transfers and protects accrued transfer rights. EO13303 section 2(a) removes specified property from EO12722/12724 and section 2(b) expressly preserves prior administrative measures subject to exceptions. EO13350 revokes EO12722 effective July 30, 2004 at 12:01 a.m. EDT and saves accrued matters while expressly continuing some blocked-property prohibitions. Current 31 CFR 576.201 and 50 USC 1701 note leads may bear directly on residual independence and cutoff status; only snippets are held. They must be acquired and read, not resolved by treating every citation as current law or every nominal revocation as total cessation."
        s["earlier_endings_and_partial_scope"] = "The actual EO12724/13303 partial changes and express EO13350 continuation defeat a blanket same-date first-end assignment. EO12771 is a false-positive target relation. EO13350's explicit section 10 supplies the 2004 effective date, but that is insufficient to resolve earlier first ends or the current-law conflict."
        s["savings"] = {"state":None,"source_id":"ACTOR_TEXT:EO:13350","reason":"Section 1 distinguishes NEA accrued savings from continued prohibitions on property blocked under EO12722/12724. This may be a continuing independent rule under the later order, not merely accrued rights. Full current regulation and statutory note are needed before choosing a whole-order savings state."}
        for c in s["clauses"]:
            c["reason"] = "Original command read; state and first-end remain unapproved pending the individual EO12724 inconsistency analysis, EO13303 property carveout, and current-law/savings evidence. No group revocation date is assigned."
    s["unresolved_material_gaps"] = gaps
    return s


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    audit, outcomes, claims, integrity = [], [], [], []
    existing = HERE / "ASSEMBLER_AUDIT.json"
    if existing.exists():
        raise RuntimeError("Audit exists: preserve it and run a separately named correction attempt rather than overwrite.")
    ownership = json.loads((HERE.parent / "OWNERSHIP.json").read_text(encoding="utf-8"))
    for n in NUMBERS:
        path = FROZEN / f"EO_{n}.json"
        d = json.loads(path.read_text(encoding="utf-8"))
        s = decision_for(d)
        dump(HERE / "decisions" / f"EO_{n}.json", s)
        claim, errors = assemble.assemble(s, d, REPO)
        attempt = {"attempt":1,"instrument_id":d["instrument_id"],"dossier_path":str(path.relative_to(REPO)),
                   "dossier_file_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                   "dossier_fingerprint":d["fingerprint"],"decision_path":f"decisions/EO_{n}.json",
                   "producer_approved":s["approved"],"assembler_errors":errors,"claim":claim,
                   "assembler_claim_sha256":assemble.canonical_sha(claim) if claim else None,
                   "post_assembly_check_errors":assemble.check_claim(claim,REPO,d) if claim else None}
        dump(HERE / "attempts" / f"EO_{n}-attempt-01.json", {"sheet":s,"result":attempt})
        audit.append(attempt)
        route = ownership[d["instrument_id"]]["route"]
        outcome = "producer_approved_assembled_proposal" if claim and not errors else "unable_from_frozen_evidence" if not s["approved"] else "assembly_failed"
        outcomes.append({"instrument_id":d["instrument_id"],"outcome":outcome,"ownership_route":route,
                         "decision_path":f"decisions/EO_{n}.json","approved":s["approved"],
                         "assembler_pass":claim is not None and not errors,"assembler_error_count":len(errors),
                         "proposed_whole_order_end":claim.get("whole_order_end") if claim else None,
                         "unresolved_material_gaps":s["unresolved_material_gaps"]})
        integrity.append({"instrument_id":d["instrument_id"],"dossier_fingerprint_matches":assemble.canonical_sha(d)==d["fingerprint"],
                          "dossier_bytes":path.stat().st_size,"held_source_texts":source_integrity(d)})
        if claim:
            claims.append(claim)
        print(d["instrument_id"],outcome,len(errors),errors)
    dump(HERE / "ASSEMBLER_AUDIT.json",audit)
    dump(HERE / "OUTCOMES.json",{"schema":"matched-research-producer-outcomes/v1","arm":"A","interface":"existing blank_sheet/assemble, independent per-order JSON decisions",
                                  "legal_cutoff":"2026-10-14","experimental_only":True,"publication":False,
                                  "counts":{"members":len(outcomes),"producer_approved_assembled_proposals":sum(o["assembler_pass"] for o in outcomes),
                                            "unable":sum(o["outcome"]=="unable_from_frozen_evidence" for o in outcomes),
                                            "unexpected_assembly_failures":sum(o["outcome"]=="assembly_failed" for o in outcomes)},"members":outcomes})
    dump(HERE / "SOURCE_INTEGRITY.json",integrity)
    (HERE / "assembled-proposals.jsonl").write_text("".join(json.dumps(c,ensure_ascii=False)+"\n" for c in claims),encoding="utf-8")
    dump(HERE / "ACQUISITION_TASKS.json",[
        {"task_id":"A-12696-complete-original","instrument_id":"EO:12696","task_type":"shared_source_acquisition_and_inventory_repair",
         "url":"https://www.govinfo.gov/content/pkg/FR-1989-11-15/pdf/FR-1989-11-15.pdf","expected_sha256":"02105ade4671e8d0c6dd14c31a457eba501d45d946c9a28029781a89684aed3a",
         "pages":"PDF pages 11-12; 54 FR 47507-47508","required_fact":"Complete section 4, including FACA delegation and subsection 4(b), official printed signing/filing and all final text; compare selected recheck text stopping at section 3(c).",
         "next_action":"Acquire or locate held scan through shared source queue; inspect original pages; repair attribution/inventory in a future separately frozen dossier. No exhaustion asserted."},
        {"task_id":"A-12722-cutoff-current-law","instrument_id":"EO:12722","task_type":"shared_source_acquisition_and_legal_fact",
         "urls":["https://www.govinfo.gov/bulkdata/ECFR/title-31/ECFR-title31.xml","https://uscode.house.gov/download/releasepoints/us/pl/119/121/xml_uscAll@119-121.zip"],
         "required_fact":"Full attributable text of 31 CFR 576.201, especially (b), at 2026-10-14 and full 50 USC 1701 Iraq Sanctions note; determine whether continued blocking is a separate EO13350 rule, original command, or statutory continuation; establish statutory currency through October 14.",
         "next_action":"Materialize exact legal-text slices with byte custody/hashes and cutoff currency. Snippets and serialized fragments are not substitutes; no exhaustion asserted."},
        {"task_id":"A-12722-partial-scope","instrument_id":"EO:12722","task_type":"shared_legal_fact_analysis",
         "held_sources":["ACTOR_TEXT:EO:12724","ACTOR_TEXT:EO:13303","ACTOR_TEXT:EO:13350"],
         "required_fact":"Map each original prohibition, blocking command and delegation against EO12724 section 6's to-the-extent-inconsistent revocation and savings; map EO13303 section 2(a)'s property exception; distinguish first effective ends from 2004 nominal revocation and continuing blocked property.",
         "next_action":"Source review using held full actor texts plus full current-law text; do not assign group first-end dates or treat EO12771 as revoking EO12722."}
    ])


if __name__ == "__main__":
    main()
