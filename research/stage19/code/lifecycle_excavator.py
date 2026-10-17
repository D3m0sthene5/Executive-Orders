"""Batch causal-research quarry for the working EO bibliography.

Reads the immutable Stage 17 SQLite and reconciled YES/NO overlay. It never
promotes a label, a relationship candidate, or a scoped sunset into a complete
whole-order history. Outputs a population queue and reusable review packets.
"""

import argparse
import csv
import hashlib
import html
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from claim_gate import claim_sha, validate_claim, validate_review


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DECISIONS = ROOT / "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
DEFAULT_MANIFEST = ROOT / "research/stage18/SOURCE_MANIFEST.json"


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def rows_by(conn, query, key):
    grouped = defaultdict(list)
    for row in conn.execute(query):
        item = dict(row)
        grouped[item[key]].append(item)
    return grouped


def load_overlay(path, included):
    with open(path, newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    result = {}
    for row in rows:
        identity = row["instrument_id"]
        if identity in result or identity not in included:
            raise ValueError(f"duplicate or outside-bibliography decision: {identity}")
        status = row["provisional_substantive_status"]
        if status not in ("yes", "no"):
            raise ValueError(f"non-decision in reconciled overlay: {identity}")
        result[identity] = row
    return result


def source_overlay(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    by_id = {}
    for item in manifest["federal_register"]:
        for order in item["executive_orders"]:
            by_id[f"EO:{order}"] = {
                "kind": "contemporaneous_official_publication_not_signed_original",
                "url": item["issue_url"],
                "local_file": "research/stage18/" + item["local_excerpt"],
                "sha256": item["local_excerpt_sha256"],
                "printed_pages": item["printed_register_pages"],
            }
    return by_id


def load_claims(path, included):
    """Load untrusted claim proposals; structural and human gates run later."""
    if path is None:
        return {}
    out = {}
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            identity = row.get("instrument_id")
            if row.get("schema") != "eo-lifecycle-claim/v1" or identity not in included or identity in out:
                raise ValueError("invalid, duplicate, or excluded lifecycle claim")
            out[identity] = row
    return out


def load_reviews(path):
    if path is None:
        return defaultdict(list)
    result=defaultdict(list)
    with open(path,encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            review=json.loads(line)
            result[review.get("instrument_id")].append(review)
    return result


def priority(meta, decision, counts):
    year = int(meta["issuance_date"][:4]) if meta["issuance_date"] and meta["issuance_date"][:4].isdigit() else None
    if year is not None and year <= 1906:
        lane = "early_historical"
    elif counts["quarantined"]:
        lane = "contradiction"
    elif counts["relations"] >= 2:
        lane = "relation_rich"
    elif counts["scoped"]:
        lane = "existing_scoped_pilot"
    else:
        lane = "unmapped"
    # Triage opportunity, never legal probability or correctness confidence.
    score = (6 if year is not None and year <= 1906 else 0)
    score += min(counts["relations"], 8) * 2 + min(counts["quarantined"], 3) * 5
    score += min(counts["observations"], 5) + min(counts["scoped"], 2) * 4
    if decision["provisional_substantive_status"] == "no":
        score += 2
    return lane, score


def make_html(packets, output):
    # Historical text is untrusted; embed as JSON and display with textContent.
    payload = json.dumps(packets, ensure_ascii=False).replace("</", "<\\/")
    page = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EO lifecycle excavator — review packets</title><style>
body{font:15px/1.48 system-ui,sans-serif;background:#f6f8fa;color:#17212d;margin:0}header{background:#17334c;color:white;padding:20px 4vw}h1{font-size:24px;margin:0}main{max-width:1400px;margin:0 auto;padding:18px;display:grid;grid-template-columns:minmax(260px,360px) 1fr;gap:16px}section{background:white;border:1px solid #d7dee7;border-radius:8px;padding:15px;margin-bottom:15px}input,select,textarea,button{font:inherit;padding:8px;box-sizing:border-box}input,select,textarea{width:100%;border:1px solid #adb8c6;border-radius:5px}textarea{min-height:78px}button{background:#1e537d;color:white;border:0;border-radius:5px;cursor:pointer;padding:10px 14px}label{display:block;font-weight:600;margin-top:10px}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:420px;overflow:auto;background:#f3f5f8;padding:10px}a{overflow-wrap:anywhere}.muted{color:#576779}.warning{color:#852c1d}#list{max-height:74vh;overflow:auto}#list button{display:block;width:100%;text-align:left;background:white;color:#17212d;border-bottom:1px solid #d7dee7;border-radius:0}#list button:hover{background:#eaf2f9}@media(max-width:800px){main{display:block}}
</style><header><h1>Lifecycle research packets</h1><div>Candidate evidence and missing fields. No packet is a completed legal finding or human certification.</div></header><main><aside><section><label for="search">Find EO, era, or blocker</label><input id="search" placeholder="EO:10084, early, source…"><div id="count" class="muted"></div><div id="list"></div></section></aside><article><section><h2 id="title">Select a packet</h2><p id="warning" class="warning"></p><div id="sources"></div><h3>Known evidence and unresolved edges</h3><pre id="detail"></pre></section><section><h2>Research and human audit worksheet</h2><p class="muted">Export a proposal for independent checking. A reviewer must inspect cited pages; export does not promote a status or count toward the lifecycle tracker.</p><label>Reviewer or researcher</label><input id="reviewer"><label>Original document/source URL and exact page</label><textarea id="original"></textarea><label>Complete operative clause inventory and scope</label><textarea id="clauses"></textarea><label>First effective end (NO) or continuing predicate (YES); actor, mechanism, date, exact source</label><textarea id="cause"></textarea><label>Later amendments, savings, accrued rights, residuals, revival and counterevidence</label><textarea id="residuals"></textarea><label>Unresolved gaps</label><textarea id="gaps"></textarea><label>Disposition</label><select id="disposition"><option value="hold">Hold for evidence</option><option value="research_proposal">Research proposal for legal review</option></select><p><button id="export">Export worksheet JSON</button></p></section></article></main>
<script id="data" type="application/json">%%DATA%%</script><script>
const packets=JSON.parse(document.querySelector('#data').textContent),$=id=>document.getElementById(id);let selected=null;
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function renderList(){const q=$('search').value.toLowerCase();const a=packets.filter(x=>(x.instrument.id+' '+x.queue.priority_lane+' '+x.queue.blocker_codes.join(' ')).toLowerCase().includes(q));$('count').textContent=a.length+' / '+packets.length+' prepared packets';$('list').innerHTML=a.map(x=>'<button data-id="'+esc(x.instrument.id)+'">'+esc(x.instrument.id)+' — '+esc(x.queue.priority_lane)+'<br><small>'+esc(x.instrument.issuance_date||'date unknown')+' • '+esc(x.queue.legacy_status.toUpperCase())+' • '+x.queue.blocker_codes.length+' blockers</small></button>').join('');for(const b of $('list').querySelectorAll('button'))b.onclick=()=>show(b.dataset.id)}
function show(id){selected=packets.find(x=>x.instrument.id===id);if(!selected)return;$('title').textContent=id+' — '+selected.queue.legacy_status.toUpperCase()+' provisional';$('warning').textContent='Whole-lifecycle completion: '+selected.queue.lifecycle_state+'. First-cause and current-predicate fields require source review.';const links=selected.source_links.filter(s=>/^https:\/\//.test(s.url)).map(s=>'<li><a target="_blank" rel="noopener noreferrer" href="'+esc(s.url)+'">'+esc(s.label)+'</a> — '+esc(s.grade)+'</li>');$('sources').innerHTML='<h3>Source entry points</h3><ul>'+links.join('')+'</ul>';$('detail').textContent=JSON.stringify({queue:selected.queue,provisions:selected.provisions,transitions:selected.transitions,episodes:selected.episodes,legal_events:selected.legal_events,relationship_leads:selected.relationship_leads,source_observations:selected.source_observations,assessments:selected.assessments,stage17_claims:selected.stage17_claims},null,2)}
function download(name,obj){const u=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}
$('export').onclick=()=>{if(!selected)return;const v=id=>$(id).value.trim();if(!v('reviewer')){alert('Identify the researcher or reviewer.');return;}download(selected.instrument.id.replace(':','_')+'_worksheet.json',{schema:'eo-lifecycle-worksheet/v1',instrument_id:selected.instrument.id,packet_fingerprint:selected.packet_fingerprint,reviewer:v('reviewer'),disposition:v('disposition'),original_source_and_page:v('original'),clause_inventory:v('clauses'),causal_or_continuing_predicate:v('cause'),residuals_and_counterevidence:v('residuals'),unresolved_gaps:v('gaps'),exported_at:new Date().toISOString()})};$('search').oninput=renderList;renderList();if(packets.length)show(packets[0].instrument.id);
</script></html>'''
    output.write_text(page.replace("%%DATA%%", payload), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--claims", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-packets", type=int, default=80)
    args = parser.parse_args()
    if args.max_packets < 1:
        raise ValueError("--max-packets must be positive")
    args.out.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{args.db.resolve().as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    included = {r["id"]: dict(r) for r in conn.execute("SELECT * FROM instruments WHERE include_proxy=1")}
    overlay = load_overlay(args.decisions, included)
    official = source_overlay(args.source_manifest)
    claim_overlay = load_claims(args.claims, included)
    reviews = load_reviews(args.reviews)
    claim_errors={}
    structurally_complete=set()
    reviewed_complete=set()
    for identity,claim in claim_overlay.items():
        errors=validate_claim(claim,overlay[identity]["provisional_substantive_status"] if identity in overlay else None)
        if identity not in overlay:
            errors.append("no_reconciled_provisional_status")
        claim_errors[identity]=errors
        if not errors:
            structurally_complete.add(identity)
            if any(not validate_review(review,claim) for review in reviews[identity]):
                reviewed_complete.add(identity)
    grouped = {
        "sources": rows_by(conn, "SELECT * FROM stage17_source", "subject_id"),
        "provisions": rows_by(conn, "SELECT * FROM stage17_provision", "instrument_id"),
        "episodes": rows_by(conn, "SELECT * FROM legal_episode", "instrument_id"),
        "events": rows_by(conn, "SELECT * FROM legal_event", "affected_instrument"),
        "relationships": rows_by(conn, "SELECT * FROM candidate_relationships", "predecessor"),
        "observations": rows_by(conn, "SELECT * FROM source_observations", "related_id"),
        "assessments": rows_by(conn, "SELECT * FROM stage17_assessment", "instrument_id"),
        "claims": rows_by(conn, "SELECT claim_id,instrument_id,claim_kind,claim_scope,source_ids_json,policy_version,fingerprint FROM stage17_claim", "instrument_id"),
    }
    transition_by_provision = rows_by(conn, "SELECT * FROM stage17_transition", "affected_provision_id")
    queue = []
    for identity, decision in overlay.items():
        meta = included[identity]
        provisions = grouped["provisions"][identity]
        episodes = grouped["episodes"][identity]
        transitions = [t for p in provisions for t in transition_by_provision[p["provision_id"]]]
        relations = grouped["relationships"][identity]
        counts = {
            "scoped": len(provisions) + len(episodes),
            "transitions": len(transitions),
            "relations": len(relations),
            "quarantined": sum(not r["eligible_for_research"] for r in relations),
            "observations": len(grouped["observations"][identity]),
        }
        lane, score = priority(meta, decision, counts)
        source_locally_preserved = identity in official or any(s["local_original_bytes"] for s in grouped["sources"][identity])
        blockers = []
        if not source_locally_preserved:
            blockers.append("NO_LOCAL_PRIMARY_REPRESENTATION")
        if not counts["scoped"]:
            blockers.append("NO_STRUCTURED_OPERATIVE_FOOTPRINT")
        if decision["provisional_substantive_status"] == "no":
            blockers.append("WHOLE_ORDER_FIRST_END_UNPROVED")
        else:
            blockers.append("CURRENT_PREDICATE_UNPROVED")
        blockers.append("SAVINGS_AND_RESIDUALS_NOT_CLOSED")
        if counts["quarantined"]:
            blockers.append("QUARANTINED_RELATIONSHIP_CONFLICT")
        if decision["decision_origin"].startswith("opus") and str(decision["opus_original_images_in_supplied_zip"]) in ("0", "False"):
            blockers.append("OPUS_ORIGINAL_IMAGE_COMPANION_MISSING")
        if identity in claim_overlay:
            if claim_errors[identity]:
                blockers.append("CLAIM_GATE_FAILED:"+",".join(claim_errors[identity]))
            elif identity not in reviewed_complete:
                blockers.append("CLAIM_SUBMITTED_NOT_INDEPENDENTLY_REVIEWED")
        if identity in reviewed_complete:
            # The independent reviewed dossier supplies the original, whole
            # footprint, causal/current path and residual evidence. Historical
            # graph leads remain visible in the packet, but cannot overrule it.
            blockers=[]
        lifecycle_state="independently_reviewed_documented_complete" if identity in reviewed_complete else ("research_claim_structurally_complete_pending_review" if identity in structurally_complete else "not_whole_lifecycle_complete")
        queue.append({
            "instrument_id": identity,
            "issuance_date": meta["issuance_date"],
            "legacy_status": decision["provisional_substantive_status"],
            "decision_origin": decision["decision_origin"],
            "priority_lane": lane,
            "triage_score_not_confidence": score,
            "locally_preserved_primary_representation": int(bool(source_locally_preserved)),
            "structured_scope_count": counts["scoped"],
            "scoped_transition_count": counts["transitions"],
            "relationship_lead_count": counts["relations"],
            "quarantined_relationship_count": counts["quarantined"],
            "source_observation_count": counts["observations"],
            "lifecycle_state": lifecycle_state,
            "blocker_codes": blockers,
        })
    queue.sort(key=lambda r: (-r["triage_score_not_confidence"], r["instrument_id"]))
    with (args.out / "CAUSAL_QUEUE.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=[x for x in queue[0] if x != "blocker_codes"] + ["blocker_codes"])
        writer.writeheader()
        for item in queue:
            writer.writerow({**item, "blocker_codes": "|".join(item["blocker_codes"])})

    # Stratify prepared packets: opportunity across early, contradictions,
    # relation-rich, scoped, and unmapped cases, with no duplicated identities.
    lanes = ["early_historical", "contradiction", "relation_rich", "existing_scoped_pilot", "unmapped"]
    selected = []
    used = set()
    per_lane = max(1, args.max_packets // len(lanes))
    for lane in lanes:
        for row in (r for r in queue if r["priority_lane"] == lane):
            if sum(x["priority_lane"] == lane for x in selected) >= per_lane:
                break
            selected.append(row)
            used.add(row["instrument_id"])
    for row in queue:
        if len(selected) >= args.max_packets:
            break
        if row["instrument_id"] not in used:
            selected.append(row)
            used.add(row["instrument_id"])
    packets = []
    for row in selected:
        identity = row["instrument_id"]
        provisions = grouped["provisions"][identity]
        links = []
        for src in grouped["sources"][identity]:
            links.append({"label": src["source_id"], "url": src["source_url"], "grade": src["transcript_grade"]})
        if identity in official:
            src = official[identity]
            links.append({"label": "Stage 18 official printed page", "url": src["url"], "grade": src["kind"], "local_file": src["local_file"], "sha256": src["sha256"], "printed_pages": src["printed_pages"]})
        for relation in grouped["relationships"][identity]:
            if relation["source_url"] and not any(link["url"] == relation["source_url"] for link in links):
                links.append({"label": "relationship lead (unverified scope)", "url": relation["source_url"], "grade": "candidate_only"})
        for observation in grouped["observations"][identity]:
            if observation["source_url"] and not any(link["url"] == observation["source_url"] for link in links):
                links.append({"label": "source observation entry point", "url": observation["source_url"], "grade": observation["source_kind"] + "_not_primary_verified"})
        packet = {
            "schema": "eo-lifecycle-research-packet/v1",
            "instrument": included[identity],
            "queue": row,
            "source_links": links,
            "provisions": provisions,
            "transitions": [t for p in provisions for t in transition_by_provision[p["provision_id"]]],
            "episodes": grouped["episodes"][identity],
            "legal_events": grouped["events"][identity],
            "relationship_leads": grouped["relationships"][identity],
            "source_observations": grouped["observations"][identity],
            "assessments": grouped["assessments"][identity],
            "stage17_claims": grouped["claims"][identity],
            "submitted_lifecycle_claim": claim_overlay.get(identity),
            "submitted_lifecycle_claim_gate_errors": claim_errors.get(identity),
            "submitted_independent_reviews": reviews[identity],
            "original_stage11_raw_json": None,
            "research_form_fields": ["original_source_and_page", "clause_inventory", "causal_or_continuing_predicate", "residuals_and_counterevidence", "unresolved_gaps"],
        }
        raw = conn.execute("SELECT raw_json FROM original_stage11_rows WHERE record_id=?", (identity,)).fetchone()
        if raw:
            packet["original_stage11_raw_json"] = json.loads(raw[0])
        packet["packet_fingerprint"] = fingerprint(packet)
        packets.append(packet)
    with (args.out / "REVIEW_PACKETS.jsonl").open("w", encoding="utf-8") as stream:
        for packet in packets:
            stream.write(json.dumps(packet, ensure_ascii=False, sort_keys=True) + "\n")
    make_html(packets, args.out / "REVIEW_WORKBENCH.html")
    summary = {
        "schema": "eo-lifecycle-progress/v1",
        "database_sha256": file_sha(args.db),
        "decisions_sha256": file_sha(args.decisions),
        "source_manifest_sha256": file_sha(args.source_manifest),
        "working_identities": len(included),
        "provisional_yes_no": len(overlay),
        "provisional_label_coverage_percent": round(100 * len(overlay) / len(included), 6),
        "structurally_complete_research_claims_pending_or_reviewed": len(structurally_complete),
        "independently_reviewed_whole_lifecycle_complete": len(reviewed_complete),
        "whole_lifecycle_coverage_percent": round(100*len(reviewed_complete)/len(included),6),
        "documented_whole_lifecycle_lower_bound": len(reviewed_complete),
        "not_whole_lifecycle_complete_or_unassessed": len(included)-len(reviewed_complete),
        "reconciled_decisions_without_any_structured_scoped_history": sum(r["structured_scope_count"] == 0 for r in queue),
        "prepared_human_research_packets": len(packets),
        "packets_with_source_entry_point": sum(any(link.get("url") for link in packet["source_links"]) for packet in packets),
        "packets_requiring_source_acquisition": sum(not any(link.get("url") for link in packet["source_links"]) for packet in packets),
        "candidate_graph_leads_are_not_causal_findings": True,
        "interpretation": "The headline counts source-linked whole-order lifecycle dossiers passing structural and separately recorded independent-human review gates. The number is a documented lower bound, not proof other cases lack recoverable histories. Legacy YES/NO coverage is a separate provisional label measure.",
    }
    (args.out / "PROGRESS.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps({"queue": len(queue), "packets": len(packets), "headline_whole_lifecycle_complete": len(reviewed_complete)}))


if __name__ == "__main__":
    main()
