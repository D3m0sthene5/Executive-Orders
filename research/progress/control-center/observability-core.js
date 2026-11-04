/* Validates a dated measurement snapshot independently of live tracker counts. */
(function(root){
'use strict';
const GAP_IDS=['phase_role','repetition','blockers_retries','ready_conversion','time'];
const CHECKS=['text','commands','lifecycle','evidence','gates'];
const TOKEN_KEYS=['fresh_input','cache_read','cache_creation','output'];
const pin=v=>typeof v==='string'&&/^[0-9a-f]{40}$/.test(v);
const text=v=>typeof v==='string'&&v.trim().length>0&&v.length<=12000;
const integer=v=>Number.isSafeInteger(v)&&v>=0;
const date=v=>typeof v==='string'&&/^\d{4}-\d\d-\d\dT/.test(v)&&Number.isFinite(Date.parse(v));
const safePath=v=>typeof v==='string'&&v.length<=500&&/^[A-Za-z0-9_./-]+$/.test(v)&&!v.startsWith('/')&&!v.split('/').some(s=>!s||s==='.'||s==='..');
function requireThat(condition,message){if(!condition)throw Error('Observability: '+message);}
function amount(v){return v===null||(typeof v==='number'&&Number.isFinite(v)&&v>=0);}
function tokens(v){return !!v&&TOKEN_KEYS.every(k=>v[k]===null||integer(v[k]));}
function validate(data){
 requireThat(data&&data.schema_version===1,'unsupported schema');
 requireThat(date(data.generated_at)&&pin(data.source_pin),'missing generation or source pin');
 const b=data.baseline;
 requireThat(b&&pin(b.source_pin)&&date(b.finished_utc),'unversioned baseline');
 requireThat(['orders_total','ready','unfinished','human_certified'].every(k=>integer(b[k]))&&b.orders_total>0,'invalid baseline counts');
 requireThat(b.ready+b.unfinished===b.orders_total&&b.human_certified<=b.orders_total,'baseline totals disagree');
 requireThat(b.first_missing&&[...CHECKS,'ready'].every(k=>integer(b.first_missing[k]))&&Object.values(b.first_missing).every(integer),'invalid partition');
 requireThat(Object.keys(b.first_missing).length===6&&[...CHECKS,'ready'].reduce((n,k)=>n+b.first_missing[k],0)===b.orders_total&&b.first_missing.ready===b.ready,'partition does not reconcile');
 requireThat(b.open_anywhere&&Object.keys(b.open_anywhere).length===5&&CHECKS.every(k=>integer(b.open_anywhere[k])&&b.open_anywhere[k]>=b.first_missing[k]&&b.open_anywhere[k]<=b.unfinished)&&b.open_anywhere.text===b.first_missing.text&&b.open_anywhere.gates===b.first_missing.gates,'invalid overlapping counts');
 requireThat(Array.isArray(data.sources)&&data.sources.length>0,'missing provenance');
 const sourceIds=new Set();
 for(const s of data.sources){requireThat(text(s.id)&&!sourceIds.has(s.id)&&safePath(s.path)&&pin(s.ref),'invalid source reference');sourceIds.add(s.id);}
 const provenance=v=>Array.isArray(v)&&v.length>0&&new Set(v).size===v.length&&v.every(id=>sourceIds.has(id));
 requireThat(Array.isArray(data.gaps)&&data.gaps.length===5&&new Set(data.gaps.map(g=>g.id)).size===5,'five measurement views required');
 for(const g of data.gaps)requireThat(GAP_IDS.includes(g.id)&&['title','recovered','prospective','unavailable'].every(k=>text(g[k]))&&provenance(g.source_ids),'invalid gap coverage');
 requireThat(Array.isArray(data.campaigns)&&Array.isArray(data.roles),'missing campaign or role coverage');
 const campaignIds=new Map();
 for(const c of data.campaigns){
  requireThat(text(c.id)&&!campaignIds.has(c.id)&&['label','window','scope','coverage','outcomes'].every(k=>text(c[k]))&&provenance(c.source_ids),'invalid campaign scope');
  requireThat((c.workers===null||integer(c.workers))&&tokens(c.tokens)&&amount(c.api_equivalent_usd)&&amount(c.actual_cash_usd),'invalid campaign measurement');
  campaignIds.set(c.id,c);
 }
 const roleIds=new Set();
 for(const r of data.roles){
  const key=JSON.stringify([r.campaign_id,r.role,r.model]);
  requireThat(campaignIds.has(r.campaign_id)&&['role','model','coverage'].every(k=>text(r[k]))&&!roleIds.has(key),'invalid role attribution');roleIds.add(key);
  requireThat((r.workers===null||integer(r.workers))&&tokens(r.tokens),'invalid role measurement');
 }
 for(const [id,c] of campaignIds){
  const roles=data.roles.filter(r=>r.campaign_id===id);
  for(const k of TOKEN_KEYS){const known=roles.filter(r=>r.tokens[k]!==null);if(c.tokens[k]!==null)requireThat(known.reduce((n,r)=>n+r.tokens[k],0)<=c.tokens[k],'role tokens exceed campaign total');}
  if(c.workers!==null)requireThat(roles.reduce((n,r)=>n+(r.workers||0),0)<=c.workers,'role workers exceed campaign total');
 }
 requireThat(Array.isArray(data.boundaries)&&data.boundaries.length>0&&data.boundaries.every(text),'missing outcome boundaries');
 return data;
}
function accept(previous,candidate){try{validate(candidate);requireThat(!previous||Date.parse(candidate.generated_at)>=Date.parse(previous.generated_at),'older generation refused');return {data:JSON.parse(JSON.stringify(candidate)),error:null};}catch(err){return {data:previous,error:err.message};}}
function sourceUrl(s){requireThat(s&&safePath(s.path)&&pin(s.ref),'unsafe source link');return 'https://github.com/D3m0sthene5/Executive-Orders/blob/'+s.ref+'/'+s.path.split('/').map(encodeURIComponent).join('/');}
const api={GAP_IDS,TOKEN_KEYS,validate,accept,sourceUrl,safePath};
if(typeof module==='object'&&module.exports)module.exports=api;else root.EOObservability=api;
})(typeof globalThis!=='undefined'?globalThis:this);
