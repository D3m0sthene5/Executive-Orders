from pathlib import Path
import json,hashlib,datetime,csv
B=Path('research/excavator/machiavelli-modern-undecided-20261105');O=B/'continuation-20261105/procurement';d=json.loads((O/'SOURCE_FINDINGS.json').read_text());issues=[];rows=[];counts={};now=datetime.datetime.now(datetime.timezone.utc).isoformat()
for n in [13788,13980]:
 p=json.loads((O/f'EO_{n}/LIFECYCLE_PROPOSAL.json').read_text());ds=json.loads((B/f'b02/packet-v1/overlay/v1/EO_{n}/DOSSIER.json').read_text());assert p['approved'] is False;assert {c['scope_id'] for c in p['clauses']}=={c['scope_id'] for c in ds['clauses']};counts[str(n)]=len(p['clauses']);original=d['sources']['original'+str(n)];t=Path(original['text_path']).read_text();by={c['scope_id']:c for c in ds['clauses']}
 for c in p['clauses']:
  a=by[c['scope_id']];assert t[a['char_start']:a['char_end']]==a['text'];assert c['reason'] and c['checked_through']=='2026-10-14'
  rows.append({k:c[k] for k in ['scope_id','clause_id','state','end_id','effective_date','effective_date_confirmed','reason','checked_through']}|{'original_pdf_page':a['pdf_page'],'original_char_start':a['char_start'],'original_char_end':a['char_end'],'original_text_sha256':original['text_sha256'],'later_event_ids':json.dumps(c['later_event_ids'])})
for k,s in d['sources'].items():
 for pk,hk in [('raw_path','raw_sha256'),('text_path','text_sha256')]:
  if s.get(pk) and s.get(hk):assert hashlib.sha256(Path(s[pk]).read_bytes()).hexdigest()==s[hk],k+' '+pk
 for span in s.get('spans',[]):
  if s.get('text_path'):assert 0<=span['char_start']<span['char_end']<=len(Path(s['text_path']).read_text()),k
with (O/'clauses.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
with (O/'cumulative-journal.jsonl').open('w') as f:
 for row in d['command_ledger']:f.write(json.dumps({'entry':'continuation-command-research','recorded_at_utc':now,'instrument_id':row['instrument_id'],'command':row['command'],'source_keys':row['source_keys'],'finding':row['finding'],'first_ending_exact':row['first_ending_exact'],'performance_interval':row['performance_interval'],'actual_performance':row['actual_performance'],'approval':False})+'\n')
r={'schema':'machiavelli-producer-local-validation/v1','checked_at_utc':now,'approved_false':True,'native_inventory_counts':counts,'native_original_spans_equal_dossier_text':True,'source_count':len(d['sources']),'command_count':len(d['command_ledger']),'issues':issues,'scope':'Read-only hash, JSON, inventory and original-offset validation; not native scientific approval/readiness/exhaustion.'};(O/'VALIDATION.json').write_text(json.dumps(r,indent=2)+'\n')
t=json.loads((O/'TIMING.json').read_text());t['checked_at_utc']=now;(O/'TIMING.json').write_text(json.dumps(t,indent=2)+'\n');print(json.dumps(r))
