/** Source custody task planner: source retrieval is shared; legal inference remains per case.
Run from repo root: node research/stage20/code/build_shared_source_workbench.mjs [--check]
Node >=18, no external dependencies.
*/
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');

function parseCSV(s){
 let lines=[],row=[],buf="",quote=false;
 for(let i=0;i<s.length;i++){
  const c=s[i]; if(quote){if(c==='"'&&s[i+1]==='"'){buf+='"';i++;}else if(c==='"')quote=false;else buf+=c}
  else if(c==='"')quote=true;else if(c===','){row.push(buf);buf=""}
  else if(c==='\n'){row.push(buf.replace(/\r$/,""));if(row.length>1)lines.push(row);row=[];buf=""}else buf+=c;
 }
 if(quote)throw Error("malformed CSV unclosed quote");
 if(buf||row.length){row.push(buf);lines.push(row)}
 const fields=lines.shift();if(!fields||fields.length!==new Set(fields).size)throw Error("bad header");
 return lines.map((r,i)=>{if(r.length!==fields.length)throw Error("CSV width error "+i);return Object.fromEntries(fields.map((name,j)=>[name,r[j]]))});
}

function writeCSV(rows,fields){
 const escape=v=>{const s=v===undefined||v===null?"":String(v);return /[,"\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
 return fields.join(",")+"\n"+rows.map(row=>fields.map(field=>escape(row[field])).join(",")).join("\n")+"\n";
}

function discoveryRoutes(type,reference){
 const text=type==="EO"?"Executive Order "+reference:reference;
 const domain=(type==="EO"?"federalregister.gov":type==="CFR"?"ecfr.gov":type==="USC"?"uscode.house.gov":"govinfo.gov");
 const base=(type==="EO"?"https://www.federalregister.gov/documents/search":type==="CFR"?"https://www.ecfr.gov/":type==="USC"?"https://uscode.house.gov/":"https://www.govinfo.gov/app/collection/statute");
 return [{source:"official_repository_portal",url:base,query:text,state:"directory_only_not_evidence"},
 {source:"site_restricted_discovery",url:"https://www.google.com/search?q="+encodeURIComponent("site:"+domain+' "'+text+'"'),query:text,state:"search_route_not_executed"}];
}

function makeModel(groups,queue,sourceBlobIDs){
 if(groups.length!==98||queue.length!==3359)throw Error("frozen stage20 inputs changed; reconcile before rebuild");
 const indexes=new Map();
 for(const row of queue){if(!row.instrument_id||indexes.has(row.instrument_id))throw Error("missing or duplicated case");indexes.set(row.instrument_id,row)}
 const families=[],tasks=[],familyIds=new Set(),links=new Set();
 for(const row of groups){
  const type=row.reference_type,ref=row.reference_as_mentioned;
  if(!["EO","USC","CFR","STAT"].includes(type)||!ref||!["textual_cooccurrence_only"].includes(row.evidence_state))throw Error("unexpected reference family");
  const key=type+"::"+ref;
  if(familyIds.has(key))throw Error("duplicate source acquisition key "+key);
  familyIds.add(key);
  const ids=row.case_ids.split("|").map(s=>s.trim());
  if(ids.length!==Number(row.affected_candidate_count)||ids.length<2||new Set(ids).size!==ids.length)throw Error("count/duplication mismatch in "+key);
  const perCase=ids.map(id=>{
   const item=indexes.get(id);if(!item)throw Error("missing case in link "+key+" "+id);
   if(item.whole_lifecycle_completed!=="no")throw Error("current certification state changed in "+id);
   links.add(key+"|"+id);
   return {instrument_id:id,provisional_status:item.provisional_status,legacy_decision_origin:item.decision_origin,
    research_lane:item.conversion_lane,existing_source_seed:String(item.source_entry_locally_preserved||"0"),
    possible_causal_role:"unknown",affected_original_clause:null,source_page:null,
    effective_date_proposal:null,independent_authority_and_savings_review:null,
    earlier_cessation_check:null,review_state:"not_started",
    reviewed_evidence_claim:false,independently_certified:false};
  });
  const f={schema:"eo-shared-source-research-task/v1",source_key:key,reference_type:type,reference_as_mentioned:ref,
   candidate_cases:perCase.length,priority_metric:"number_of_distinct_legacy_cases_referencing_source_not_legal_confidence",
   retrieval:{state:"not_acquired_by_stage21",official_document_url:null,source_archive_path:null,
    bytes_sha256:null,exact_page_or_item:null,retrieved_utc:null,source_authentication:"unverified"},
   discovery_routes:discoveryRoutes(type,ref),affected_cases:perCase,source_reuse_state:"source_text_cooccurrence_only",
   legal_effect_claims_adjudicated:0,independent_human_approvals:0,
   scientific_warning:"One source may affect these cases differently or not at all. This artifact records a potential common retrieval task and leaves every legal effect unresolved."};
  families.push(f);
  for(const caseRow of perCase)tasks.push({authority:key,cited_in:caseRow.instrument_id,provisional_status:caseRow.provisional_status,
   source_already_retrieved:"no",affected_clause_id:"",proposed_role:"unknown",first_effective_change_date:"",case_specific_evidence:"",review_state:"not_started",certified:"no"});
 }
 families.sort((a,b)=>b.candidate_cases-a.candidate_cases||a.source_key.localeCompare(b.source_key));
 const casesWithReuse=new Set(tasks.map(t=>t.cited_in));
 const metrics={schema:"eo-shared-source-reuse-metrics/v1",source_git_blob_sha1:sourceBlobIDs,
  parent_stage20_cases:3359,source_families:families.length,cross_case_source_research_tasks:tasks.length,
  distinct_cases_with_repeated_authority_mentions:casesWithReuse.size,
  sources_automatically_located:0,sources_automatically_authenticated:0,
  official_search_routes_not_executed:families.length*2,
  proposed_effective_dates_accepted_as_fact:0,certified_lifecycle_dossiers_generated:0,
  methodology:"Strictly planning and review scaffolding; share retrieved, hashed primary-source bytes, but never share a causal conclusion across distinct original EO clauses."};
 if(families.length!==98||tasks.length!==links.size||metrics.certified_lifecycle_dossiers_generated!==0)throw Error("source review planning invariant failed");
 return {families,tasks,metrics};
}

function workbench(model){
 const data=JSON.stringify(model.families).replace(/</g,"\\u003c").replace(/>/g,"\\u003e");
 return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EO shared authority source review</title>
<style>body{font:15px/1.45 system-ui,sans-serif;background:#f4f6f7;color:#172d38;margin:0}
header{background:#1e3744;color:white;padding:18px 3vw}header h1{font-size:23px;margin:0 0 7px}
header p{margin:0;max-width:1150px}main{padding:16px;max-width:1560px;margin:auto}
.layout{display:grid;grid-template-columns:minmax(310px,420px) 1fr;gap:16px}@media(max-width:920px){.layout{grid-template-columns:1fr}}
article,aside{background:#fff;border:1px solid #d3dfe3;border-radius:6px;padding:13px}
input,select,textarea,button{font:inherit;box-sizing:border-box}input,select,textarea{border:1px solid #b5c7d0;border-radius:4px;padding:7px}
input,textarea{width:100%}select{max-width:100%}button{cursor:pointer;padding:8px;border:1px solid #bfced4;border-radius:4px;background:#f7fafb}
button.rowbtn{width:100%;display:block;margin:5px 0;text-align:left}button:hover{background:#e8f2f5}
.warnings{color:#77420a;font-weight:600}.muted{color:#5d7280}#family-list{max-height:62vh;overflow:auto}
.casebox{border:1px solid #d5e1e5;border-radius:5px;margin:9px 0;padding:9px}
.casebox label{display:block;margin:7px 0}.sourcefields{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.sourcefields>label{display:block}@media(max-width:900px){.sourcefields{grid-template-columns:1fr}}
fieldset{border:1px solid #d0dadf;margin:14px 0}a{overflow-wrap:anywhere}
</style>
<header><h1>Shared-source excavation workbench</h1><p>98 prior AI citation clusters. Acquire each controlling text once, then test its relevance and legal effect independently against each executive order's original operative clauses.</p></header>
<main><p class="warnings">All source routes are unexecuted. Every role, date, first cessation, and legal conclusion begins unknown. Exported packets are research proposals, never independent human certification or lifecycle completion.</p>
<div class="layout"><aside><input id="query" placeholder="EO 9337, 31 USC 1552, a case number…"><p id="counter"></p><div id="family-list"></div></aside>
<article id="details"><p>Choose a citation cluster to plan source acquisition and document separate effects.</p></article></div></main>
<script id="data" type="application/json">${data}</script>
<script>
const db=JSON.parse(document.getElementById("data").textContent),byId=id=>document.getElementById(id);
let selected=null,sourceWork={},caseWork={};
function escapeHTML(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function currentField(source,key){return (sourceWork[source]||{})[key]||""}
function save(){if(!selected)return;const key=selected.source_key;sourceWork[key]=sourceWork[key]||{};
for(const k of ["official_document_url","bytes_sha256","source_archive_path","exact_page_or_item","retrieved_utc","source_research_notes"]){const target=byId("source-"+k);if(target)sourceWork[key][k]=target.value}
for(const row of selected.affected_cases){let record=caseWork[key+"|"+row.instrument_id]||{};for(const k of ["role","scope","page","date","contrary","savings"]){const target=byId("case-"+row.instrument_id+"-"+k);if(target)record[k]=target.value}caseWork[key+"|"+row.instrument_id]=record}}
function view(f){save();selected=f;const key=f.source_key,source=sourceWork[key]||{};
const route=f.discovery_routes.map(x=>'<a href="'+escapeHTML(x.url)+'" target="_blank" rel="noopener noreferrer">'+escapeHTML(x.source)+" ("+escapeHTML(x.state)+")</a>").join(" · ");
let html='<h2>'+escapeHTML(f.source_key)+'</h2><p>'+f.candidate_cases+' cited EOs. Citation co-occurrence is a retrieval lead, not proof of legal effect.</p><p>'+route+'</p>'+
'<fieldset><legend>Single source-custody record</legend><div class="sourcefields">';
const fields=[["official_document_url","Actual verified original URL"],["bytes_sha256","SHA-256 of retrieved source bytes"],["source_archive_path","Source vault member path"],["exact_page_or_item","Exact page/item"],["retrieved_utc","Acquisition UTC timestamp"],["source_research_notes","Document identity and provenance limitations"]];
for(const [k,name] of fields){html+='<label>'+escapeHTML(name)+'<input id="source-'+k+'" value="'+escapeHTML(source[k]||"")+'" placeholder="Unverified until manually researched"></label>'}
html+='</div></fieldset><h3>Potentially different impacts per EO</h3><p class="muted">Every case has its own relevant original clause, asserted role, effective date, adverse sources and savings inquiry.</p>';
for(const row of f.affected_cases){const c=caseWork[key+"|"+row.instrument_id]||{};
html+='<div class="casebox"><b>'+escapeHTML(row.instrument_id)+'</b> · provisional '+escapeHTML(row.provisional_status)+
' <p><a target="_blank" rel="noopener noreferrer" href="https://github.com/D3m0sthene5/Executive-Orders/blob/main/research/stage20/output/CONVERSION_INDEX.csv">View conversion index for this case</a></p>'+
'<label>Proposed legal role<select id="case-'+row.instrument_id+'-role">';
for(const [value,title] of [["unknown","Unknown / unchecked"],["formally_revokes","Formal revocation allegation"],["amends_scope","Amends scope allegation"],["earlier_functional_end","Earlier functional end allegation"],["continues_or_saves","Continues or saves legal effect allegation"],["independent_authority","Independent authority / successor policy allegation"],["context_only","Background mention only"],["irrelevant","Not relevant"]]){html+='<option value="'+value+'"'+((c.role||"unknown")===value?" selected":"")+'>'+title+'</option>'}
html+='</select></label>';
for(const [k,name] of [["scope","Exact affected original clause"],["page","Source page/item and text"],["date","Candidate effective date (unverified)"],["contrary","Earlier-ending and contrary-source search"],["savings","Savings, accrued rights, successor predicates"]]){html+='<label>'+name+'<input id="case-'+row.instrument_id+'-'+k+'" value="'+escapeHTML(c[k]||"")+'"></label>'}
html+='</div>';}
html+='<button id="export" type="button">Export uncertified multi-EO source worksheet</button><p class="warnings">Export has no independent human verdict, cannot alter a clause state, and cannot pass Stage 19 claim gate.</p>';
byId("details").innerHTML=html;byId("export").onclick=exportProposal}
function exportProposal(){if(!selected)return;save();const f=selected,key=f.source_key;
const out={schema:"eo-shared-source-review-proposal/v1",source_key:key,reference_as_mentioned:f.reference_as_mentioned,origin:"stage20 repeated source mention, unverified",
 source_custody:{...sourceWork[key],retrieval_state:"researcher_entered_unvalidated"},
 per_case:f.affected_cases.map(x=>({instrument_id:x.instrument_id,legacy_provisional_status:x.provisional_status,
  reviewed_effect_proposal:caseWork[key+"|"+x.instrument_id]||{role:"unknown"},verified_effective_date:false,independent_human_approval:false})),
 unresolved_material_gaps:["source identity and authentic original","per-clause earlier cessation and continuing predicates","savings and adverse later source search","independent source review"],certification_state:"research_only_not_adjudicated"};
const json=JSON.stringify(out,null,2),url=URL.createObjectURL(new Blob([json],{type:"application/json"})),a=document.createElement("a");
a.href=url;a.download=key.replace(/[^A-Za-z0-9]+/g,"_")+"_source_research.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function list(){const q=byId("query").value.toLowerCase();const matches=db.filter(f=>(f.source_key+" "+f.affected_cases.map(x=>x.instrument_id).join(" ")).toLowerCase().includes(q));
byId("counter").textContent=matches.length+" of "+db.length+" citation families";byId("family-list").replaceChildren();
for(const f of matches){const b=document.createElement("button");b.type="button";b.className="rowbtn";b.textContent=f.source_key+" · "+f.candidate_cases+" cases";b.onclick=()=>view(f);byId("family-list").append(b)}}
byId("query").oninput=list;list();
</script></html>`;
}

export {parseCSV,writeCSV,discoveryRoutes,makeModel,workbench};
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const dirs={
  shared:"research/stage20/output/SHARED_SOURCE_REFERENCE_QUEUE.csv",
  conversion:"research/stage20/output/CONVERSION_INDEX.csv"
 };
 const contents=Object.fromEntries(Object.entries(dirs).map(([name,p])=>[name,fs.readFileSync(path.join(root,p))]));
 const observed=Object.fromEntries(Object.entries(contents).map(([name,buf])=>[name,createHash('sha1').update('blob '+buf.length+'\0').update(buf).digest('hex')]));
 const pinned={"shared":"db7dc6f0ad374a2b4a9526fea359527a66c50030","conversion":"82fb95469038eba8d7659c4222a9cead5bdbd3ba"};
 for(const name in pinned)if(observed[name]!==pinned[name])throw Error('Source input drift for '+name+'; manual reconciliation required');
 const model=makeModel(parseCSV(contents.shared.toString('utf8')),parseCSV(contents.conversion.toString('utf8')),observed);
 const outputs={
  "SHARED_SOURCE_TASKS.jsonl":model.families.map(f=>JSON.stringify(f)).join('\n')+'\n',
  "SHARED_SOURCE_CASE_REVIEW_QUEUE.csv":writeCSV(model.tasks,Object.keys(model.tasks[0])),
  "SHARED_SOURCE_WORKBENCH.html":workbench(model),
  "SHARED_SOURCE_METRICS.json":JSON.stringify(model.metrics,null,2)+'\n'
 };
 const dir=path.join(root,'research/stage20/output');
 if(process.argv.includes('--check')){
  for(const [name,data] of Object.entries(outputs))if(fs.readFileSync(path.join(dir,name),'utf8')!==data)throw Error('Stale workbench output: '+name);
  console.log('Source workbench outputs reproducible: '+model.families.length+' families, '+model.tasks.length+' linked case research tasks.');
 }else{
  fs.mkdirSync(dir,{recursive:true});for(const [name,data] of Object.entries(outputs))fs.writeFileSync(path.join(dir,name),data);
  console.log(JSON.stringify(model.metrics,null,2));
 }
}
