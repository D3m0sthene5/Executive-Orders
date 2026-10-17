#!/usr/bin/env python3
"""Offline evidence-oriented claim review: dossier export + transactional signed-by-operator import.
No file download or backend required for the HTML form. Importer is intentionally separate and auditable.
"""
import argparse,base64,datetime,hashlib,html,json,os,pathlib,shutil,sqlite3,sys

def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def digest(v):return hashlib.sha256(canon(v).encode()).hexdigest()
def dbopen(db):
 c=sqlite3.connect(db);c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON');return c

def make_dossier(db, id, blind=False):
 c=dbopen(db);a=c.execute('SELECT * FROM instruments WHERE id=?',(id,)).fetchone()
 if not a:raise ValueError('Identity not found in canonical census: '+id)
 inst=dict(a)
 opus=c.execute('SELECT * FROM opus_checkpoint2_import WHERE instrument_id=?',(id,)).fetchone()
 rows=[dict(x) for x in c.execute('SELECT * FROM stage17_claim WHERE instrument_id=? ORDER BY claim_kind,claim_id',(id,))]
 for r in rows:r['claim_payload']=json.loads(r['claim_payload']);r['source_ids_json']=json.loads(r['source_ids_json'])
 src=[dict(x) for x in c.execute('SELECT * FROM stage17_source WHERE subject_id=?',(id,))]
 ep=[dict(x) for x in c.execute('SELECT * FROM legal_episode WHERE instrument_id=?',(id,))]
 pv=[dict(x) for x in c.execute('SELECT * FROM stage17_provision WHERE instrument_id=?',(id,))]
 tr=[]
 for p in pv:
  tr += [dict(x) for x in c.execute('SELECT * FROM stage17_transition WHERE affected_provision_id=? ORDER BY event_date',(p['provision_id'],))]
 legal=[dict(x) for x in c.execute('SELECT * FROM legal_event WHERE affected_instrument=? OR actor_instrument=? ORDER BY effective_date',(id,id))]
 evidence=[dict(x) for x in c.execute('SELECT source_url,source_sha,source_kind,valid_asof,category,disposition,amendments,notes FROM source_observations WHERE related_id=? LIMIT 150',(id,))]
 a17=[dict(x) for x in c.execute('SELECT * FROM stage17_assessment WHERE instrument_id=?',(id,))]
 graph=[dict(x) for x in c.execute('SELECT actor,predecessor,relation,source_url,source_sha,eligible_for_research,quarantine_reason FROM candidate_relationships WHERE predecessor=? OR actor=? LIMIT 250',(id,id))]
 source_state={'curated_originals_locally_stored':sum(int(x.get('local_original_bytes') or 0) for x in src),'curated_sources':len(src),'archival_source_observations':len(evidence),'graph_leads':len(graph),'quarantined_graph_leads':sum(1 for x in graph if not x['eligible_for_research'])}
 raw=c.execute('SELECT raw_json FROM original_stage11_rows WHERE record_id=?',(id,)).fetchone()
 out={'instrument':inst,'claim_records':rows,'stage17_source':src,'stage16_episodes':ep,'stage17_provisions':pv,'stage17_transitions':tr,'source_events':legal,'source_observations':evidence,'independent_assessments':a17,'legacy_record':json.loads(raw[0]) if raw else None,'opus_provisional':dict(opus) if opus else None,'human_certifications':0,'shared_rule_dependencies':graph,'source_search_coverage':source_state}
 if blind:
  # No legacy candidate answer, rationale, same-model review text, or Opus status leaks to blind reviewer.
  out['opus_provisional']=None;out['independent_assessments']=[];out['legacy_record']=None
  out['instrument'].pop('original_legacy_status',None);out['instrument'].pop('original_any_effect',None);out['instrument'].pop('original_review',None)
  out['claim_records']=[dict(x) for x in rows if x['claim_kind'] in ('identity','authenticity')]
  out['blind_review_instructions']='Record independent source-derived identity/authenticity findings before seeing any inherited status; coordinator later compares separate blinded decision file.'
 c.close();return out

