/** Stage 20 deterministic, source-first conversion excavator. Node 18+ standard library. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
function parseCSV(s){
 const all=[];let line=[],buf="",quoted=false;
 for(let i=0;i<s.length;i++){const c=s[i];if(quoted){if(c==='"'){if(s[i+1]==='"'){buf+='"';i++;}else quoted=false;}else buf+=c;}else if(c==='"')quoted=true;else if(c===','){line.push(buf);buf="";}else if(c==='\n'){line.push(buf.replace(/\r$/,""));all.push(line);line=[];buf="";}else buf+=c;}
 if(quoted)throw Error("CSV quotes unclosed");if(line.length||buf){line.push(buf);all.push(line);}
 const hdr=all.shift().map(s=>s.replace(/^\uFEFF/,""));return all.filter(x=>x.length>1).map((r,i)=>{if(r.length!==hdr.length)throw Error("CSV width "+i);return Object.fromEntries(hdr.map((k,j)=>[k,r[j]]));});
}
function writeCSV(rows,cols){return cols.join(",")+"\n"+rows.map(r=>cols.map(k=>{const v=String(r[k]??"");return /[,"\n\r]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;}).join(",")).join("\n")+"\n";}
function unique(a){return [...new Set(a)].sort();}
function leads(note){
 const refs=[];for(const [type,rx] of [
  ["EO",/\b(?:E\.?O\.?|Executive Order(?:s)?)\s*(?:No\.?\s*)?#?\s*(\d{1,5}[A-Z]?)\b/gi],
  ["CFR",/\b(\d{1,2}\s+C\.?\s*F\.?\s*R\.?\s*(?:part|parts|§|sec(?:tion)?\.?)?\s*\d+(?:\.\d+)?)/gi],
  ["USC",/\b(\d{1,2}\s+U\.?\s*S\.?\s*C\.?\s*(?:§|sec(?:tion)?\.?)?\s*\d+[A-Za-z0-9().-]*)/gi],
  ["STAT",/\b(\d{1,3}\s+Stat\.\s*\d+)\b/gi]
 ]){for(const m of note.matchAll(rx))refs.push({type,value:m[1].replace(/\s+/g," ").trim()});}
 const keyed=new Map(refs.map(x=>[x.type+":"+x.value,x]));
 const types=[["statutory",/\b(statute|statutory|U\.?S\.?C\.?)\b/i],["formal_revocation",/\brevok|rescind/i],["amendment",/\bamend/i],["sunset",/\bexpir|\bsunset|\blaps/i],["completed_function",/\bcomplet|\bfulfill|\bexecuted and obsolete/i],["regulation",/\bCFR|regulation|rulemaking/i],["court",/\bcourt|judgment/i],["delegation",/\bdelegat|transferred|reorgani[sz]/i]].filter(([name,rx])=>rx.test(note)).map(([x])=>x);
 return {dates:unique(note.match(/\b(?:17|18|19|20)\d{2}-\d\d-\d\d\b/g)||[]),references:[...keyed.values()],mechanism_keywords:types};
}
function buildIndex(decisions,originalNotes,queue,sourceSHAs,fullRecords=[]){
 if(decisions.length!==3359||originalNotes.length!==304||queue.length!==3359)throw Error("Unexpected frozen Stage 19 size; reconcile before changing pipeline");
 const qmap=new Map(queue.map(x=>[x.instrument_id,x]));
 const dmap=new Map(decisions.map(x=>[x.instrument_id,x]));
 const omap=new Map(originalNotes.map(x=>[x.instrument_id,x]));
 if(dmap.size!==3359||qmap.size!==3359||omap.size!==304)throw Error("Duplicate identity");
 let full=false;
 if(fullRecords.length){
   if(fullRecords.length!==844)throw Error("The complete Opus archive must contain exactly 844 accepted cases");
   const fm=new Map(fullRecords.map(x=>[x.instrument_id,x]));if(fm.size!==844)throw Error("Duplicate full Opus records");
   for(const [id,o] of omap){const other=fm.get(id);if(!other||other.final_substantive_effect!==o.final_substantive_effect||String(other.review_problems)!==o.review_problems)throw Error("Opus 304/full ZIP disagreement: "+id);}
   for(const [id,x] of fm){if(!dmap.has(id)||dmap.get(id).provisional_substantive_status!==x.final_substantive_effect)throw Error("Unmatched full Opus record: "+id);}
   for(const [id,x] of fm)omap.set(id,x);full=true;
 }
 let footprint=0,withDates=0;
 const notes=[],rank=[],refGroup=new Map();
 for(const d of decisions){
   const id=d.instrument_id,q=qmap.get(id);if(!q||q.legacy_status!==d.provisional_substantive_status)throw Error("Stage 19 queue mismatch "+id);
   const o=omap.get(id);let parsed={dates:[],references:[],mechanism_keywords:[]};
   if(o){
     if(o.final_substantive_effect!==d.provisional_substantive_status)throw Error("Opus verdict conflict "+id);
     const text=(o.review_problems||"")+"\n"+(o.what_remains_inferential||"");
     parsed=leads(text);
     if(String(o.footprint_complete).toLowerCase()==="true")footprint++;
     if(parsed.dates.length)withDates++;
     notes.push({instrument_id:id,verdict:d.provisional_substantive_status,source_status:"opus_ai_research_unverified",opus_lane:o.lane,opus_footprint_complete_claim:o.footprint_complete,source_grade_claim:o.text_source_grade,historical_causes:o.historical_causes,review_verdict:o.review_verdict,review_problems_verbatim:o.review_problems,what_remains_inferential_verbatim:o.what_remains_inferential,evidence_dir_in_archive:o.evidence_dir,review_dir_in_archive:o.review_dir,date_mentions_not_causal_findings:parsed.dates,explicit_references_not_verified:parsed.references,mechanism_keywords_not_verified:parsed.mechanism_keywords,original_image_member_verified:false,independent_human_certification:false});
     for(const ref of parsed.references){const key=ref.type+"::"+ref.value;if(!refGroup.has(key))refGroup.set(key,{type:ref.type,reference:ref.value,ids:new Set()});refGroup.get(key).ids.add(id);}
   }
   const source=Number(q.locally_preserved_primary_representation||0)>0;
   const scope=Number(q.structured_scope_count||0)>0;
   const quarantine=Number(q.quarantined_relationship_count||0)>0;
   let lane,action;
   if(quarantine){lane="resolve_contradiction";action="Test quarantined relationship and scope against source; do not treat a citation as an operative event.";}
   else if(o&&d.provisional_substantive_status==="yes"){lane="verify_current_predicate";action="Locate original clause and cutoff-date continuation, review all later interventions and savings, then inventory other scopes.";}
   else if(o&&parsed.dates.length){lane="differentiate_date_and_first_end";action="Identify what each date represents; search earlier effective cessation and any saved/transferred effects for every clause.";}
   else if(o){lane="trace_end_or_footprint";action="Verify Opus narrative against the original and locate controlling cessation for each substantive clause.";}
   else if(d.decision_origin==="opus_checkpoint2"){lane="recover_540_opus_narratives";action="Extract complete Opus LFS JSONL to reuse the accepted-case source and reviewer research.";}
   else if(scope){lane="extend_structured_episode";action="Inspect existing scoped history; reconcile original text, later effective events, counterevidence and savings.";}
   else{lane="acquire_original_and_clauses";action="Acquire original authoritative source, enumerate all operative clauses, and then reconstruct legal history.";}
   const score=(o?20:0)+(o&&String(o.footprint_complete).toLowerCase()==="true"?8:0)+(parsed.dates.length>0?5:0)+Math.min(4,parsed.references.length)*2+(source?5:0)+(scope?5:0)-(quarantine?8:0);
   rank.push({instrument_id:id,provisional_status:d.provisional_substantive_status,decision_origin:d.decision_origin,conversion_lane:lane,research_triage_not_confidence:score,opus_narrative_materialized:o?"yes":"no",opus_footprint_claim:o?String(o.footprint_complete):"not_in_available_notes",date_mentions_unclassified:parsed.dates.join(" | "),reference_leads_count:parsed.references.length,possible_mechanism_keywords:parsed.mechanism_keywords.join(" | "),source_entry_locally_preserved:q.locally_preserved_primary_representation,structured_history_rows:q.structured_scope_count,quarantined_leads:q.quarantined_relationship_count,next_action:action,whole_lifecycle_completed:"no",original_decision_unchanged:"yes"});
 }
 rank.sort((a,b)=>b.research_triage_not_confidence-a.research_triage_not_confidence||a.instrument_id.localeCompare(b.instrument_id,undefined,{numeric:true}));
 notes.sort((a,b)=>a.instrument_id.localeCompare(b.instrument_id,undefined,{numeric:true}));
 const families=[...refGroup.values()].filter(x=>x.ids.size>=2).map(x=>({reference_type:x.type,reference_as_mentioned:x.reference,affected_candidate_count:x.ids.size,case_ids:unique([...x.ids]).join(" | "),evidence_state:"textual_cooccurrence_only",review_action:"Retrieve authoritative source once, compare clause/effective-date reach separately for every listed EO."})).sort((a,b)=>b.affected_candidate_count-a.affected_candidate_count||a.reference_as_mentioned.localeCompare(b.reference_as_mentioned));
 const metrics={schema:"eo-stage20-conversion/v1",frozen_source_git_blob_sha:sourceSHAs,working_population:14972,provisional_decisions:3359,opus_accepted:844,opus_full_844_notes_loaded:full,opus_notes_recovered:notes.length,opus_footprint_claims_unverified:footprint,opus_cases_with_unclassified_ISO_date_mentions:withDates,shared_legal_reference_clusters:families.length,human_certified_whole_lifecycle:0,interpretation:"Materials are research leads; a complete Opus footprint claim does not constitute a verified first-cause history. Never automatically promote a dossier."};
 return {rank,notes,families,metrics};
}
function makeWorkbench(model){
 const compact=model.notes.map(n=>({id:n.instrument_id,status:n.verdict,lane:n.opus_lane,footprint:String(n.opus_footprint_complete_claim),dates:n.date_mentions_not_causal_findings,refs:n.explicit_references_not_verified,notes:n.review_problems_verbatim,limits:n.what_remains_inferential_verbatim,shard:n.evidence_dir_in_archive}));
 const payload=JSON.stringify(compact).replace(/</g,"\\u003c");
 return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Lifecycle conversion excavation</title>
<style>body{font:15px/1.5 system-ui,sans-serif;background:#f3f6fa;color:#233040;margin:0}header{background:#233e59;color:white;padding:16px 24px}header h1{margin:0;font-size:23px}main{display:grid;grid-template-columns:minmax(260px,360px) 1fr;gap:16px;max-width:1440px;margin:auto;padding:18px}section{background:white;padding:16px;border:1px solid #d6dce5;border-radius:6px;margin-bottom:16px}label{display:block;font-weight:600;margin:10px 0 4px}input,select,textarea,button{font:inherit;box-sizing:border-box}input,select,textarea{width:100%;padding:7px;border:1px solid #aeb9c8;border-radius:4px}textarea{min-height:74px}button{background:#245d8c;color:white;border:0;padding:8px 12px;cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fa;padding:10px}#list{max-height:65vh;overflow:auto}#list button{width:100%;display:block;text-align:left;color:#233040;background:white;border-bottom:1px solid #ddd}#list button:hover{background:#e9f2fa}.warn{color:#8a3727}@media(max-width:850px){main{display:block}}</style>
<header><h1>Opus-to-whole-lifecycle conversion workbench</h1><p>${model.notes.length} detailed AI reviewer narratives recovered. No record is source-certified or independently human-reviewed.</p></header><main><aside><section><label for="q">Search narratives, EO numbers, references</label><input id="q" placeholder="EO:10033, CFR, amendment…"><label for="lane">Research lane</label><select id="lane"><option value="">All</option><option value="E_POSITIVE_CONTINUITY">Positive continuity</option><option value="G_LATER_ENDING_EVENT">Later event</option><option value="B_NARA_EXECUTED_OBSOLETE">Executed or obsolete</option></select><p id="count"></p><div id="list"></div></section></aside><article><section><h2 id="head">Select a case</h2><p class="warn">Opus flags and date/citation matches are hypotheses. A later revocation need not establish first loss of operative effect.</p><div id="context"></div><h3>Verbatim Opus review</h3><pre id="review"></pre><h3>What remains inferential</h3><pre id="limits"></pre></section>
<section><h2>Research proposal, not certification</h2><label for="researcher">Researcher</label><input id="researcher"><label for="original">Authenticated original and page/item</label><textarea id="original"></textarea><label for="scope">All original operative clauses and exact source locations</label><textarea id="scope"></textarea><label for="history">Subsequent legal sources and provision-specific changes</label><textarea id="history"></textarea><label for="cause">First effective cessation (NO) or present predicate (YES) and earlier-cause checks</label><textarea id="cause"></textarea><label for="savings">Savings, accrued or transferred rights, contrary evidence</label><textarea id="savings"></textarea><label for="gaps">Remaining unresolved questions</label><textarea id="gaps"></textarea><p><button id="export">Export research-only JSON</button></p></section></article></main>
<script id="data" type="application/json">${payload}</script><script>
const cases=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id);let selected=null;
function render(){const q=$('q').value.toLowerCase(),lane=$('lane').value;const rows=cases.filter(x=>(!lane||x.lane===lane)&&[x.id,x.notes,x.limits,JSON.stringify(x.refs)].join(' ').toLowerCase().includes(q));$('count').textContent=rows.length+' of '+cases.length;const root=$('list');root.replaceChildren();for(const x of rows){const b=document.createElement('button');b.textContent=x.id+' | '+x.status.toUpperCase()+' | '+x.lane;b.onclick=()=>select(x);root.append(b);}}
function select(x){selected=x;$('head').textContent=x.id+' — '+x.status.toUpperCase()+' provisional';$('context').textContent='Footprint claimed: '+x.footprint+' | Unclassified dates: '+x.dates.join(', ')+' | Citation leads: '+x.refs.map(r=>r.type+' '+r.value).join('; ')+' | Opus archive path: '+x.shard;$('review').textContent=x.notes;$('limits').textContent=x.limits;}
$('export').onclick=()=>{if(!selected)return;const v=id=>$(id).value.trim();if(!v('researcher'))return alert('Identify the researcher');const obj={schema:'eo-conversion-research-proposal/v1',instrument_id:selected.id,provisional_status:selected.status,researcher:v('researcher'),original_source_and_page:v('original'),original_operative_scope:v('scope'),later_source_history:v('history'),first_end_or_current_predicate:v('cause'),savings_and_counterevidence:v('savings'),unresolved_material_gaps:v('gaps'),independent_certification:false};const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=selected.id.replace(':','_')+'_research.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
$('q').oninput=render;$('lane').onchange=render;render();if(cases.length)select(cases[0]);</script></html>`;
}
const paths={"decisions":"research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv","opus":"research/progress/OPUS_COMPLETE_304_PENDING_CANONICAL_INTEGRATION.csv","queue":"research/stage19/output/CAUSAL_QUEUE.csv"};
const pinnedSourceBlobShas={"decisions":"f579711285cad6784b4eb213656b0fd9f9a32217","opus":"b00b870299c0e68fb38e3068ef438ddfd9609567","queue":"1eac9a4dd8ba4892fa6df6fff401ad829bef6f7f"};
function main(){
 const params=process.argv.slice(2);
 const read=name=>parseCSV(fs.readFileSync(path.join(ROOT,paths[name]),'utf8'));
 const at=params.indexOf('--full-opus');
 const full=at<0?[]:fs.readFileSync(path.resolve(params[at+1]),'utf8').split(/\r?\n/).filter(Boolean).map(x=>JSON.parse(x));
 const m=buildIndex(read('decisions'),read('opus'),read('queue'),pinnedSourceBlobShas,full);
 if(m.notes.length==304 && (m.metrics.opus_footprint_claims_unverified!==297 ||m.metrics.opus_cases_with_unclassified_ISO_date_mentions!==110))throw Error('Published 304-case regression');
 const content={
 'CONVERSION_INDEX.csv':writeCSV(m.rank,["instrument_id","provisional_status","decision_origin","conversion_lane","research_triage_not_confidence","opus_narrative_materialized","opus_footprint_claim","date_mentions_unclassified","reference_leads_count","possible_mechanism_keywords","source_entry_locally_preserved","structured_history_rows","quarantined_leads","next_action","whole_lifecycle_completed","original_decision_unchanged"]),
 'OPUS_NOTE_LEADS.jsonl':m.notes.map(x=>JSON.stringify(x)).join('\n')+'\n',
 'SHARED_SOURCE_REFERENCE_QUEUE.csv':writeCSV(m.families,["reference_type","reference_as_mentioned","affected_candidate_count","case_ids","evidence_state","review_action"]),
 'CONVERSION_METRICS.json':JSON.stringify(m.metrics,null,2)+'\n',
 'CONVERSION_WORKBENCH.html':makeWorkbench(m)
 };
 const out=path.join(ROOT,'research/stage20/output');
 if(params.includes('--check')){for(const [name,body] of Object.entries(content)){if(fs.readFileSync(path.join(out,name),'utf8')!==body)throw Error('Stale build: '+name);}console.log('Byte-for-byte conversion check passed');return;}
 fs.mkdirSync(out,{recursive:true});for(const [name,body] of Object.entries(content))fs.writeFileSync(path.join(out,name),body,'utf8');console.log(JSON.stringify(m.metrics,null,2));
}
main();
