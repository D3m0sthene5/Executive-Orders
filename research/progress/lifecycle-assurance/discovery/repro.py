from pathlib import Path
import sys, tempfile, hashlib
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
import build, evidence_preflight
sys.path.insert(0,str(ROOT/'jobs/claim-checker'))
import checker
from types import SimpleNamespace

# Real selector used to reject/accept a candidate order text.
wrong='EXECUTIVE ORDER 8119\nSection 1. Florence Lake withdrawn.\n'
rec={'acceptable_as_original':True,'grade':'original_representation_unverified',
     'source':{'url':'https://example.gov/EO_8119.pdf','sha256':'a'*64}}
print('selector_explicit_wrong_order=',build.identity_conflict('EO:8123',rec,wrong))
class Copy: instrument_ids=['EO:8123']; origin='misattributed fixture'
class Index:
    def lookup_sha(self, sha): return [Copy()]
rows=[]
checker.check_identity({'sha256':'a'*64},'original_representation','EO:8123',SimpleNamespace(index=Index()),rows)
print('checker_identity_with_misattributed_registry=',[(r['result'],r['status']) for r in rows])

# The actual dossier preflight does detect that explicit marker if it sees this record.
with tempfile.TemporaryDirectory() as tmp:
    repo=Path(tmp); p=repo/'wrong.txt'; p.write_text(wrong,encoding='utf-8')
    sha=hashlib.sha256(wrong.encode()).hexdigest()
    d={'instrument_id':'EO:8123','original_source_id':'ORIGINAL:EO:8123','actor_provisions':[],
       'evidence':{'ORIGINAL:EO:8123':{'text':wrong,'char_start':0,'char_end':len(wrong),
          'source':{'url':'https://example.gov/EO_8119.pdf','sha256':'a'*64,'text_path':'wrong.txt','text_sha256':sha}}},
       'clauses':[{'char_start':0,'char_end':len(wrong)}]}
    print('preflight_explicit_wrong_order=',[t['kind'] for t in evidence_preflight.inspect(d,repo)['tasks']])

# The bounded inventory detector only compares numbered section headings.
body='Instrument: EO:2\nExecutive Order 2\nSection 1. Board established.\nThe Secretary shall separately issue instructions.\n'
with tempfile.TemporaryDirectory() as tmp:
    repo=Path(tmp); p=repo/'eo2.txt'; p.write_text(body,encoding='utf-8')
    sha=hashlib.sha256(body.encode()).hexdigest()
    a=body.index('Section 1.')
    omitted=body.index('The Secretary')
    d={'instrument_id':'EO:2','original_source_id':'ORIGINAL:EO:2','actor_provisions':[],
       'evidence':{'ORIGINAL:EO:2':{'text':body,'char_start':0,'char_end':len(body),
          'source':{'url':'https://example.gov/eo2','sha256':'b'*64,'text_path':'eo2.txt','text_sha256':sha}}},
       'clauses':[{'char_start':a,'char_end':omitted}]}
    result=evidence_preflight.inspect(d,repo)
    print('preflight_omitted_unnumbered_command_tasks=',[t['kind'] for t in result['tasks']])
