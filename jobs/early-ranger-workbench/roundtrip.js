/* Browser and Node share the import/export contract; no research approval. */
const RangerRoundtrip = (() => {
const schema='eo-early-source-worksheet/v2',state='research_only_never_certification';
const canonical=x=>JSON.stringify(x&&typeof x==='object'?Array.isArray(x)?x.map(v=>JSON.parse(canonical(v))):Object.fromEntries(Object.keys(x).sort().map(k=>[k,JSON.parse(canonical(x[k]))])):x);
function parse(text){
 let i=0;
 const ws=()=>{while(/\s/.test(text[i]||'')&&i<text.length)i++;};
 function string(){const start=i++;while(i<text.length){if(text[i]==='\\'){i+=2;continue;}if(text[i++]==='"')return JSON.parse(text.slice(start,i));}throw Error('Unterminated JSON string');}
 function value(){
  ws();const ch=text[i];
  if(ch==='"')return string();
  if(ch==='{'){
   i++;ws();const out=Object.create(null),seen=new Set();if(text[i]==='}'){i++;return out;}
   while(true){ws();if(text[i]!=='"')throw Error('Expected JSON key');const key=string();if(seen.has(key))throw Error('Duplicate worksheet key: '+key);seen.add(key);ws();if(text[i++]!==':')throw Error('Expected colon');out[key]=value();ws();const next=text[i++];if(next==='}')return out;if(next!==',')throw Error('Expected comma');}
  }
  if(ch==='['){i++;ws();const out=[];if(text[i]===']'){i++;return out;}while(true){out.push(value());ws();const next=text[i++];if(next===']')return out;if(next!==',')throw Error('Expected comma');}}
  const start=i;while(i<text.length&&!/[\s,}\]]/.test(text[i]))i++;if(i===start)throw Error('Expected JSON value');return JSON.parse(text.slice(start,i));
 }
 const out=value();ws();if(i!==text.length)throw Error('Trailing JSON content');return out;
}
async function health(b){
 if(!b||b.schema!=='eo-early-case-sources/v1')return 'unknown_version';
 const body={...b};delete body.fingerprint;
 const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(body)));
 if([...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('')!==b.fingerprint)return 'conflicting_representation';
 if(!Array.isArray(b.sources))return 'unknown_version';
 const seen=new Map();for(const s of b.sources){
  if(!s||typeof s!=='object')return 'unknown_version';
  const key=canonical([s.role,s.path]);if(seen.has(key)&&seen.get(key)!==canonical(s))return 'conflicting_representation';seen.set(key,canonical(s));
  if(s.expected_sha256&&s.sha256&&s.expected_sha256!==s.sha256)return 'conflicting_representation';
 }
 if(b.sources.some(s=>!s.present))return 'missing_source';
 return !b.candidate_version||!b.sources.length?'unknown_version':'unchanged_source';
}
async function classify(id,e,c){
 if(!e||!c||e.candidate_id!=='LOC:'+id)return 'conflicting_representation';
 const a=e.source_binding,b=c.source_binding;if(!a||!b)return 'unknown_version';
 for(const x of [a,b])if(x.item_id!==id||x.candidate_id!=='LOC:'+id||x.item_url!==c.url)return 'conflicting_representation';
 for(const x of [a,b]){const s=await health(x);if(s!=='unchanged_source')return s;}
 return canonical(a)===canonical(b)?'unchanged_source':'changed_source';
}
function exportWorksheet(cases,notes,unverified=[]){
 const by=new Map(cases.map(c=>[c.id,c]));if(by.size!==cases.length||Object.keys(notes).some(id=>!by.has(id)))throw Error('Duplicate or unknown catalog item');
 return {schema,review_state:state,per_case:Object.fromEntries(Object.entries(notes).map(([id,n])=>[id,{candidate_id:'LOC:'+id,source_binding:by.get(id).source_binding,notes:n}])),unverified_notes:unverified};
}
async function validate(d,cases){
 if(!d||d.review_state!==state||![schema,'eo-early-source-worksheet/v1'].includes(d.schema))throw Error('Unrecognized research worksheet');
 if(!d.per_case||typeof d.per_case!=='object'||Array.isArray(d.per_case))throw Error('per_case must be an object');
 const by=new Map(cases.map(c=>[c.id,c]));if(by.size!==cases.length)throw Error('Duplicate current catalog item');
 const result=[];for(const [id,e] of Object.entries(d.per_case)){
  const legacy=d.schema.endsWith('/v1'),n=legacy?e:e?.notes;
  let status=legacy&&by.has(id)?'legacy_unverified':await classify(id,e,by.get(id));
  if(!n||typeof n!=='object'||Array.isArray(n))status='conflicting_representation';
  result.push({item_id:id,validation:status,entry:e,notes:n,research_only:true});
 }
 for(const old of d.unverified_notes||[])result.push({item_id:old.item_id,validation:'legacy_unverified',entry:old,notes:null,research_only:true});
 return result;
}
return {exportWorksheet,validate,classify,parse};
})();
if(typeof module!=='undefined')module.exports=RangerRoundtrip;
