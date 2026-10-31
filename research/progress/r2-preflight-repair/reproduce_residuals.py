"""Exact two lifecycle-discovery fixtures against pinned main and R2."""
import hashlib, json, tempfile
from pathlib import Path
from compare import baseline, patched, HERE

def main():
    old, old_sha = baseline()
    rows = []
    fixtures = [('wrong_heading', 'EO:8123', 'EXECUTIVE ORDER 8119\nSection 1. Florence Lake withdrawn.\n'),
                ('omitted_unnumbered', 'EO:2', 'Instrument: EO:2\nExecutive Order 2\nSection 1. Board established.\nThe Secretary shall separately issue instructions.\n')]
    for name, iid, body in fixtures:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo/'text.txt').write_text(body)
            oid = 'ORIGINAL:'+iid
            a = 0 if name == 'wrong_heading' else body.index('Section 1.')
            b = len(body) if name == 'wrong_heading' else body.index('The Secretary')
            d = {'instrument_id':iid,'original_source_id':oid,'actor_provisions':[],
                 'evidence':{oid:{'text':body,'char_start':0,'char_end':len(body),
                                 'source':{'text_path':'text.txt','text_sha256':hashlib.sha256(body.encode()).hexdigest(),'sha256':'a'*64}}},
                 'clauses':[{'char_start':a,'char_end':b}]}
            rows.append({'fixture':name,'dossier':d,'baseline':old.inspect(d,repo),
                         'patched':patched.inspect(d,repo)})
    out = {'baseline_code_sha256':old_sha,'fixtures':rows}
    (HERE/'RESIDUAL_REPRO.json').write_text(json.dumps(out,indent=2)+'\n')
    print([(r['fixture'],[t['kind'] for t in r['baseline']['tasks']],
            [t['kind'] for t in r['patched']['tasks']]) for r in rows])

if __name__=='__main__':
    main()