def export_html(db,id,out,blind=False):
 data=make_dossier(db,id,blind)
 # Escape html/script injection from historical source text and titles in JSON.
 packed=json.dumps(data,ensure_ascii=False).replace('</','<\\/')
 template='''<!doctype html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><title>EO Stage 17 Review</title>
 <style>body{font:15px/1.5 system-ui, sans-serif;max-width:1220px;margin:0 auto;padding:18px;color:#19202a;background:#f6f8fa}h1{font-size:22px}h2{font-size:17px}section{padding:16px;margin:15px 0;background:white;border:1px solid #d8dee5;border-radius:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f5f8;padding:12px}label{display:block;font-weight:600;margin:12px 0 3px}input,textarea,select{font:inherit;width:100%;box-sizing:border-box;padding:8px;border:1px solid #aeb8c4;border-radius:5px}textarea{min-height:95px}button{background:#223d5a;color:white;border:0;padding:10px 16px;cursor:pointer;margin:8px 4px 8px 0;border-radius:5px}.muted{color:#5d6877}.danger{color:#a34129}a{overflow-wrap:anywhere}code{font-size:12px}</style></head><body>
 <h1>Executive Order claim-by-claim human review</h1><div id="banner" class="muted"></div><section><h2>Identity and legal record</h2><pre id="identity"></pre><p class="danger">Source URL or hosted transcript is NOT a locally preserved signed original unless the source record expressly says so. No AI finding is a human certification.</p></section>
 <section><h2>Sources and source-search gaps</h2><div id="sources"></div></section>
 <section><h2>Provisions, host amendments, and redline candidates</h2><div id="provisions"></div></section>
 <section><h2>Dated event and legal-state timeline</h2><div id="timeline"></div></section>
 <section><h2>Claim and legal memorandum</h2><label for="claim">Claim to review</label><select id="claim"></select><pre id="claimtext"></pre><pre id="memo"></pre></section>
 <section><h2>Review decision — local export only</h2><p>Every record requires a real reviewer and evidence-based rationale. Export the JSON and import it into the canonical SQLite database with <code>review_docket.py import</code>.</p><label for="reviewer">Reviewer identity</label><input id="reviewer" placeholder="Human reviewer name"/><label for="decision">Decision</label><select id="decision"><option value="hold">Hold unresolved</option><option value="uphold">Uphold claim</option><option value="revise">Revise claim</option></select><label for="rationale">Evidence and reasoning</label><textarea id="rationale" placeholder="State the legal evidence and strongest counterargument"></textarea><label for="gaps">Outstanding evidence gap</label><textarea id="gaps" placeholder="Exactly what remains unproved"></textarea><label for="revision">Proposed revised finding (only for revise)</label><textarea id="revision"></textarea><button id="add">Add reviewed claim</button><button id="export">Export JSON review file</button><p id="queued"></p></section>
 <script id="record" type="application/json">%%DATA%%</script><script>
 const x=JSON.parse(document.querySelector('#record').textContent), byId=id=>document.getElementById(id),j=v=>JSON.stringify(v,null,2);let pending=[];
 byId('banner').textContent=x.instrument.id+' • '+(x.blind_review_instructions?'BLINDED independent review':'Exposed-record review')+' • '+x.stage17_source.length+' curated source records';
 byId('identity').textContent=j(x.instrument);
 byId('sources').innerHTML=(x.stage17_source.length?x.stage17_source.map(s=>'<p><strong>'+esc(s.source_id)+'</strong> — <a rel="noopener noreferrer" href="'+esc(s.source_url)+'" target="_blank">'+esc(s.source_url)+'</a><br>'+esc(s.transcript_grade)+' • '+esc(s.acquisition_limit)+'</p>').join(''):'<p>No locally authenticated original source recorded.</p>')+'<p><strong>Source-search coverage:</strong> '+esc(j(x.source_search_coverage))+'</p>'+(x.source_observations.length?'<details><summary>Other historical editorial source observations (not necessarily originals)</summary><pre>'+esc(j(x.source_observations))+'</pre></details>':'')+'<details><summary>Shared dependency and quarantine evidence</summary><pre>'+esc(j(x.shared_rule_dependencies))+'</pre></details>';
 function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
 const provisions=x.stage17_provisions.concat(x.stage16_episodes);byId('provisions').innerHTML=provisions.length?'<pre>'+esc(j(provisions))+'</pre>':'<p>No reconstructed provision footprint; whole-order closure is unverified.</p>';
 const tl=[...x.stage17_transitions,...x.source_events];tl.sort((a,b)=>String(a.event_date||a.effective_date||'').localeCompare(String(b.event_date||b.effective_date||'')));byId('timeline').innerHTML=tl.length?tl.map(t=>'<p><strong>'+esc(t.event_date||t.effective_date||'?')+'</strong> — '+esc(t.kind||t.event_kind||'event')+'<br><del>'+esc(t.old_rule||'')+'</del> → <ins>'+esc(t.new_rule||t.scope||'')+'</ins><br><small>'+esc(t.source_id||'')+'</small></p>').join(''):'<p>No dated legal transitions established.</p>';
 const select=byId('claim');x.claim_records.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.claim_kind+' — '+c.claim_scope;select.append(o);});
 function show(){const c=x.claim_records[Number(select.value||0)];byId('claimtext').textContent=j(c?c.claim_payload:{});byId('memo').textContent=x.blind_review_instructions||j(x.independent_assessments);};select.addEventListener('change',show);show();
 byId('add').onclick=()=>{const c=x.claim_records[Number(select.value)];const reviewer=byId('reviewer').value.trim(), rationale=byId('rationale').value.trim(), decision=byId('decision').value;
 if(!reviewer||rationale.length<12){alert('Reviewer and a specific rationale of at least twelve characters are required.');return;}
 if(decision==='revise'&&!byId('revision').value.trim()){alert('Revisions require proposed replacement text');return;}
 pending.push({claim_id:c.claim_id,claim_fingerprint:c.fingerprint,codebook_version:c.policy_version,reviewer_name:reviewer,reviewed_at:new Date().toISOString(),decision:decision,rationale:rationale,new_claim_text:byId('revision').value.trim()||null,source_gaps:byId('gaps').value.trim(),review_scope:c.claim_scope,test_only:false});byId('queued').textContent=pending.length+' pending decision(s)';};
 byId('export').onclick=()=>{if(!pending.length){alert('Add at least one decision first');return;}const blob=new Blob([JSON.stringify({schema:'eo-stage17-review-v1',instrument_id:x.instrument.id,review_decisions:pending},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='EO_STAGE17_review_'+x.instrument.id.replace(/[^a-zA-Z0-9]/g,'_')+'.json';a.click();URL.revokeObjectURL(a.href);};
 </script></body></html>'''
 pathlib.Path(out).parent.mkdir(parents=True,exist_ok=True);pathlib.Path(out).write_text(template.replace('%%DATA%%',packed),encoding='utf-8');return len(data['claim_records'])

