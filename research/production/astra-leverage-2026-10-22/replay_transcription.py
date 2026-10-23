import csv,hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path
repo=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(repo/'jobs/claim-kit'))
import inputs as I,excavate as E,build as B,assemble as A,working_text as W
sys.path.insert(0,str(repo/'jobs/claim-checker'))
import sources as S
out=Path(__file__).with_name('transcription-sample');out.mkdir(exist_ok=True)
old=out/'baseline_inputs.py';old.write_bytes(subprocess.check_output(['git','show','46a29e15d6ed4c252416b28e0ccc0590fcf6abc2:jobs/claim-kit/inputs.py'],cwd=repo))
spec=importlib.util.spec_from_file_location('baseline_inputs',old);baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)
ids={'EO:23','EO:249','EO:254'};fragments=repo/'jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl'
rows=[f for line in fragments.read_text().splitlines() if (f:=json.loads(line)).get('instrument_id') in ids and f.get('kind')=='original_representation']
results={};elapsed={}
for label,module in [('baseline',baseline),('patched',I)]:
 start=time.perf_counter();c=module._Collector(repo,ids,[])
 for f in rows:c.fragment(f,fragments.parent,fragments.relative_to(repo).as_posix())
 elapsed[label]=time.perf_counter()-start
 results[label]={r['instrument_id']:r for r in c.texts}
 results[label+'_warnings']=c.warnings
statuses={r['id'] if 'id' in r else r['instrument_id']:r for r in csv.DictReader((repo/I.STATUSES).open())}
index=S.HeldIndex();S.load_replica_fragments(index,repo);reader=S.TextReader()
policy_index=W.Index(repo);summaries=[]
for f in rows:
 iid=f['instrument_id'];rec=results['patched'][iid];before=results['baseline'][iid]
 rec['text']=(repo/rec['text_path']).read_text();segment=E.segment(iid,rec['text'],rec['source'])
 status=statuses.get(iid,{})
 corpus={'drafts':{},'statuses':{iid:status.get('provisional_substantive_status')},'machine_searches':{}}
 dossier=B.package(iid,corpus,{iid:rec},segment,[],[],{},[],[]);sheet=A.blank_sheet(dossier,'unassigned:requires independent review')
 full=dict(rec['source'],char_start=0,char_end=len(rec['text']),quote=rec['text'])
 errors,dependent=W.policy({'instrument_id':iid,'original_representation':full,'working_text':sheet['working_text']},repo,policy_index)
 copies=index.lookup_sha(f['data']['sha256']);verified=any(reader.verify_bytes(c) is True for c in copies)
 data={'instrument_id':iid,'original_source_sha256':f['data']['sha256'],'text_sha256':rec['source']['text_sha256'],
       'raw_bytes_verified':verified,'text_chars':len(rec['text']),'text_quality':f['data'].get('text_quality'),
       'pages':f['data'].get('pages'),'clause_leads':len(segment['clauses']),
       'before_grade':before['grade'],'after_grade':rec['grade'],
       'before_source_has_grade':bool(before['source'].get('grade')),
       'after_source_false_flag':rec['source']['acceptable_as_original'],
       'standing_note':sheet['working_text']['standing_note'],
       'working_text_pending_checks':errors,'approved':sheet['approved'],
       'reviewed_claims':0,'ready_gain':0}
 summaries.append(data)
 name=iid.replace(':','_')
 (out/(name+'.dossier.json')).write_text(json.dumps(dossier,indent=2)+'\n')
 (out/(name+'.DECISIONS.json')).write_text(json.dumps(sheet,indent=2)+'\n')
report={'scope':'Three held, decided, text-step-open ProQuest inputs; mechanical preparation only; no legal/page/identity review performed.',
        'sample_selection':['EO:23','EO:249','EO:254'],'local_collector_seconds':elapsed,
        'source_discovery_warnings':{k:v for k,v in results.items() if k.endswith('_warnings')},
        'cases':summaries,'new_ready_claims':0,'exact_pdf_and_text_hash_checks_passed':sum(s['raw_bytes_verified'] for s in summaries),
        'provisional_grade_or_identity_relabeling':False,
        'blocked_control':'EO:254 text_quality 0.31; page/identity/completeness confirmation remains blank, as in the other two cases.',
        'cost_limit':'Local collector timings are not a campaign throughput or end-to-end cost estimate. Source materialization, engineering, independent review and failed variants are not excluded from campaign cost.'}
(out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
