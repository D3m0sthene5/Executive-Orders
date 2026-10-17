"""Stage 21 batch forge: one retrieval per authority, independent questions per EO.

Repackages every reconciled provisional decision into nonoverlapping research
batches. Review UI exports unverified proposals only, never lifecycle decisions.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "research/stage21/batches"
INPUTS = {
    "conversion": "research/stage20/output/CONVERSION_INDEX.csv",
    "source_cases": "research/stage20/output/SHARED_SOURCE_CASE_REVIEW_QUEUE.csv",
    "statute_cases": "research/stage20/output/STATUTE_CASE_REVIEW_QUEUE.csv",
    "causal": "research/stage20/output/CAUSAL_LEAD_PRIORITIES_844.csv",
    "original_links": "research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv",
    "original_custody": "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
}
MAX_PER_BATCH = 20


def parse_csv(raw):
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))


def csv_bytes(rows, fields):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n",
                            extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def count_bool(value):
    return str(value).lower() in ("true", "yes", "1")


def build(conversion, source_cases, statute_cases, causal, source_hashes,
          original_links=None, original_custody=None):
    if len(conversion) != 3359 or len(source_cases) != 352 or len(statute_cases) != 42:
        raise ValueError("Unexpected Stage 20 inventory; reconcile before bulk batching")
    by_case = {}
    for c in conversion:
        identity = c.get("instrument_id")
        if not identity or identity in by_case:
            raise ValueError("Duplicate/missing conversion identity")
        if c.get("whole_lifecycle_completed") != "no":
            raise ValueError("A reviewed finding appeared in frozen Stage20; reconcile")
        if c.get("provisional_status") not in ("yes", "no"):
            raise ValueError("Unexpected legacy status")
        by_case[identity] = c
    original_links = [] if original_links is None else original_links
    original_custody = [] if original_custody is None else original_custody
    if original_links and len(original_links) != 3359:
        raise ValueError("Original-source crosswalk is incomplete")
    original_by_case = {}
    for item in original_links:
        identity = item["instrument_id"]
        if identity not in by_case or identity in original_by_case:
            raise ValueError("Duplicate/missing original source identity")
        if item["provisional_status_UNVERIFIED"] != by_case[identity]["provisional_status"]:
            raise ValueError("Original URL crosswalk status conflict")
        if any(item.get(k) != "no" for k in (
            "document_identity_authenticated",
            "operative_clause_legal_effect_verified", "independent_human_review")):
            raise ValueError("Unreviewed original source became certified")
        if item.get("selected_literal_URL") and item.get("selected_format") not in (
            "pdf_url", "html_url", "full_text_xml_url"):
            raise ValueError("Unrecognized official source format")
        original_by_case[identity] = item

    if original_custody and len(original_custody) != 386:
        raise ValueError("Original PDF custody crosswalk changed")
    custody_by_case = {}
    for item in original_custody:
        identity = item["instrument_id"]
        reference = original_by_case.get(identity, {})
        if not reference.get("PDF_candidate") or identity in custody_by_case:
            raise ValueError("Unmatched or duplicate original PDF custody")
        if reference["PDF_candidate"] != item["official_PDF_candidate_URL"]:
            raise ValueError("Acquired PDF source does not match original indexed URL")
        if any(item.get(k) != "no" for k in (
            "original_EO_identity_and_pages_human_verified",
            "operative_clause_scope_verified", "causal_effects_verified",
            "independent_human_certified")):
            raise ValueError("Acquired PDF improperly marked legally certified")
        state = item["custody_state"]
        if state not in ("not_attempted", "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED",
                         "fetch_failed_REVIEW_MANUALLY"):
            raise ValueError("Unrecognized PDF custody state")
        if state == "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED":
            rel = item.get("source_repository_path") or ""
            digest = item.get("sha256_source_bytes_if_present") or ""
            if (rel != "research/stage21/original_sources/EO_" + identity[3:] + ".pdf"
                or len(digest) != 64
                or any(x not in "0123456789abcdef" for x in digest)):
                raise ValueError("Captured PDF missing expected path/digest")
        custody_by_case[identity] = item

    family_members = defaultdict(set)
    authorities = defaultdict(set)
    for s in source_cases:
        id_ = s["cited_in"]
        key = s["authority"]
        if id_ not in by_case or not key:
            raise ValueError("Unknown source link identity")
        if (key, id_) in authorities.get("_seen", set()):
            raise ValueError("Duplicate case-source research edge")
        authorities["_seen"].add((key, id_))
        family_members[key].add(id_)
        authorities[id_].add(key)
        if s["certified"] != "no":
            raise ValueError("Unexpected preapproved shared source edge")
    del authorities["_seen"]
    if len(family_members) != 98:
        raise ValueError("Unexpected number of source families")
    statute_by_pair = {}
    downloaded = defaultdict(set)
    statute_paths = {}
    for s in statute_cases:
        pair = (s["source_key"], s["instrument_id"])
        if pair in statute_by_pair:
            raise ValueError("Duplicate statute case link")
        if pair[0] not in family_members or pair[1] not in family_members[pair[0]]:
            raise ValueError("Statute acquisition not in shared source ledger")
        if s.get("human_certified") != "no":
            raise ValueError("Unexpected human certification")
        statute_by_pair[pair] = s
        if count_bool(s.get("acquired_pdf_bytes", "")):
            if not s.get("stored_local_pdf_candidate_path") or not (
                len(s.get("sha256_acquired_candidate_pdf", "")) == 64):
                raise ValueError("Acquired PDF lacks provenance path/hash")
            downloaded[pair[1]].add(pair[0])
            statute_paths[pair[0]] = {
                "source_key": pair[0], "citation": s["citation"],
                "pdf_repository_path": s["stored_local_pdf_candidate_path"],
                "pdf_sha256_from_prior_custody": s["sha256_acquired_candidate_pdf"],
                "source_state": "prior_downloaded_pdf_candidate_NOT_LEGAL_AUTHENTICATION"
            }
    causal_by_case = {}
    for row in causal:
        id_ = row["instrument_id"]
        if id_ in causal_by_case or id_ not in by_case:
            raise ValueError("Bad causal lead identity")
        causal_by_case[id_] = row
    if len(causal_by_case) != 844:
        raise ValueError("All 844 causal research leads required")
    # Each case is assigned one batch, even if it has multiple source families.
    # Batch ownership is only a workload optimization; all source associations
    # remain visible to the researcher and cannot be used as shared verdicts.
    ranking = sorted(family_members,
        key=lambda f: (-sum(f in downloaded.get(id_, set()) for id_ in family_members[f]),
                       -len(family_members[f]), f))
    owner = {}
    for family in ranking:
        for id_ in sorted(family_members[family]):
            owner.setdefault(id_, family)
    buckets = defaultdict(list)
    for id_, c in by_case.items():
        family = owner.get(id_)
        priority = int(c.get("research_triage_not_confidence") or 0)
        original = original_by_case.get(id_, {})
        custody = custody_by_case.get(id_, {})
        if custody.get("custody_state") == "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED":
            bucket = "00_original_pdf_bytes_captured"
        elif family and downloaded.get(id_):
            bucket = "01_downloaded_statute_reference"
        elif original.get("selected_literal_URL"):
            bucket = "02_official_original_URL_candidate"
        elif family and family.startswith("EO::"):
            bucket = "03_shared_executive_order_reference"
        elif family:
            bucket = "04_other_shared_authority"
        elif count_bool(c.get("source_entry_locally_preserved")):
            bucket = "05_local_source_seed"
        elif c.get("opus_narrative_materialized") == "yes":
            bucket = "06_opus_notes_recovered"
        else:
            bucket = "07_original_source_acquisition"
        buckets[bucket].append((id_, family, priority))
    outputs = []
    for bucket in sorted(buckets):
        # Family co-location where possible; higher research triage first
        # inside a family. Score explicitly is NOT legal confidence.
        rows = sorted(buckets[bucket], key=lambda x: (x[1] or "~",
                         -x[2], x[0]))
        for offset in range(0, len(rows), MAX_PER_BATCH):
            chunk = rows[offset:offset + MAX_PER_BATCH]
            batch_id = bucket + "-" + str(offset // MAX_PER_BATCH + 1).zfill(3)
            cases = []
            source_details = {}
            for identity, family, score in chunk:
                c = by_case[identity]
                keys = sorted(authorities.get(identity, []))
                for key in keys:
                    source_details.setdefault(key, statute_paths.get(key, {
                        "source_key": key, "source_state":
                        "textual_reference_ONLY_source_not_authenticated"
                    }))
                causal_seed = causal_by_case.get(identity)
                original = original_by_case.get(identity, {})
                custody = custody_by_case.get(identity, {})
                cases.append({
                    "instrument_id": identity,
                    "literal_official_original_candidate_URL":
                        original.get("selected_literal_URL", ""),
                    "literal_official_original_PDF_candidate_URL":
                        original.get("PDF_candidate", ""),
                    "original_PDF_custody_state":
                        custody.get("custody_state", "not_indexed_or_attempted"),
                    "captured_original_PDF_candidate_repository_path":
                        custody.get("source_repository_path", ""),
                    "captured_original_PDF_candidate_SHA256":
                        custody.get("sha256_source_bytes_if_present", ""),
                    "original_legal_text_and_page_authenticated": False,
                    "legacy_provisional_status": c["provisional_status"],
                    "decision_origin": c["decision_origin"],
                    "source_batch_owner": family or "",
                    "all_shared_authority_mention_keys": keys,
                    "retrieved_statute_pdf_candidate_keys":
                        sorted(downloaded.get(identity, set())),
                    "prior_AI_footprint_claim_UNVERIFIED":
                        c.get("opus_footprint_claim", ""),
                    "prior_AI_date_mentions_UNVERIFIED":
                        c.get("date_mentions_unclassified", ""),
                    "prior_AI_mechanism_keywords_UNVERIFIED":
                        c.get("possible_mechanism_keywords", ""),
                    "possible_event_cues_UNVERIFIED": int(
                        (causal_seed or {}).get(
                            "possible_event_date_mentions_NOT_FINDINGS") or 0),
                    "partial_structured_episode_count": int(
                        c.get("structured_history_rows") or 0),
                    "locally_preserved_source_seed":
                        c.get("source_entry_locally_preserved", "0"),
                    "triage_score_NOT_legal_confidence": score,
                    "original_text_verified": False,
                    "first_cause_or_current_predicate_verified": False,
                    "independently_human_reviewed": False,
                })
            outputs.append({
                "schema": "eo-mass-research-batch/v1",
                "batch_id": batch_id,
                "workload_lane": bucket,
                "case_count": len(cases),
                "shared_source_custody_candidates":
                    [source_details[key] for key in sorted(source_details)],
                "cases": cases,
                "certification_state": "research_queue_only",
                "legal_findings_auto_generated": 0,
                "instruction": ("Authenticate common source once; check entire "
                   "original clause inventory, actual impact, first effective "
                   "cessation or continuing predicate, earlier alternatives "
                   "and savings independently for EACH executive order.")
            })
    seen = [x["instrument_id"] for b in outputs for x in b["cases"]]
    if len(seen) != len(by_case) or len(seen) != len(set(seen)) or set(seen) != set(by_case):
        raise ValueError("Missing or duplicated case in workload assignment")
    if any(b["case_count"] > MAX_PER_BATCH for b in outputs):
        raise ValueError("Oversized review batch")
    by_batch = {c["instrument_id"]: b for b in outputs for c in b["cases"]}
    assignments = []
    for identity in sorted(by_case):
        b = by_batch[identity]
        c = next(x for x in b["cases"] if x["instrument_id"] == identity)
        assignments.append({
            "instrument_id": identity, "batch_id": b["batch_id"],
            "batch_lane": b["workload_lane"],
            "provisional_status_NOT_CERTIFIED": c["legacy_provisional_status"],
            "shared_reference_count": len(c["all_shared_authority_mention_keys"]),
            "official_original_link_candidate": c["literal_official_original_candidate_URL"],
            "original_PDF_custody_state": c["original_PDF_custody_state"],
            "original_PDF_repository_path": c[
                "captured_original_PDF_candidate_repository_path"],
            "original_PDF_SHA256_NOT_AUTHENTICATION": c[
                "captured_original_PDF_candidate_SHA256"],
            "downloaded_statute_reference_count": len(
                c["retrieved_statute_pdf_candidate_keys"]),
            "all_shared_references": " | ".join(
                c["all_shared_authority_mention_keys"]),
            "source_retrieval_group_owner": c["source_batch_owner"],
            "AI_footprint_claim_UNVERIFIED": c[
                "prior_AI_footprint_claim_UNVERIFIED"],
            "earlier_event_candidate_count_UNVERIFIED": c[
                "possible_event_cues_UNVERIFIED"],
            "original_clause_completeness_verified": "no",
            "first_cause_or_current_predicate_verified": "no",
            "savings_and_counterevidence_verified": "no",
            "independent_human_reviewed": "no"
        })
    pilot = []
    for bucket in sorted(buckets):
        samples = [r for r in assignments if r["batch_lane"] == bucket][:10]
        for r in samples:
            pilot.append({
                "instrument_id": r["instrument_id"], "lane": bucket,
                "batch_id": r["batch_id"], "blind_reviewer_A": "",
                "blind_reviewer_B": "", "original_scope_check": "",
                "first_cause_or_current_predicate": "",
                "saved_consequences": "", "disagreement": "",
                "minutes_spent": "", "independent_certification": "no"
            })
    metrics = {
        "schema": "eo-mass-verification-workload-metrics/v1",
        "reconciled_provisional_cases": len(by_case),
        "case_level_batch_assignments": len(assignments),
        "distinct_batch_count": len(outputs),
        "max_cases_per_batch": MAX_PER_BATCH,
        "actual_largest_batch": max(b["case_count"] for b in outputs),
        "shared_authority_families": len(family_members),
        "candidate_case_source_edges": len(source_cases),
        "cases_with_one_or_more_shared_source_families": len(owner),
        "cases_with_acquired_statute_pdf_candidates": sum(bool(links) for links in downloaded.values()),
        "candidate_case_statute_pdf_edges": sum(map(len, downloaded.values())),
        "provisional_cases_with_official_original_source_URL":
            sum(bool(x.get("selected_literal_URL")) for x in original_by_case.values()),
        "provisional_cases_with_PDF_source_candidate":
            sum(bool(x.get("PDF_candidate")) for x in original_by_case.values()),
        "original_candidate_PDFs_locally_captured":
            sum(x.get("custody_state") == "PDF_BYTES_CAPTURED_NOT_AUTHENTICATED"
                for x in custody_by_case.values()),
        "original_candidate_PDF_acquisition_failures":
            sum(x.get("custody_state") == "fetch_failed_REVIEW_MANUALLY"
                for x in custody_by_case.values()),
        "original_page_identities_authenticated": 0,
        "opus_causal_note_context_cases": len(causal_by_case),
        "stratified_pilot_assignments": len(pilot),
        "batches_by_lane": dict(Counter(b["workload_lane"] for b in outputs)),
        "cases_by_lane": dict(Counter(r["batch_lane"] for r in assignments)),
        "input_sha256": source_hashes,
        "case_source_relationships_proven": 0,
        "human_certified_dossiers": 0,
        "automatically_promoted_lifecycle_findings": 0
    }
    return {"batches": outputs, "assignments": assignments,
            "pilot": pilot, "metrics": metrics}


def make_html(model):
    # Strip nothing about provenance/uncertainty; use compact JSON for a
    # self-contained file opened locally without server/network access.
    compact = [{
        "id": b["batch_id"], "lane": b["workload_lane"],
        "sources": b["shared_source_custody_candidates"],
        "cases": b["cases"]
    } for b in model["batches"]]
    payload = json.dumps(compact, ensure_ascii=False,
                         separators=(",", ":")).replace("<", "\\u003c")
    content = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EO mass verification research workbench</title>
<style>
body{font:15px/1.45 system-ui,sans-serif;margin:0;background:#f4f6f8;color:#152c3a}
header{background:#223e4d;color:#fff;padding:15px 3vw}header h1{font-size:22px;margin:0}
header p{margin:6px 0 0}main{max-width:1550px;margin:auto;padding:12px}
.layout{display:grid;grid-template-columns:minmax(290px,360px) 1fr;gap:12px}
@media(max-width:830px){.layout{grid-template-columns:1fr}}section{background:#fff;border:1px solid #cdd9df;border-radius:6px;padding:12px}
input,select,textarea,button{font:inherit;box-sizing:border-box;padding:7px}
input,textarea,select{width:100%}textarea{min-height:62px}button{cursor:pointer;border:1px solid #bacad2;background:#f4f7fa;border-radius:4px;margin:3px}
button.row{display:block;text-align:left;width:100%}button:hover{background:#e5f0f5}
.warning{color:#884c14;font-weight:600}.muted{color:#607684}.case{border-top:1px solid #d5e0e5;margin-top:14px;padding-top:11px}
label{display:block;margin:8px 0}.hidden{display:none}code{overflow-wrap:anywhere}
#batches{max-height:68vh;overflow:auto}#detail{min-height:300px}a{overflow-wrap:anywhere}
</style>
<header><h1>Executive-order batch research and review preparation</h1>
<p>One common authority can be located once; every EO requires its own operative-clause, causal, counterevidence and savings inquiry.</p></header>
<main><p class="warning">This workbench produces uncertified research worksheets only. No imported/exported field can change legal classifications or create independent human certification.</p>
<div class="layout"><section><input id="search" placeholder="Find batch, EO number or family"><p id="number"></p>
<div id="batches"></div><hr><button id="export">Export all research work</button>
<label>Resume from earlier exported JSON<input type="file" id="import" accept=".json,application/json"></label>
<p class="muted">Export before closing the tab. These notes are held in this browser session; import restores a previous export.</p></section>
<section id="detail">Choose a research batch.</section></div></main>
<script type="application/json" id="data">%%PAYLOAD%%</script>
<script>
const data=JSON.parse(document.getElementById('data').textContent), E=id=>document.getElementById(id);
const allCases=new Set(data.flatMap(b=>b.cases.map(c=>c.instrument_id)));
const allBatchIds=new Set(data.map(b=>b.id)), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','"':'&quot;',"'":'&#39;'}[c]));
const fields=['original_page','complete_operative_clauses','later_change_exact_source_and_page','first_cessation_or_live_predicate','earlier_cause_countersearch','savings_and_independent_authority','contrary_evidence','unresolved_material_gaps'];
let current=null, research={},sourceNotes={};
function save(){if(!current)return;
 for(const c of current.cases){const key=c.instrument_id,obj=research[key]||{};for(const f of fields){
 const el=E('case-'+key+'-'+f);if(el)obj[f]=el.value;}research[key]=obj}
 for(const s of current.sources){const el=E('source-'+s.source_key);if(el)sourceNotes[s.source_key]=el.value}
}
function renderBatch(b){save();current=b;let s='<h2>'+esc(b.id)+'</h2><p>'+b.cases.length+
 ' individual cases. Lane: '+esc(b.lane)+'. This queue shares retrieval work, never a legal verdict.</p>';
s+='<h3>Shared source candidates — verify once before using</h3>';
for(const item of b.sources){s+='<div class="case"><b>'+esc(item.source_key)+'</b> · '+esc(item.source_state);
 if(item.pdf_repository_path)s+=' · <a href="https://github.com/D3m0sthene5/Executive-Orders/blob/main/'+encodeURI(item.pdf_repository_path)+'" target="_blank" rel="noopener">PDF in GitHub (candidate)</a>';
 s+='<p class="muted">A hash or catalog link does not establish clause-level legal effect.</p><label>Research memo: exact source page, quote and verification limits<textarea id="source-'+esc(item.source_key)+'">'+esc(sourceNotes[item.source_key]||'')+'</textarea></label></div>';
}
for(const c of b.cases){const w=research[c.instrument_id]||{};
s+='<div class="case"><h3>'+esc(c.instrument_id)+' — provisional '+esc(c.legacy_provisional_status)+'</h3>';
if(c.literal_official_original_candidate_URL){
s+='<p><a href="'+esc(c.literal_official_original_candidate_URL)+'" target="_blank" rel="noopener noreferrer">Open indexed official EO source candidate</a></p>';}
if(c.captured_original_PDF_candidate_repository_path){
s+='<p><a href="https://github.com/D3m0sthene5/Executive-Orders/blob/main/'+encodeURI(c.captured_original_PDF_candidate_repository_path)+'" target="_blank" rel="noopener noreferrer">Open archived PDF candidate</a> · SHA-256: <code>'+esc(c.captured_original_PDF_candidate_SHA256)+'</code></p>';}
s+='<p class="muted">Original PDF custody: '+esc(c.original_PDF_custody_state)+' — original pages and clause inventory NOT verified.</p>';
s+='<p class="muted">AI footprint claim: '+esc(c.prior_AI_footprint_claim_UNVERIFIED)+
 ' · AI date mentions: '+esc(c.prior_AI_date_mentions_UNVERIFIED)+
 ' · references: '+esc(c.all_shared_authority_mention_keys.join(' · '))+'</p>';
for(const [key,label] of [
 ['original_page','Original EO text and exact source page (all clauses)'],
 ['complete_operative_clauses','Complete operative-clause inventory and scope'],
 ['later_change_exact_source_and_page','Later legal authorities: effective text, actor, date and page'],
 ['first_cessation_or_live_predicate','For NO: earliest end of each clause; for YES: live cutoff-date predicate'],
 ['earlier_cause_countersearch','Earlier possible endings and bounded negative search'],
 ['savings_and_independent_authority','Accrued rights, savings, residual effects and independent authority'],
 ['contrary_evidence','Contrary sources and disagreement assessment'],
 ['unresolved_material_gaps','Remaining unresolved material gaps']
 ])s+='<label>'+esc(label)+'<textarea id="case-'+esc(c.instrument_id)+'-'+key+'">'+esc(w[key]||'')+'</textarea></label>';
s+='</div>'}s+='<button id="export-batch">Export this batch as research worksheet</button>';
E('detail').innerHTML=s;E('export-batch').onclick=()=>exportData(b.id)}
function download(name,content){const blob=new Blob([JSON.stringify(content,null,2)],{type:'application/json'});
const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function exportData(only=null){save();const ids=new Set((only?[data.find(b=>b.id===only)]:data).flatMap(b=>b.cases.map(c=>c.instrument_id)));
const obj={schema:'eo-mass-batch-research-worksheet/v1',selected_batch_id:only||'all',
 producer_entered_case_research:Object.fromEntries(Object.entries(research).filter(([id])=>ids.has(id))),
 source_research_memos:sourceNotes,original_complete_legal_claims_created:0,
 independent_human_certifications_created:0,approval_state:'research_only_never_certification'};
download((only||'all')+'-research.json',obj)}
E('export').onclick=()=>exportData();
E('import').onchange=async()=>{
try{const file=E('import').files[0];if(!file)return;const d=JSON.parse(await file.text());
 if(d.schema!=='eo-mass-batch-research-worksheet/v1'||
 d.approval_state!=='research_only_never_certification')throw Error('not a compatible research-only export');
 if(Object.keys(d.producer_entered_case_research||{}).some(x=>!allCases.has(x)))throw Error('unknown case ID');
 research={...research,...d.producer_entered_case_research};sourceNotes={...sourceNotes,...(d.source_research_memos||{})};
 if(current){let tmp=current;current=null;renderBatch(tmp);}alert('Research worksheet imported. Certification state unchanged.');
 }catch(err){alert('Import rejected: '+err.message)}};
function draw(){const q=E('search').value.toLowerCase(),matches=data.filter(b=>
 b.id.toLowerCase().includes(q)||b.lane.toLowerCase().includes(q)||
 b.sources.some(s=>s.source_key.toLowerCase().includes(q))||
 b.cases.some(c=>c.instrument_id.toLowerCase().includes(q)));
 E('number').textContent=matches.length+' of '+data.length+' batches';E('batches').replaceChildren();
 for(const b of matches){const btn=document.createElement('button');btn.className='row';
 btn.textContent=b.id+' · '+b.cases.length+' cases';btn.onclick=()=>renderBatch(b);E('batches').append(btn);}}
E('search').oninput=draw;draw();if(data.length)renderBatch(data[0]);
</script></html>'''
    # NOTE: HTML entities in escaped reviewer-entered data prevent script/data
    # injection; interactive exports are research-only, never certification.
    return content.replace("%%PAYLOAD%%", payload).encode("utf-8")


def output_bytes(model):
    return {
        "BATCH_ASSIGNMENTS_3359.csv": csv_bytes(
            model["assignments"], list(model["assignments"][0])),
        "BATCH_REVIEW_PACKETS.jsonl": (
            "\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True)
                      for x in model["batches"]) + "\n").encode("utf-8"),
        "BLIND_PILOT_QUEUE.csv": csv_bytes(model["pilot"], list(model["pilot"][0])),
        "BATCH_RESEARCH_WORKBENCH.html": make_html(model),
        "BATCH_METRICS.json": (json.dumps(model["metrics"], indent=2,
                           sort_keys=True) + "\n").encode("utf-8")
    }


def build_files(root=ROOT):
    paths = {name: root / rel for name, rel in INPUTS.items()}
    raw = {name: p.read_bytes() for name, p in paths.items()}
    parsed = {name: parse_csv(data) for name, data in raw.items()}
    model = build(parsed["conversion"], parsed["source_cases"],
                  parsed["statute_cases"], parsed["causal"],
                  {n: hashlib.sha256(v).hexdigest() for n, v in raw.items()},
                  parsed["original_links"], parsed["original_custody"])
    return model, output_bytes(model)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    model, produced = build_files()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.check:
        for name, data in produced.items():
            if (OUT / name).read_bytes() != data:
                raise SystemExit("Stale batch output " + name)
    else:
        for name, data in produced.items():
            (OUT / name).write_bytes(data)
    print(json.dumps(model["metrics"], indent=2))


if __name__ == "__main__":
    main()
