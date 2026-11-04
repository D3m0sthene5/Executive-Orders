/* Read-only view of existing tracker rows. No scientific state is inferred. */
(function(root){
'use strict';
const CHECKPOINTS=[
 {id:'text',title:'Get usable text',short:'Text',fields:['original_text'],why:'Hold a usable copy and verify the page and identity. A provisional text can carry replacement and quotation obligations.',action:'Reuse exact confirmed text; acquire and check the copies still missing.',jobs:['source-ladder','fr-originals-pages','pinakes-proquest-ingest','official-fixity','astra-source-retention'],gap:'Retrieval exists. Page examination and missing originals still need work.',measure:'Record source wait, page-check time, repeated downloads and exact confirmation reuse.'},
 {id:'commands',title:'List every command',short:'Commands',fields:['clause_inventory'],why:'Account for each operative command so a small clause cannot disappear from the history.',action:'Use clause drafts as the starting list; examine omissions before research and review.',jobs:['clause-drafts','claim-kit-case-bundles','geddes'],gap:'Drafting and diagnostics exist. An extracted list still needs source examination.',measure:'Record missing clauses caught early, corrections, and later rework avoided.'},
 {id:'lifecycle',title:'Explain its legal life',short:'Legal history',fields:['provisional_status','ending_or_current_basis','savings_residuals'],why:'Support the provisional status, how each command ended or continues, and any surviving effects.',action:'Research source-ready families together, then test applicability for each order.',jobs:['later-events-status-history-current-law','corpus-excavator','norton','valla','claim-kit-case-bundles'],gap:'Search, evidence packaging and reuse exist. Legal application and missing evidence remain case work.',measure:'Separate searching, reading, analysis, shared research and per-order exceptions.'},
 {id:'evidence',title:'Test the evidence',short:'Evidence',fields:['counterevidence','shared_sources','opus_media'],why:'Examine contrary leads and finish applicable shared-source and media checks.',action:'Resolve specific missing sources and contrary leads before another full review.',jobs:['later-events-status-history-current-law','cruden-retrieval-cache','opus-media-match','mountweazel'],gap:'Retrieval and review support exist. A source hit does not establish what it proves.',measure:'Record duplicate source reads, first useful evidence, failed searches and unresolved leads.'},
 {id:'gates',title:'Finish review & filing',short:'Final gates',fields:[],why:'Complete independent review, exact-version corrections, machine gates and authorized filing. The tracker has no separate population count for each of these substeps.',action:'Inspect the exact hold or failed receipt, repair that version, and use ordinary completion.',jobs:['independent-ai-review','mountweazel','claim-checker','claim-kit-case-bundles','readiness-tracker'],gap:'Review and filing routes exist. Separate AI-review and filing queue sizes are not measured in these rows.',measure:'Link producer, reviewer, corrections, gate outcomes and final readiness to the same exact attempt.'}
];
const accepted=v=>v==='done'||v==='provisional'||v==='n/a';
function missing(row,cp){return cp.fields.some(f=>!accepted(row['step_'+f]));}
function analyze(rows){
 const buckets=Object.fromEntries([...CHECKPOINTS.map(c=>[c.id,[]]),['ready',[]]]);
 const remaining=Object.fromEntries(CHECKPOINTS.map(c=>[c.id,[]]));
 const checkCounts={};let provisional=0,obligations=0;
 for(const row of rows){
  if(row.step_original_text==='provisional')provisional++;
  if(row.original_copy_replacement_required==='yes'||row.quotation_recheck_required==='yes')obligations++;
  for(const [key,val] of Object.entries(row))if(key.startsWith('step_')){checkCounts[key]??={done:0,provisional:0,open:0,na:0,unknown:0};checkCounts[key][val==='n/a'?'na':['done','provisional','open'].includes(val)?val:'unknown']++;}
  if(row.ready_for_human_review==='yes'){buckets.ready.push(row);continue;}
  let first=null;
  for(const cp of CHECKPOINTS.filter(c=>c.fields.length))if(missing(row,cp)){remaining[cp.id].push(row);first??=cp.id;}
  buckets[first||'gates'].push(row);
  // Final-gate population is observable only after all listed checks close.
  if(!first)remaining.gates.push(row);
 }
 return {buckets,remaining,checkCounts,total:rows.length,ready:buckets.ready.length,unfinished:rows.length-buckets.ready.length,provisional,obligations};
}
function blockers(rows){const counts=new Map();for(const row of rows){for(const code of new Set((row.blockers||'').split('|').filter(Boolean))){counts.set(code,(counts.get(code)||0)+1);}}return [...counts].sort((a,b)=>b[1]-a[1]);}
const api={CHECKPOINTS,accepted,missing,analyze,blockers};
if(typeof module==='object'&&module.exports)module.exports=api;else root.EOFlow=api;
})(typeof globalThis!=='undefined'?globalThis:this);