def review_import(db,jsonpath,test_only=False):
 payload=json.loads(pathlib.Path(jsonpath).read_text());assert payload.get('schema')=='eo-stage17-review-v1'
 decisions=payload.get('review_decisions');assert isinstance(decisions,list) and decisions
 c=dbopen(db);added=0
 try:
  c.execute('BEGIN IMMEDIATE')
  for d in decisions:
   keys={'claim_id','claim_fingerprint','codebook_version','reviewer_name','reviewed_at','decision','rationale','new_claim_text','source_gaps','review_scope','test_only'}
   if not keys.issubset(d):raise ValueError('Missing fields: '+str(keys-set(d)))
   claim=c.execute('SELECT * FROM stage17_claim WHERE claim_id=?',(d['claim_id'],)).fetchone()
   if claim is None or claim['fingerprint']!=d['claim_fingerprint']:raise ValueError('Stale or unknown claim: '+d['claim_id'])
   if claim['policy_version']!=d['codebook_version']:raise ValueError('Changed legal codebook')
   if d['decision'] not in ('uphold','revise','hold'):raise ValueError('Invalid decision')
   if not isinstance(d['reviewer_name'],str) or not d['reviewer_name'].strip():raise ValueError('Reviewer required')
   if not isinstance(d['rationale'],str) or len(d['rationale'].strip())<12:raise ValueError('Evidence-based explanation required')
   if d['decision']=='revise' and not d['new_claim_text']:raise ValueError('Missing revised finding')
   if d['test_only'] and not test_only:raise ValueError('Test-only decision cannot enter authoritative DB without explicit test mode')
   datetime.datetime.fromisoformat(d['reviewed_at'].replace('Z','+00:00'))
   stable={k:d[k] for k in keys if k not in ('test_only',)}
   event_hash=digest(stable);rid='rv17-'+event_hash
   c.execute('INSERT OR IGNORE INTO stage17_review VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(rid,d['claim_id'],d['claim_fingerprint'],d['reviewer_name'],d['reviewed_at'],d['decision'],d['rationale'],d['new_claim_text'],d['source_gaps'],d['review_scope'],int(test_only),event_hash,'TEST_ONLY' if test_only else 'EXTERNAL_USER_REVIEW'))
   added+=c.execute('SELECT changes()').fetchone()[0]
  c.commit()
 except Exception:
  c.rollback();raise
 finally:c.close()
 return added

if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
 e=sub.add_parser('dossier');e.add_argument('db');e.add_argument('instrument');e.add_argument('--html',required=True);e.add_argument('--blind',action='store_true')
 imp=sub.add_parser('import');imp.add_argument('db');imp.add_argument('review_json');imp.add_argument('--test-only',action='store_true')
 a=p.parse_args()
 if a.cmd=='dossier':print('Claims available:',export_html(a.db,a.instrument,a.html,a.blind))
 else:print('New review decisions committed:',review_import(a.db,a.review_json,a.test_only))
