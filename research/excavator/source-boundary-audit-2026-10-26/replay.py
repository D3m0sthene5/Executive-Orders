"""Bounded same-source old/new parser replay; never files claims or edits outputs."""
import collections, csv, hashlib, json, subprocess, sys, time, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE='899671f30776c715f66141291125dd0fda9da202'
sys.path.insert(0,str(ROOT/'jobs/claim-kit'))
import excavate as new
old=types.ModuleType('boundary_old_replay');sys.modules[old.__name__]=old
exec(compile(subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':jobs/claim-kit/excavate.py']),'old-excavate.py','exec'),old.__dict__)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rows=list(csv.DictReader((OUT/'SCREEN.csv').open()));changes=[];seconds={'baseline':0.,'patched':0.};counts=collections.Counter()
    sample={x['instrument_id'] for x in json.loads((OUT/'SAMPLE.json').read_text())['cases']};examples={}
    for index,row in enumerate(rows):
        iid=row['instrument_id'];text=(ROOT/row['text_path']).read_bytes().decode();source={'page_or_item':'PDF pages 1','sha256':row['source_sha256'],'text_path':row['text_path']}
        result={}
        # Alternate order to avoid systematically favoring one parser's warm file cache.
        arms=[('baseline',old),('patched',new)]
        if index%2:arms.reverse()
        for name,mod in arms:
            start=time.monotonic();r=mod.segment(iid,text,source);terms=mod.own_terms(iid,text,source,r['clauses']);mentions=mod.discover_mentions(iid,text,source);seconds[name]+=time.monotonic()-start
            for c in r['clauses']:
                if text[c['char_start']:c['char_end']]!=c['text']:raise ValueError('Quote differs from raw text')
            result[name]={'inventory':r,'own_terms':terms,'mentions':mentions}
        a,b=result['baseline']['inventory']['clauses'],result['patched']['inventory']['clauses']
        changed=a!=b;counts['orders']+=1;counts['changed']+=changed;counts['unchanged']+=not changed
        loc=new._trailing_extent(iid,text)
        outside=bool(loc and any(c['char_start']<loc.doc_start or c['char_end']>loc.body_end for c in b))
        counts['patched_outside_bound']+=outside
        changes.append(dict(instrument_id=iid,changed=changed,baseline_clauses=len(a),patched_clauses=len(b),patched_locator_used=bool(loc),patched_outside_bound=outside,
                            text_path=row['text_path'],text_sha256=row['text_sha256'],source_sha256=row['source_sha256'],
                            old_term_count=len(result['baseline']['own_terms']),new_term_count=len(result['patched']['own_terms']),
                            old_mention_count=len(result['baseline']['mentions']),new_mention_count=len(result['patched']['mentions']),
                            old_mentioned_targets=sorted({v['target_id'] for v in result['baseline']['mentions']}),
                            new_mentioned_targets=sorted({v['target_id'] for v in result['patched']['mentions']})))
        if iid in sample or iid in {'EO:8083','EO:8123','EO:8126','EO:8992'}:examples[iid]=result
    (OUT/'REPLAY.json').write_text(json.dumps({'counts':dict(counts),'machine_seconds':seconds,'rows':changes,'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'jobs/claim-kit/excavate.py',ROOT/'jobs/clause-drafts/segment.py')},'not_agent_time':True,'not_complete_inventory_certification':True},indent=2)+'\n')
    (OUT/'REPLAY_EXAMPLES.json').write_text(json.dumps(examples,indent=2)+'\n')
    print(json.dumps({'counts':dict(counts),'machine_seconds':seconds}))
if __name__=='__main__':main()
