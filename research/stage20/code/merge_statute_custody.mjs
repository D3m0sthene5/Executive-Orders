/* Integrate previously downloaded GovInfo PDF candidates into per-case source-review tasks.
   This tool never adjudicates a legal effect; Node 18+, no dependencies. */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
function csvParse(s){let a=[],row=[],v="",q=false;for(let i=0;i<s.length;i++){const c=s[i];if(q){if(c==='"'&&s[i+1]==='"'){v+='"';i++}else if(c==='"')q=false;else v+=c;}else if(c==='"')q=true;else if(c===','){row.push(v);v=""}else if(c==='\n'){row.push(v.replace(/\r$/,""));if(row.some(x=>x!==""))a.push(row);row=[];v=""}else v+=c;}if(q)throw Error("unterminated CSV");if(v||row.length){row.push(v);a.push(row)}const hdr=a.shift();if(!hdr||new Set(hdr).size!==hdr.length)throw Error("invalid CSV header");return a.map((r,i)=>{if(r.length!==hdr.length)throw Error("bad CSV row "+(i+2));return Object.fromEntries(hdr.map((k,j)=>[k,r[j]]))});}

function csvWrite(rows,fields){const x=v=>{const s=v==null?"":String(v);return /[,"\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};return fields.join(",")+"\n"+rows.map(r=>fields.map(k=>x(r[k])).join(",")).join("\n")+"\n";}

function combine(families,statutes,shas){
 if(families.length!==98||statutes.length!==10)throw Error("unexpected Stage20 input counts");
 const fmap=new Map(families.map(x=>[x.source_key,x]));
 if(fmap.size!==98)throw Error("duplicate source family");
 const records=[],pairs=[];
 for(const s of statutes){
  const key="STAT::"+s.citation,f=fmap.get(key);if(!f)throw Error("statute does not match source-reference family "+key);
  const ids=s.case_ids_mentioned.split("|").map(x=>x.trim()).sort(),groups=f.affected_cases.map(x=>x.instrument_id).sort();
  if(ids.length!==groups.length||ids.some((v,i)=>v!==groups[i]))throw Error("statute-case mismatch "+key);
  const acquired=s.download_state==="downloaded_govinfo_candidate_pdf";
  if(acquired&&!(Number(s.bytes)>50&&/^[a-f0-9]{64}$/.test(s.sha256)&&s.local_relpath.endsWith(".pdf")))throw Error("invalid downloaded PDF index "+key);
  const record={schema:"eo-shared-statute-source-acquisition-review/v1",source_key:key,
   citation:s.citation,source_url_attempted:s.source_url,
   download_state:s.download_state,source_bytes_candidate_present:acquired,
   retrieved_candidate_local_repo_path:acquired?s.local_relpath:null,
   retrieved_candidate_sha256:acquired?s.sha256:null,retrieved_candidate_bytes:acquired?Number(s.bytes):null,
   archive_retrieval_limitation:s.error||null,first_page_hint_unverified:s.start_page_hint,
   document_authenticity_legal_effect_human_verified:false,
   related_orders:f.affected_cases.map(c=>({instrument_id:c.instrument_id,provisional_status:c.provisional_status,
    legal_source_role:"unknown",affected_clause:null,effective_date:null,savings:null,
    counterevidence:null,exact_printed_page:null,legal_review_state:"unresearched"})),
   scientific_notice:"GovInfo PDF candidate and SHA verify acquisition metadata only; printed source text, full statute effective scope and each executive-order effect remain to be checked."};
  records.push(record);
  for(const x of record.related_orders){
   pairs.push({source_key:key,citation:s.citation,instrument_id:x.instrument_id,provisional_status:x.provisional_status,
    acquired_pdf_bytes:acquired?"yes":"no",stored_local_pdf_candidate_path:acquired?s.local_relpath:"",
    sha256_acquired_candidate_pdf:acquired?s.sha256:"",
    retrieval_issue:s.error||"",printed_page_hint_unverified:s.start_page_hint,
    exact_legal_clause_still_unchecked:"yes",review_state:"not_started",human_certified:"no"});
  }
 }
 records.sort((a,b)=>Number(b.source_bytes_candidate_present)-Number(a.source_bytes_candidate_present)||a.source_key.localeCompare(b.source_key));
 const metrics={schema:"eo-statute-source-custody-integration/v1",frozen_source_git_blob_sha1:shas,
  repeated_statute_families:records.length,pdf_candidates_locally_downloaded:records.filter(x=>x.source_bytes_candidate_present).length,
  requests_unavailable_or_invalid:records.filter(x=>!x.source_bytes_candidate_present).length,
  candidate_case_source_links_with_pdf:pairs.filter(x=>x.acquired_pdf_bytes==="yes").length,
  distinct_cases_with_acquired_statute_reference:new Set(pairs.filter(x=>x.acquired_pdf_bytes==="yes").map(x=>x.instrument_id)).size,
  all_candidate_case_source_links:pairs.length,
  document_identity_and_effect_human_verified:0,first_effective_end_determined:0,
  completed_lifecycle_dossiers:0,interpretation:"Downloaded PDF + hash means candidate source recovered. Every case's affected clauses, relevant statute provisions, legal mechanism, first effective date and surviving consequences are still separate unknowns."};
 if(metrics.pdf_candidates_locally_downloaded!==7||metrics.requests_unavailable_or_invalid!==3||metrics.candidate_case_source_links_with_pdf!==18||metrics.completed_lifecycle_dossiers!==0)throw Error("retrieval audit mismatch");
 return {records,pairs,metrics};
}

function htmlView(result){
 const payload=JSON.stringify(result.records).replace(/</g,"\\u003c").replace(/>/g,"\\u003e");
 return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EO Statutes at Large source review</title>
<style>body{font:15px/1.5 system-ui,sans-serif;color:#17323f;background:#f2f5f7;margin:0}
header{background:#204153;color:white;padding:20px 3vw}header h1{font-size:23px;margin:0}
main{max-width:1500px;margin:auto;padding:15px;display:grid;grid-template-columns:minmax(280px,390px) 1fr;gap:12px}
@media(max-width:860px){main{display:block}}aside,article{background:white;border:1px solid #d2e0e7;border-radius:5px;padding:12px}
button{font:inherit;border:1px solid #b8cbd2;background:#f7fafb;cursor:pointer;padding:8px;margin:4px 0;text-align:left}
button.rowbtn{display:block;width:100%}button:hover{background:#eaf2f5}
label{display:block;margin:8px 0}input,textarea,select{font:inherit;box-sizing:border-box;border:1px solid #bdcbd0;padding:6px;width:100%}
.warn{color:#8b451c;font-weight:600}.case{border:1px solid #cddbe1;border-radius:4px;padding:9px;margin:9px 0}
code,a{overflow-wrap:anywhere}.small{color:#647985}
</style>
<header><h1>Official PDF candidate → EO-specific legal review</h1><p>7 GovInfo candidate PDFs acquired and hashed; 3 unavailable/invalid routes. Acquisition is not proof of any executive order's legal fate.</p></header>
<main><aside><label>Find a statute or EO<input id="search" placeholder="66 Stat. 259, EO:9704"></label><p id="count"></p><div id="list"></div></aside>
<article id="detail">Choose a repeatedly cited statute to inspect the downloaded source and review its separate effects on cited executive orders.</article></main>
<script type="application/json" id="data">${payload}</script><script>
const data=JSON.parse(document.getElementById("data").textContent),$=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let selected=null,notes={};
function save(){if(!selected)return;let obj=notes[selected.source_key]||{};for(const c of selected.related_orders){const k=c.instrument_id,x=obj[k]||{};
for(const f of ["role","scope","page","date","savings","contrary"]){const el=$("f-"+k+"-"+f);if(el)x[f]=el.value}obj[k]=x;}notes[selected.source_key]=obj;}
function openStatute(s){save();selected=s;const d=notes[s.source_key]||{};
let h='<h2>'+esc(s.citation)+'</h2><p class="warn">'+(s.source_bytes_candidate_present?'GovInfo candidate PDF downloaded, source bytes SHA recorded; legal import pending.':'Retrieval failed or returned unusable response; do not infer online unavailability.')+'</p>'+
'<p><a href="'+esc(s.source_url_attempted)+'" target="_blank" rel="noopener noreferrer">Attempted GovInfo PDF URL</a></p>';
if(s.source_bytes_candidate_present){const repo='https://github.com/D3m0sthene5/Executive-Orders/blob/main/'+s.retrieved_candidate_local_repo_path;
h+='<p><a href="'+esc(repo)+'" target="_blank" rel="noopener noreferrer">Open source PDF stored in GitHub</a></p>'+
'<p>Recorded byte count: '+s.retrieved_candidate_bytes+' · SHA-256: <code>'+esc(s.retrieved_candidate_sha256)+'</code></p>'}
else h+='<p>Recorded acquisition issue: <code>'+esc(s.archive_retrieval_limitation)+'</code></p>';
h+='<p class="small">Citation start-page hint: '+esc(s.first_page_hint_unverified)+'. Verify actual printed pagination, surrounding sections, enactment/effective provisions and prior legal states.</p>'+
'<h3>Separate case-specific legal reasoning</h3>';
for(const c of s.related_orders){
 const n=d[c.instrument_id]||{};
 h+='<section class="case"><h4>'+esc(c.instrument_id)+' (provisional '+esc(c.provisional_status)+')</h4>'+
 '<label>Proposed legal role<select id="f-'+c.instrument_id+'-role">';
 for(const [value,label] of [["unknown","Unknown/unexamined"],["first_effective_cessation_candidate","First effective cessation allegation"],["partial_amendment","Partial amendment allegation"],["continuing_authority","Continuing authority allegation"],["superseding_independent_law","Independent successor law"],["no_operative_relationship","Background/no operative relationship"]])h+='<option value="'+value+'"'+((n.role||"unknown")===value?" selected":"")+'>'+label+'</option>';
 h+='</select></label>';
 for(const [f,label] of [["scope","Original affected clause and statute provision"],["page","Exact printed page and passage"],["date","Candidate legally effective date (NOT verified)"],["savings","Savings, accrued rights, successor legal effects"],["contrary","Earlier cause and counterevidence search"]])h+='<label>'+label+'<input id="f-'+c.instrument_id+'-'+f+'" value="'+esc(n[f]||"")+'"></label>';
 h+='</section>';
}
h+='<button id="export" type="button">Export uncertified source-to-case proposals</button><p class="warn">Exports preserve research hypotheses; they never certify any lifecycle.</p>';
$("detail").innerHTML=h;$("export").onclick=exportPacket;
}
function exportPacket(){if(!selected)return;save();const s=selected,entries=notes[s.source_key]||{};
const value={schema:"eo-statute-multi-case-research-proposal/v1",authority:s.citation,
 candidate_pdf_url:s.source_url_attempted,source_bytes_sha256:s.retrieved_candidate_sha256,
 acquisition_state:s.download_state,case_research:s.related_orders.map(c=>({instrument_id:c.instrument_id,original_provisional_status:c.provisional_status,
  proposed_source_relationship:entries[c.instrument_id]||{role:"unknown"},source_legally_authenticated:false,
  earlier_cessation_and_savings_verified:false,independent_human_review:false})),
 unresolved_material_gaps:["authenticate printed statute and full legal section","verify original EO clause scope","test first legal effective date and prior events","check savings and independent continuing authority","obtain independent review"],certification_state:"research_only"};
const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:"application/json"})),a=document.createElement("a");
a.href=url;a.download=s.citation.replace(/[^a-z0-9]+/gi,"_")+"_source_case_proposals.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function list(){const q=$("search").value.toLowerCase();const rows=data.filter(s=>(s.source_key+" "+s.related_orders.map(x=>x.instrument_id).join(" ")).toLowerCase().includes(q));
$("count").textContent=rows.length+" citation families";$("list").replaceChildren();
for(const s of rows){const b=document.createElement("button");b.className="rowbtn";b.textContent=s.citation+" · "+s.related_orders.length+" cited EOs · "+(s.source_bytes_candidate_present?"PDF captured":"needs alternate acquisition");
b.onclick=()=>openStatute(s);$("list").append(b)}}
$("search").oninput=list;list();
</script></html>`;
}

export {csvParse,csvWrite,combine,htmlView};
if(process.argv[1]&&fileURLToPath(import.meta.url)===path.resolve(process.argv[1])){
 const paths={family_tasks:"research/stage20/output/SHARED_SOURCE_TASKS.jsonl",govinfo_statute_index:"research/stage20/output/STATUTE_FETCH_INDEX.csv"};
 const bytes=Object.fromEntries(Object.entries(paths).map(([name,p])=>[name,fs.readFileSync(path.join(ROOT,p))]));
 const expected={"family_tasks":"ce0a4682ea713eb38bcdbd6e841de9f5c7cd574e","govinfo_statute_index":"aff375864d74dece7bea7998462d72a5cb43ebff"};
 const shas=Object.fromEntries(Object.entries(bytes).map(([name,value])=>[name,createHash("sha1").update("blob "+value.length+"\0").update(value).digest("hex")]));
 for(const k of Object.keys(expected))if(shas[k]!==expected[k])throw Error("Frozen input changed; reconsider provenance: "+k);
 const families=bytes.family_tasks.toString("utf8").split(/\r?\n/).filter(Boolean).map(x=>JSON.parse(x)),statutes=csvParse(bytes.govinfo_statute_index.toString("utf8"));
 const m=combine(families,statutes,shas),dir=path.join(ROOT,"research/stage20/output");
 const outputs={
  "STATUTE_CASE_REVIEW_QUEUE.csv":csvWrite(m.pairs,Object.keys(m.pairs[0])),
  "STATUTE_SOURCE_CASE_PACKETS.jsonl":m.records.map(r=>JSON.stringify(r)).join("\n")+"\n",
  "STATUTE_SOURCE_READY_WORKBENCH.html":htmlView(m),
  "STATUTE_CUSTODY_METRICS.json":JSON.stringify(m.metrics,null,2)+"\n"
 };
 if(process.argv.includes("--check")){
  for(const [name,s] of Object.entries(outputs))if(fs.readFileSync(path.join(dir,name),"utf8")!==s)throw Error("Stale derived statutory evidence: "+name);
  console.log("Statute source→case review index reproducible.");
 }else{
  fs.mkdirSync(dir,{recursive:true});for(const [name,s] of Object.entries(outputs))fs.writeFileSync(path.join(dir,name),s,"utf8");
  console.log(JSON.stringify(m.metrics,null,2));
 }
}
