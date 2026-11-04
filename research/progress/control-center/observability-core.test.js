'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const O=require('./observability-core.js');
function fixture(){
 const tokens={fresh_input:10,cache_read:100,cache_creation:20,output:5};
 return {schema_version:1,generated_at:'2026-11-04T12:00:00Z',source_pin:'a'.repeat(40),
 baseline:{source_pin:'a'.repeat(40),finished_utc:'2026-11-02T19:33:11Z',orders_total:10,ready:2,unfinished:8,human_certified:0,first_missing:{text:3,commands:3,lifecycle:1,evidence:0,gates:1,ready:2},open_anywhere:{text:3,commands:6,lifecycle:7,evidence:5,gates:1}},
 sources:[{id:'telemetry',path:'research/progress/example.json',ref:'a'.repeat(40)}],
 gaps:O.GAP_IDS.map(id=>({id,title:id,recovered:'Partial historical recovery',prospective:'Capture ordinary receipts',unavailable:'Complete denominator unknown',source_ids:['telemetry']})),
 campaigns:[{id:'sample',label:'Historical sample',window:'2026-10-31',scope:'Worker telemetry only',coverage:'Coordinator excluded; unknown possible calls',outcomes:'Not an exact attempt-to-readiness attribution',source_ids:['telemetry'],workers:2,tokens,api_equivalent_usd:null,actual_cash_usd:null}],
 roles:[{campaign_id:'sample',role:'producer',model:'actual model',workers:1,tokens:{...tokens},coverage:'One reported role; no phase split'}],
 boundaries:['AI review is not human certification.']};
}
test('accepts a reconciled frozen snapshot without mutating the supplied object',()=>{
 const input=fixture(),accepted=O.accept(null,input);assert.equal(accepted.error,null);input.campaigns[0].label='changed';assert.equal(accepted.data.campaigns[0].label,'Historical sample');
});
test('unknown measurements must be explicit null and do not become zero',()=>{
 const f=fixture();for(const c of [...f.campaigns,...f.roles]){c.workers=null;for(const k of O.TOKEN_KEYS)c.tokens[k]=null;}
 const result=O.accept(null,f);assert.equal(result.error,null);assert.equal(result.data.campaigns[0].tokens.output,null);
 delete f.campaigns[0].actual_cash_usd;assert.match(O.accept(null,f).error,/measurement/);
});
test('baseline rejects duplicate extra categories, inconsistent totals and invalid overlap',()=>{
 for(const mutate of [f=>f.baseline.ready++,f=>f.baseline.first_missing.text++,f=>f.baseline.first_missing.unknown=0,f=>f.baseline.open_anywhere.commands=1,f=>f.baseline.open_anywhere.gates=2,f=>f.baseline.open_anywhere.text++,f=>f.baseline.open_anywhere.unknown=0]){
  const f=fixture();mutate(f);assert.throws(()=>O.validate(f));
 }
});
test('an older fetched generation cannot replace newer last-good measurements',()=>{
 const previous=O.accept(null,fixture()).data,candidate=fixture();candidate.generated_at='2026-11-03T12:00:00Z';
 const result=O.accept(previous,candidate);assert.equal(result.data,previous);assert.match(result.error,/older generation/);
});
test('source paths and pins cannot inject a URL, traversal or HTML',()=>{
 for(const path of ['https://evil.example/a','//evil.example/a','../a','research/../../a','research/a?x=1','research/<img>.json','research//a']){
  const f=fixture();f.sources[0].path=path;assert.throws(()=>O.validate(f));assert.throws(()=>O.sourceUrl(f.sources[0]));
 }
 const f=fixture();f.sources[0].ref='main';assert.throws(()=>O.validate(f));
 assert.equal(O.sourceUrl(fixture().sources[0]),'https://github.com/D3m0sthene5/Executive-Orders/blob/'+'a'.repeat(40)+'/research/progress/example.json');
});
test('unknown source joins, incomplete gap scope and duplicate gaps refuse atomically',()=>{
 const previous=O.accept(null,fixture()).data;
 for(const mutate of [f=>f.gaps[0].source_ids=['missing'],f=>f.gaps[0].unavailable='',f=>f.gaps[0].id=f.gaps[1].id,f=>f.source_pin='main',f=>f.schema_version=2]){
  const candidate=fixture();mutate(candidate);const result=O.accept(previous,candidate);assert.equal(result.data,previous);assert.ok(result.error);
 }
});
test('role totals cannot exceed campaign usage and API price cannot substitute for cash',()=>{
 const f=fixture();f.roles[0].tokens.output=6;assert.throws(()=>O.validate(f),/role tokens/);
 f.roles[0].tokens.output=5;f.campaigns[0].api_equivalent_usd=2.5;assert.equal(O.validate(f).campaigns[0].actual_cash_usd,null);
 f.campaigns[0].actual_cash_usd='0';assert.throws(()=>O.validate(f));
});
test('measurement view escapes all supplied text and keeps missing dollars visible',()=>{
 const f=fixture();f.campaigns[0].label='<img src=x onerror=alert(1)>';
 const e=v=>String(v??'').replace(/[&<>"']/g,k=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[k]));
 const sandbox={observations:O.validate(f),measurementMsg:'Validated',EOObservability:O,EOFlow:require('./flow-core.js'),e,num:n=>Number.isFinite(n)?String(n):'Unknown',fmt:s=>s,tag:e};
 vm.createContext(sandbox);vm.runInContext(fs.readFileSync(__dirname+'/flow-view.js','utf8'),sandbox);
 // Historic card helper uses existing catalog helpers; no untrusted data reaches them.
 sandbox.flowHistoricalCosts=()=>'<p>Historical comparisons</p>';
 const html=vm.runInContext('flowCosts()+flowTelemetry()',sandbox);
 assert.ok(html.includes('&lt;img src=x onerror=alert(1)&gt;'));assert.ok(!html.includes('<img src=x'));
 assert.ok(html.includes('Unavailable'));assert.ok(html.includes('frozen reference counts'));assert.ok(html.includes('Coordinator excluded'));
});
test('failed fetch or invalid measurement refresh preserves last good snapshot and main data',async()=>{
 const dom={addEventListener(){},getElementById(){return {addEventListener(){}};}};
 const sandbox={document:dom,window:{addEventListener(){}},console,EOObservability:O,AbortSignal,fetch:async()=>{throw Error('offline');}};
 vm.createContext(sandbox);
 const app=fs.readFileSync(__dirname+'/app.js','utf8');
 vm.runInContext(app.slice(0,app.lastIndexOf('(async()=>')),sandbox);
 sandbox.saved=O.validate(fixture());
 vm.runInContext('observations=saved;snap={sha:"original"};',sandbox);
 await vm.runInContext('refreshObservability()',sandbox);
 assert.equal(vm.runInContext('observations===saved',sandbox),true);
 assert.equal(vm.runInContext('snap.sha',sandbox),'original');
 assert.match(vm.runInContext('measurementMsg',sandbox),/last good/);
 sandbox.fetch=async()=>({ok:true,json:async()=>({schema_version:999})});
 await vm.runInContext('refreshObservability()',sandbox);
 assert.equal(vm.runInContext('observations===saved',sandbox),true);
});
test('bundled real measurements validate and render with native first/overlap counts intact',()=>{
 const load=name=>JSON.parse(fs.readFileSync(__dirname+'/'+name,'utf8'));
 const data=O.validate(load('observability.json'));
 const dom={addEventListener(){},getElementById(){return {addEventListener(){}};}};
 const sandbox={document:dom,window:{addEventListener(){}},EOObservability:O,EOFlow:require('./flow-core.js'),
  input:{snap:load('snapshot.json'),atlas:load('atlas.json'),ev:load('evidence.json'),data,orders:fs.readFileSync(__dirname+'/orders.csv','utf8')}};
 vm.createContext(sandbox);
 vm.runInContext(fs.readFileSync(__dirname+'/flow-view.js','utf8'),sandbox);
 const app=fs.readFileSync(__dirname+'/app.js','utf8');vm.runInContext(app.slice(0,app.lastIndexOf('(async()=>')),sandbox);
 vm.runInContext('snap=input.snap;atlas=input.atlas;ev=input.ev;observations=input.data;setRows(csv(input.orders));',sandbox);
 const first=vm.runInContext('productionFlow()',sandbox);
 assert.ok(first.includes('Resources used by observed campaigns'));
 assert.ok(first.includes('Worker, review, correction and filing queue sizes and phase costs are unavailable here.'));
 assert.ok(first.includes('Recovered evidence'));assert.ok(first.includes('Prospective capture'));assert.ok(first.includes('Still unavailable'));
 assert.ok(first.includes('frozen reference counts'));assert.ok(first.includes('14,972'));assert.ok(first.includes('7,892'));
 vm.runInContext('flowMode="all"',sandbox);const overlap=vm.runInContext('productionFlow()',sandbox);
 assert.ok(overlap.includes('14,120'));assert.ok(overlap.includes('Counts overlap and must not be added'));
 for(const c of data.campaigns)for(const id of c.source_ids){const source=data.sources.find(s=>s.id===id);assert.ok(first.includes(O.sourceUrl(source)));}
});
