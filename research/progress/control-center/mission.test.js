'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const M=require('./mission.js');

async function fixture(humanCount=0){
 const ref='a'.repeat(40), status={job:'readiness-tracker',result:'succeeded',exit_code:0,commit_run:'b'.repeat(40),finished_utc:'2026-11-04T12:00:00Z',run_url:'https://github.com/example/actions/runs/1'};
 const checker={...status,job:'claim-checker',finished_utc:'2026-11-04T11:59:00Z'};
 const summary={orders_total:10,ready_for_human_review:2,orders_with_provisional_status:7};
 const texts={tracker:'instrument_id,ready_for_human_review\nEO:1,yes\n',tracker_status:JSON.stringify(status),tracker_summary:JSON.stringify(summary),checker_status:JSON.stringify(checker),universe:'id,title\nEO:1,Example\n',weights:'frozen weights\r\n',human_review:JSON.stringify({independently_reviewed_whole_lifecycle_complete:humanCount})};
 const hashes=Object.fromEntries(await Promise.all(Object.entries(texts).map(async([key,value])=>[key,await M.hash(value)])));
 const end=109+24/60+15/3600,latest={date:'2026-11-04',committed_at:status.finished_utc,commit:status.commit_run.slice(0,10),progress:.25,met_hours:Math.round(end*.25*1000)/1000,phase:'Translunar coast',orders_in_census:10,orders_goal:1324,ready_for_human_review:2,provisional_statuses:7,human_certified:0};
 const payload={schema:'eo-mission/v1',generated_utc:'2026-11-04T12:01:00Z',repository_input_commit:ref,tracker_generation:{...status},checker_generation:{...checker},readiness_inputs:{path:'research/readiness',git_tree:'d'.repeat(40)},sources:Object.fromEntries(Object.keys(texts).map(key=>[key,{path:M.PATHS[key],sha256:hashes[key]}])),model:{version:'capcom-frozen-weights-v1',denominator_version:'current-census-plus-frozen-gap-v1',weights_sha256:hashes.weights,census_gap:1314,orders_goal:1324,first_step_hours:end,history_compatible:true},freshness:{state:'generation_reported',claim_receipts:'claim_versions_match'},latest,history:[{...latest}],milestones:[{key:'launch',hours:0},{key:'tli',hours:2+44/60+26/3600},{key:'loi',hours:75+50/60},{key:'landing',hours:102+45/60+39/3600},{key:'first_step',hours:end}],human_review:{published_whole_lifecycle_certifications:humanCount},limits:['Fixture: no scientific result.']};
 const receipt={schema:'eo-mission-refresh/v1',state:'ready',attempted_utc:'2026-11-04T12:01:00Z',reason:null,tracker_generation:status,readiness_inputs:{...payload.readiness_inputs}};
 const sync=()=>{texts.mission=JSON.stringify(payload);texts.refresh=JSON.stringify(receipt);};sync();
 const readTree=async treeSha=>treeSha===ref?{sha:'f'.repeat(40),truncated:false,tree:[{path:'research',mode:'040000',type:'tree',sha:'e'.repeat(40)}]}:{sha:'e'.repeat(40),truncated:false,tree:[{path:'readiness',mode:'040000',type:'tree',sha:payload.readiness_inputs.git_tree}]};
 return {ref,status,checker,summary,hashes,texts,payload,receipt,sync,readTree,context:{status,checker,summary,hashes},read:path=>{const key=Object.keys(M.PATHS).find(key=>M.PATHS[key]===path);if(!(key in texts))throw Error('HTTP 404');return Promise.resolve(texts[key]);}};
}
test('loads a hash-bound generation and separates the human register from legacy zero',async()=>{
 const f=await fixture(3),state=await M.load(M.initial(),f.ref,f.read,f.readTree);
 assert.equal(state.state,'current');assert.equal(state.human,3);assert.equal(state.data.latest.human_certified,0);assert.equal(state.ref,f.ref);
 const html=M.render(state);assert.match(html,/Matching published generation/);assert.match(html,/Human-certified/);assert.match(html,/T\+27h 21m/);assert.match(html,/>3<\/strong>/);
});
test('unknown human certification stays unknown',async()=>{
 const f=await fixture(null),state=await M.load(null,f.ref,f.read,f.readTree);assert.equal(state.state,'current');assert.equal(state.human,null);assert.match(M.render(state),/>Unknown<\/strong>/);
});
test('rejects mixed generation, source bytes, model change and count mismatch',async()=>{
 const cases=[p=>p.tracker_generation.commit_run='c'.repeat(40),p=>p.sources.tracker.sha256='d'.repeat(64),p=>p.sources.tracker_status.sha256='d'.repeat(64),p=>p.model.census_gap=1200,p=>p.model.weights_sha256='e'.repeat(64),p=>p.model.history_compatible=false,p=>p.latest.ready_for_human_review=9,p=>p.latest.met_hours=70,p=>p.history[0].orders_goal=1400,p=>p.milestones=[]];
 for(const mutate of cases){const f=await fixture();mutate(f.payload);assert.equal(M.validate(f.payload,f.context).ok,false);}
 const f=await fixture();f.texts.tracker_status+='\n';const s=await M.load(null,f.ref,f.read,f.readTree);assert.equal(s.data,null);assert.equal(s.state,'pending');assert.match(s.message,/Source mismatch/);
});
test('new tracker with absent mission retains last good flight and its date',async()=>{
 const f=await fixture(),previous=await M.load(null,f.ref,f.read,f.readTree);delete f.texts.mission;f.receipt.tracker_generation={...f.status,finished_utc:'2026-11-05T12:00:00Z'};f.texts.refresh=JSON.stringify(f.receipt);
 const next=await M.load(previous,'c'.repeat(40),f.read,f.readTree);assert.equal(next.state,'pending');assert.equal(next.data,previous.data);assert.equal(next.ref,previous.ref);assert.equal(next.accepted_utc,previous.accepted_utc);const html=M.render(next);assert.match(html,/Last verified flight \/ retained/);assert.match(html,/Displayed tracker:/);assert.doesNotMatch(html,/Matching published generation/);
});
test('pending receipt overrides old matching STATUS when claims are newer',async()=>{
 const f=await fixture(),previous=await M.load(null,f.ref,f.read,f.readTree);f.receipt.state='pending';f.receipt.reason='Current claims need a checker/tracker refresh.';f.sync();
 let reads=0;const next=await M.load(previous,'c'.repeat(40),path=>{reads++;return f.read(path);});assert.equal(reads,1);assert.equal(next.data,previous.data);assert.equal(next.state,'pending');assert.match(next.message,/claims/);
 const first=await M.load(null,f.ref,f.read,f.readTree);assert.equal(first.state,'pending');assert.ok(first.data);assert.match(first.message,/claims/);
 delete f.texts.mission;const missing=await M.load(null,f.ref,f.read,f.readTree);assert.equal(missing.data,null);assert.match(missing.message,/claims/);
});
test('receipt and mission must bind the same tracker, and network failures retain data',async()=>{
 const f=await fixture(),previous=await M.load(null,f.ref,f.read,f.readTree);f.receipt.tracker_generation={...f.status,commit_run:'c'.repeat(40)};f.sync();
 const mismatch=await M.load(previous,f.ref,f.read,f.readTree);assert.equal(mismatch.state,'pending');assert.match(mismatch.message,/receipt does not match/);
 const failed=await M.load(previous,f.ref,()=>Promise.reject(Error('offline')));assert.equal(failed.data,previous.data);assert.match(failed.message,/unavailable/);
 const html=M.render(M.initial());assert.match(html,/Awaiting a verified flight/);assert.doesNotMatch(html,/mission-flight"/);
});
test('render escapes source-provided phase, limits and pending reasons',async()=>{
 const f=await fixture();f.payload.latest.phase='<img src=x onerror=alert(1)>';f.payload.history[0].phase=f.payload.latest.phase;f.payload.limits=['<script>alert(1)</script>'];f.sync();const state=await M.load(null,f.ref,f.read,f.readTree);const html=M.render(M.reject(state,'<img onerror=x>'));assert.doesNotMatch(html,/<img|<script/);assert.match(html,/&lt;img/);assert.match(html,/&lt;script/);
});
test('new main with unchanged outputs but changed readiness inputs stays pending',async()=>{
 const f=await fixture(),previous=await M.load(null,f.ref,f.read,f.readTree),newRef='c'.repeat(40),calls=[];
 const readTree=async treeSha=>{calls.push(treeSha);return treeSha===newRef?{sha:'f'.repeat(40),truncated:false,tree:[{path:'research',mode:'040000',type:'tree',sha:'e'.repeat(40)}]}:{sha:'e'.repeat(40),truncated:false,tree:[{path:'readiness',mode:'040000',type:'tree',sha:'9'.repeat(40)}]};};
 const next=await M.load(previous,newRef,f.read,readTree);assert.equal(next.state,'pending');assert.equal(next.data,previous.data);assert.equal(next.ref,previous.ref);assert.match(next.message,/Research inputs changed/);assert.deepEqual(calls,[newRef,'e'.repeat(40)]);assert.doesNotMatch(M.render(next),/Matching published generation/);
 const first=await M.load(null,newRef,f.read,readTree);assert.equal(first.state,'pending');assert.ok(first.data);assert.equal(first.data.latest.ready_for_human_review,2);assert.match(M.render(first),/Last verified flight \/ retained/);
});
test('output-only main commit with unchanged readiness tree can use the same mission',async()=>{
 const f=await fixture(),newRef='c'.repeat(40);
 const readTree=async treeSha=>treeSha===newRef?{sha:'f'.repeat(40),truncated:false,tree:[{path:'research',mode:'040000',type:'tree',sha:'e'.repeat(40)}]}:f.readTree(treeSha);
 const next=await M.load(null,newRef,f.read,readTree);assert.equal(next.state,'current');assert.equal(next.ref,newRef);assert.equal(next.data.repository_input_commit,f.ref);
});
test('new failed or replaced checker cannot leave an old mission looking current',async()=>{
 const f=await fixture(),previous=await M.load(null,f.ref,f.read,f.readTree);
 f.texts.checker_status=JSON.stringify({...f.checker,result:'failed',exit_code:1,finished_utc:'2026-11-04T13:00:00Z'});
 let next=await M.load(previous,f.ref,f.read,f.readTree);assert.equal(next.state,'pending');assert.equal(next.data,previous.data);assert.match(next.message,/current checker generation has not succeeded/);assert.doesNotMatch(M.render(next),/Matching published generation/);
 f.texts.checker_status=JSON.stringify({...f.checker,commit_run:'9'.repeat(40)});next=await M.load(previous,f.ref,f.read,f.readTree);assert.equal(next.state,'pending');assert.match(next.message,/Newer checker/);
});
test('changed current census bytes cannot certify an old denominator as current',async()=>{
 const f=await fixture(),previous=await M.load(null,f.ref,f.read,f.readTree);f.texts.universe+='EO:2,Newly admitted identity\n';
 const next=await M.load(previous,f.ref,f.read,f.readTree);assert.equal(next.state,'pending');assert.equal(next.data,previous.data);assert.match(next.message,/Source mismatch \(universe\)/);assert.doesNotMatch(M.render(next),/Matching published generation/);
});
test('unknown, missing, truncated or inconsistent input-tree evidence cannot claim current',async()=>{
 const f=await fixture(),previous=await M.load(null,f.ref,f.read,f.readTree);
 for(const readTree of [undefined,async()=>{throw Error('network unavailable');},async()=>({truncated:true,tree:[]}),async()=>({truncated:false,tree:[]}),async treeSha=>treeSha===f.ref?{truncated:false,tree:[{path:'research',mode:'040000',type:'tree',sha:'e'.repeat(40)}]}:{sha:'f'.repeat(40),truncated:false,tree:[{path:'readiness',mode:'040000',type:'tree',sha:f.payload.readiness_inputs.git_tree}] }]){
  const next=await M.load(previous,f.ref,f.read,readTree);assert.equal(next.state,'pending');assert.equal(next.data,previous.data);assert.match(next.message,/freshness is unknown/);
  const first=await M.load(null,f.ref,f.read,readTree);assert.equal(first.state,'pending');assert.ok(first.data);
 }
 delete f.payload.readiness_inputs;f.sync();let next=await M.load(previous,f.ref,f.read,f.readTree);assert.equal(next.state,'pending');assert.match(next.message,/witness is missing/);
 f.payload.readiness_inputs={path:'research/readiness',git_tree:'d'.repeat(40)};f.receipt.readiness_inputs.git_tree='9'.repeat(40);f.sync();next=await M.load(previous,f.ref,f.read,f.readTree);assert.equal(next.state,'pending');assert.match(next.message,/witness is missing or inconsistent/);
});
test('pinned immutable reads are shared and failures are retried',async()=>{
 const app=fs.readFileSync(__dirname+'/app.js','utf8');const start=app.indexOf('async function read('),end=app.indexOf('async function refreshObservability',start);let calls=0,fail=false;
 const context={immutableReads:new Map(),AbortSignal,fetch:async()=>{calls++;return {ok:!fail,status:503,text:async()=>'{"orders":10}'};}};vm.createContext(context);vm.runInContext(app.slice(start,end)+'\nglobalThis.read=read;',context);
 const url='https://raw.githubusercontent.com/owner/repo/'+'a'.repeat(40)+'/data.json';const results=await Promise.all([context.read(url),context.read(url,'text')]);assert.equal(calls,1);assert.equal(results[0].orders,10);assert.equal(results[1],'{"orders":10}');await context.read(url);assert.equal(calls,1);
 fail=true;const next=url.replace('a'.repeat(40),'b'.repeat(40));await assert.rejects(context.read(next));fail=false;await context.read(next);assert.equal(calls,3);
});
test('scoped nonrecursive tree responses cache the shared research tree across output commits',async()=>{
 const app=fs.readFileSync(__dirname+'/app.js','utf8'),start=app.indexOf('async function read('),end=app.indexOf('async function refreshObservability',start),urls=[];
 const research='e'.repeat(40),readiness='d'.repeat(40),first='a'.repeat(40),next='c'.repeat(40),base='https://api.github.com/repos/owner/repo/git/trees/';
 const context={immutableReads:new Map(),AbortSignal,fetch:async url=>{urls.push(url);const tree=url===base+research?{sha:research,truncated:false,tree:[{path:'readiness',mode:'040000',type:'tree',sha:readiness}]}:{sha:'f'.repeat(40),truncated:false,tree:[{path:'research',mode:'040000',type:'tree',sha:research}]};return {ok:true,text:async()=>JSON.stringify(tree)};}};
 vm.createContext(context);vm.runInContext(app.slice(start,end)+'\nglobalThis.read=read;',context);const readTree=ref=>context.read(base+ref);
 assert.equal(await M.readinessTree(first,readTree),readiness);assert.equal(await M.readinessTree(next,readTree),readiness);assert.equal(await M.readinessTree(next,readTree),readiness);
 assert.deepEqual(urls,[base+first,base+research,base+next]);assert.ok(urls.every(url=>!url.includes('?')&&!url.includes('recursive')));
});

// Optional offline visual fixture: EO_MISSION_PREVIEW=/tmp/mission-preview.html
if(process.env.EO_MISSION_PREVIEW){fixture().then(async f=>{const state=await M.load(null,f.ref,f.read,f.readTree);fs.writeFileSync(process.env.EO_MISSION_PREVIEW,'<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>'+fs.readFileSync(__dirname+'/style.css','utf8')+'\n'+fs.readFileSync(__dirname+'/mission.css','utf8')+'</style></head><body><main class="wrap">'+M.render(state)+'</main></body></html>');});}
